"""Core-Engine durability tests: internal consumers do not depend on n8n."""
from datetime import timedelta

import pytest
from sqlalchemy import select, text

from fattech import core_engine
from fattech.core_engine import claim, flush_buffers, process, run_once, schedule
from fattech.core_models import (CoreDelivery, CoreFailure, EventFact, MessageBatch,
                                 MessageBuffer, ProcessedEvent)
from fattech.models import Outbox, Record, now
from fattech.services import audit_event
from fattech.events import emit_event, envelope_for
from test_api import system as system  # noqa: F401 - share the full tenant/auth fixture


def test_consumers_run_without_n8n_and_message_batch_is_atomic(system, monkeypatch):
    client, app, factory, tenant_id, *_ = system
    with factory() as db:
        contact = Record(tenant_id=tenant_id, kind="contacts", data={"name": "Core Contact"})
        db.add(contact)
        db.flush()
        conversation = Record(tenant_id=tenant_id, kind="conversations", data={
            "title": "Core conversation", "contact_id": contact.id, "channel": "instagram", "status": "open"})
        db.add(conversation)
        db.flush()
        message = Record(tenant_id=tenant_id, kind="messages", data={
            "conversation_id": conversation.id, "contact_id": contact.id, "direction": "inbound",
            "status": "received", "body": "Olá", "channel": "instagram"})
        db.add(message)
        db.flush()
        audit_event(db, tenant_id, None, "messages.received", message.id,
                    {"conversation_id": conversation.id, "contact_id": contact.id})
        db.commit()

    # The n8n URL is intentionally empty in this fixture. Core workers remain useful.
    assert not app.state.settings.n8n_outbound_url
    assert run_once(factory, app.state.settings) > 0
    with factory() as db:
        deliveries = list(db.scalars(select(CoreDelivery).where(CoreDelivery.tenant_id == tenant_id)))
        assert {delivery.worker_role for delivery in deliveries} >= {"bi", "messaging"}
        assert all(delivery.status == "completed" for delivery in deliveries)
        assert db.scalar(select(EventFact).where(EventFact.tenant_id == tenant_id)) is not None
        buffer = db.get(MessageBuffer, (tenant_id, conversation.id))
        assert buffer is not None
        buffer.due_at = now() - timedelta(seconds=1)
        db.commit()
    original_emit = core_engine.emit_event

    def interrupt_flush(*args, **kwargs):
        original_emit(*args, **kwargs)
        args[0].flush()
        raise RuntimeError("crash after publication, before buffer completion")

    with monkeypatch.context() as patch:
        patch.setattr(core_engine, "emit_event", interrupt_flush)
        with pytest.raises(RuntimeError), factory() as db:
            flush_buffers(db, tenant_id, app.state.settings)
    with factory() as db:
        assert db.get(MessageBuffer, (tenant_id, conversation.id)) is not None
        assert db.scalar(select(MessageBatch).where(MessageBatch.tenant_id == tenant_id)) is None
        assert db.scalar(select(Outbox).where(Outbox.event_type == "messaging.session.buffered")) is None
        assert flush_buffers(db, tenant_id, app.state.settings) == 1
        batch = db.scalar(select(MessageBatch).where(MessageBatch.tenant_id == tenant_id))
        assert batch and batch.status == "ready" and batch.message_ids == [message.id]
        child = db.scalar(select(Outbox).where(Outbox.event_type == "messaging.session.buffered"))
        assert child and child.hops == 1 and child.trace_id
        # A different event repeating the same message must also be harmless after flushing.
        audit_event(db, tenant_id, None, "messages.received", message.id)
        db.commit()
    # Scheduling and processing a replay has no second effect.
    run_once(factory, app.state.settings)
    with factory() as db:
        assert db.scalar(select(MessageBatch.id).where(MessageBatch.tenant_id == tenant_id)) == batch.id
        assert len(list(db.scalars(select(ProcessedEvent).where(ProcessedEvent.tenant_id == tenant_id,
                                                  ProcessedEvent.worker_role == "messaging")))) == 2
        assert db.get(MessageBuffer, (tenant_id, conversation.id)) is None


def test_invalid_envelope_is_dead_lettered_and_can_be_recovered_by_attempt_count(system):
    _client, app, factory, tenant_id, *_ = system
    with factory() as db:
        source = Outbox(tenant_id=tenant_id, event_type="invalid event", payload={}, trace_id="legacy")
        db.add(source)
        db.commit()
    run_once(factory, app.state.settings)
    with factory() as db:
        delivery = db.scalar(select(CoreDelivery).where(CoreDelivery.tenant_id == tenant_id,
                                                         CoreDelivery.event_id == source.id,
                                                         CoreDelivery.worker_role == "bi"))
        assert delivery and delivery.status == "dead_letter"
        assert db.scalar(select(CoreFailure).where(CoreFailure.delivery_id == delivery.id)) is not None
    response = _client.post(f"/api/v1/core/deliveries/{delivery.id}/retry", json={"expected_attempts": 1})
    assert response.status_code == 200
    assert _client.post(f"/api/v1/core/deliveries/{delivery.id}/retry",
                        json={"expected_attempts": 1}).status_code == 409
    with factory() as db:
        recovered = db.get(CoreDelivery, delivery.id)
        assert recovered.attempts == 1 and recovered.cycle_attempts == 0 and recovered.status == "pending"


