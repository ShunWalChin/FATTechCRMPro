"""A creation and its receipt commit together. No network effects belong in this transaction."""
import hashlib
import json
import re

from fastapi import HTTPException
from sqlalchemy import select, text

from .models import Idempotency


def creation_receipt(db, principal, kind, key, payload):
    """Return a locked receipt plus whether this is a replay; caller commits the business operation.

    Keys belong to an organization, principal/credential and resource. A rotated API key starts
    a distinct namespace. The stored response is the original creation result, not a current read.
    """
    if not re.fullmatch(r"[A-Za-z0-9._:-]{8,200}", key):
        raise HTTPException(422, "Idempotency-Key deve ter de 8 a 200 caracteres: letras, números, ponto, _, : ou -")
    credential = "key:" + principal.key.id if principal.key else "user:" + principal.actor_id
    scope = json.dumps([principal.tenant_id, credential, kind, key], separators=(",", ":"))
    stored_key = "create:" + hashlib.sha256(scope.encode()).hexdigest()
    try:
        encoded = json.dumps(["create", kind, payload], sort_keys=True,
                             separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, "Conteúdo JSON inválido para criação idempotente") from exc
    body_hash = hashlib.sha256(encoded).hexdigest()
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"), {"scope": stored_key})
    else:
        # SQLite serializes writers; take its write lock before reading the receipt.
        db.execute(text("UPDATE idempotency_keys SET key=key WHERE 1=0"))
    receipt = db.scalar(select(Idempotency).where(Idempotency.tenant_id == principal.tenant_id,
                                                 Idempotency.key == stored_key))
    if receipt:
        if receipt.body_hash != body_hash:
            raise HTTPException(409, "Idempotency-Key já foi usada com outro conteúdo")
        return receipt, True
    receipt = Idempotency(tenant_id=principal.tenant_id, key=stored_key, body_hash=body_hash, response={})
    db.add(receipt)
    db.flush()
    return receipt, False
