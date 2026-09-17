"""Contas Instagram por organizacao, com o token guardado cifrado e nunca devolvido.

Uma conta Instagram pertence a exatamente uma organizacao: a unicidade de
instagram_user_id e uma restricao do banco, e nao uma checagem de aplicacao, porque
e ela que deixa o webhook resolver o tenant sem confiar em nada que chega de fora.

O token nunca aparece em resposta, log, auditoria ou documentacao. O que se pode ver
dele e a impressao digital -- oito bytes de SHA-256 -- suficiente para conferir que
uma rotacao de fato trocou o valor, insuficiente para reconstruir o valor.
"""
from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import Field, StringConstraints
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .credentials import CofreIndisponivel, contexto_de, digital, selar
from .db import get_db
from .models import Audit, InstagramAccount, InstagramCredential, now, uid
from .permissions import ADMIN_ROLES
from .schemas import DateText, Name, StrictModel
from .security import require_auth

router = APIRouter(prefix="/api/v1/integrations/instagram", tags=["Instagram"])
# O id numerico da Meta. Restringir o formato aqui e o que impede um id inventado virar rota de tenant.
MetaId = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[0-9]{1,32}$")]
Token = Annotated[str, StringConstraints(strip_whitespace=True, min_length=20, max_length=1000)]


class AccountConnect(StrictModel):
    instagram_user_id: MetaId
    label: Name
    username: str = Field(default="", max_length=120)
    access_token: Token
    scopes: list[Name] = Field(default_factory=list, max_length=20)
    expires_at: DateText | None = None


class AccountUpdate(StrictModel):
    version: int = Field(ge=1, strict=True)
    label: Name | None = None
    username: str | None = Field(default=None, max_length=120)
    status: Literal["connected", "paused"] | None = None


class TokenRotate(StrictModel):
    version: int = Field(ge=1, strict=True)
    access_token: Token
    scopes: list[Name] = Field(default_factory=list, max_length=20)
    expires_at: DateText | None = None


def conta_dict(conta: InstagramAccount, credencial: InstagramCredential | None) -> dict:
    """A unica serializacao desta tabela. O token nao tem representacao aqui, nem cifrado."""
    corpo = {"id": conta.id, "instagram_user_id": conta.instagram_user_id, "username": conta.username,
             "label": conta.label, "status": conta.status, "version": conta.version,
             "connected_at": conta.connected_at.isoformat() if conta.connected_at else None,
             "updated_at": conta.updated_at.isoformat() if conta.updated_at else None,
             "token": None}
    if credencial:
        corpo["token"] = {"fingerprint": credencial.fingerprint, "scopes": credencial.scopes or [],
                          "expires_at": credencial.expires_at.isoformat() if credencial.expires_at else None,
                          "rotated_at": credencial.rotated_at.isoformat() if credencial.rotated_at else None}
    return corpo


def cofre(request: Request) -> str:
    chave = request.app.state.settings.credential_key
    if not chave:
        # Sem cofre nao se guarda token: recusar e a alternativa honesta a guardar em claro.
        raise HTTPException(503, "Cofre de credenciais não configurado; defina FATTECH_CREDENTIAL_KEY no servidor")
    return chave


def exigir_admin(principal):
    if principal.role not in ADMIN_ROLES:
        raise HTTPException(403, "Somente administradores conectam contas externas")


def buscar(db: Session, tenant_id: str, account_id: str) -> InstagramAccount:
    conta = db.scalar(select(InstagramAccount).where(InstagramAccount.id == account_id,
                                                     InstagramAccount.tenant_id == tenant_id))
    if conta is None:
        # A tabela nao tem RLS; o filtro por tenant em toda consulta e o que faz o isolamento.
        raise HTTPException(404, "Conta Instagram não encontrada")
    return conta


def credencial_de(db: Session, conta: InstagramAccount) -> InstagramCredential | None:
    return db.scalar(select(InstagramCredential).where(InstagramCredential.account_id == conta.id,
                                                       InstagramCredential.tenant_id == conta.tenant_id))


def guardar_token(db, chave, conta, token, scopes, expires_at, credencial=None):
    selado = selar(chave, token, contexto_de(conta.tenant_id, conta.id))
    vence = datetime.fromisoformat(expires_at).astimezone(timezone.utc) if expires_at else None
    if credencial is None:
        credencial = InstagramCredential(account_id=conta.id, tenant_id=conta.tenant_id)
        db.add(credencial)
    credencial.sealed_token, credencial.fingerprint = selado, digital(token)
    credencial.scopes, credencial.expires_at, credencial.rotated_at = list(scopes), vence, now()
    return credencial


def registrar(db, principal, acao, conta, detalhes=None):
    db.add(Audit(tenant_id=principal.tenant_id, actor_id=principal.actor_id, action=acao,
                 resource_id=conta.id, details={"instagram_user_id": conta.instagram_user_id, **(detalhes or {})}))


