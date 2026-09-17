"""Contratos: do modelo ao aceite, com o texto de cada revisao preservado.

Um contrato nao e mais um registro do CRM. Tres coisas o separam do resto:

**O texto importa mais que o campo.** Guardar so a revisao corrente responde "o que vale hoje" e
nao responde "o que a outra parte leu quando concordou". Por isso cada mudanca de conteudo grava
uma revisao inteira, com o texto, em `contract_revisions` -- um kind que de proposito **nao** esta
em RESOURCES, porque um registro legal append-only nao pode ganhar PATCH e DELETE automaticos.

**Ativar exige aprovacao.** A cadeia de niveis vem do modelo e bloqueia a ativacao enquanto houver
nivel pendente. Um contrato que entra em vigor sem passar pelos niveis torna os niveis enfeite.

**Assinatura nao e simulada.** Nao ha provedor configurado, entao pedir assinatura responde 503 com
o motivo, como todo envio externo deste sistema. Registrar "assinado" sem assinatura seria a pior
mentira que um CRM pode contar.
"""
import re
from datetime import date, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request, Response
from pydantic import Field, StringConstraints, model_validator
from sqlalchemy import update

from . import approval_chain
from .db import get_db
from .idempotency import creation_receipt
from .models import Record, now
from .schemas import Cents, DateText, Identifier, Name, StrictModel, Text
from .security import require_auth
from .services import audit_event, get_record, scoped, serialize

router = APIRouter(prefix="/api/v1/contracts", tags=["contracts"])
VARIAVEL = re.compile(r"\{\{\s*([a-z][a-z0-9_]{0,39})\s*\}\}")
# draft escreve, in_review espera niveis, approved pode entrar em vigor, active vale hoje.
TRANSICOES = {
    "draft": {"in_review", "cancelled"},
    "in_review": {"draft", "approved", "cancelled"},
    "approved": {"active", "draft", "cancelled"},
    "active": {"terminated", "expired", "renewed"},
    "renewed": {"terminated", "expired"},
    "expired": {"renewed"},
    "terminated": set(),
    "cancelled": set(),
}
Estado = Literal[tuple(TRANSICOES)]


class Signer(StrictModel):
    name: Name
    email: Annotated[str, StringConstraints(strip_whitespace=True, max_length=320)]
    role: str = Field(default="", max_length=80)


class ContractCreate(StrictModel):
    title: Name
    template_id: Identifier | None = None
    company_id: Identifier | None = None
    contact_id: Identifier | None = None
    deal_id: Identifier | None = None
    proposal_id: Identifier | None = None
    owner_id: Identifier | None = None
    value_cents: Cents = 0
    recurrence: Literal["nenhuma", "mensal", "trimestral", "semestral", "anual"] = "nenhuma"
    starts_on: DateText | None = None
    ends_on: DateText | None = None
    renewal: Literal["nenhuma", "manual", "automatica"] = "manual"
    notice_days: int = Field(default=30, strict=True, ge=0, le=365)
    variables: dict = Field(default_factory=dict)
    signers: list[Signer] = Field(default_factory=list, max_length=10)
    documents: list[dict] = Field(default_factory=list, max_length=20)
    notes: Text = ""

    @model_validator(mode="after")
    def validate_vigencia(self):
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValueError("O fim da vigência não pode ser anterior ao início")
        if not self.company_id and not self.contact_id:
            # Um contrato sem parte identificada nao tem com quem valer.
            raise ValueError("Informe a empresa ou o contato com quem o contrato é firmado")
        return self


class ContractEdit(StrictModel):
    version: int = Field(strict=True, ge=1)
    title: Name | None = None
    owner_id: Identifier | None = None
    value_cents: Cents | None = None
    starts_on: DateText | None = None
    ends_on: DateText | None = None
    renewal: Literal["nenhuma", "manual", "automatica"] | None = None
    notice_days: int | None = Field(default=None, strict=True, ge=0, le=365)
    variables: dict | None = None
    signers: list[Signer] | None = None
    documents: list[dict] | None = None
    notes: Text | None = None
    reason: str = Field(default="", max_length=400)


