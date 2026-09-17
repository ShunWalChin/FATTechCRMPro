"""Fila de leads: quem precisa de atenção agora, e por quê.

A fila de tarefas responde "o que eu preciso fazer". Esta responde outra pergunta, que a
ordem separa de propósito: "qual lead está esfriando, estourou o prazo de primeira resposta,
ou entrou e ninguém assumiu". São conjuntos diferentes — um lead sem tarefa nenhuma é
invisível para a fila de tarefas e é exatamente o que mais se perde.

Os filtros são do servidor. Filtro de navegador sobre uma página de cinquenta registros mente
sobre o total, e o total é o que a pessoa usa para decidir se o dia está sob controle.
"""
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from .compliance import instant
from .db import get_db
from .lead_scoring import prazo_sla, sla_estourado
from .models import Record, User, now
from .security import require_auth
from .services import regras_de_lead, scoped

router = APIRouter(prefix="/api/v1/crm", tags=["leads"])
ESTAGIOS_ABERTOS = ("novo", "em_contato")


def momento(valor, alternativa=None):
    return instant(valor) or alternativa


def linha(registro: Record, regras: dict | None, agora: datetime, nomes: dict) -> dict:
    data = registro.data
    criado = registro.created_at or agora
    if criado.tzinfo is None:
        criado = criado.replace(tzinfo=timezone.utc)
    respondido = momento(data.get("first_response_at"))
    ultima = momento(data.get("last_interaction_at"), registro.updated_at)
    sla_horas = (regras or {}).get("sla_hours")
    resumo = data.get("score_breakdown") or {}
    proxima = momento(data.get("next_action_at"))
    return {
        "id": registro.id, "version": registro.version, "name": data.get("name", ""),
        "company": data.get("company", ""), "email": data.get("email"), "phone": data.get("phone", ""),
        "status": data.get("status"), "lead_stage": data.get("lead_stage", "novo"),
        "source": data.get("source", ""), "utm_source": data.get("utm_source", ""),
        "utm_medium": data.get("utm_medium", ""), "utm_campaign": data.get("utm_campaign", ""),
        "owner_id": data.get("owner_id"), "owner_name": nomes.get(data.get("owner_id"), ""),
        "score": data.get("score", 0),
        # Sem regra ativa nao existe temperatura: devolver "frio" seria afirmar uma classificacao
        # que ninguem fez, e a tela mostraria um julgamento inventado pelo servidor.
        "temperature": resumo.get("temperature"),
        "scored_by": resumo.get("rules_name"),
        "created_at": criado.isoformat(),
        "last_interaction_at": ultima.isoformat() if ultima else None,
        "first_response_at": respondido.isoformat() if respondido else None,
        "next_action_at": data.get("next_action_at"),
        "needs_action": not proxima or proxima <= agora,
        "unassigned": not data.get("owner_id"),
        "sla_deadline": prazo_sla(criado, sla_horas).isoformat() if sla_horas else None,
        "sla_breached": bool(sla_horas) and sla_estourado(criado, sla_horas, respondido, agora),
        "awaiting_first_response": respondido is None,
    }


@router.get("/leads")
def leads(principal=Depends(require_auth), db=Depends(get_db),
          q: str = Query("", max_length=200), owner_id: str = Query("", max_length=36),
          stage: Literal["all", "open", "novo", "em_contato", "qualificado",
                         "descartado", "convertido"] = "open",
          temperature: Literal["all", "quente", "morno", "frio", "sem_regra"] = "all",
          attention: Literal["all", "sem_responsavel", "sem_acao", "sla_estourado"] = "all",
          order: Literal["score", "sla", "recentes"] = "score",
          limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=10000)):
    principal.require("contacts:read")
    agora = now()
    regras = regras_de_lead(db, principal.tenant_id)
    nomes = {usuario.id: usuario.name for usuario in db.scalars(
        select(User).where(User.tenant_id == principal.tenant_id))}

    termo = q.strip().lower()
    registros = []
    for registro in db.scalars(scoped(principal.tenant_id, "contacts")):
        item = linha(registro, regras, agora, nomes)
        if stage == "open" and item["lead_stage"] not in ESTAGIOS_ABERTOS:
            continue
        if stage not in ("all", "open") and item["lead_stage"] != stage:
            continue
        if temperature == "sem_regra" and item["temperature"] is not None:
            continue
        if temperature not in ("all", "sem_regra") and item["temperature"] != temperature:
            continue
        if owner_id and item["owner_id"] != owner_id:
            continue
        if attention == "sem_responsavel" and not item["unassigned"]:
            continue
        if attention == "sem_acao" and not item["needs_action"]:
            continue
        if attention == "sla_estourado" and not item["sla_breached"]:
            continue
        if termo and termo not in " ".join(str(item.get(campo) or "") for campo in
                                          ("name", "company", "email", "phone", "utm_campaign")).lower():
            continue
        registros.append(item)

    chaves = {"score": lambda item: (-item["score"], item["created_at"]),
              "sla": lambda item: (not item["sla_breached"], item["sla_deadline"] or item["created_at"]),
              "recentes": lambda item: (item["created_at"],)}
    registros.sort(key=chaves[order], reverse=(order == "recentes"))

    # O resumo conta o conjunto filtrado inteiro, nao a pagina: e o numero que diz se o dia esta sob controle.
    resumo = {
        "sem_responsavel": sum(1 for item in registros if item["unassigned"]),
        "sem_acao": sum(1 for item in registros if item["needs_action"]),
        "sla_estourado": sum(1 for item in registros if item["sla_breached"]),
        "aguardando_resposta": sum(1 for item in registros if item["awaiting_first_response"]),
        "quente": sum(1 for item in registros if item["temperature"] == "quente"),
    }
    return {"items": registros[offset:offset + limit], "total": len(registros), "summary": resumo,
            "rules": {"name": regras.get("name"), "sla_hours": regras.get("sla_hours"),
                      "warm_at": regras.get("warm_at"), "hot_at": regras.get("hot_at"),
                      "assignment": regras.get("assignment", {}).get("strategy", "nenhuma")}
            if regras else None}


@router.get("/leads/{record_id}/score")
def explicar(record_id: str, principal=Depends(require_auth), db=Depends(get_db)):
    """A explicacao vem guardada do calculo, nao recalculada na leitura.

    Recalcular na leitura mostraria o score de hoje ao lado de decisoes tomadas ontem, e a pessoa
    concluiria que o sistema mudou de ideia sozinho.
    """
    principal.require("contacts:read")
    registro = db.scalar(scoped(principal.tenant_id, "contacts").where(Record.id == record_id))
    if registro is None:
        raise HTTPException(404, "Lead não encontrado")
    resumo = registro.data.get("score_breakdown")
    # explained separa "pontuou zero" de "ninguem pontuou": a tela precisa dizer coisas diferentes.
    return {"id": registro.id, "name": registro.data.get("name", ""),
            "score": registro.data.get("score", 0), "breakdown": resumo,
            "explained": resumo is not None}
