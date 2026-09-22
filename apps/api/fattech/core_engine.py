"""Transactional internal event execution; no broker, LLM or network call in a DB transaction."""
import hashlib
from datetime import timedelta

from pydantic import ValidationError
from sqlalchemy import and_, exists, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .core_models import (BufferedMessage, CoreDelivery, CoreFailure, CoreHeartbeat, EventFact,
                          MessageBatch, MessageBuffer, ProcessedEvent)
from .db import set_tenant
from .events import MAX_HOPS, emit_event, envelope_for, utc
from .models import Outbox, Record, Tenant, now, uid

# `openclaw` desperta agentes. Ele entra aqui, como consumidor do motor que ja existe, em vez
# de virar um segundo motor de automacao -- `fattech:walchat:two-engines-debt`.
ROLES = ("bi", "messaging", "openclaw")
LEASE_SECONDS = 90
BATCH_LIMIT = 50


def insert_unique(db, model, values, keys):
    insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    return db.execute(insert(model).values(**values).on_conflict_do_nothing(index_elements=keys))


def pulse(db, tenant_id, role):
    insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    statement = insert(CoreHeartbeat).values(tenant_id=tenant_id, worker_role=role, last_seen_at=now())
    db.execute(statement.on_conflict_do_update(index_elements=["tenant_id", "worker_role"],
                                              set_={"last_seen_at": now()}))


def schedule(db, tenant_id, *, limit=100):
    """Bounded fanout; neither reads nor changes external delivery status."""
    set_tenant(db, tenant_id)
    count = 0
    for role in ROLES:
        missing = ~exists(select(CoreDelivery.id).where(
            CoreDelivery.tenant_id == tenant_id, CoreDelivery.event_id == Outbox.id,
            CoreDelivery.worker_role == role))
        query = select(Outbox.id).where(Outbox.tenant_id == tenant_id, missing)
        if role == "messaging":
            query = query.where(Outbox.event_type == "messages.received", Outbox.origin.in_(("internal", "webhook")))
        if role == "openclaw":
            # So os tipos que algum agente ativo observa. Conjunto vazio nao cria entrega nenhuma,
            # e e essa a trava de rollback do estagio: sem agente ativo com gatilho, nada muda.
            from .agent_dispatch import tipos_observados
            observados = tipos_observados(db, tenant_id)
            if not observados:
                continue
            query = query.where(Outbox.event_type.in_(sorted(observados)))
        ids = list(db.scalars(query.order_by(Outbox.created_at, Outbox.id).limit(limit)))
        for event_id in ids:
            result = insert_unique(db, CoreDelivery, {"tenant_id": tenant_id, "event_id": event_id,
                                   "worker_role": role}, ["tenant_id", "event_id", "worker_role"])
            count += result.rowcount
    pulse(db, tenant_id, "scheduler")
    db.commit()
    return count


def claim(db, tenant_id, role):
    if role not in ROLES:
        raise ValueError("Unknown internal consumer")
    set_tenant(db, tenant_id)
    instant = now()
    eligible = or_(and_(CoreDelivery.status == "pending", CoreDelivery.available_at <= instant),
                   and_(CoreDelivery.status == "processing", CoreDelivery.locked_until <= instant))
    query = select(CoreDelivery).where(CoreDelivery.tenant_id == tenant_id,
        CoreDelivery.worker_role == role, eligible).order_by(CoreDelivery.created_at, CoreDelivery.id).limit(1)
    if db.bind.dialect.name == "postgresql":
        query = query.with_for_update(skip_locked=True)
    delivery = db.scalar(query)
    if delivery is None:
        db.rollback()
        return None
    token = uid()
    changed = db.execute(update(CoreDelivery).where(CoreDelivery.id == delivery.id,
        CoreDelivery.tenant_id == tenant_id, eligible).values(
            status="processing", attempts=CoreDelivery.attempts + 1,
            cycle_attempts=CoreDelivery.cycle_attempts + 1,
            claim_token=token, locked_until=instant + timedelta(seconds=LEASE_SECONDS))
                         .execution_options(synchronize_session=False))
    if changed.rowcount != 1:
        db.rollback()
        return None
    result = {"id": delivery.id, "tenant_id": tenant_id, "token": token, "role": role}
    db.commit()
    return result


def owns_claim(ticket, *, unexpired=True):
    clauses = [CoreDelivery.id == ticket["id"], CoreDelivery.tenant_id == ticket["tenant_id"],
               CoreDelivery.worker_role == ticket["role"], CoreDelivery.status == "processing",
               CoreDelivery.claim_token == ticket["token"]]
    if unexpired:
        clauses.append(CoreDelivery.locked_until > now())
    return clauses


