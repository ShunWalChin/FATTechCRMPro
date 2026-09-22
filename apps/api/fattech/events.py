"""Core-Engine v1 envelope, adapted without rewriting historical n8n payloads."""
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, NAMESPACE_URL, uuid5

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import Outbox, now, uid

MAX_HOPS = 5


class EventActor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["user", "system", "webhook"]
    id: str = Field(min_length=1, max_length=200)


class EventEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID
    # Two-part names already form the public CRM contract (contacts.created).
    event: str = Field(max_length=100, pattern=r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){1,7}$")
    version: Literal[1] = 1
    agency_id: UUID
    occurred_at: datetime
    actor: EventActor
    trace_id: UUID
    hops: int = Field(default=0, strict=True, ge=0, le=MAX_HOPS)
    data: dict

    @field_validator("occurred_at")
    @classmethod
    def utc_timestamp(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Event timestamp requires a timezone")
        return value.astimezone(timezone.utc)

    @field_validator("data")
    @classmethod
    def json_payload(cls, value):
        if len(json.dumps(value, allow_nan=False, ensure_ascii=False).encode()) > 1_048_576:
            raise ValueError("Event payload exceeds the size limit")
        return value


def utc(value):
    # SQLite strips tzinfo from DateTime; historical database timestamps are UTC.
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def canonical_trace(tenant_id, trace_id):
    try:
        return UUID(trace_id)
    except (ValueError, TypeError, AttributeError):
        return uuid5(NAMESPACE_URL, f"fattech:trace:{tenant_id}:{trace_id}")


def envelope_for(event: Outbox):
    return EventEnvelope(event_id=event.id, event=event.event_type, agency_id=event.tenant_id,
                         occurred_at=utc(event.created_at),
                         actor=event.actor or {"type": "system", "id": "legacy-unknown"},
                         trace_id=canonical_trace(event.tenant_id, event.trace_id),
                         hops=event.hops, data=event.payload)


def emit_event(db, tenant_id, event, data, *, actor=None, parent: EventEnvelope | None = None,
               origin="internal"):
    """Never commit here: business effects and event publication share the caller's transaction."""
    if parent is not None and str(parent.agency_id) != tenant_id:
        raise ValueError("Child event must belong to the same tenant")
    if parent is not None and parent.hops >= MAX_HOPS:
        raise ValueError("Event hop limit exceeded")
    envelope = EventEnvelope(event_id=uid(), event=event, agency_id=tenant_id, occurred_at=now(),
                             actor=actor or {"type": "system", "id": "core-engine"},
                             trace_id=parent.trace_id if parent else uid(),
                             hops=parent.hops + 1 if parent else 0, data=data)
    row = Outbox(id=str(envelope.event_id), tenant_id=tenant_id, event_type=envelope.event,
                 payload=envelope.data, trace_id=str(envelope.trace_id), hops=envelope.hops,
                 created_at=envelope.occurred_at, actor=envelope.actor.model_dump(), origin=origin)
    db.add(row)
    return row