class ContractTransition(StrictModel):
    version: int = Field(strict=True, ge=1)
    status: Estado
    reason: str = Field(default="", max_length=400)


class ChainDecision(StrictModel):
    version: int = Field(strict=True, ge=1)
    level: int = Field(strict=True, ge=1, le=6)
    decision: Literal["approved", "rejected"]
    reason: str = Field(default="", max_length=2000)


class Renewal(StrictModel):
    version: int = Field(strict=True, ge=1)
    months: int = Field(default=12, strict=True, ge=1, le=600)
    value_cents: Cents | None = None


def ler_caminho(dados: dict, caminho: str):
    alvo, _, folha = caminho.partition(".")
    valor = dados.get(alvo)
    if not folha:
        return valor
    return valor.get(folha) if isinstance(valor, dict) else None


def resolver_variaveis(db, tenant_id, modelo: dict, contrato: dict, manuais: dict) -> tuple[dict, list[str]]:
    """Le cada variavel da sua fonte. Devolve os valores e o que ficou faltando, sem inventar nada."""
    fontes = {"contract": contrato}
    for chave, kind in (("company", "companies"), ("contact", "contacts"),
                        ("deal", "deals"), ("proposal", "sales_proposals")):
        alvo = contrato.get(f"{chave}_id")
        if alvo:
            registro = db.scalar(scoped(tenant_id, kind).where(Record.id == alvo))
            if registro is not None:
                fontes[chave] = registro.data
    valores, faltando = {}, []
    for variavel in modelo.get("variables", []):
        chave = variavel["key"]
        if variavel["source"] == "manual":
            bruto = manuais.get(chave)
        else:
            bruto = ler_caminho(fontes.get(variavel["source"], {}), variavel["path"])
        texto = "" if bruto is None else str(bruto).strip()
        if not texto and variavel.get("required"):
            faltando.append(variavel["label"])
        valores[chave] = texto
    return valores, faltando


def montar(corpo: str, valores: dict) -> str:
    """Substitui {{chave}} pelo valor. Chave sem valor vira marca visivel, nunca some em silencio."""
    return VARIAVEL.sub(lambda achado: valores.get(achado.group(1)) or f"[{achado.group(1)} não informado]", corpo)


def gravar_revisao(db, tenant_id, contrato: Record, autor: str, motivo: str) -> int:
    """Append-only e fora de RESOURCES: o texto do que foi acordado nao ganha PATCH nem DELETE."""
    revisao = contrato.data.get("revision", 0) + 1
    db.add(Record(tenant_id=tenant_id, kind="contract_revisions", data={
        "contract_id": contrato.id, "revision": revisao, "content": contrato.data.get("content", ""),
        "value_cents": contrato.data.get("value_cents", 0), "status": contrato.data.get("status"),
        "created_by": autor, "reason": motivo[:400], "created_at": now().isoformat()}))
    return revisao


def dias_para_fim(dados: dict, hoje: date | None = None) -> int | None:
    fim = dados.get("ends_on")
    if not fim:
        return None
    try:
        return (date.fromisoformat(str(fim)[:10]) - (hoje or now().date())).days
    except ValueError:
        return None


def corpo_do_contrato(registro: Record) -> dict:
    dados = registro.data
    restantes = dias_para_fim(dados)
    aviso = dados.get("notice_days", 30)
    return {
        **serialize(registro),
        "approval": approval_chain.resumo(dados.get("approval")),
        "days_to_end": restantes,
        # Alerta e derivado, nunca guardado: resolver a vigencia faz o aviso sumir sozinho, e
        # nenhum processo de fundo precisa reconciliar uma fila de avisos com a realidade.
        "expiring": bool(dados.get("status") in ("active", "renewed") and restantes is not None
                         and 0 <= restantes <= aviso),
        "overdue": bool(dados.get("status") in ("active", "renewed") and restantes is not None
                        and restantes < 0),
    }


