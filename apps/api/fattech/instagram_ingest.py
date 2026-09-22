"""Authenticated Instagram messages become durable CRM records in the caller's transaction.

Only the signature-verifying ingress calls this module. No provider call or delivery is
performed here. Contact locks serialize identity creation and event receipts, including
different envelopes carrying the same provider message. Unknown content is never a tool.
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from .compliance import instant, is_opt_out_keyword
from .models import Idempotency, Record, now
from .services import audit_event, create_record, lock_contacts, scoped


def digest(parts):
    return hashlib.sha256(json.dumps(parts, separators=(",", ":")).encode()).hexdigest()


def outbox_envelope(payload):
    """Keep the n8n envelope structure, excluding temporary bearer URLs in media payloads."""
    result = json.loads(json.dumps(payload))
    for entry in result.get("entry", []):
        events = entry.get("messaging", [])
        for event in events if isinstance(events, list) else []:
            message = event.get("message") if isinstance(event, dict) else None
            if isinstance(message, dict) and isinstance(message.get("attachments"), list):
                message["attachments"] = [{"type": attachment.get("type", "unknown")}
                                          for attachment in message["attachments"] if isinstance(attachment, dict)]
    return result


def provider_timestamp(value, received_at):
    """Meta messaging timestamps are milliseconds; absent/invalid/future dates open no window."""
    if not isinstance(value, (float, int)) or isinstance(value, bool):
        return None
    try:
        value = datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    except (ValueError, OverflowError, OSError):
        return None
    if value < datetime(2000, 1, 1, tzinfo=timezone.utc) or value > received_at + timedelta(minutes=5):
        return None
    return min(value, received_at)


def inbound_event(account_id, event, received_at):
    """Ignore echoes, receipts and malformed legacy events without guessing sender identity."""
    if not isinstance(event, dict) or not isinstance(event.get("message"), dict):
        return None
    message = event["message"]
    if message.get("is_echo") or message.get("is_deleted"):
        return None
    sender = event.get("sender")
    recipient = event.get("recipient")
    if not isinstance(sender, dict) or not isinstance(recipient, dict):
        return None
    sender_id, recipient_id = str(sender.get("id") or ""), str(recipient.get("id") or "")
    if not sender_id.isascii() or not sender_id.isdigit() or len(sender_id) > 64:
        return None
    if recipient_id != account_id or sender_id == account_id:
        return None
    mid = message.get("mid")
    if not isinstance(mid, str) or not mid.strip() or len(mid) > 512:
        return None
    body = message.get("text") if isinstance(message.get("text"), str) else ""
    types = []
    attachments = message.get("attachments")
    if isinstance(attachments, list):
        for attachment in attachments[:20]:
            if not isinstance(attachment, dict):
                continue
            kind = attachment.get("type")
            types.append(kind if kind in {"image", "audio", "video", "file", "share", "story_mention"} else "unknown")
    if not body.strip() and not types:
        return None
    labels = {"image": "Imagem", "audio": "Áudio", "video": "Vídeo", "file": "Arquivo",
              "share": "Publicação compartilhada", "story_mention": "Menção em story", "unknown": "Anexo"}
    display = body if body.strip() else "\n".join(f"[{labels[kind]} recebido pelo Instagram]" for kind in types)
    return {"mid": mid, "sender_id": sender_id, "body": display[:10000],
            "body_truncated": len(display) > 10000, "attachments": [{"type": kind} for kind in types],
            "occurred_at": provider_timestamp(event.get("timestamp"), received_at)}


def ingest_messages(db, tenant_id, payload):
    """Return counters; every message, receipt, contact and event commits together in ingress."""
    lock_contacts(db, tenant_id)
    result = {"messages_created": 0, "messages_duplicate": 0, "events_ignored": 0}
    received_at = now()
    for entry in payload["entry"]:
        account_id = str(entry["id"])
        events = entry.get("messaging", [])
        if not isinstance(events, list):
            result["events_ignored"] += 1
            continue
        for raw_event in events:
            event = inbound_event(account_id, raw_event, received_at)
            if event is None:
                result["events_ignored"] += 1
                continue
            event_key = "instagram:message:" + digest([account_id, event["mid"]])
            receipt = db.scalar(select(Idempotency).where(
                Idempotency.tenant_id == tenant_id, Idempotency.key == event_key))
            if receipt:
                # A provider redelivery may contain updated envelope metadata. First write wins.
                result["messages_duplicate"] += 1
                continue
            identity = digest([tenant_id, "instagram", account_id, event["sender_id"]])
            contact = db.scalar(scoped(tenant_id, "contacts").where(
                Record.data["channel_identity"].as_string() == identity).with_for_update())
            if contact is None:
                contact = create_record(db, tenant_id, None, "contacts", {
                    "name": f"Contato Instagram · {event['sender_id'][-6:]}",
                    "source": "instagram", "consent": False})
                contact.data = {**contact.data, "channel_identity": identity,
                                "provider_account_id": account_id, "provider_sender_id": event["sender_id"]}
                db.flush()
            conversation = db.scalar(scoped(tenant_id, "conversations").where(
                Record.data["channel_identity"].as_string() == identity).with_for_update())
            if conversation is None:
                conversation = create_record(db, tenant_id, None, "conversations", {
                    "title": contact.data["name"], "contact_id": contact.id,
                    "channel": "instagram", "owner_id": contact.data.get("owner_id")})
                conversation.data = {**conversation.data, "channel_identity": identity,
                                     "provider_account_id": account_id,
                                     "provider_sender_id": event["sender_id"]}
            occurred_at = event["occurred_at"]
            message = Record(tenant_id=tenant_id, kind="messages", data={
                "conversation_id": conversation.id, "contact_id": contact.id, "direction": "inbound",
                "status": "received", "body": event["body"], "body_truncated": event["body_truncated"],
                "channel": "instagram", "provider_message_id": event["mid"],
                "provider_account_id": account_id, "provider_sender_id": event["sender_id"],
                "attachments": event["attachments"], "received_at": received_at.isoformat(),
                "occurred_at": occurred_at.isoformat() if occurred_at else None})
            db.add(message)
            db.flush()
            data = dict(conversation.data)
            previous_inbound = instant(data.get("last_inbound_at"))
            if occurred_at and (not previous_inbound or occurred_at >= previous_inbound):
                data.update(last_inbound_at=occurred_at.isoformat(), last_message=event["body"][:1000],
                            last_message_id=message.id, status="open")
            elif not previous_inbound:
                # An undated authentic message is still visible, but cannot grant a send window.
                data.update(last_message=event["body"][:1000], last_message_id=message.id, status="open")
            conversation.data, conversation.version = data, conversation.version + 1
            conversation.updated_at = received_at
            if is_opt_out_keyword(event["body"]):
                contact.data = {**contact.data, "consent": False,
                                "opted_out_at": contact.data.get("opted_out_at") or received_at.isoformat()}
                contact.version, contact.updated_at = contact.version + 1, received_at
                audit_event(db, tenant_id, None, "contacts.opted_out", contact.id,
                            {"channel": "instagram", "conversation_id": conversation.id})
            audit_event(db, tenant_id, None, "messages.received", message.id,
                        {"conversation_id": conversation.id, "contact_id": contact.id, "channel": "instagram"})
            db.add(Idempotency(tenant_id=tenant_id, key=event_key, body_hash=digest([account_id, event["mid"]]),
                               response={"message_id": message.id, "conversation_id": conversation.id,
                                         "contact_id": contact.id}))
            db.flush()
            result["messages_created"] += 1
    return result
