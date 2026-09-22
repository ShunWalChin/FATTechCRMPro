"""Real inbound ingestion: identities, isolation, replays, service window and atomicity."""
import hashlib
import hmac
import json
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from fattech import instagram_ingest
from fattech.db import set_tenant
from fattech.models import Audit, Idempotency, InstagramAccount, Outbox, Record, now
from test_api import system as system

ACCOUNT_A = "17841400000000010"
ACCOUNT_B = "17841400000000020"
ACCOUNT_C = "17841400000000030"
SENDER = "123456789012345"
ROUTE = "/api/public/webhooks/instagram"


@pytest.fixture
def inbox(system):
    client, app, factory, first, second, *_ = system
    with factory() as db:
        db.add_all([InstagramAccount(tenant_id=first, instagram_user_id=ACCOUNT_A, label="Principal"),
                    InstagramAccount(tenant_id=first, instagram_user_id=ACCOUNT_C, label="Segunda"),
                    InstagramAccount(tenant_id=second, instagram_user_id=ACCOUNT_B, label="Outra organização")])
        db.commit()
    return client, app, factory, first, second


def message(mid="mid-001", body="Olá, quero saber mais", account=ACCOUNT_A, timestamp=None, **extra):
    return {"sender": {"id": SENDER}, "recipient": {"id": account},
            "timestamp": timestamp if timestamp is not None else int(now().timestamp() * 1000),
            "message": {"mid": mid, "text": body, **extra}}


def envelope(*events, account=ACCOUNT_A):
    return {"object": "instagram", "entry": [{"id": account, "messaging": list(events)}]}


def deliver(client, payload):
    raw = json.dumps(payload, separators=(",", ":")).encode()
    signature = "sha256=" + hmac.new(b"meta-test-secret", raw, hashlib.sha256).hexdigest()
    return client.post(ROUTE, content=raw, headers={"X-Hub-Signature-256": signature,
                                                  "Content-Type": "application/json"})


def records(db, tenant_id, kind):
    set_tenant(db, tenant_id)
    return db.scalars(select(Record).where(Record.tenant_id == tenant_id, Record.kind == kind)).all()


def test_different_messages_for_same_account_enter_one_operational_conversation(inbox):
    client, _, factory, first, _ = inbox
    first_delivery = deliver(client, envelope(message()))
    second_delivery = deliver(client, envelope(message(mid="mid-002", body="Preciso de uma proposta")))
    assert first_delivery.status_code == second_delivery.status_code == 202
    assert first_delivery.json()["id"] != second_delivery.json()["id"]
    with factory() as db:
        contacts, conversations, messages = (records(db, first, kind) for kind in ("contacts", "conversations", "messages"))
        assert len(contacts) == len(conversations) == 1
        assert len(messages) == 2
        contact, conversation = contacts[0], conversations[0]
        assert not contact.data["consent"] and "consented_at" not in contact.data
        assert conversation.data["last_inbound_at"]
        assert conversation.data["last_message"] == "Preciso de uma proposta"
        assert {item.data["conversation_id"] for item in messages} == {conversation.id}
        assert {item.data["direction"] for item in messages} == {"inbound"}
        assert {item.data["status"] for item in messages} == {"received"}
    found = client.get(f"/api/v1/messages?conversation_id={conversation.id}")
    assert found.status_code == 200 and found.json()["total"] == 2
    assert client.get("/api/v1/conversations").json()["total"] == 1


def test_replay_deduplicates_envelope_and_message_even_with_changed_metadata(inbox):
    client, _, factory, first, _ = inbox
    payload = envelope(message())
    assert deliver(client, payload).json()["messages_created"] == 1
    assert deliver(client, payload).json()["duplicate"] is True
    payload["entry"][0]["time"] = 12345
    payload["entry"][0]["messaging"][0]["message"]["text"] = "Changed replay must not rewrite history"
    repeated = deliver(client, payload)
    assert repeated.status_code == 202
    assert repeated.json()["messages_duplicate"] == 1 and repeated.json()["messages_created"] == 0
    with factory() as db:
        stored = records(db, first, "messages")
        assert len(stored) == 1 and stored[0].data["body"] == "Olá, quero saber mais"
        assert len(records(db, first, "contacts")) == len(records(db, first, "conversations")) == 1
        audits = db.scalars(select(Audit).where(Audit.action == "messages.received", Audit.tenant_id == first)).all()
        assert len(audits) == 1


