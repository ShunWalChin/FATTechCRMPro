"""Rotas do agente: catalogo de ferramentas, identidade e leitura das corridas.

Estagio E1 do projeto em docs/OPENCLAW_BLUEPRINT.md. O que **nao** esta aqui, de proposito: nada
escreve em `agent_runs` ainda. O portao de execucao que grava corrida e passo e o E2, e chamar isto
de agente funcionando antes disso seria exatamente o que o §10 da ordem proibe.

O que E1 entrega e verificavel: o catalogo existe e bate com os escopos, a identidade nasce com
papel proprio, e a chave do agente e recusada em toda operacao administrativa -- nao por regra nova,
mas porque `Principal.admin()` recusa qualquer chave de API.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import Field
from sqlalchemy import func, select

from . import agent_dispatch, agent_gate, agent_identity, agent_tools
from .db import get_db
from .models import AgentRun, AgentStep, ApiKey, Tenant, User, now
from typing import Literal

from .schemas import StrictModel
from .security import require_auth
from .services import audit_event, get_record, scoped

router = APIRouter(prefix="/api/v1/agent", tags=["agente"])


class Provisionamento(StrictModel):
    """As ferramentas sao a lista de permissao. Vazia e recusada: um agente sem ferramenta nao opera,
    e emitir chave sem escopo produziria uma credencial que parece funcionar e nao faz nada."""
    agent_id: str = Field(min_length=1, max_length=36)
    tools: list[str] = Field(min_length=1, max_length=200)


@router.get("/tools")
def tools(principal=Depends(require_auth)):
    """O catalogo derivado. Toda pessoa autenticada le: saber o que um agente *pode* fazer nao é
    privilegio administrativo, e esconder isso da equipe seria esconder o alcance do automatismo."""
    principal.require("agents:read")
    return agent_tools.catalogo_publicado()


@router.post("/identity", status_code=201)
def identity(payload: Provisionamento, principal=Depends(require_auth), db=Depends(get_db)):
    """Emite a identidade e a chave do agente. Exige administrador — e nega chave de API.

    Um agente provisionando outro agente seria escalada de privilégio silenciosa: `admin()` já
    recusa qualquer chave, então essa porta está fechada pelo mesmo mecanismo que fecha as outras.
    """
    principal.admin()
    tenant = db.get(Tenant, principal.tenant_id)
    resultado = agent_identity.provisionar(db, principal, tenant.slug if tenant else "fattech",
                                           payload.agent_id, payload.tools)
    db.commit()
    return resultado


@router.get("/identity/{agent_id}")
def identity_status(agent_id: str, principal=Depends(require_auth), db=Depends(get_db)):
    """Estado da identidade, sem nunca devolver o token — só o prefixo e a validade."""
    principal.admin()
    usuario = agent_identity.usuario_do_agente(db, principal.tenant_id, agent_id)
    if usuario is None:
        return {"agent_id": agent_id, "provisionado": False, "chaves": []}
    chaves = list(db.scalars(select(ApiKey).where(ApiKey.created_by == usuario.id)))
    return {
        "agent_id": agent_id, "provisionado": True, "user_id": usuario.id, "email": usuario.email,
        "role": usuario.role, "is_agent": usuario.is_agent, "active": usuario.active,
        "chaves": [{"id": chave.id, "prefix": chave.prefix, "scopes": chave.scopes,
                    "revoked": chave.revoked, "expires_at": chave.expires_at.isoformat()}
                   for chave in chaves],
        "chaves_ativas": sum(1 for chave in chaves if not chave.revoked),
    }


@router.delete("/identity/{agent_id}")
def disable_identity(agent_id: str, principal=Depends(require_auth), db=Depends(get_db)):
    """Desliga o agente: revoga toda chave ativa dele e desativa o usuário.

    Existe porque `DELETE /api/v1/api-keys/{id}` não alcança: `can_manage` exige patente
    estritamente maior e o agente é `root`, então nem o owner que o criou conseguia revogar a chave.
    A exceção vale só para `is_agent` — contenção de automatismo não pode depender de superar a
    patente do automatismo, e isso não afrouxa a regra de patente entre pessoas.
    """
    principal.admin()
    resultado = agent_identity.desligar(db, principal, agent_id)
    db.commit()
    return resultado


class AberturaDeCorrida(StrictModel):
    """O evento que disparou é obrigatório: é ele que a unicidade do banco usa para deduplicar.

    `rationale` também é obrigatório, e não por formalidade. Uma corrida sem justificativa declarada
    deixa a trilha respondendo o que aconteceu e nunca por quê, que é a pergunta que o cliente faz
    sobre ação autônoma.
    """
    agent_id: str = Field(min_length=1, max_length=36)
    trigger_event_id: str = Field(min_length=1, max_length=36)
    trigger_type: str = Field(min_length=1, max_length=100)
    rationale: str = Field(min_length=1, max_length=20000)
    model: str = Field(default="", max_length=120)


class Tentativa(StrictModel):
    run_id: str = Field(min_length=1, max_length=36)
    tool: str = Field(min_length=1, max_length=120)
    arguments: dict = Field(default_factory=dict)


class Fechamento(StrictModel):
    status: Literal["done", "failed", "degraded", "refused"] = "done"
    tokens_in: int = Field(default=0, strict=True, ge=0, le=100_000_000)
    tokens_out: int = Field(default=0, strict=True, ge=0, le=100_000_000)
    cost_cents: int = Field(default=0, strict=True, ge=0, le=100_000_000)
    error: str = Field(default="", max_length=20000)


def configuracao_do_agente(db, principal, agent_id: str) -> dict:
    return get_record(db, principal.tenant_id, "agents", agent_id).data or {}


def corrida_ou_404(db, principal, run_id: str) -> AgentRun:
    corrida = db.scalar(select(AgentRun).where(AgentRun.id == run_id,
                                               AgentRun.tenant_id == principal.tenant_id))
    if corrida is None:
        raise HTTPException(404, "Corrida não encontrada")
    return corrida


@router.post("/runs", status_code=201)
def open_run(payload: AberturaDeCorrida, principal=Depends(require_auth), db=Depends(get_db)):
    """Abre uma corrida para um evento. O mesmo evento nunca abre duas.

    A entrega do outbox é **pelo menos uma vez**, então o replay é esperado, não excepcional. Em vez
    de erro, o replay recebe a corrida que já existe — o agente que reprocessa um evento descobre
    isso em vez de falhar, e nenhum efeito acontece duas vezes.
    """
    principal.require("agent:operate")
    configuracao = configuracao_do_agente(db, principal, payload.agent_id)
    existente = db.scalar(select(AgentRun).where(
        AgentRun.tenant_id == principal.tenant_id, AgentRun.agent_id == payload.agent_id,
        AgentRun.trigger_event_id == payload.trigger_event_id))
    if existente is not None:
        return {**resumo_da_corrida(existente), "replay": True,
                "nota": "Este evento já abriu uma corrida; nada foi executado de novo."}
    corrida = AgentRun(tenant_id=principal.tenant_id, agent_id=payload.agent_id,
                       trigger_event_id=payload.trigger_event_id, trigger_type=payload.trigger_type,
                       mode=configuracao.get("mode") or "sugestao", status="planning",
                       rationale=payload.rationale, model=payload.model or configuracao.get("model", ""))
    db.add(corrida)
    db.flush()
    audit_event(db, principal.tenant_id, principal.actor_id, "agent.run_opened", corrida.id,
                {"agent_id": payload.agent_id, "trigger_event_id": payload.trigger_event_id,
                 "trigger_type": payload.trigger_type, "mode": corrida.mode})
    db.commit()
    return {**resumo_da_corrida(corrida), "replay": False}


@router.post("/act")
def act(payload: Tentativa, request: Request, principal=Depends(require_auth), db=Depends(get_db)):
    """Uma tentativa do agente. Sempre devolve 200 e **sempre** grava o passo.

    Recusa de portão não é erro de protocolo: é resultado. Devolvê-la como 4xx faria o agente tratar
    uma decisão de negócio como falha de rede e reenviar, e a recusa que deveria contê-lo viraria um
    laço de tentativas.
    """
    principal.require("agent:operate")
    corrida = corrida_ou_404(db, principal, payload.run_id)
    if corrida.finished_at is not None:
        raise HTTPException(409, "Esta corrida já foi encerrada")
    configuracao = configuracao_do_agente(db, principal, corrida.agent_id)
    resultado = agent_gate.agir(db, principal, corrida, configuracao, payload.tool,
                                payload.arguments, request.app.state.settings)
    if corrida.status == "planning":
        corrida.status = "executing"
    db.commit()
    return resultado


@router.post("/runs/{run_id}/finish")
def finish_run(run_id: str, payload: Fechamento, principal=Depends(require_auth), db=Depends(get_db)):
    """Encerra a corrida com o custo declarado pelo agente.

    O custo entra aqui e é somado na leitura, nunca acumulado num contador: `spent_cents` do agente
    continua gravado como zero, e o gasto do mês é derivado das corridas.
    """
    principal.require("agent:operate")
    corrida = corrida_ou_404(db, principal, run_id)
    if corrida.finished_at is not None:
        raise HTTPException(409, "Esta corrida já foi encerrada")
    corrida.status = payload.status
    corrida.tokens_in, corrida.tokens_out = payload.tokens_in, payload.tokens_out
    corrida.cost_cents = payload.cost_cents
    corrida.error = payload.error or None
    corrida.finished_at = now()
    audit_event(db, principal.tenant_id, principal.actor_id, "agent.run_finished", corrida.id,
                {"status": payload.status, "cost_cents": payload.cost_cents})
    db.commit()
    return resumo_da_corrida(corrida)


@router.post("/steps/{step_id}/apply")
def apply_suggestion(step_id: str, principal=Depends(require_auth), db=Depends(get_db)):
    """Uma **pessoa** aplica o rascunho que o agente propôs. Chave de API é recusada aqui.

    O agente sugeriu; quem aplica é o autor do que acontece, e a trilha registra o nome dela. Deixar
    o agente aplicar o próprio rascunho seria devolver a ele escrita sem modo de execução, por um
    caminho lateral — a mesma forma de `fattech:aprovacao:segregacao-de-funcoes`: quem propõe não
    decide.
    """
    if principal.key:
        raise HTTPException(403, "Aplicar um rascunho é decisão de uma pessoa, não do agente")
    principal.require("agents:read")
    passo = db.scalar(select(AgentStep).where(AgentStep.id == step_id,
                                              AgentStep.tenant_id == principal.tenant_id))
    if passo is None:
        raise HTTPException(404, "Passo não encontrado")
    corrida = corrida_ou_404(db, principal, passo.run_id)
    resultado = agent_gate.aplicar_sugestao(db, principal, passo, corrida)
    db.commit()
    return resultado


def resumo_da_corrida(corrida: AgentRun, passos: int = 0, recusados: int = 0) -> dict:
    return {"id": corrida.id, "agent_id": corrida.agent_id, "mode": corrida.mode,
            "status": corrida.status, "trigger_type": corrida.trigger_type,
            "trigger_event_id": corrida.trigger_event_id, "model": corrida.model,
            "cost_cents": corrida.cost_cents, "tokens_in": corrida.tokens_in,
            "tokens_out": corrida.tokens_out, "started_at": corrida.started_at.isoformat(),
            "finished_at": corrida.finished_at.isoformat() if corrida.finished_at else None,
            "error": corrida.error, "passos": passos, "passos_recusados": recusados}


class Reclamacao(StrictModel):
    """Quantas corridas o agente quer de uma vez. O limite existe para que um agente lento não
    reclame a fila inteira e a deixe presa em `planning` enquanto processa uma por uma."""
    agent_id: str = Field(min_length=1, max_length=36)
    limit: int = Field(default=5, strict=True, ge=1, le=25)


@router.post("/runs/claim")
def claim_runs(payload: Reclamacao, principal=Depends(require_auth), db=Depends(get_db)):
    """O agente reclama as corridas que o evento criou para ele. É o E4: ele acorda sozinho.

    O CRM **não empurra** trabalho para o OpenClaw — ver o cabeçalho de `agent_dispatch.py`. Puxar
    evita um segundo mecanismo de entrega ao lado do outbox e dá o modo degradado de graça: agente
    fora do ar, as corridas ficam em `pending` e ele recupera o atraso quando voltar.

    A resposta traz a fila **depois** da reclamação, com a idade da mais antiga. A contagem sozinha
    não diz se a operação está saudável: dez corridas de um minuto atrás é normal; uma de seis horas
    atrás é um agente que morreu.
    """
    principal.require("agent:operate")
    configuracao = configuracao_do_agente(db, principal, payload.agent_id)
    if configuracao.get("status") != "active":
        # Recusa explícita em vez de lista vazia: "não há trabalho" e "você está pausado" são
        # estados diferentes, e devolver vazio faria o agente esperar por uma fila que nunca vem.
        raise HTTPException(409, "Este agente está pausado e não recebe trabalho")
    corridas = agent_dispatch.reclamar(db, principal, payload.agent_id, payload.limit)
    for corrida in corridas:
        audit_event(db, principal.tenant_id, principal.actor_id, "agent.run_claimed", corrida.id,
                    {"agent_id": payload.agent_id, "trigger_type": corrida.trigger_type,
                     "trigger_event_id": corrida.trigger_event_id})
    db.commit()
    return {"items": [{**resumo_da_corrida(corrida), "trigger_event_id": corrida.trigger_event_id}
                      for corrida in corridas],
            "total": len(corridas),
            "fila": agent_dispatch.fila_do_agente(db, principal.tenant_id, payload.agent_id)}


@router.get("/{agent_id}/queue")
def queue(agent_id: str, principal=Depends(require_auth), db=Depends(get_db)):
    """A fila do agente, para a tela e para quem opera. Não reclama nada; só mede."""
    principal.require("agents:read")
    configuracao = configuracao_do_agente(db, principal, agent_id)
    fila = agent_dispatch.fila_do_agente(db, principal.tenant_id, agent_id)
    presas = list(db.scalars(select(AgentRun).where(
        AgentRun.tenant_id == principal.tenant_id, AgentRun.agent_id == agent_id,
        AgentRun.status == "planning")))
    return {"agent_id": agent_id, "status": configuracao.get("status", "paused"),
            "mode": configuracao.get("mode", "sugestao"),
            "triggers": configuracao.get("triggers") or [], **fila,
            # Corrida reclamada que não voltou. Não há reciclagem automática neste estágio, e
            # declarar o número é melhor que fingir que o problema não existe.
            "reclamadas_sem_retorno": len(presas)}


@router.get("/suggestions")
def suggestions(principal=Depends(require_auth), db=Depends(get_db),
                limit: int = Query(50, ge=1, le=200)):
    """Os rascunhos que esperam uma pessoa, com o contexto que permite decidir sem abrir a corrida.

    Um rascunho que só existe dentro do detalhe de uma execução é um rascunho que ninguém encontra.
    Cada item traz a justificativa da corrida junto, porque a pergunta de quem vai aplicar é sempre
    a mesma: *por que o agente propôs isto?*

    `pendentes` conta o conjunto inteiro, não a página: quem olha este número decide se o dia está
    sob controle, e um total que é o tamanho da página mente sobre isso.
    """
    principal.require("agents:read")
    condicoes = (AgentStep.tenant_id == principal.tenant_id,
                 AgentStep.decision == "suggested", AgentStep.result_ref == "")
    total = db.scalar(select(func.count()).select_from(AgentStep).where(*condicoes)) or 0
    passos = list(db.scalars(select(AgentStep).where(*condicoes)
                             .order_by(AgentStep.created_at.desc()).limit(limit)))
    corridas = {}
    if passos:
        corridas = {corrida.id: corrida for corrida in db.scalars(
            select(AgentRun).where(AgentRun.tenant_id == principal.tenant_id,
                                   AgentRun.id.in_([passo.run_id for passo in passos])))}
    nomes = {registro.id: (registro.data or {}).get("name", "")
             for registro in db.scalars(scoped(principal.tenant_id, "agents"))}
    items = []
    for passo in passos:
        corrida = corridas.get(passo.run_id)
        items.append({
            "step_id": passo.id, "run_id": passo.run_id, "seq": passo.seq, "tool": passo.tool,
            "arguments": passo.arguments, "created_at": passo.created_at.isoformat(),
            "agent_id": corrida.agent_id if corrida else "",
            "agent_name": nomes.get(corrida.agent_id, "") if corrida else "",
            "trigger_type": corrida.trigger_type if corrida else "",
            "rationale": corrida.rationale if corrida else "",
        })
    return {"items": items, "total": total, "pendentes": total}


@router.get("/runs")
def runs(principal=Depends(require_auth), db=Depends(get_db),
         agent_id: str = Query(default="", max_length=36),
         status: str = Query(default="", max_length=24),
         limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    """As corridas, mais recentes primeiro. O total conta o conjunto filtrado, nunca a página.

    Uma lista paginada cujo total é o tamanho da página mente sobre a operação, e é por isso que o
    resumo aqui é calculado sobre o filtro inteiro.
    """
    principal.require("agents:read")
    condicoes = [AgentRun.tenant_id == principal.tenant_id]
    if agent_id:
        condicoes.append(AgentRun.agent_id == agent_id)
    if status:
        condicoes.append(AgentRun.status == status)
    total = db.scalar(select(func.count()).select_from(AgentRun).where(*condicoes))
    corridas = list(db.scalars(select(AgentRun).where(*condicoes)
                               .order_by(AgentRun.started_at.desc()).limit(limit).offset(offset)))
    # Uma consulta para todos os passos da página, em vez de uma por corrida.
    contagem = {}
    if corridas:
        for run_id, decisao, quantos in db.execute(
                select(AgentStep.run_id, AgentStep.decision, func.count())
                .where(AgentStep.tenant_id == principal.tenant_id,
                       AgentStep.run_id.in_([corrida.id for corrida in corridas]))
                .group_by(AgentStep.run_id, AgentStep.decision)).all():
            alvo = contagem.setdefault(run_id, {"total": 0, "refused": 0})
            alvo["total"] += quantos
            if decisao == "refused":
                alvo["refused"] += quantos
    gasto = db.scalar(select(func.coalesce(func.sum(AgentRun.cost_cents), 0))
                      .where(*condicoes)) or 0
    return {
        "items": [resumo_da_corrida(corrida,
                                    contagem.get(corrida.id, {}).get("total", 0),
                                    contagem.get(corrida.id, {}).get("refused", 0))
                  for corrida in corridas],
        "total": total,
        "gasto_cents": gasto,
        "por_status": {estado: quantos for estado, quantos in db.execute(
            select(AgentRun.status, func.count()).where(*condicoes).group_by(AgentRun.status)).all()},
    }


@router.get("/runs/{run_id}")
def run(run_id: str, principal=Depends(require_auth), db=Depends(get_db)):
    """A corrida inteira: evento que disparou, justificativa, e cada passo — inclusive os recusados.

    A cadeia de hash da trilha responde o que aconteceu e quem fez. `rationale` responde por quê, e
    junto com `trigger_event_id` fecha a pergunta que um cliente faz sobre ação autônoma.

    Declaração que acompanha o campo e precisa acompanhar o produto: a justificativa é o que o
    modelo declarou ter pensado, não prova do que pensou. Serve para auditar decisão, não para
    atribuir intenção.
    """
    principal.require("agents:read")
    corrida = db.scalar(select(AgentRun).where(AgentRun.id == run_id,
                                               AgentRun.tenant_id == principal.tenant_id))
    if corrida is None:
        raise HTTPException(404, "Corrida não encontrada")
    passos = list(db.scalars(select(AgentStep).where(AgentStep.tenant_id == principal.tenant_id,
                                                    AgentStep.run_id == run_id)
                             .order_by(AgentStep.seq.asc())))
    return {
        **resumo_da_corrida(corrida, len(passos),
                            sum(1 for passo in passos if passo.decision == "refused")),
        "rationale": corrida.rationale,
        "rationale_nota": ("O que o modelo declarou ter pensado, não prova do que pensou."),
        "steps": [{"seq": passo.seq, "tool": passo.tool, "arguments": passo.arguments,
                   "decision": passo.decision, "refusal_reason": passo.refusal_reason,
                   "result_ref": passo.result_ref, "created_at": passo.created_at.isoformat()}
                  for passo in passos],
    }


@router.get("/{agent_id}/budget")
def budget(agent_id: str, principal=Depends(require_auth), db=Depends(get_db),
           month: str = Query(default="", max_length=7)):
    """Gasto do mês, **derivado** da soma de agent_runs. Nunca há contador gravado.

    Teto igual a zero é devolvido como `null` e com `teto_declarado: false`: "ninguém declarou" e
    "zero" são estados diferentes, e o portão do E3 recusa executar no primeiro caso em vez de
    tratá-lo como ilimitado.
    """
    principal.require("agents:read")
    from datetime import datetime, timezone
    registro = next((r for r in db.scalars(scoped(principal.tenant_id, "agents")) if r.id == agent_id), None)
    if registro is None:
        raise HTTPException(404, "Agente não encontrado")
    dados = registro.data or {}
    alvo = month or datetime.now(timezone.utc).strftime("%Y-%m")
    if len(alvo) != 7 or alvo[4] != "-":
        raise HTTPException(422, "Mês deve estar no formato AAAA-MM")
    gasto = 0
    corridas = 0
    for corrida in db.scalars(select(AgentRun).where(AgentRun.tenant_id == principal.tenant_id,
                                                     AgentRun.agent_id == agent_id)):
        if corrida.started_at.isoformat()[:7] == alvo:
            gasto += corrida.cost_cents
            corridas += 1
    teto = dados.get("budget_month_cents") or 0
    return {"agent_id": agent_id, "month": alvo, "gasto_cents": gasto, "corridas": corridas,
            "teto_cents": teto or None, "teto_declarado": bool(teto),
            "restante_cents": max(0, teto - gasto) if teto else None,
            "max_actions_per_hour": dados.get("max_actions_per_hour") or None,
            "mode": dados.get("mode", "sugestao"), "status": dados.get("status", "paused")}


def register_agent_api(app):
    app.include_router(router)
