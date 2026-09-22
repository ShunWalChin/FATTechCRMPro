"""Operação de conteúdo da vertente FAT Tech Posiciona, dentro do CRM em vez de dentro do Excel.

A planilha de produção entregue com o material já resolve a parte fácil: escrever o que vai ao ar
e quando. O que ela não consegue fazer é a pergunta que paga a conta — **entregamos o que o
contrato diz?**. Frequência contratada mora na aba de clientes, o publicado mora na grade semanal,
e ninguém cruza as duas porque cruzar à mão, todo mês, por conta, não acontece. Aqui a comparação
é uma consulta.

Três decisões que a planilha não tomava e esta camada toma:

1. **Déficit é medido contra o contrato, não contra a meta.** Frequência zero desliga a comparação
   em vez de acusar déficit de zero: "sem frequência contratada" e "contratou zero" são estados
   diferentes, e tratá-los igual acusaria toda conta de vitrine de inadimplência.
2. **Publicado é o que tem data de publicação.** Status `publicado` sem `published_at` é recusado
   na escrita, então a apuração nunca precisa adivinhar o mês de uma peça.
3. **Pauta se gasta ao ser publicada, não ao ser escolhida.** A peça cancelada devolve a pauta ao
   banco; a planilha marcava "Usado? S" na escolha e perdia a ideia junto com a peça.
"""
from collections import Counter
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field
from sqlalchemy import select

from .db import get_db
from .models import Record, User
from .schemas import PILARES, StrictModel
from .security import require_auth
from .services import audit_event, create_record, get_record, scoped

router = APIRouter(prefix="/api/v1/content", tags=["conteudo"])
# Status que já consumiram trabalho de produção; o resto ainda é intenção.
EM_ANDAMENTO = ("producao", "aprovacao", "agendado")


def mes_valido(mes: str) -> str:
    try:
        datetime.strptime(mes, "%Y-%m")
    except ValueError:
        raise HTTPException(422, "Mês deve estar no formato AAAA-MM")
    return mes


def mes_de(valor) -> str:
    """Primeiros sete caracteres de um ISO-8601 são sempre AAAA-MM, com ou sem hora e fuso."""
    return str(valor or "")[:7]


class ImportacaoPautas(StrictModel):
    """`commit` falso devolve exatamente o que a confirmação gravaria — mesma contagem, mesmo corte."""
    pillars: list[str] = Field(default_factory=list, max_length=6)
    limit: int = Field(default=400, strict=True, ge=1, le=400)
    commit: bool = False


def banco_de_pautas() -> dict:
    import json
    import pathlib
    arquivo = pathlib.Path(__file__).resolve().parents[3] / "docs/knowledge/data/posiciona-pautas.json"
    if not arquivo.exists():
        raise HTTPException(503, "Banco de pautas não está publicado nesta instalação")
    return json.loads(arquivo.read_text(encoding="utf-8"))


@router.post("/pautas/importar")
def importar_pautas(payload: ImportacaoPautas, principal=Depends(require_auth), db=Depends(get_db)):
    """Carrega o banco de 330 pautas do material da vertente para dentro da organização.

    Reimportar não duplica: o título já existente é pulado e contado à parte, porque quem roda isto
    duas vezes quer saber que rodou duas vezes, não descobrir 660 pautas na tela.
    """
    principal.admin()
    documento = banco_de_pautas()
    pedidos = set(payload.pillars) or set(PILARES)
    if not pedidos.issubset(set(PILARES)):
        raise HTTPException(422, f"Pilar desconhecido; use {', '.join(PILARES)}")
    existentes = {(registro.data or {}).get("title") for registro in
                  db.scalars(scoped(principal.tenant_id, "content_ideas"))}
    candidatas = [ideia for ideia in documento["ideias"] if ideia["pillar"] in pedidos]
    disponiveis = [ideia for ideia in candidatas if ideia["title"] not in existentes]
    novas = disponiveis[:payload.limit]
    resumo = {"no_material": len(documento["ideias"]), "no_filtro": len(candidatas),
              "ja_existiam": len(candidatas) - len(disponiveis),
              "importadas": len(novas), "cortadas_pelo_limite": len(disponiveis) - len(novas),
              "por_pilar": dict(Counter(ideia["pillar"] for ideia in novas)),
              "commit": payload.commit}
    if not payload.commit:
        resumo["amostra"] = [ideia["title"] for ideia in novas[:5]]
        return resumo
    for ideia in novas:
        create_record(db, principal.tenant_id, principal.actor_id, "content_ideas",
                      {"title": ideia["title"], "pillar": ideia["pillar"], "format": ideia["format"],
                       "source": ideia["source"]}, role=principal.role)
    audit_event(db, principal.tenant_id, principal.actor_id, "content.ideas_imported",
                principal.tenant_id, {"importadas": len(novas), "por_pilar": resumo["por_pilar"]})
    db.commit()
    return resumo


