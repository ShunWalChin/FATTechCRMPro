"""Commercial documents and goals with immutable money snapshots and explicit transitions.

`issued` records internal issuance only; this module never sends a message, charges a
customer or marks a deal won. Reports describe the current outcome of a creation-date
cohort, because legacy deals do not have a reliable closing timestamp.
"""
from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Literal
from uuid import NAMESPACE_URL, uuid5

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from pydantic import Field, StringConstraints, model_validator
from sqlalchemy import BigInteger, and_, cast, func, select, text, update
from sqlalchemy.orm import aliased
from sqlalchemy.exc import IntegrityError

from .db import get_db
from .idempotency import creation_receipt
from .models import Record, User, now
from .permissions import ADMIN_ROLES
from .schemas import Cents, Identifier, Name, StrictModel
from .security import require_auth
from .services import audit_event, get_record, scoped, serialize

router = APIRouter(prefix="/api/v1/sales", tags=["Sales operations"])
Status = Literal["draft", "issued", "accepted", "rejected"]
Period = Annotated[str, StringConstraints(pattern=r"^[1-9][0-9]{3}-(0[1-9]|1[0-2])$")]
MAX_CENTS = 100_000_000_000


class ProposalItem(StrictModel):
    product_id: Identifier
    quantity: int = Field(strict=True, ge=1, le=10_000)


class ProposalCreate(StrictModel):
    title: Name
    deal_id: Identifier
    items: list[ProposalItem] = Field(min_length=1, max_length=100)
    discount_cents: Cents = 0

    @model_validator(mode="after")
    def distinct_products(self):
        if len({item.product_id for item in self.items}) != len(self.items):
            raise ValueError("Um produto deve aparecer uma única vez; ajuste a quantidade")
        return self


class ProposalDecision(StrictModel):
    version: int = Field(strict=True, ge=1)
    status: Status


class GoalCreate(StrictModel):
    owner_id: Identifier
    period: Period
    target_cents: Cents


class GoalUpdate(StrictModel):
    version: int = Field(strict=True, ge=1)
    target_cents: Cents


def active_owner(db, tenant_id, owner_id):
    user = db.scalar(select(User).where(User.id == owner_id, User.tenant_id == tenant_id,
                                       User.active.is_(True)).with_for_update(read=True))
    if user is None:
        raise HTTPException(404, "Responsável ativo não encontrado")
    return user


def visible_owner(principal, owner_id):
    if principal.role not in ADMIN_ROLES:
        if owner_id is not None and owner_id != principal.actor_id:
            raise HTTPException(403, "Você pode consultar somente suas metas e resultados")
        return principal.actor_id
    return owner_id


def page_of(db, query, limit, offset):
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(Record.created_at.desc(), Record.id).limit(limit).offset(offset))
    return {"items": [serialize(item) for item in items], "total": total}


def save_change(db, principal, record, version, data, action):
    result = db.execute(update(Record).where(Record.id == record.id, Record.tenant_id == principal.tenant_id,
        Record.kind == record.kind, Record.version == version, Record.deleted.is_(False))
        .values(data=data, version=version + 1, updated_at=now()))
    if result.rowcount != 1:
        raise HTTPException(409, "Versão desatualizada; atualize o registro")
    audit_event(db, principal.tenant_id, principal.actor_id, action, record.id, {"version": version + 1})
    db.commit()
    db.refresh(record)
    return serialize(record)