def test_one_envelope_can_materialize_multiple_messages_in_order(inbox):
    client, _, factory, first, _ = inbox
    event = message()
    response = deliver(client, envelope(event, event, message(mid="mid-002")))
    assert response.status_code == 202
    assert response.json()["messages_created"] == 2 and response.json()["messages_duplicate"] == 1
    with factory() as db:
        assert len(records(db, first, "messages")) == 2


def test_sender_and_mid_are_scoped_to_account_and_tenant(inbox):
    client, _, factory, first, second = inbox
    for account in (ACCOUNT_A, ACCOUNT_B, ACCOUNT_C):
        response = deliver(client, envelope(message(account=account), account=account))
        assert response.status_code == 202 and response.json()["messages_created"] == 1
    with factory() as db:
        assert len(records(db, first, "contacts")) == len(records(db, first, "conversations")) == 2
        assert len(records(db, second, "contacts")) == len(records(db, second, "conversations")) == 1
        foreign_message = records(db, second, "messages")[0]
    assert client.get(f"/api/v1/messages/{foreign_message.id}").status_code == 404
    assert client.get("/api/v1/messages").json()["total"] == 2


@pytest.mark.parametrize("other_account", [ACCOUNT_B, "99999999999999999"])
def test_mixed_or_partly_unknown_accounts_reject_entire_envelope(inbox, other_account):
    client, _, factory, first, second = inbox
    payload = envelope(message())
    payload["entry"].append({"id": other_account, "messaging": [message(account=other_account)]})
    response = deliver(client, payload)
    assert response.status_code == 404
    assert first not in response.text and second not in response.text
    with factory() as db:
        for tenant_id in (first, second):
            assert not records(db, tenant_id, "messages")
            assert not records(db, tenant_id, "contacts")
        assert not db.scalar(select(Outbox).where(Outbox.event_type == "instagram.webhook.received"))


def test_multiple_known_accounts_for_same_tenant_are_supported(inbox):
    client, _, factory, first, _ = inbox
    payload = envelope(message())
    payload["entry"].append({"id": ACCOUNT_C, "messaging": [message(account=ACCOUNT_C)]})
    response = deliver(client, payload)
    assert response.status_code == 202 and response.json()["messages_created"] == 2
    with factory() as db:
        assert len(records(db, first, "conversations")) == 2


def test_out_of_order_and_future_timestamps_cannot_extend_service_window(inbox):
    client, _, factory, first, _ = inbox
    clock = now() - timedelta(hours=2)
    assert deliver(client, envelope(message(timestamp=int(clock.timestamp() * 1000)))).status_code == 202
    for mid, timestamp in (("old", clock - timedelta(days=2)), ("future", clock + timedelta(days=2))):
        response = deliver(client, envelope(message(mid=mid, body=mid, timestamp=int(timestamp.timestamp() * 1000))))
        assert response.status_code == 202
    with factory() as db:
        conversation = records(db, first, "conversations")[0]
        assert conversation.data["last_inbound_at"].startswith(clock.isoformat()[:23])
        assert conversation.data["last_message"] == "Olá, quero saber mais"
        assert len(records(db, first, "messages")) == 3
        future = next(item for item in records(db, first, "messages") if item.data["body"] == "future")
        assert future.data["occurred_at"] is None


def test_undated_message_does_not_grant_send_window(inbox):
    client, _, factory, first, _ = inbox
    event = message()
    del event["timestamp"]
    assert deliver(client, envelope(event)).status_code == 202
    with factory() as db:
        assert records(db, first, "conversations")[0].data["last_inbound_at"] is None
        assert len(records(db, first, "messages")) == 1