@router.get("/indicadores")
def indicadores(principal=Depends(require_auth), db=Depends(get_db),
                mes: str = Query(default="", max_length=7)):
    """O que o mês prometeu, o que produziu e o que o contrato exigia — lado a lado.

    Conta sem frequência contratada aparece com `contratado: null` e sem déficit, e não some do
    relatório: uma conta que ninguém apura é exatamente a que fica meses sem entregar nada.
    """
    alvo = mes_valido(mes) if mes else datetime.now(timezone.utc).strftime("%Y-%m")
    contas = {registro.id: registro.data or {} for registro in
              db.scalars(scoped(principal.tenant_id, "content_accounts"))}
    pecas = [registro for registro in db.scalars(scoped(principal.tenant_id, "content_posts"))]
    # Uma peça pertence ao mês em que foi publicada; se ainda não foi, ao mês em que está agendada.
    do_mes = [registro for registro in pecas
              if mes_de((registro.data or {}).get("published_at")) == alvo
              or (not (registro.data or {}).get("published_at")
                  and mes_de((registro.data or {}).get("scheduled_at")) == alvo)]
    por_status = Counter((registro.data or {}).get("status", "planejado") for registro in do_mes)
    por_pilar = Counter((registro.data or {}).get("pillar", "storytelling") for registro in do_mes)
    ideias = [registro.data or {} for registro in db.scalars(scoped(principal.tenant_id, "content_ideas"))]

    linhas = []
    for conta_id, conta in contas.items():
        minhas = [registro for registro in do_mes if (registro.data or {}).get("account_id") == conta_id]
        publicadas = sum(1 for registro in minhas if (registro.data or {}).get("status") == "publicado")
        contratado = conta.get("contracted_posts_month") or 0
        linhas.append({
            "account_id": conta_id, "name": conta.get("name", ""), "network": conta.get("network", ""),
            "catalog_line": conta.get("catalog_line", ""), "status": conta.get("status", "active"),
            "contratado": contratado or None,
            "planejadas": sum(1 for r in minhas if (r.data or {}).get("status") == "planejado"),
            "em_andamento": sum(1 for r in minhas if (r.data or {}).get("status") in EM_ANDAMENTO),
            "publicadas": publicadas,
            "canceladas": sum(1 for r in minhas if (r.data or {}).get("status") == "cancelado"),
            # None quando não há frequência contratada: sem contrato não existe déficit a cobrar.
            "deficit": max(0, contratado - publicadas) if contratado else None,
        })
    linhas.sort(key=lambda linha: (linha["deficit"] is None, -(linha["deficit"] or 0), linha["name"]))
    sem_conta = sum(1 for registro in do_mes if not (registro.data or {}).get("account_id"))
    return {
        "mes": alvo,
        "contas": linhas,
        "pecas_no_mes": len(do_mes),
        "pecas_totais": len(pecas),
        "pecas_sem_conta": sem_conta,
        "por_status": {estado: por_status.get(estado, 0) for estado in
                       ("planejado", "producao", "aprovacao", "agendado", "publicado", "cancelado")},
        # Todo pilar aparece, inclusive com zero: pilar vazio é o achado, e some se só contar o que existe.
        "por_pilar": {pilar: por_pilar.get(pilar, 0) for pilar in PILARES},
        "banco_de_pautas": {
            "total": len(ideias),
            "disponiveis": sum(1 for ideia in ideias if not ideia.get("used")),
            "por_pilar_disponivel": {pilar: sum(1 for ideia in ideias
                                                if ideia.get("pillar") == pilar and not ideia.get("used"))
                                     for pilar in PILARES},
        },
        "contratado_total": sum(linha["contratado"] or 0 for linha in linhas),
        "deficit_total": sum(linha["deficit"] or 0 for linha in linhas),
        "contas_sem_frequencia": sum(1 for linha in linhas if linha["contratado"] is None),
    }


def marcar_pauta(db, principal, peca_anterior: dict, peca_nova: dict):
    """A pauta é gasta quando a peça publica, e devolvida quando a peça é cancelada.

    Chamado pelo caminho normal de escrita de `content_posts`; sem isto o banco de pautas seria um
    campo que alguém marca à mão — e um campo que alguém marca à mão não é um controle.
    """
    idea_id = peca_nova.get("idea_id") or peca_anterior.get("idea_id")
    if not idea_id:
        return
    antes, depois = peca_anterior.get("status"), peca_nova.get("status")
    if antes == depois:
        return
    if depois == "publicado":
        usar = True
    elif antes == "publicado" and depois == "cancelado":
        usar = False
    else:
        return
    try:
        registro = get_record(db, principal.tenant_id, "content_ideas", idea_id, lock=True)
    except HTTPException:
        # A pauta pode ter sido removida depois de a peça nascer; a peça continua válida.
        return
    if (registro.data or {}).get("used") == usar:
        return
    registro.data = {**registro.data, "used": usar}
    registro.version += 1
    audit_event(db, principal.tenant_id, principal.actor_id,
                "content.idea_used" if usar else "content.idea_released", idea_id, {"post_status": depois})


def register_content_ops(app):
    app.include_router(router)
