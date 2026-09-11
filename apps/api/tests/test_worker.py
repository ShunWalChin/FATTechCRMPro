from datetime import timedelta

import httpx
from sqlalchemy import select

from fattech.config import Settings
from fattech.db import make_engine, session_factory
from fattech.migrate import migrate
from fattech.models import Outbox, Tenant, now
from fattech.worker import claim_event, deliver_event, finish_event, run_once


def test_durable_claim_retry_dead_letter_and_stale_worker(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'worker.db'}")
    migrate(engine)
    factory = session_factory(engine)
    with factory() as db:
        tenant = Tenant(name="Worker Test", slug="worker-test")
        db.add(tenant)
        db.flush()
        event = Outbox(tenant_id=tenant.id, event_type="contacts.created", payload={"id": "example"})
        db.add(event)
        db.commit()
        tenant_id, event_id = tenant.id, event.id
    with factory() as db:
        first = claim_event(db, tenant_id)
    with factory() as db:
        assert claim_event(db, tenant_id) is None
        expired = db.get(Outbox, event_id)
        expired.locked_until = now() - timedelta(seconds=1)
        db.commit()
    with factory() as db:
        second = claim_event(db, tenant_id)
        assert second["attempts"] == 2 and first["claim_token"] != second["claim_token"]
        assert finish_event(db, first) is False
        assert finish_event(db, second, error="network", max_attempts=2) is True
        assert db.get(Outbox, event_id).status == "dead_letter"
        assert claim_event(db, tenant_id) is None
    engine.dispose()


def test_worker_delivery_signature_failure_classes_and_no_configuration(tmp_path):
    import hashlib
    import hmac
    import json

    settings = Settings(_env_file=None, env="test", webhook_secret="test-secret-" * 4,
                        n8n_outbound_url="https://n8n.example.com/webhook/crm")
    claim = {"id": "event-001", "event_type": "contacts.created", "payload": {"id": "contact"},
             "trace_id": "trace-001", "hops": 0, "attempts": 1}
    received = []

    def handler(request):
        received.append(request)
        timestamp = request.headers["X-Fattech-Timestamp"]
        expected = hmac.new(settings.webhook_secret.encode(), timestamp.encode() + b"." + request.content, hashlib.sha256).hexdigest()
        assert request.headers["X-Fattech-Signature"] == "sha256=" + expected
        assert request.headers["Idempotency-Key"] == claim["id"]
        assert json.loads(request.content)["hops"] == 1
        return httpx.Response(202)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert deliver_event(client, settings, claim) == (None, False)
        assert deliver_event(client, settings, {**claim, "hops": 5}) == ("hop_limit_exceeded", True)
        assert len(received) == 1
    for code, expected in ((429, False), (503, False), (401, True), (302, True)):
        with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(code))) as client:
            assert deliver_event(client, settings, claim) == (f"upstream_http_{code}", expected)
    engine = make_engine(f"sqlite:///{tmp_path / 'worker.db'}")
    migrate(engine)
    factory = session_factory(engine)
    with factory() as db:
        tenant = Tenant(name="Worker Test", slug="worker-test")
        db.add(tenant)
        db.flush()
        db.add(Outbox(tenant_id=tenant.id, event_type="test.event", payload={}))
        db.commit()
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(204))) as client:
        assert run_once(factory, Settings(_env_file=None), client) == 0
        assert run_once(factory, settings, client) == 1
    with factory() as db:
        event = db.scalar(select(Outbox))
        assert event.status == "delivered" and event.attempts == 1
    engine.dispose()