def test_echoes_receipts_wrong_recipient_and_legacy_messages_do_not_create_contacts(inbox):
    client, _, factory, first, _ = inbox
    outbound = message(mid="outbound")
    outbound["sender"]["id"] = ACCOUNT_A
    outbound["recipient"]["id"] = SENDER
    events = [message(is_echo=True), outbound, {"read": {"mid": "read-1"}},
              {"reaction": {"mid": "react-1"}}, {"message": {"text": "legacy"}},
              message(mid="wrong-recipient", account=ACCOUNT_B)]
    response = deliver(client, envelope(*events))
    assert response.status_code == 202 and response.json()["events_ignored"] == len(events)
    with factory() as db:
        assert not records(db, first, "contacts") and not records(db, first, "messages")


def test_attachment_is_a_visible_placeholder_without_fetching_or_persisting_url(inbox):
    client, _, factory, first, _ = inbox
    media_url = "https://example.test/private-image?access_token=never-copy-media-token"
    response = deliver(client, envelope(message(body="", attachments=[{"type": "image", "payload": {"url": media_url}}])))
    assert response.status_code == 202 and response.json()["messages_created"] == 1
    with factory() as db:
        stored = records(db, first, "messages")[0]
        assert stored.data["body"] == "[Imagem recebido pelo Instagram]"
        assert stored.data["attachments"] == [{"type": "image"}]
        assert media_url not in json.dumps(stored.data)
        outbox = db.scalars(select(Outbox).where(Outbox.tenant_id == first)).all()
        assert media_url not in json.dumps([item.payload for item in outbox])


def test_stop_revokes_consent_and_subsequent_message_does_not_restore_it(inbox):
    client, _, factory, first, _ = inbox
    deliver(client, envelope(message()))
    with factory() as db:
        contact = records(db, first, "contacts")[0]
        contact.data = {**contact.data, "consent": True}
        db.commit()
    deliver(client, envelope(message(mid="stop", body="PARAR")))
    deliver(client, envelope(message(mid="return", body="Tenho uma dúvida")))
    with factory() as db:
        contact = records(db, first, "contacts")[0]
        assert contact.data["consent"] is False and contact.data["opted_out_at"]
        assert len(records(db, first, "messages")) == 3


def test_forged_signature_and_malformed_envelopes_produce_no_records(inbox):
    client, _, factory, first, _ = inbox
    forged = client.post(ROUTE, json=envelope(message()), headers={"X-Hub-Signature-256": "sha256=" + "0" * 64})
    assert forged.status_code == 401
    for payload in ([1], None, {}, {"object": "instagram", "entry": [1]},
                    {"object": "instagram", "entry": []}, {"object": "instagram", "entry": [{}]}):
        assert deliver(client, payload).status_code == 422
    with factory() as db:
        assert not records(db, first, "messages") and not records(db, first, "contacts")


def test_failure_after_first_message_rolls_back_entire_envelope_and_retry_recovers(inbox, monkeypatch):
    _, app, factory, first, _ = inbox
    original = instagram_ingest.audit_event
    seen = []

    def failing_audit(*args, **kwargs):
        seen.append(args[3])
        if seen.count("messages.received") == 2:
            raise RuntimeError("injected persistence failure")
        return original(*args, **kwargs)

    payload = envelope(message(), message(mid="mid-002"))
    monkeypatch.setattr(instagram_ingest, "audit_event", failing_audit)
    with TestClient(app, raise_server_exceptions=False) as client:
        assert deliver(client, payload).status_code == 500
        with factory() as db:
            for kind in ("contacts", "conversations", "messages"):
                assert not records(db, first, kind)
            assert not db.scalar(select(Idempotency).where(Idempotency.tenant_id == first))
            assert not db.scalar(select(Outbox).where(Outbox.event_type == "messages.received"))
        monkeypatch.setattr(instagram_ingest, "audit_event", original)
        response = deliver(client, payload)
        assert response.status_code == 202 and response.json()["messages_created"] == 2
