"""Tenant-scoped operational views and controlled recovery; never arbitrary event execution."""
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import Field
from sqlalchemy import func, select, update

from .core_models import CoreDelivery, CoreFailure, CoreHeartbeat, EventFact, MessageBatch, MessageBuffer
from .db import get_db
from .events import EventEnvelope, utc
from .models import Outbox, now
from .schemas import StrictModel
from .security import require_auth
from .services import audit_event

router = APIRouter(prefix="/api/v1/core", tags=["Core-Engine"])
ERROR_LABELS = {"invalid_event": "O evento não atende ao contrato aceito pelo processador.",
                "handler_failed": "O processamento falhou e foi revertido; verifique o worker e tente novamente."}


class Retry(StrictModel):
    expected_attempts: int = Field(strict=True, ge=1)


@router.get("/contract")
def contract(principal=Depends(require_auth)):
    principal.admin()
    return {"id": "core-engine-v1", "envelope": EventEnvelope.model_json_schema(),
            "max_hops": 5, "external_delivery_contract": "n8n-legacy-v1"}


@router.get("/overview")
def overview(request: Request, principal=Depends(require_auth), db=Depends(get_db)):
    principal.admin()
    tenant_id = principal.tenant_id
    counts = dict(db.execute(select(CoreDelivery.status, func.count()).where(CoreDelivery.tenant_id == tenant_id)
                             .group_by(CoreDelivery.status)).all())
    heartbeats = {row.worker_role: row.last_seen_at for row in db.scalars(select(CoreHeartbeat)
                  .where(CoreHeartbeat.tenant_id == tenant_id))}
    instant = now()
    threshold = max(120, request.app.state.settings.worker_poll_seconds * 3)
    workers = []
    for role in ("bi", "messaging", "scheduler"):
        last = heartbeats.get(role)
        age = (instant - utc(last)).total_seconds() if last else None
        status = "unknown" if age is None else "healthy" if 0 <= age <= threshold else "stale"
        workers.append({"role": role, "last_seen_at": utc(last).isoformat() if last else None, "status": status})
    metrics = db.execute(select(EventFact.event_type, func.count()).where(EventFact.tenant_id == tenant_id,
                         EventFact.occurred_at >= instant - timedelta(hours=24))
                         .group_by(EventFact.event_type).order_by(EventFact.event_type)).all()
    oldest = db.scalar(select(func.min(CoreDelivery.created_at)).where(CoreDelivery.tenant_id == tenant_id,
                       CoreDelivery.status.in_(("pending", "processing"))))
    return {"id": "core-engine", "transport": db.bind.dialect.name,
            "n8n_configured": bool(request.app.state.settings.n8n_outbound_url),
            "counts": {key: counts.get(key, 0) for key in ("pending", "processing", "completed", "dead_letter")},
            "oldest_pending_at": utc(oldest).isoformat() if oldest else None,
            "buffers": db.scalar(select(func.count()).select_from(MessageBuffer).where(MessageBuffer.tenant_id == tenant_id)),
            "workers": workers, "events_24h": [{"event": event, "count": count} for event, count in metrics]}


@router.get("/deliveries")
def deliveries(status: Literal["pending", "processing", "completed", "dead_letter"] | None = None,
               worker_role: Literal["bi", "messaging"] | None = None,
               limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=100000),
               principal=Depends(require_auth), db=Depends(get_db)):
    principal.admin()
    query = select(CoreDelivery, Outbox.event_type).join(Outbox, CoreDelivery.event_id == Outbox.id).where(
        CoreDelivery.tenant_id == principal.tenant_id, Outbox.tenant_id == principal.tenant_id)
    if status:
        query = query.where(CoreDelivery.status == status)
    if worker_role:
        query = query.where(CoreDelivery.worker_role == worker_role)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.execute(query.order_by(CoreDelivery.created_at.desc(), CoreDelivery.id.desc()).offset(offset).limit(limit))
    return {"items": [{"id": row.id, "event_id": row.event_id, "event_type": event_type,
                       "worker_role": row.worker_role, "status": row.status, "attempts": row.attempts,
                       "last_error": ERROR_LABELS.get(row.last_error, "Falha de processamento.") if row.last_error else None,
                       "created_at": utc(row.created_at).isoformat()} for row, event_type in rows], "total": total}


@router.post("/deliveries/{delivery_id}/retry")
def retry(delivery_id: str, payload: Retry, principal=Depends(require_auth), db=Depends(get_db)):
    principal.admin()
    row = db.scalar(select(CoreDelivery).where(CoreDelivery.id == delivery_id,
                    CoreDelivery.tenant_id == principal.tenant_id))
    if row is None:
        raise HTTPException(404, "Entrega não encontrada")
    changed = db.execute(update(CoreDelivery).where(CoreDelivery.id == delivery_id,
        CoreDelivery.tenant_id == principal.tenant_id, CoreDelivery.status == "dead_letter",
        CoreDelivery.attempts == payload.expected_attempts).values(
            status="pending", cycle_attempts=0, claim_token=None, locked_until=None,
            available_at=now(), last_error=None))
    if changed.rowcount != 1:
        raise HTTPException(409, "A entrega mudou; atualize a lista antes de tentar novamente")
    audit_event(db, principal.tenant_id, principal.actor_id, "core.delivery.retried", delivery_id,
                {"worker_role": row.worker_role, "previous_attempts": payload.expected_attempts})
    db.commit()
    return {"id": delivery_id, "status": "pending"}


@router.get("/deliveries/{delivery_id}/failures")
def failures(delivery_id: str, limit: int = Query(20, ge=1, le=100),
             principal=Depends(require_auth), db=Depends(get_db)):
    principal.admin()
    delivery = db.scalar(select(CoreDelivery.id).where(CoreDelivery.id == delivery_id,
                         CoreDelivery.tenant_id == principal.tenant_id))
    if delivery is None:
        raise HTTPException(404, "Entrega não encontrada")
    query = select(CoreFailure).where(CoreFailure.tenant_id == principal.tenant_id,
                                     CoreFailure.delivery_id == delivery_id)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    return {"items": [{"id": row.id, "attempt": row.attempt,
                       "error": ERROR_LABELS.get(row.error_code, "Falha de processamento."),
                       "created_at": utc(row.created_at).isoformat()}
                      for row in db.scalars(query.order_by(CoreFailure.created_at.desc()).limit(limit))], "total": total}


@router.get("/message-batches")
def batches(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=100000),
            principal=Depends(require_auth), db=Depends(get_db)):
    principal.admin()
    query = select(MessageBatch).where(MessageBatch.tenant_id == principal.tenant_id)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(MessageBatch.created_at.desc(), MessageBatch.id.desc()).offset(offset).limit(limit))
    return {"items": [{"id": row.id, "conversation_id": row.conversation_id,
                       "message_count": len(row.message_ids), "status": row.status, "reason": row.reason,
                       "created_at": utc(row.created_at).isoformat()} for row in rows], "total": total}
