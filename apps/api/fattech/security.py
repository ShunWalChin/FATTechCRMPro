import hashlib
import hmac
import time
from dataclasses import dataclass
from datetime import timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select

from .db import get_db, set_tenant
from .models import ApiKey, LoginSession, RateLimit, User
from .permissions import ADMIN_ROLES, LABELS, RANK, capabilities
from .passwords import DUMMY_HASH as DUMMY_HASH, hasher as hasher, verify_password as verify_password


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def rate_limit(db, bucket: str, limit: int, seconds: int):
    """Atomic fixed window counter shared by all API processes using the database."""
    window = int(time.time()) // seconds
    dialect = db.bind.dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    from sqlalchemy import case
    statement = insert(RateLimit).values(bucket=digest(bucket), window=window, count=1)
    statement = statement.on_conflict_do_update(
        index_elements=[RateLimit.bucket],
        set_={"window": window, "count": case((RateLimit.window == window, RateLimit.count + 1), else_=1)},
    ).returning(RateLimit.count)
    count = db.execute(statement).scalar_one()
    db.commit()  # Limit accounting survives rejected auth/business transactions.
    if count > limit:
        raise HTTPException(429, "Limite de requisições excedido", headers={"Retry-After": str(seconds)})


@dataclass
class Principal:
    tenant_id: str
    actor_id: str
    role: str
    user: User
    session: LoginSession | None = None
    key: ApiKey | None = None

    def require(self, scope: str):
        if self.role not in RANK:
            raise HTTPException(403, "Papel de acesso inválido")
        if self.key and scope not in self.key.scopes:
            raise HTTPException(403, "Escopo de API insuficiente")
        if scope.endswith(":write") and self.role == "viewer":
            raise HTTPException(403, "Perfil somente leitura")

    def admin(self):
        if self.key or self.role not in ADMIN_ROLES:
            raise HTTPException(403, "Requer proprietário ou administrador")


def require_auth(request: Request, db=Depends(get_db)) -> Principal:
    from .models import now
    authorization = request.headers.get("authorization", "")
    if authorization.startswith("Bearer "):
        key = db.scalar(select(ApiKey).where(ApiKey.key_hash == digest(authorization[7:]), ApiKey.revoked.is_(False)))
        if key is None or utc(key.expires_at) <= now():
            raise HTTPException(401, "Chave inválida ou expirada")
        user = db.get(User, key.created_by)
        if not user or not user.active or user.tenant_id != key.tenant_id or user.role not in RANK:
            raise HTTPException(401, "Conta inativa")
        set_tenant(db, key.tenant_id)
        return Principal(key.tenant_id, user.id, user.role, user, key=key)
    token = request.cookies.get("fattech_session", "")
    session = db.get(LoginSession, digest(token)) if token else None
    if session is None or session.revoked or utc(session.expires_at) <= now():
        raise HTTPException(401, "Sessão expirada. Entre novamente.")
    user = db.get(User, session.user_id)
    if not user or not user.active or user.role not in RANK:
        raise HTTPException(401, "Conta inativa")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        csrf = request.headers.get("x-csrf-token", "")
        if origin is not None:
            if origin.rstrip("/") not in request.app.state.settings.origins:
                raise HTTPException(403, "Origem não autorizada")
        elif not csrf or not hmac.compare_digest(csrf, session.csrf_token):
            raise HTTPException(403, "Token CSRF obrigatório")
    set_tenant(db, user.tenant_id)
    return Principal(user.tenant_id, user.id, user.role, user, session=session)


def user_dict(user: User):
    return {"id": user.id, "tenant_id": user.tenant_id, "name": user.name, "email": user.email,
            "role": user.role, "role_label": LABELS.get(user.role, "Inválido"), "permissions": capabilities(user.role)}