def fail(db, ticket, code, *, permanent=False, max_attempts=8):
    """Record only safe codes; SQL errors and provider payloads may contain credentials or PII."""
    set_tenant(db, ticket["tenant_id"])
    changed = db.execute(update(CoreDelivery).where(*owns_claim(ticket, unexpired=False))
                         .values(claim_token=CoreDelivery.claim_token)
                         .execution_options(synchronize_session=False))
    if changed.rowcount != 1:
        db.rollback()
        return False
    delivery = db.get(CoreDelivery, ticket["id"])
    delivery.status = "dead_letter" if permanent or delivery.cycle_attempts >= max_attempts else "pending"
    delivery.last_error, delivery.claim_token, delivery.locked_until = code, None, None
    delivery.available_at = now() + timedelta(seconds=min(3600, 5 * 2 ** min(delivery.cycle_attempts, 10)))
    db.add(CoreFailure(tenant_id=ticket["tenant_id"], delivery_id=delivery.id,
                       attempt=delivery.attempts, error_code=code))
    db.commit()
    return True


def messaging_lock(db, tenant_id):
    """One lock order for adding and draining buffers, including their first insertion."""
    if db.bind.dialect.name == "postgresql":
        key = int.from_bytes(hashlib.sha256(f"fattech:core-buffer:{tenant_id}".encode()).digest()[:8],
                             "big", signed=True)
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
    else:
        db.execute(update(MessageBuffer).where(MessageBuffer.tenant_id == "")
                   .values(due_at=MessageBuffer.due_at))


def record_in_tenant(db, tenant_id, kind, record_id):
    if not isinstance(record_id, str):
        return None
    return db.scalar(select(Record).where(Record.tenant_id == tenant_id, Record.kind == kind,
                     Record.id == record_id, Record.deleted.is_(False)))


def project_event(db, source, envelope, settings):
    db.add(EventFact(event_id=source.id, tenant_id=source.tenant_id, event_type=envelope.event,
                     origin=source.origin, trace_id=str(envelope.trace_id), occurred_at=envelope.occurred_at))


def buffer_message(db, source, envelope, settings):
    # Integrations cannot turn an arbitrary event name into an internal command.
    if source.origin not in ("internal", "webhook") or envelope.event != "messages.received":
        return
    if envelope.hops >= MAX_HOPS:
        raise ValueError("hop_limit_exceeded")
    message = record_in_tenant(db, source.tenant_id, "messages", envelope.data.get("resource_id"))
    if not message or message.data.get("direction") != "inbound" or message.data.get("status") != "received":
        return
    conversation_id = message.data.get("conversation_id")
    conversation = record_in_tenant(db, source.tenant_id, "conversations", conversation_id)
    if not conversation:
        return
    messaging_lock(db, source.tenant_id)
    # Membership survives flushing. A second source event cannot repeat a completed message.
    added = insert_unique(db, BufferedMessage, {
        "tenant_id": source.tenant_id, "message_id": message.id, "conversation_id": conversation_id,
        "source_event_id": source.id, "received_at": message.created_at}, ["tenant_id", "message_id"])
    if added.rowcount != 1:
        return
    instant = now()
    buffer = db.get(MessageBuffer, (source.tenant_id, conversation_id))
    if buffer is None:
        db.add(MessageBuffer(tenant_id=source.tenant_id, conversation_id=conversation_id,
                              opened_at=instant, due_at=instant + timedelta(seconds=settings.core_debounce_seconds)))
    else:
        # Continuous typing never postpones the first batch indefinitely.
        buffer.due_at = min(instant + timedelta(seconds=settings.core_debounce_seconds),
                            utc(buffer.opened_at) + timedelta(seconds=settings.core_max_buffer_seconds))


def wake_agents(db, source, envelope, settings):
    from .agent_dispatch import despertar
    despertar(db, source, envelope, settings)


HANDLERS = {"bi": project_event, "messaging": buffer_message, "openclaw": wake_agents}