@router.get("/accounts")
def listar(principal=Depends(require_auth), db: Session = Depends(get_db)):
    principal.require("integrations:read")
    contas = db.scalars(select(InstagramAccount).where(InstagramAccount.tenant_id == principal.tenant_id)
                        .order_by(InstagramAccount.created_at)).all()
    return {"items": [conta_dict(c, credencial_de(db, c)) for c in contas], "total": len(contas)}


@router.get("/accounts/{account_id}")
def detalhar(account_id: str, principal=Depends(require_auth), db: Session = Depends(get_db)):
    principal.require("integrations:read")
    conta = buscar(db, principal.tenant_id, account_id)
    return conta_dict(conta, credencial_de(db, conta))


@router.post("/accounts", status_code=201)
def conectar(payload: AccountConnect, request: Request, principal=Depends(require_auth),
             db: Session = Depends(get_db)):
    principal.require("integrations:write")
    exigir_admin(principal)
    chave = cofre(request)
    conta = InstagramAccount(id=uid(), tenant_id=principal.tenant_id,
                             instagram_user_id=payload.instagram_user_id, username=payload.username,
                             label=payload.label, status="connected")
    db.add(conta)
    try:
        guardar_token(db, chave, conta, payload.access_token, payload.scopes, payload.expires_at)
        registrar(db, principal, "instagram.account.connected", conta)
        db.commit()
    except CofreIndisponivel as erro:
        db.rollback()
        raise HTTPException(503, "Cofre de credenciais indisponível") from erro
    except IntegrityError as erro:
        db.rollback()
        # A unicidade e global de proposito: duas organizacoes nao compartilham uma conta Instagram.
        raise HTTPException(409, "Esta conta Instagram já está conectada a uma organização") from erro
    return conta_dict(conta, credencial_de(db, conta))


@router.patch("/accounts/{account_id}")
def atualizar(account_id: str, payload: AccountUpdate, principal=Depends(require_auth),
              db: Session = Depends(get_db)):
    principal.require("integrations:write")
    exigir_admin(principal)
    conta = buscar(db, principal.tenant_id, account_id)
    if conta.version != payload.version:
        raise HTTPException(409, "A conta foi alterada por outra pessoa; recarregue antes de salvar")
    for campo in ("label", "username", "status"):
        valor = getattr(payload, campo)
        if valor is not None:
            setattr(conta, campo, valor)
    conta.version, conta.updated_at = conta.version + 1, now()
    registrar(db, principal, "instagram.account.updated", conta, {"status": conta.status})
    db.commit()
    return conta_dict(conta, credencial_de(db, conta))


@router.post("/accounts/{account_id}/token")
def rotacionar(account_id: str, payload: TokenRotate, request: Request, principal=Depends(require_auth),
               db: Session = Depends(get_db)):
    principal.require("integrations:write")
    exigir_admin(principal)
    chave = cofre(request)
    conta = buscar(db, principal.tenant_id, account_id)
    if conta.version != payload.version:
        raise HTTPException(409, "A conta foi alterada por outra pessoa; recarregue antes de salvar")
    credencial = credencial_de(db, conta)
    anterior = credencial.fingerprint if credencial else ""
    try:
        credencial = guardar_token(db, chave, conta, payload.access_token, payload.scopes,
                                   payload.expires_at, credencial)
    except CofreIndisponivel as erro:
        db.rollback()
        raise HTTPException(503, "Cofre de credenciais indisponível") from erro
    conta.version, conta.updated_at = conta.version + 1, now()
    # A auditoria guarda as duas impressoes digitais, nunca os tokens: prova a troca sem revelar nada.
    registrar(db, principal, "instagram.account.token_rotated", conta,
              {"fingerprint_anterior": anterior, "fingerprint_atual": credencial.fingerprint})
    db.commit()
    return conta_dict(conta, credencial)


@router.delete("/accounts/{account_id}")
def desconectar(account_id: str, principal=Depends(require_auth), db: Session = Depends(get_db)):
    principal.require("integrations:write")
    exigir_admin(principal)
    conta = buscar(db, principal.tenant_id, account_id)
    credencial = credencial_de(db, conta)
    if credencial:
        db.delete(credencial)
        # Sem relacao declarada o SQLAlchemy nao ordena os dois DELETE; o flush garante que a
        # credencial some por decisao nossa, e nao por efeito do CASCADE da chave estrangeira.
        db.flush()
    registrar(db, principal, "instagram.account.disconnected", conta)
    db.delete(conta)
    db.commit()
    # Desconectar apaga o token de verdade; o webhook volta a nao reconhecer esta conta.
    return {"deleted": True, "id": account_id}
