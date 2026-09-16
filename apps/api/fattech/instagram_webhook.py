"""Meta Instagram webhook ingress.

The endpoint only acknowledges authentic, new events. Business processing is
queued in the existing durable outbox so Meta retries cannot duplicate work.
"""
import hashlib
import hmac
import json
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_db
from .models import Audit, Idempotency, Outbox, Record, Tenant, now, uid


def register_instagram_webhook(app, settings):
    router = APIRouter(prefix="/api/public/webhooks/instagram", tags=["Instagram"])

    @router.get("")
    def verify(mode: str = Query(default="", alias="hub.mode"), challenge: str = Query(default="", alias="hub.challenge"), verify_token: str = Query(default="", alias="hub.verify_token")):
        if mode != "subscribe" or not settings.meta_verify_token or not verify_token or not hmac.compare_digest(verify_token, settings.meta_verify_token):
            raise HTTPException(403, "Verificação inválida")
        return int(challenge) if challenge.isdigit() else challenge

    @router.post("", status_code=202)
    async def receive(request: Request, db: Session = Depends(get_db), x_hub_signature_256: str = Header(default="")):
        if not settings.meta_app_secret:
            raise HTTPException(503, "Instagram não configurado")
        raw = await request.body()
        expected = "sha256=" + hmac.new(settings.meta_app_secret.encode(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, x_hub_signature_256):
            raise HTTPException(401, "Assinatura Meta inválida")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(422, "Payload JSON inválido") from exc
        if payload.get("object") != "instagram" or not isinstance(payload.get("entry"), list):
            raise HTTPException(422, "Envelope Instagram inválido")
        # Webhook delivery is tenant-neutral until the Instagram account id is resolved.
        tenant = db.scalar(select(Tenant).where(Tenant.slug == settings.public_tenant_slug))
        if tenant is None:
            raise HTTPException(503, "Tenant público não provisionado")
        delivery_id = payload.get("id") or (payload.get("entry") or [{}])[0].get("id") or uid()
        key = f"instagram:{delivery_id}"
        body_hash = hashlib.sha256(raw).hexdigest()
        previous = db.scalar(select(Idempotency).where(Idempotency.tenant_id == tenant.id, Idempotency.key == key))
        if previous:
            if previous.body_hash != body_hash:
                raise HTTPException(409, "Evento Instagram reutilizado com outro conteúdo")
            return {**previous.response, "duplicate": True}
        result = {"id": delivery_id, "status": "accepted", "duplicate": False}
        db.add(Idempotency(tenant_id=tenant.id, key=key, body_hash=body_hash, response=result))
        db.add(Outbox(tenant_id=tenant.id, event_type="instagram.webhook.received", payload=payload,
                      trace_id=delivery_id))
        db.add(Audit(tenant_id=tenant.id, actor_id=None, action="instagram.webhook.accepted",
                     resource_id=delivery_id, details={"object": payload.get("object")}))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            previous = db.scalar(select(Idempotency).where(Idempotency.tenant_id == tenant.id, Idempotency.key == key))
            if previous and previous.body_hash == body_hash:
                return {**previous.response, "duplicate": True}
            raise HTTPException(409, "Conflito idempotente")
        return result

    app.include_router(router)