def process(factory, settings, ticket):
    """Effect, receipt and completion are atomic. A stale lease never produces an effect."""
    try:
        with factory() as db:
            set_tenant(db, ticket["tenant_id"])
            guarded = db.execute(update(CoreDelivery).where(*owns_claim(ticket))
                                 .values(claim_token=CoreDelivery.claim_token)
                                 .execution_options(synchronize_session=False))
            if guarded.rowcount != 1:
                db.rollback()
                return False
            delivery = db.get(CoreDelivery, ticket["id"])
            if delivery.cycle_attempts > settings.worker_max_attempts:
                raise ValueError("attempt_limit_exceeded")
            source = db.scalar(select(Outbox).where(Outbox.id == delivery.event_id,
                               Outbox.tenant_id == ticket["tenant_id"]))
            if source is None:
                raise ValueError("source_event_missing")
            receipt_key = (ticket["tenant_id"], source.id, ticket["role"])
            if db.get(ProcessedEvent, receipt_key) is None:
                envelope = envelope_for(source)
                HANDLERS[ticket["role"]](db, source, envelope, settings)
                db.add(ProcessedEvent(tenant_id=source.tenant_id, event_id=source.id, worker_role=ticket["role"]))
                db.flush()
            finished = db.execute(update(CoreDelivery).where(*owns_claim(ticket)).values(
                status="completed", completed_at=now(), locked_until=None, claim_token=None, last_error=None)
                                  .execution_options(synchronize_session=False))
            if finished.rowcount != 1:
                db.rollback()
                return False
            db.commit()
            return True
    except Exception as exc:
        # Do not persist exception text: validation embeds input and database errors embed SQL parameters.
        code = "invalid_event" if isinstance(exc, (ValidationError, ValueError)) else "handler_failed"
        with factory() as db:
            fail(db, ticket, code, permanent=code == "invalid_event", max_attempts=settings.worker_max_attempts)
        return False


def flush_buffers(db, tenant_id, settings, *, limit=10):
    """Drain and publish in one transaction; crashes leave either the buffer or the complete batch."""
    set_tenant(db, tenant_id)
    messaging_lock(db, tenant_id)
    instant = now()
    buffers = list(db.scalars(select(MessageBuffer).where(MessageBuffer.tenant_id == tenant_id,
                   MessageBuffer.due_at <= instant).order_by(MessageBuffer.due_at).limit(limit)))
    count = 0
    for buffer in buffers:
        entries = list(db.scalars(select(BufferedMessage).where(BufferedMessage.tenant_id == tenant_id,
            BufferedMessage.conversation_id == buffer.conversation_id, BufferedMessage.batch_id.is_(None))
            .order_by(BufferedMessage.received_at, BufferedMessage.message_id).limit(BATCH_LIMIT)))
        if not entries:
            db.delete(buffer)
            continue
        conversation = record_in_tenant(db, tenant_id, "conversations", buffer.conversation_id)
        contact = record_in_tenant(db, tenant_id, "contacts", conversation.data.get("contact_id")) if conversation else None
        reason = ("conversation_unavailable" if not conversation else
                  "conversation_closed" if conversation.data.get("status") == "closed" else
                  "contact_unavailable" if not contact else "contact_opted_out" if contact.data.get("opted_out_at") else None)
        batch = MessageBatch(id=uid(), tenant_id=tenant_id, conversation_id=buffer.conversation_id,
                             message_ids=[item.message_id for item in entries],
                             status="blocked" if reason else "ready", reason=reason)
        db.add(batch)
        parent_row = db.scalar(select(Outbox).where(Outbox.id == entries[0].source_event_id,
                               Outbox.tenant_id == tenant_id))
        parent = envelope_for(parent_row)
        emit_event(db, tenant_id, "messaging.session.buffered", {
            "resource_id": batch.id, "conversation_id": buffer.conversation_id,
            "message_ids": batch.message_ids, "status": batch.status, "reason": reason,
            "causation_event_ids": list(dict.fromkeys(entry.source_event_id for entry in entries)),
        }, parent=parent)
        db.flush()
        for entry in entries:
            entry.batch_id = batch.id
        db.flush()
        remains = db.scalar(select(BufferedMessage.message_id).where(BufferedMessage.tenant_id == tenant_id,
                           BufferedMessage.conversation_id == buffer.conversation_id,
                           BufferedMessage.batch_id.is_(None)).limit(1))
        if remains:
            buffer.due_at = instant
        else:
            db.delete(buffer)
        count += 1
    db.commit()
    return count


def run_once(factory, settings, *, per_role=25, on_progress=None):
    with factory() as db:
        tenant_ids = list(db.scalars(select(Tenant.id).order_by(Tenant.id)))
    count = 0
    for tenant_id in tenant_ids:
        with factory() as db:
            count += schedule(db, tenant_id)
        for role in ROLES:
            for _ in range(per_role):
                with factory() as db:
                    ticket = claim(db, tenant_id, role)
                if ticket is None:
                    break
                count += int(process(factory, settings, ticket))
                if on_progress:
                    on_progress()
            with factory() as db:
                set_tenant(db, tenant_id)
                pulse(db, tenant_id, role)
                db.commit()
        with factory() as db:
            count += flush_buffers(db, tenant_id, settings)
        if on_progress:
            on_progress()
    return count
