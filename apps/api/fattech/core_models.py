"""Durable internal consumers. External delivery remains owned by event_outbox."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base
from .models import now, uid


class CoreDelivery(Base):
    __tablename__ = "core_deliveries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "event_id", "worker_role", name="uq_core_delivery_consumer"),
        Index("ix_core_delivery_ready", "tenant_id", "worker_role", "status", "available_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    event_id: Mapped[str] = mapped_column(ForeignKey("event_outbox.id"))
    worker_role: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    cycle_attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claim_token: Mapped[str | None] = mapped_column(String(36), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProcessedEvent(Base):
    __tablename__ = "core_processed_events"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("event_outbox.id"), primary_key=True)
    worker_role: Mapped[str] = mapped_column(String(30), primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class CoreFailure(Base):
    __tablename__ = "core_event_failures"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    delivery_id: Mapped[str] = mapped_column(ForeignKey("core_deliveries.id"), index=True)
    attempt: Mapped[int] = mapped_column(Integer)
    error_code: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class CoreHeartbeat(Base):
    __tablename__ = "core_worker_heartbeats"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), primary_key=True)
    worker_role: Mapped[str] = mapped_column(String(30), primary_key=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class EventFact(Base):
    """Operational event counts, not a financial ledger. No customer text or secrets."""
    __tablename__ = "core_event_facts"
    __table_args__ = (Index("ix_core_facts_period", "tenant_id", "occurred_at", "event_type"),)
    event_id: Mapped[str] = mapped_column(ForeignKey("event_outbox.id"), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    event_type: Mapped[str] = mapped_column(String(100))
    origin: Mapped[str] = mapped_column(String(30))
    trace_id: Mapped[str] = mapped_column(String(36))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MessageBuffer(Base):
    __tablename__ = "core_message_buffers"
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("records.id"), primary_key=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class BufferedMessage(Base):
    __tablename__ = "core_buffered_messages"
    __table_args__ = (Index("ix_core_buffer_conversation", "tenant_id", "conversation_id", "received_at"),)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), primary_key=True)
    message_id: Mapped[str] = mapped_column(ForeignKey("records.id"), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("records.id"))
    source_event_id: Mapped[str] = mapped_column(ForeignKey("event_outbox.id"))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    batch_id: Mapped[str | None] = mapped_column(ForeignKey("core_message_batches.id"), nullable=True)


class MessageBatch(Base):
    __tablename__ = "core_message_batches"
    __table_args__ = (Index("ix_core_batches_created", "tenant_id", "created_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("records.id"))
    message_ids: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