def test_expired_lease_cannot_commit_or_duplicate_effect(system):
    _, app, factory, tenant_id, *_ = system
    with factory() as db:
        schedule(db, tenant_id)
        first = claim(db, tenant_id, "bi")
    assert first
    with factory() as db:
        delivery = db.get(CoreDelivery, first["id"])
        delivery.locked_until = now() - timedelta(seconds=1)
        db.commit()
    with factory() as db:
        second = claim(db, tenant_id, "bi")
    assert second["token"] != first["token"]
    assert process(factory, app.state.settings, first) is False
    assert process(factory, app.state.settings, second) is True
    assert process(factory, app.state.settings, second) is False
    with factory() as db:
        assert db.get(CoreDelivery, first["id"]).attempts == 2
        assert len(list(db.scalars(select(EventFact).where(EventFact.tenant_id == tenant_id)))) == 1


def test_handler_effect_rolls_back_before_receipt_and_retry(system, monkeypatch):
    _, app, factory, tenant_id, *_ = system
    with factory() as db:
        schedule(db, tenant_id)
        ticket = claim(db, tenant_id, "bi")
    original = core_engine.HANDLERS["bi"]

    def broken(db, source, envelope, settings):
        original(db, source, envelope, settings)
        db.flush()
        raise RuntimeError("sensitive contents must not be stored")

    monkeypatch.setitem(core_engine.HANDLERS, "bi", broken)
    assert process(factory, app.state.settings, ticket) is False
    with factory() as db:
        assert list(db.scalars(select(EventFact).where(EventFact.tenant_id == tenant_id))) == []
        assert list(db.scalars(select(ProcessedEvent).where(ProcessedEvent.tenant_id == tenant_id))) == []
        delivery = db.get(CoreDelivery, ticket["id"])
        assert delivery.last_error == "handler_failed"
        delivery.available_at = now() - timedelta(seconds=1)
        db.commit()
    monkeypatch.setitem(core_engine.HANDLERS, "bi", original)
    with factory() as db:
        retried = claim(db, tenant_id, "bi")
    assert process(factory, app.state.settings, retried)


def test_canonical_lineage_preserves_legacy_trace_and_hop_limit(system):
    _, _, factory, tenant_id, second, *_ = system
    with factory() as db:
        source = Outbox(tenant_id=tenant_id, event_type="contacts.created", payload={}, trace_id="a" * 64)
        db.add(source)
        db.flush()
        parent = envelope_for(source)
        assert parent == envelope_for(source)
        assert parent.actor.id == "legacy-unknown"
        for _ in range(5):
            child = emit_event(db, tenant_id, "core.test.created", {}, parent=parent)
            db.flush()
            envelope = envelope_for(child)
            assert envelope.event_id != parent.event_id and envelope.trace_id == parent.trace_id
            assert envelope.hops == parent.hops + 1
            parent = envelope
        with pytest.raises(ValueError):
            emit_event(db, tenant_id, "core.test.created", {}, parent=parent)
        with pytest.raises(ValueError):
            emit_event(db, second, "core.test.created", {}, parent=parent)
        db.rollback()


def test_integration_cannot_schedule_internal_messaging(system):
    _, app, factory, tenant_id, *_ = system
    with factory() as db:
        source = Outbox(tenant_id=tenant_id, event_type="messages.received", payload={}, origin="integration")
        db.add(source)
        db.commit()
    run_once(factory, app.state.settings)
    with factory() as db:
        assert db.scalar(select(CoreDelivery).where(CoreDelivery.event_id == source.id,
                         CoreDelivery.worker_role == "messaging")) is None
        assert db.get(Outbox, source.id).status == "pending"


def test_migration_adds_outbox_metadata_to_existing_database(system):
    from fattech.migrate import migrate
    _, app, factory, tenant_id, *_ = system
    with app.state.engine.begin() as connection:
        connection.execute(text("DELETE FROM schema_migrations WHERE version = '0008'"))
        connection.execute(text("ALTER TABLE event_outbox DROP COLUMN actor"))
        connection.execute(text("ALTER TABLE event_outbox DROP COLUMN origin"))
    migrate(app.state.engine)
    migrate(app.state.engine)
    with factory() as db:
        source = db.scalar(select(Outbox).where(Outbox.tenant_id == tenant_id))
        assert source.actor == {} and source.origin == "legacy"