def guardar(db, principal, registro: Record, versao: int, dados: dict, acao: str, detalhes=None):
    resultado = db.execute(update(Record).where(Record.id == registro.id, Record.version == versao,
                                                Record.tenant_id == principal.tenant_id,
                                                Record.deleted.is_(False))
                           .values(data=dados, version=versao + 1, updated_at=now()))
    if resultado.rowcount != 1:
        raise HTTPException(409, "O contrato foi alterado por outra pessoa. Atualize e tente novamente.")
    audit_event(db, principal.tenant_id, principal.actor_id, acao, registro.id,
                {"version": versao + 1, **(detalhes or {})})
    db.commit()
    db.refresh(registro)
    return corpo_do_contrato(registro)


@router.post("", status_code=201)
def criar(payload: ContractCreate, response: Response,
          idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
          principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("contracts:write")
    receipt = None
    if idempotency_key is not None:
        receipt, replayed = creation_receipt(db, principal, "contracts", idempotency_key,
                                             payload.model_dump(mode="json"))
        response.headers["Idempotency-Replayed"] = str(replayed).lower()
        if replayed:
            resultado = receipt.response
            db.commit()
            return resultado

    dados = payload.model_dump(mode="json")
    modelo = None
    if payload.template_id:
        modelo = get_record(db, principal.tenant_id, "contract_templates", payload.template_id, share=True)
        if modelo.data.get("status") != "active":
            raise HTTPException(409, "Este modelo contratual está inativo")
    for campo, kind in (("company_id", "companies"), ("contact_id", "contacts"),
                        ("deal_id", "deals"), ("proposal_id", "sales_proposals")):
        if dados.get(campo):
            get_record(db, principal.tenant_id, kind, dados[campo], share=True)

    dados.update(status="draft", revision=0, content="", created_by=principal.actor_id,
                 signature={"status": "not_requested", "provider": "", "requested_at": None,
                            "signed_at": None},
                 template_name=modelo.data["name"] if modelo else "",
                 approval=approval_chain.nova(modelo.data.get("approval_levels", []) if modelo else []))
    if modelo and not dados.get("ends_on") and dados.get("starts_on"):
        meses = modelo.data.get("default_term_months", 12)
        inicio = date.fromisoformat(dados["starts_on"][:10])
        # Aproximacao declarada: meses de 30 dias. Vigencia exata e do juridico, nao do calendario nosso.
        dados["ends_on"] = (inicio + timedelta(days=30 * meses)).isoformat()
        dados["term_is_approximate"] = True
    if modelo:
        valores, faltando = resolver_variaveis(db, principal.tenant_id, modelo.data, dados, payload.variables)
        dados["variables"] = valores
        dados["missing_variables"] = faltando
        dados["content"] = montar(modelo.data["body"], valores)

    registro = Record(tenant_id=principal.tenant_id, kind="contracts", data=dados)
    db.add(registro)
    db.flush()
    # Reatribuir um dicionario novo, e nao mutar o que ja esta preso ao registro: SQLAlchemy nao
    # rastreia mutacao dentro de uma coluna JSON, entao o `revision` escrito no dicionario original
    # ficava so na resposta e o banco guardava zero -- a resposta afirmava o que nao fora gravado.
    registro.data = {**dados, "revision": gravar_revisao(db, principal.tenant_id, registro,
                                                         principal.actor_id, "criação")}
    dados = registro.data
    audit_event(db, principal.tenant_id, principal.actor_id, "contracts.created", registro.id,
                {"version": 1, "template_id": payload.template_id})
    resultado = corpo_do_contrato(registro)
    if receipt is not None:
        receipt.response = resultado
    db.commit()
    return resultado


class FromProposal(StrictModel):
    template_id: Identifier | None = None
    title: Name | None = None
    starts_on: DateText | None = None
    variables: dict = Field(default_factory=dict)


@router.post("/from-proposal/{proposal_id}", status_code=201)
def da_proposta(proposal_id: str, payload: FromProposal, request: Request,
                principal=Depends(require_auth), db=Depends(get_db)):
    """A proposta aceita e o unico ponto em que o contrato nasce com valor ja acordado.

    Exigir o aceite antes e o que impede um contrato existir a partir de um numero que o cliente
    ainda estava negociando -- e um contrato so tem uma chance de nascer com o valor certo.
    """
    principal.require("contracts:write")
    proposta = get_record(db, principal.tenant_id, "sales_proposals", proposal_id, share=True)
    if proposta.data.get("status") != "accepted":
        raise HTTPException(409, {"message": "Só uma proposta aceita vira contrato",
                                  "status": proposta.data.get("status")})
    existente = next((registro for registro in db.scalars(scoped(principal.tenant_id, "contracts"))
                      if registro.data.get("proposal_id") == proposal_id), None)
    if existente is not None:
        # Duas vias do mesmo acordo e a forma silenciosa de cobrar duas vezes.
        raise HTTPException(409, {"message": "Esta proposta já gerou um contrato",
                                  "contract_id": existente.id})
    corpo = ContractCreate(
        title=payload.title or f"Contrato · {proposta.data['title']}"[:200],
        template_id=payload.template_id,
        company_id=proposta.data.get("company_id"), contact_id=proposta.data.get("contact_id"),
        deal_id=proposta.data.get("deal_id"), proposal_id=proposta.id,
        owner_id=proposta.data.get("owner_id"), value_cents=proposta.data.get("total_cents", 0),
        starts_on=payload.starts_on, variables=payload.variables)
    return criar(corpo, Response(), None, principal, db)


@router.get("")
def listar(principal=Depends(require_auth), db=Depends(get_db),
           status: Estado | None = None, company_id: str | None = None, contact_id: str | None = None,
           attention: Literal["all", "expiring", "overdue", "awaiting_approval"] = "all",
           limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    principal.require("contracts:read")
    itens = []
    for registro in db.scalars(scoped(principal.tenant_id, "contracts").order_by(Record.created_at.desc())):
        corpo = corpo_do_contrato(registro)
        if status and corpo["status"] != status:
            continue
        if company_id and corpo.get("company_id") != company_id:
            continue
        if contact_id and corpo.get("contact_id") != contact_id:
            continue
        if attention == "expiring" and not corpo["expiring"]:
            continue
        if attention == "overdue" and not corpo["overdue"]:
            continue
        if attention == "awaiting_approval" and not (corpo["status"] == "in_review"
                                                     and corpo["approval"]["blocking"]):
            continue
        itens.append(corpo)
    resumo = {"expiring": sum(1 for item in itens if item["expiring"]),
              "overdue": sum(1 for item in itens if item["overdue"]),
              "awaiting_approval": sum(1 for item in itens if item["status"] == "in_review"),
              "active": sum(1 for item in itens if item["status"] in ("active", "renewed"))}
    return {"items": itens[offset:offset + limit], "total": len(itens), "summary": resumo}


@router.get("/{contract_id}")
def detalhar(contract_id: str, principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("contracts:read")
    return corpo_do_contrato(get_record(db, principal.tenant_id, "contracts", contract_id))


@router.get("/{contract_id}/revisions")
def revisoes(contract_id: str, principal=Depends(require_auth), db=Depends(get_db)):
    """O texto de cada revisao, do mais recente ao mais antigo. E o que responde o que foi acordado."""
    principal.require("contracts:read")
    get_record(db, principal.tenant_id, "contracts", contract_id)
    itens = [registro.data for registro in db.scalars(scoped(principal.tenant_id, "contract_revisions"))
             if registro.data.get("contract_id") == contract_id]
    itens.sort(key=lambda item: item["revision"], reverse=True)
    return {"items": itens, "total": len(itens)}


@router.patch("/{contract_id}")
def editar(contract_id: str, payload: ContractEdit, principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("contracts:write")
    registro = get_record(db, principal.tenant_id, "contracts", contract_id, lock=True)
    if registro.version != payload.version:
        raise HTTPException(409, "O contrato foi alterado por outra pessoa. Atualize e tente novamente.")
    if registro.data["status"] not in ("draft", "in_review"):
        # Editar o que ja foi aprovado desfaz a aprovacao sem que ninguem perceba.
        raise HTTPException(409, "Só um contrato em rascunho ou em revisão pode ser editado")
    mudancas = {campo: valor for campo, valor in payload.model_dump(mode="json").items()
                if valor is not None and campo not in ("version", "reason")}
    if not mudancas:
        raise HTTPException(422, "Informe ao menos um campo para alterar")
    dados = {**registro.data, **mudancas}
    if dados.get("starts_on") and dados.get("ends_on") and dados["ends_on"] < dados["starts_on"]:
        raise HTTPException(422, "O fim da vigência não pode ser anterior ao início")
    if payload.variables is not None and registro.data.get("template_id"):
        modelo = get_record(db, principal.tenant_id, "contract_templates",
                            registro.data["template_id"], share=True)
        valores, faltando = resolver_variaveis(db, principal.tenant_id, modelo.data, dados, payload.variables)
        dados.update(variables=valores, missing_variables=faltando,
                     content=montar(modelo.data["body"], valores))
    registro.data = dados
    dados["revision"] = gravar_revisao(db, principal.tenant_id, registro, principal.actor_id,
                                       payload.reason or "edição")
    return guardar(db, principal, registro, payload.version, dados, "contracts.updated",
                   {"fields": sorted(mudancas), "revision": dados["revision"]})


@router.post("/{contract_id}/status")
def transicionar(contract_id: str, payload: ContractTransition,
                 principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("contracts:write")
    registro = get_record(db, principal.tenant_id, "contracts", contract_id, lock=True)
    if registro.version != payload.version:
        raise HTTPException(409, "O contrato foi alterado por outra pessoa. Atualize e tente novamente.")
    atual = registro.data["status"]
    if payload.status not in TRANSICOES[atual]:
        raise HTTPException(409, f"Transição de {atual} para {payload.status} não é permitida")
    if payload.status == "in_review" and registro.data.get("missing_variables"):
        raise HTTPException(409, {"message": "O contrato tem variáveis obrigatórias sem valor",
                                  "missing": registro.data["missing_variables"]})
    if payload.status == "approved" and approval_chain.resumo(registro.data.get("approval"))["blocking"]:
        raise HTTPException(409, {"message": "Ainda há nível de aprovação pendente",
                                  "approval": approval_chain.resumo(registro.data.get("approval"))})
    if payload.status == "active" and not registro.data.get("starts_on"):
        raise HTTPException(409, "Um contrato em vigor precisa de data de início")
    dados = {**registro.data, "status": payload.status,
             f"{payload.status}_at": now().isoformat(), "updated_by": principal.actor_id}
    if payload.reason:
        dados[f"{payload.status}_reason"] = payload.reason
    return guardar(db, principal, registro, payload.version, dados, f"contracts.{payload.status}",
                   {"from": atual, "reason": payload.reason})


@router.post("/{contract_id}/approval")
def decidir(contract_id: str, payload: ChainDecision, principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("contracts:write")
    registro = get_record(db, principal.tenant_id, "contracts", contract_id, lock=True)
    if registro.version != payload.version:
        raise HTTPException(409, "O contrato foi alterado por outra pessoa. Atualize e tente novamente.")
    if registro.data["status"] != "in_review":
        raise HTTPException(409, "Só um contrato em revisão recebe decisão de aprovação")
    cadeia = approval_chain.decidir(registro.data.get("approval") or approval_chain.nova([]),
                                    level=payload.level, actor_id=principal.actor_id,
                                    role=principal.role, decision=payload.decision,
                                    reason=payload.reason)
    dados = {**registro.data, "approval": cadeia}
    if cadeia["status"] == approval_chain.RECUSADA:
        # Recusa devolve ao rascunho: seguir "em revisão" depois de um não esconde o não.
        dados["status"] = "draft"
        dados["rejected_at"] = now().isoformat()
    return guardar(db, principal, registro, payload.version, dados,
                   f"contracts.approval_{payload.decision}",
                   {"level": payload.level, "chain": cadeia["status"]})


@router.post("/{contract_id}/renew")
def renovar(contract_id: str, payload: Renewal, principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("contracts:write")
    registro = get_record(db, principal.tenant_id, "contracts", contract_id, lock=True)
    if registro.version != payload.version:
        raise HTTPException(409, "O contrato foi alterado por outra pessoa. Atualize e tente novamente.")
    if registro.data["status"] not in ("active", "expired", "renewed"):
        raise HTTPException(409, "Só um contrato vigente ou vencido pode ser renovado")
    if registro.data.get("renewal") == "nenhuma":
        raise HTTPException(409, "Este contrato foi firmado sem renovação")
    fim = registro.data.get("ends_on")
    base = date.fromisoformat(fim[:10]) if fim else now().date()
    dados = {**registro.data, "status": "renewed",
             "starts_on": (base + timedelta(days=1)).isoformat(),
             # Mesma aproximacao de trinta dias por mes, e declarada pelo mesmo motivo.
             "ends_on": (base + timedelta(days=30 * payload.months)).isoformat(),
             "term_is_approximate": True, "renewed_at": now().isoformat(),
             "renewal_count": registro.data.get("renewal_count", 0) + 1,
             "previous_ends_on": fim, "updated_by": principal.actor_id}
    if payload.value_cents is not None:
        dados["value_cents"] = payload.value_cents
    registro.data = dados
    dados["revision"] = gravar_revisao(db, principal.tenant_id, registro, principal.actor_id,
                                       f"renovação por {payload.months} meses")
    return guardar(db, principal, registro, payload.version, dados, "contracts.renewed",
                   {"months": payload.months, "count": dados["renewal_count"]})


@router.post("/{contract_id}/signature")
def assinar(contract_id: str, request: Request, payload: dict = Body(default_factory=dict),
            principal=Depends(require_auth), db=Depends(get_db)):
    """Preparado, nao ligado. Sem provedor configurado isto recusa com motivo, como todo envio externo.

    Registrar 'assinado' sem assinatura seria a pior mentira que um CRM pode contar, entao a rota
    existe para provar o caminho e recusar no ponto exato onde faltaria o provedor.
    """
    principal.require("contracts:write")
    registro = get_record(db, principal.tenant_id, "contracts", contract_id)
    if registro.data["status"] not in ("approved", "active"):
        raise HTTPException(409, "Só um contrato aprovado pode ir para assinatura")
    if not registro.data.get("signers"):
        raise HTTPException(422, "Informe ao menos um signatário antes de pedir assinatura")
    provedor = getattr(request.app.state.settings, "signature_provider", "")
    audit_event(db, principal.tenant_id, principal.actor_id, "contracts.signature_refused", registro.id,
                {"signers": len(registro.data["signers"]), "reason": "no_provider"})
    db.commit()
    raise HTTPException(503, {"message": "Nenhum provedor de assinatura eletrônica está configurado. "
                                         "O contrato está pronto para assinatura e nada foi enviado.",
                              "provider": provedor, "ready": True,
                              "signers": [s["email"] for s in registro.data["signers"]]})


def register_contracts(app):
    app.include_router(router)