@router.post("/proposals", status_code=201)
def create_proposal(payload: ProposalCreate, response: Response,
                    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
                    principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("deals:write")
    receipt = None
    if db.bind.dialect.name == "sqlite":
        db.execute(text("UPDATE records SET version=version WHERE 1=0"))
    if idempotency_key is not None:
        receipt, replayed = creation_receipt(db, principal, "sales_proposals", idempotency_key,
                                            payload.model_dump(mode="json"))
        response.headers["Idempotency-Replayed"] = str(replayed).lower()
        if replayed:
            result = receipt.response
            db.commit()
            return result
    deal = get_record(db, principal.tenant_id, "deals", payload.deal_id, share=True)
    # Acquire product locks in a stable order, even when clients order their line items differently.
    products = {item.product_id: get_record(db, principal.tenant_id, "products", item.product_id, share=True)
                for item in sorted(payload.items, key=lambda item: item.product_id)}
    lines = []
    for item in payload.items:
        product = products[item.product_id]
        if product.data.get("status") != "active":
            raise HTTPException(409, "Proposta requer produtos ativos")
        price = product.data["price_cents"]
        line_total = price * item.quantity
        lines.append({"product_id": product.id, "name": product.data["name"], "sku": product.data.get("sku", ""),
                      "quantity": item.quantity, "unit_price_cents": price, "line_total_cents": line_total})
    subtotal = sum(item["line_total_cents"] for item in lines)
    if subtotal > MAX_CENTS:
        raise HTTPException(422, "Valor da proposta excede o limite monetário")
    if payload.discount_cents > subtotal:
        raise HTTPException(422, "Desconto não pode exceder o subtotal")
    record = Record(tenant_id=principal.tenant_id, kind="sales_proposals", data={
        "title": payload.title, "deal_id": deal.id, "deal_title": deal.data["title"],
        "owner_id": deal.data.get("owner_id"), "items": lines, "currency": "BRL", "status": "draft",
        "subtotal_cents": subtotal, "discount_cents": payload.discount_cents,
        "total_cents": subtotal - payload.discount_cents, "created_by": principal.actor_id,
    })
    db.add(record)
    db.flush()
    audit_event(db, principal.tenant_id, principal.actor_id, "sales_proposals.created", record.id, {"version": 1})
    result = serialize(record)
    if receipt is not None:
        receipt.response = result
    db.commit()
    return result


@router.get("/proposals")
def list_proposals(deal_id: str | None = None, status: Status | None = None,
                   limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                   principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("deals:read")
    query = scoped(principal.tenant_id, "sales_proposals")
    if deal_id is not None:
        query = query.where(Record.data["deal_id"].as_string() == deal_id)
    if status is not None:
        query = query.where(Record.data["status"].as_string() == status)
    return page_of(db, query, limit, offset)


@router.get("/proposals/{proposal_id}")
def proposal(proposal_id: str, principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("deals:read")
    return serialize(get_record(db, principal.tenant_id, "sales_proposals", proposal_id))


@router.patch("/proposals/{proposal_id}")
def decide_proposal(proposal_id: str, payload: ProposalDecision,
                    principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("deals:write")
    record = get_record(db, principal.tenant_id, "sales_proposals", proposal_id, lock=True)
    if record.version != payload.version:
        raise HTTPException(409, "Versão desatualizada; atualize a proposta")
    transitions = {"draft": {"issued"}, "issued": {"accepted", "rejected"}, "accepted": set(), "rejected": set()}
    if payload.status not in transitions[record.data["status"]]:
        raise HTTPException(409, "Transição de proposta não permitida")
    data = {**record.data, "status": payload.status, f"{payload.status}_at": now().isoformat(),
            "updated_by": principal.actor_id}
    return save_change(db, principal, record, payload.version, data, "sales_proposals." + payload.status)


@router.post("/goals", status_code=201)
def create_goal(payload: GoalCreate, principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("deals:write")
    principal.admin()
    if db.bind.dialect.name == "sqlite":
        db.execute(text("UPDATE records SET version=version WHERE 1=0"))
    active_owner(db, principal.tenant_id, payload.owner_id)
    # The primary key is the uniqueness constraint for (tenant, seller, month) on both database engines.
    record_id = str(uuid5(NAMESPACE_URL, f"fattech:sales-goal:{principal.tenant_id}:{payload.owner_id}:{payload.period}"))
    record = Record(id=record_id, tenant_id=principal.tenant_id, kind="sales_goals", data=payload.model_dump())
    db.add(record)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Este vendedor já possui meta para o período; atualize a versão existente") from exc
    audit_event(db, principal.tenant_id, principal.actor_id, "sales_goals.created", record.id, {"version": 1})
    db.commit()
    return serialize(record)


@router.get("/goals")
def list_goals(owner_id: str | None = None, period: Period | None = None,
               limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
               principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("deals:read")
    owner_id = visible_owner(principal, owner_id)
    query = scoped(principal.tenant_id, "sales_goals")
    if owner_id is not None:
        query = query.where(Record.data["owner_id"].as_string() == owner_id)
    if period is not None:
        query = query.where(Record.data["period"].as_string() == period)
    return page_of(db, query, limit, offset)


@router.patch("/goals/{goal_id}")
def update_goal(goal_id: str, payload: GoalUpdate, principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("deals:write")
    principal.admin()
    record = get_record(db, principal.tenant_id, "sales_goals", goal_id, lock=True)
    active_owner(db, principal.tenant_id, record.data["owner_id"])
    return save_change(db, principal, record, payload.version,
                       {**record.data, "target_cents": payload.target_cents}, "sales_goals.updated")


@router.get("/report")
def sales_report(owner_id: str | None = None, source: str | None = Query(None, max_length=100),
                 date_from: date | None = None, date_to: date | None = None,
                 period: Period | None = None, principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("deals:read")
    owner_id = visible_owner(principal, owner_id)
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "Data inicial deve ser anterior ou igual à data final")
    query = scoped(principal.tenant_id, "deals")
    if owner_id is not None:
        query = query.where(Record.data["owner_id"].as_string() == owner_id)
    if date_from is not None:
        query = query.where(Record.created_at >= datetime.combine(date_from, datetime.min.time(), timezone.utc))
    if date_to is not None:
        if date_to == date.max:
            raise HTTPException(422, "Data final fora do intervalo permitido")
        query = query.where(Record.created_at < datetime.combine(date_to + timedelta(days=1), datetime.min.time(), timezone.utc))
    if source is not None:
        contact = aliased(Record)
        query = query.outerjoin(contact, and_(contact.id == Record.data["contact_id"].as_string(),
            contact.tenant_id == principal.tenant_id, contact.kind == "contacts", contact.deleted.is_(False)))
        query = query.where(func.coalesce(func.nullif(Record.data["source"].as_string(), ""),
                            func.nullif(contact.data["source"].as_string(), ""), "unknown") == source)
    referenced = query.with_only_columns(Record.data["pipeline_id"].as_string()).distinct().correlate(None)
    pipelines = {record.id: {stage["key"]: stage["outcome"] for stage in record.data["stages"]}
                 for record in db.scalars(scoped(principal.tenant_id, "pipelines").where(Record.id.in_(referenced)))}
    result = {"deal_count": 0, "open_count": 0, "won_count": 0, "lost_count": 0,
              "pipeline_cents": 0, "weighted_pipeline_cents": 0, "won_cents": 0, "lost_reasons": {}}
    weighted_hundredths = 0
    pipeline_id, stage = Record.data["pipeline_id"].as_string(), Record.data["stage"].as_string()
    reason = Record.data["lost_reason"].as_string()
    amount = func.coalesce(cast(Record.data["value_cents"].as_string(), BigInteger), 0)
    probability = func.coalesce(cast(Record.data["probability"].as_string(), BigInteger), 0)
    grouped = query.with_only_columns(pipeline_id, stage, reason, func.count(), func.sum(amount),
                                     func.sum(amount * probability)).group_by(pipeline_id, stage, reason)
    for funnel, stage_key, lost_reason, count, value, weighted in db.execute(grouped):
        outcome = pipelines.get(funnel, {}).get(stage_key, "open")
        value, weighted = int(value), int(weighted)
        result["deal_count"] += count
        if outcome == "won":
            result["won_count"] += count
            result["won_cents"] += value
        elif outcome == "lost":
            result["lost_count"] += count
            label = lost_reason or "Não informado"
            result["lost_reasons"][label] = result["lost_reasons"].get(label, 0) + count
        else:
            result["open_count"] += count
            result["pipeline_cents"] += value
            weighted_hundredths += weighted
    result["weighted_pipeline_cents"] = (weighted_hundredths + 50) // 100
    goals = scoped(principal.tenant_id, "sales_goals")
    if owner_id is not None:
        goals = goals.where(Record.data["owner_id"].as_string() == owner_id)
    if period is not None:
        goals = goals.where(Record.data["period"].as_string() == period)
    return {**result, "date_basis": "deal_created_at_utc", "weighted_rounding": "half_up_after_sum",
            "filters": {"owner_id": owner_id, "source": source, "date_from": date_from, "date_to": date_to,
                        "goal_period": period}, "goals": [serialize(goal) for goal in db.scalars(goals)]}
