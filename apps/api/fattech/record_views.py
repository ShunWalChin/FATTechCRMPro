"""Tenant-scoped dossiers, immutable activities and a bounded cross-resource search."""
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from pydantic import StringConstraints
from sqlalchemy import and_, false, func, or_, select

from .db import get_db
from .idempotency import creation_receipt
from .models import Audit, Record
from .schemas import StrictModel
from .security import require_auth
from .services import audit_event, get_record, scoped, serialize

ParentKind = Literal["contacts", "companies", "deals"]
PARENT_FIELD = {"contacts": "contact_id", "companies": "company_id", "deals": "deal_id"}
SEARCH_KINDS = ("contacts", "companies", "deals", "tasks")
router = APIRouter(prefix="/api/v1", tags=["record views"])


class ActivityCreate(StrictModel):
    type: Literal["note", "call", "meeting"] = "note"
    body: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20000)]


def readable(principal, kind):
    if principal.key and f"{kind}:read" not in principal.key.scopes:
        return False
    principal.require(f"{kind}:read")
    return True


def page(db, statement, limit, offset, *, restricted=False):
    if restricted:
        return {"items": [], "total": 0, "limit": limit, "offset": offset, "restricted": True}
    total = db.scalar(select(func.count()).select_from(statement.subquery()))
    rows = db.scalars(statement.order_by(Record.created_at.desc(), Record.id.desc()).limit(limit).offset(offset))
    return {"items": [serialize(row) for row in rows], "total": total, "limit": limit, "offset": offset}


@router.post("/records/{kind}/{record_id}/activities", status_code=201)
def add_activity(kind: ParentKind, record_id: str, payload: ActivityCreate, response: Response,
                 idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
                 principal=Depends(require_auth), db=Depends(get_db)):
    principal.require(f"{kind}:write")
    # A note is an append, never an edit to the customer's existing notes field.
    data = {**payload.model_dump(), PARENT_FIELD[kind]: record_id}
    receipt = None
    if idempotency_key is not None:
        receipt, replayed = creation_receipt(db, principal, "activities", idempotency_key, data)
        response.headers["Idempotency-Replayed"] = str(replayed).lower()
        if replayed:
            result = receipt.response
            db.commit()
            return result
    get_record(db, principal.tenant_id, kind, record_id, lock=True)
    record = Record(tenant_id=principal.tenant_id, kind="activities", data={**data,
                    "author_id": principal.actor_id, "author_name": principal.user.name})
    db.add(record)
    db.flush()
    audit_event(db, principal.tenant_id, principal.actor_id, "activities.created", record.id,
                {"parent_kind": kind, "parent_id": record_id, "type": payload.type})
    result = serialize(record)
    if receipt is not None:
        receipt.response = result
    db.commit()
    return result


@router.get("/records/{kind}/{record_id}/overview")
def overview(kind: ParentKind, record_id: str, principal=Depends(require_auth), db=Depends(get_db),
             limit: int = Query(20, ge=1, le=100),
             activities_offset: int = Query(0, ge=0, le=10000),
             deals_offset: int = Query(0, ge=0, le=10000),
             tasks_offset: int = Query(0, ge=0, le=10000),
             conversations_offset: int = Query(0, ge=0, le=10000),
             history_offset: int = Query(0, ge=0, le=10000)):
    principal.require(f"{kind}:read")
    parent = get_record(db, principal.tenant_id, kind, record_id)
    tenant = principal.tenant_id
    # Subqueries keep linked data in SQL; no unbounded list of customer records in Python.
    contacts = select(Record.id).where(Record.tenant_id == tenant, Record.kind == "contacts",
                                       Record.deleted.is_(False))
    if kind == "contacts":
        contacts = contacts.where(Record.id == record_id)
        deal_relation = Record.data["contact_id"].as_string() == record_id
    elif kind == "companies":
        contacts = contacts.where(Record.data["company_id"].as_string() == record_id)
        deal_relation = or_(Record.data["company_id"].as_string() == record_id,
                            Record.data["contact_id"].as_string().in_(contacts))
    else:
        contacts = contacts.where(Record.id == parent.data.get("contact_id"))
        deal_relation = Record.id == record_id
    deals = scoped(tenant, "deals").where(deal_relation)
    linked_deal_ids = deals.with_only_columns(Record.id)
    tasks = scoped(tenant, "tasks").where(or_(Record.data["deal_id"].as_string().in_(linked_deal_ids),
        Record.data["contact_id"].as_string().in_(contacts) if kind != "deals" else false()))
    conversations = scoped(tenant, "conversations").where(Record.data["contact_id"].as_string().in_(contacts))
    activities = scoped(tenant, "activities").where(Record.data[PARENT_FIELD[kind]].as_string() == record_id)
    history = select(Audit).where(Audit.tenant_id == tenant, Audit.resource_id == record_id,
                                 Audit.action.startswith(kind + ".", autoescape=True))
    total_history = db.scalar(select(func.count()).select_from(history.subquery()))
    events = list(db.scalars(history.order_by(Audit.created_at.desc(), Audit.id.desc())
                             .limit(limit).offset(history_offset)))
    # Reuse the audit labels and batched, tenant-filtered author lookup.
    from .main import describe_audit
    return {"record": {**serialize(parent), "kind": kind},
            "activities": page(db, activities, limit, activities_offset),
            "deals": page(db, deals.where(false()) if kind == "deals" else deals, limit, deals_offset,
                          restricted=not readable(principal, "deals")),
            "tasks": page(db, tasks, limit, tasks_offset, restricted=not readable(principal, "tasks")),
            "conversations": page(db, conversations, limit, conversations_offset,
                                  restricted=not readable(principal, "conversations")),
            "history": {"items": describe_audit(db, tenant, events), "total": total_history,
                        "limit": limit, "offset": history_offset}}


@router.get("/search")
def search(principal=Depends(require_auth), db=Depends(get_db),
           q: str = Query(..., min_length=2, max_length=200),
           limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=10000)):
    term = q.strip()
    if len(term) < 2:
        raise HTTPException(422, "Informe ao menos dois caracteres para buscar")
    allowed = [kind for kind in SEARCH_KINDS if readable(principal, kind)]
    if not allowed:
        raise HTTPException(403, "Nenhum recurso autorizado para busca")
    term = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    matches = or_(*[Record.data[field].as_string().ilike(f"%{term}%", escape="\\")
                    for field in ("name", "title", "email", "phone", "document")])
    statement = select(Record).where(and_(Record.tenant_id == principal.tenant_id,
                                          Record.kind.in_(allowed), Record.deleted.is_(False), matches))
    total = db.scalar(select(func.count()).select_from(statement.subquery()))
    records = db.scalars(statement.order_by(Record.updated_at.desc(), Record.id.desc()).limit(limit).offset(offset))
    items = [{"id": record.id, "kind": record.kind,
              "title": record.data.get("name") or record.data.get("title") or "Registro",
              "subtitle": record.data.get("email") or record.data.get("phone") or record.data.get("status") or "",
              "updated_at": record.updated_at.isoformat()} for record in records]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


def register_record_views(app):
    app.include_router(router)
