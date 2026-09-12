"""Operator-only account provisioning. JSON credentials go to stdout: redirect to a private file."""
import json
import secrets
import sys

from sqlalchemy import select

from .config import get_settings
from .db import make_engine, session_factory, set_tenant
from .models import Tenant, User
from .passwords import hasher
from .schemas import TeamCreate
from .services import audit_event


def provision(db, slug, requested):
    tenant = db.scalar(select(Tenant).where(Tenant.slug == slug))
    if tenant is None:
        raise ValueError("Provision the organization first")
    set_tenant(db, tenant.id)
    if db.bind.dialect.name == "postgresql":
        from sqlalchemy import text
        db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"), {"scope": "accounts:" + tenant.id})
    output = []
    for supplied in requested:
        password = secrets.token_urlsafe(24)
        validated = TeamCreate.model_validate({**supplied, "password": password})
        email = str(validated.email).lower()
        existing = db.scalar(select(User).where(User.email == email).with_for_update())
        if existing:
            if existing.tenant_id != tenant.id or existing.role != validated.role or not existing.active:
                raise ValueError("Existing account conflicts with requested access; no changes committed")
            output.append({"email": email, "role": existing.role, "created": False})
            continue
        user = User(tenant_id=tenant.id, email=email, name=validated.name,
                    role=validated.role, password_hash=hasher.hash(password))
        db.add(user)
        db.flush()
        audit_event(db, tenant.id, None, "team.operator_provisioned", user.id, {"role": user.role})
        output.append({"email": email, "name": user.name, "role": user.role, "password": password, "created": True})
    db.commit()
    return output


def main():
    settings = get_settings()
    requested = json.load(sys.stdin)
    if not isinstance(requested, list) or not 1 <= len(requested) <= 20:
        raise ValueError("Provide one to twenty account descriptors")
    engine = make_engine(settings.database_url)
    try:
        with session_factory(engine)() as db:
            credentials = provision(db, settings.public_tenant_slug, requested)
        json.dump(credentials, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
