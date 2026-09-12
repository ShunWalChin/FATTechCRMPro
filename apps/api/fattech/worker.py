"""Durable at-least-once event delivery. Configure n8n to deduplicate Idempotency-Key before effects."""
import argparse
import hashlib
import hmac
import json
import logging
import signal
import threading
import time
from datetime import timedelta

import httpx
from sqlalchemy import and_, or_, select, update

from .config import get_settings
from .db import make_engine, session_factory, set_tenant
from .outbound import assert_safe_outbound_url
from .models import Outbox, Tenant, now, uid
from .worker_health import HEARTBEAT_PATH, write_heartbeat

log = logging.getLogger("fattech.worker")


def claim_event(db, tenant_id):
    """One short transaction; the network call happens after the lease is committed."""
    set_tenant(db, tenant_id)
    instant = now()
    eligible = or_(and_(Outbox.status == "pending", Outbox.available_at <= instant),
                   and_(Outbox.status == "processing", Outbox.locked_until <= instant))
    query = select(Outbox).where(Outbox.tenant_id == tenant_id, eligible).order_by(Outbox.created_at).limit(1)
    if db.bind.dialect.name == "postgresql":
        query = query.with_for_update(skip_locked=True)
    event = db.scalar(query)
    if event is None:
        db.rollback()
        return None
    token = uid()
    changed = db.execute(update(Outbox).where(Outbox.id == event.id, Outbox.tenant_id == tenant_id, eligible)
        .execution_options(synchronize_session="fetch")
        .values(status="processing", attempts=Outbox.attempts + 1, claim_token=token,
                locked_until=instant + timedelta(seconds=90)))
    if changed.rowcount != 1:
        db.rollback()
        return None
    db.refresh(event)
    claim = {"id": event.id, "tenant_id": tenant_id, "claim_token": token, "attempts": event.attempts,
             "event_type": event.event_type, "payload": event.payload, "trace_id": event.trace_id, "hops": event.hops}
    db.commit()
    return claim


def finish_event(db, claim, *, error=None, permanent=False, max_attempts=8):
    set_tenant(db, claim["tenant_id"])
    status = "delivered" if error is None else ("dead_letter" if permanent or claim["attempts"] >= max_attempts else "pending")
    changed = db.execute(update(Outbox).where(Outbox.id == claim["id"], Outbox.tenant_id == claim["tenant_id"],
        Outbox.status == "processing", Outbox.claim_token == claim["claim_token"])
        .execution_options(synchronize_session="fetch")
        .values(status=status, claim_token=None, locked_until=None, last_error=error,
                available_at=now() + timedelta(seconds=min(3600, 5 * 2 ** min(claim["attempts"], 10)))))
    db.commit()
    return changed.rowcount == 1


def deliver_event(client, settings, claim):
    if claim["hops"] >= 5:
        return "hop_limit_exceeded", True
    if claim["attempts"] > settings.worker_max_attempts:
        return "attempt_limit_exceeded", True
    body = json.dumps({"id": claim["id"], "event_type": claim["event_type"], "payload": claim["payload"],
        "trace_id": claim["trace_id"], "hops": claim["hops"] + 1}, separators=(",", ":"), ensure_ascii=False).encode()
    timestamp = str(int(time.time()))
    signature = hmac.new(settings.webhook_secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    headers = {"Content-Type": "application/json", "Idempotency-Key": claim["id"],
               "X-Fattech-Timestamp": timestamp, "X-Fattech-Signature": "sha256=" + signature}
    if settings.n8n_outbound_token:
        headers["Authorization"] = "Bearer " + settings.n8n_outbound_token
    try:
        # Stream just the headers/status; response bodies are untrusted and can be unbounded.
        with client.stream("POST", settings.n8n_outbound_url, content=body, headers=headers) as response:
            if 200 <= response.status_code < 300:
                return None, False
            transient = response.status_code in (408, 425, 429) or response.status_code >= 500
            return f"upstream_http_{response.status_code}", not transient
    except httpx.HTTPError:
        return "upstream_network_error", False


def run_once(factory, settings, client, *, on_progress=None):
    if not settings.n8n_outbound_url:
        return 0
    with factory() as db:
        tenant_ids = list(db.scalars(select(Tenant.id)))
    processed = 0
    for tenant_id in tenant_ids:
        with factory() as db:
            claim = claim_event(db, tenant_id)
        if claim is None:
            if on_progress is not None:
                on_progress()
            continue
        error, permanent = deliver_event(client, settings, claim)
        with factory() as db:
            finish_event(db, claim, error=error, permanent=permanent, max_attempts=settings.worker_max_attempts)
        processed += 1
        if on_progress is not None:
            on_progress()
        log.info("event=%s result=%s attempt=%s", claim["id"], error or "delivered", claim["attempts"])
    return processed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()
    HEARTBEAT_PATH.unlink(missing_ok=True)
    engine = make_engine(settings.database_url)
    factory = session_factory(engine)
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    if not settings.n8n_outbound_url:
        log.warning("n8n outbound is not configured; events remain pending without external delivery")
    else:
        # Refuse to start against a private or reserved destination instead of failing one event at a time.
        assert_safe_outbound_url(settings.n8n_outbound_url)
    with httpx.Client(timeout=httpx.Timeout(20, connect=5), follow_redirects=False, trust_env=False) as client:
        while not stop.is_set():
            try:
                processed = run_once(factory, settings, client, on_progress=write_heartbeat)
                # No independent timer: a stuck or failing loop must become unhealthy.
                write_heartbeat()
            except Exception as exc:
                HEARTBEAT_PATH.unlink(missing_ok=True)
                # Do not print database URLs, credential-bearing requests or customer payloads.
                log.error("worker_iteration_failed type=%s", type(exc).__name__)
                if args.once:
                    raise SystemExit(1) from None
                processed = 0
            if args.once:
                break
            if not processed:
                stop.wait(settings.worker_poll_seconds)
    engine.dispose()


if __name__ == "__main__":
    main()
