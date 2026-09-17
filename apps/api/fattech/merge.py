"""Deduplicacao e mesclagem de contatos.

O CRM ja detectava duplicata na criacao e recusava. Detectar sem poder resolver empurra o
problema para fora do sistema: a pessoa cria com outro e-mail, ou desiste. Aqui a duplicata
que ja existe pode ser resolvida.

Mesclar e destrutivo e este modulo nao finge o contrario. O perdedor nao e apagado: fica
excluido logicamente com `merged_into` apontando para o sobrevivente, de modo que uma
mesclagem errada possa ser investigada -- mas desfaze-la nao e automatico, e nao dizemos que e.

A regra de campo e uma so: o sobrevivente manda no que ele tem. O perdedor so preenche o que
estava vazio. Um merge que sobrescreve o registro bom com o ruim e pior do que a duplicata.
"""
from typing import Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import Field
from sqlalchemy import select, update

from .db import get_db
from .models import Record, now
from .schemas import Identifier, StrictModel
from .security import require_auth
from .services import (audit_event, find_contact_matches, get_record, lock_contacts,
                       normalize_contact_identifiers, scoped, serialize)

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])
# Onde um contato aparece como referencia. Mesclar sem repontar isto perderia o historico.
REFERENCIAS = {"deals": "contact_id", "tasks": "contact_id", "conversations": "contact_id",
               "invoices": "contact_id", "activities": "contact_id"}
LISTAS = ("tags",)
NUNCA_HERDA = ("custom",)


class MergeRequest(StrictModel):
    duplicate_id: Identifier
    version: int = Field(ge=1, strict=True)
    duplicate_version: int = Field(ge=1, strict=True)


def chave_de(dados: dict) -> list[str]:
    identificadores = normalize_contact_identifiers(dict(dados))
    chaves = []
    if identificadores.get("email"):
        chaves.append("email:" + identificadores["email"])
    if identificadores.get("phone"):
        chaves.append("phone:" + identificadores["phone"])
    return chaves


@router.get("/duplicates")
def duplicatas(principal=Depends(require_auth), db=Depends(get_db),
               limit: int = Query(50, ge=1, le=200)):
    """Agrupa por e-mail e telefone normalizados -- as mesmas chaves que a criacao ja recusa."""
    principal.require("contacts:read")
    grupos: dict[str, list] = {}
    for registro in db.scalars(scoped(principal.tenant_id, "contacts")):
        try:
            chaves = chave_de(registro.data)
        except HTTPException:
            # Telefone historico malformado nao pode esconder um e-mail que casa.
            chaves = chave_de({**registro.data, "phone": ""})
        for chave in chaves:
            grupos.setdefault(chave, []).append(registro)
    itens = []
    vistos = set()
    for chave, registros in grupos.items():
        if len(registros) < 2:
            continue
        assinatura = tuple(sorted(item.id for item in registros))
        if assinatura in vistos:
            continue
        vistos.add(assinatura)
        # O mais antigo e o candidato natural a sobreviver: e ele que o resto do sistema referencia.
        ordenados = sorted(registros, key=lambda item: item.created_at)
        itens.append({
            "match_on": chave.split(":", 1)[0], "value": chave.split(":", 1)[1],
            "survivor_id": ordenados[0].id,
            "records": [{"id": item.id, "version": item.version, "name": item.data.get("name", ""),
                         "email": item.data.get("email"), "phone": item.data.get("phone", ""),
                         "owner_id": item.data.get("owner_id"),
                         "lead_stage": item.data.get("lead_stage", "novo"),
                         "created_at": item.created_at.isoformat()} for item in ordenados],
        })
    itens.sort(key=lambda grupo: -len(grupo["records"]))
    return {"items": itens[:limit], "total": len(itens)}


def herdar(sobrevivente: dict, perdedor: dict) -> tuple[dict, list[str]]:
    """O sobrevivente manda. O perdedor so preenche buraco, e listas viram uniao."""
    resultado, herdados = dict(sobrevivente), []
    for chave, valor in perdedor.items():
        if chave in NUNCA_HERDA:
            continue
        if chave in LISTAS:
            atual = list(resultado.get(chave) or [])
            novos = [item for item in (valor or []) if item not in atual]
            if novos:
                resultado[chave] = atual + novos
                herdados.append(chave)
            continue
        if resultado.get(chave) in (None, "", [], {}) and valor not in (None, "", [], {}):
            resultado[chave] = valor
            herdados.append(chave)
    notas = [texto for texto in (sobrevivente.get("notes"), perdedor.get("notes")) if texto]
    if len(notas) == 2:
        resultado["notes"] = (notas[0] + "\n\n— mesclado —\n" + notas[1])[:20000]
        herdados.append("notes")
    # Campos personalizados do perdedor entram so onde o sobrevivente nao respondeu.
    proprios = dict(sobrevivente.get("custom") or {})
    for chave, valor in (perdedor.get("custom") or {}).items():
        proprios.setdefault(chave, valor)
    if proprios != (sobrevivente.get("custom") or {}):
        resultado["custom"] = proprios
        herdados.append("custom")
    return resultado, sorted(set(herdados))


@router.post("/{record_id}/merge")
def mesclar(record_id: str, payload: MergeRequest = Body(...),
            principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("contacts:write")
    if record_id == payload.duplicate_id:
        raise HTTPException(422, "Um contato não pode ser mesclado consigo mesmo")
    lock_contacts(db, principal.tenant_id)
    sobrevivente = get_record(db, principal.tenant_id, "contacts", record_id, lock=True)
    perdedor = get_record(db, principal.tenant_id, "contacts", payload.duplicate_id, lock=True)
    # As duas versoes viajam: mesclar e destrutivo e nenhum dos dois lados pode ter mudado.
    if sobrevivente.version != payload.version or perdedor.version != payload.duplicate_version:
        raise HTTPException(409, "Um dos contatos foi alterado por outra pessoa. Atualize e tente novamente.")

    dados, herdados = herdar(sobrevivente.data, perdedor.data)
    movidos = {}
    for kind, campo in REFERENCIAS.items():
        # Reescrito em Python, e nao com o operador de concatenacao JSONB: aquele so existe no
        # PostgreSQL, e o mesmo codigo precisa rodar no SQLite dos testes e do desenvolvimento.
        alvos = list(db.scalars(select(Record).where(
            Record.tenant_id == principal.tenant_id, Record.kind == kind, Record.deleted.is_(False),
            Record.data[campo].as_string() == perdedor.id)))
        for alvo in alvos:
            db.execute(update(Record).where(Record.id == alvo.id)
                       .values(data={**alvo.data, campo: sobrevivente.id}))
        if alvos:
            movidos[kind] = len(alvos)

    db.execute(update(Record).where(Record.id == sobrevivente.id, Record.version == payload.version)
               .values(data=dados, version=payload.version + 1, updated_at=now()))
    db.execute(update(Record).where(Record.id == perdedor.id, Record.version == payload.duplicate_version)
               .values(deleted=True, version=payload.duplicate_version + 1, updated_at=now(),
                       data={**perdedor.data, "merged_into": sobrevivente.id,
                             "merged_at": now().isoformat()}))
    audit_event(db, principal.tenant_id, principal.actor_id, "contacts.merged", sobrevivente.id,
                {"absorbed_id": perdedor.id, "absorbed_name": perdedor.data.get("name", ""),
                 "inherited_fields": herdados, "moved": movidos})
    audit_event(db, principal.tenant_id, principal.actor_id, "contacts.merged_into", perdedor.id,
                {"survivor_id": sobrevivente.id})
    db.commit()
    db.refresh(sobrevivente)
    return {**serialize(sobrevivente), "merge": {"absorbed_id": perdedor.id,
                                                 "inherited_fields": herdados, "moved": movidos}}


@router.get("/{record_id}/duplicates")
def candidatos(record_id: str, principal=Depends(require_auth), db=Depends(get_db),
               scope: Literal["active"] = "active"):
    """Quem casa com este contato agora. Serve a ficha, onde a decisao de mesclar acontece."""
    principal.require("contacts:read")
    registro = get_record(db, principal.tenant_id, "contacts", record_id)
    try:
        casam = find_contact_matches(db, principal.tenant_id, registro.data, exclude_id=record_id)
    except HTTPException:
        casam = find_contact_matches(db, principal.tenant_id, {**registro.data, "phone": ""},
                                     exclude_id=record_id)
    return {"items": [{"id": item.id, "version": item.version, "name": item.data.get("name", ""),
                       "email": item.data.get("email"), "phone": item.data.get("phone", ""),
                       "created_at": item.created_at.isoformat()} for item in casam],
            "total": len(casam)}


def register_merge(app):
    app.include_router(router)
