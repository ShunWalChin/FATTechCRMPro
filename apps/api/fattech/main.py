import hashlib
import hmac
import secrets
import time
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy import BigInteger, and_, cast, func, select, text, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .config import Settings, get_settings
from .db import Base, get_db, make_engine, session_factory, set_tenant
from .models import ApiKey, Audit, Idempotency, LoginSession, Outbox, Record, Tenant, User, now, uid
from .schemas import (RESOURCES, Decision, KeyCreate, Lead, Login, PasswordChange, PasswordReset, Simulation, TeamCreate,
                      TeamUpdate, Version, Webhook)
from .security import (DUMMY_HASH, digest, hasher, rate_limit, require_auth, user_dict, utc,
                       verify_password)
from .permissions import ADMIN_ROLES, ELEVATED_ROLES, RANK, can_manage
from . import compliance
from .services import (PRIVILEGED, RISK_ORDER, audit_event, build_radar, capture_lead, create_record,
                       default_pipeline, delete_record, get_record, list_records, serialize, simulate,
                       update_record)

COMPLIANCE_REASONS = {
    "no_consent": "Contato sem consentimento registrado.",
    "opted_out": "O contato pediu para parar de receber mensagens.",
    "blocked_content": "A mensagem contém um termo da lista de bloqueio.",
    "no_inbound_interaction": "O contato ainda não iniciou uma conversa por este canal.",
    "outside_24h": "A janela de 24 horas encerrou; use um template aprovado.",
    "outside_7d": "A janela de sete dias do atendimento humano encerrou.",
    "human_agent_is_not_automation": "A marca de atendimento humano não pode ser usada por automação.",
    "trigger_cooldown": "O gatilho já disparou para este contato dentro do intervalo mínimo.",
    "comment_already_replied": "Este comentário já recebeu uma resposta privada.",
    "outside_private_reply_window": "A janela de resposta privada ao comentário encerrou.",
    "invalid_interaction_time": "A última interação está no futuro; verifique o relógio da origem.",
    "whatsapp_template_required": "Fora da janela de 24 horas o WhatsApp exige template aprovado.",
    "whatsapp_template_not_approved": "O template ainda não foi aprovado pela Meta.",
    "whatsapp_template_missing_opt_out": "Um template usado por automação precisa conter a saída.",
}

CAPABILITIES = {
    "crm": "available", "public_leads": "available", "flow_simulator": "available",
    "api_keys": "available", "n8n_webhook": "available", "whatsapp": "not_configured",
    "instagram": "not_configured", "email_delivery": "not_configured", "ai_runtime": "not_configured",
    "calendar": "not_configured", "payments": "not_configured", "fiscal_issuance": "not_configured",
}


def create_app(settings: Settings | None = None, engine=None):
    settings = settings or get_settings()
    engine = engine or make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app):
        if not settings.production:
            Base.metadata.create_all(engine)
        else:
            with engine.connect() as connection:
                role = connection.execute(text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")).one()
                if role.rolsuper or role.rolbypassrls:
                    raise RuntimeError("API production database role must be NOSUPERUSER NOBYPASSRLS")
                unsafe = connection.execute(text("SELECT count(*) FROM pg_tables WHERE schemaname = 'public' AND tableowner = current_user")).scalar_one()
                if unsafe:
                    raise RuntimeError("API runtime must not own database tables; run migrations with a separate owner")
                secured = connection.execute(text("SELECT count(*) FROM pg_class c JOIN pg_namespace n "
                    "ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname IN "
                    "('records','audit_log','event_outbox','idempotency_keys') AND c.relrowsecurity AND c.relforcerowsecurity")).scalar_one()
                if secured != 4:
                    raise RuntimeError("Tenant tables require ENABLE and FORCE ROW LEVEL SECURITY")
                connection.execute(text("SELECT 1 FROM schema_migrations WHERE version = '0002'" )).scalar_one()
        yield

    app = FastAPI(title="FAT Tech CRM API", version="0.1.0", lifespan=lifespan,
                  docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessions = session_factory(engine)
    app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True,
                       allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
                       allow_headers=["Content-Type", "Authorization", "X-CSRF-Token", "Idempotency-Key",
                                      "X-Fattech-Timestamp", "X-Fattech-Signature"])

    @app.middleware("http")
    async def protection(request, call_next):
        trace = uid()
        request.state.trace_id = trace
        try:
            length = int(request.headers.get("content-length", "0"))
        except ValueError:
            return JSONResponse({"detail": "Content-Length inválido"}, 400)
        if length > settings.max_body_bytes:
            return JSONResponse({"detail": "Corpo excede o limite"}, 413)
        # Count actual chunks too; Content-Length is attacker-controlled.
        if request.method in ("POST", "PATCH", "PUT"):
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > settings.max_body_bytes:
                    return JSONResponse({"detail": "Corpo excede o limite"}, 413)
            request._body = bytes(body)
        response = await call_next(request)
        response.headers["X-Request-ID"] = trace
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(SQLAlchemyError)
    async def database_failure(request, exc):
        import logging
        logging.getLogger("fattech").error("Database failure trace=%s type=%s", request.state.trace_id, type(exc).__name__)
        return JSONResponse({"detail": "Falha transacional; nenhuma alteração parcial foi confirmada",
                             "request_id": request.state.trace_id}, 503)

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        return JSONResponse({"detail": [{"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
                                        for error in exc.errors()]}, 422)

    @app.get("/api/health")
    @app.get("/api/v1/health")
    def health(db=Depends(get_db)):
        db.execute(text("SELECT 1"))
        return {"status": "ok", "version": "0.1.0", "environment": settings.env}

    @app.post("/api/v1/auth/login")
    def login(payload: Login, request: Request, response: Response, db=Depends(get_db)):
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") not in settings.origins:
            raise HTTPException(403, "Origem não autorizada")
        ip = request.client.host if request.client else "unknown"
        rate_limit(db, f"login:ip:{ip}", 30, 300)
        rate_limit(db, f"login:email:{payload.email.lower()}", 10, 300)
        user = db.scalar(select(User).where(User.email == payload.email.lower()))
        valid = verify_password(user.password_hash if user else DUMMY_HASH, payload.password)
        if not user or not valid or not user.active or user.role not in RANK:
            raise HTTPException(401, "E-mail ou senha inválidos")
        token, csrf = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
        session = LoginSession(token_hash=digest(token), user_id=user.id, csrf_token=csrf,
                               expires_at=now() + timedelta(hours=settings.session_hours))
        db.add(session)
        set_tenant(db, user.tenant_id)
        audit_event(db, user.tenant_id, user.id, "auth.login", user.id)
        db.commit()
        response.set_cookie("fattech_session", token, max_age=settings.session_hours * 3600,
                            httponly=True, secure=settings.production, samesite="lax", path="/")
        return {"user": user_dict(user), "csrf_token": csrf}

    @app.get("/api/v1/auth/me")
    def me(principal=Depends(require_auth)):
        if principal.key:
            raise HTTPException(403, "Sessão de usuário obrigatória")
        return {"user": user_dict(principal.user), "csrf_token": principal.session.csrf_token}

    @app.post("/api/v1/auth/logout")
    def logout(response: Response, principal=Depends(require_auth), db=Depends(get_db)):
        if not principal.session:
            raise HTTPException(403, "Sessão de usuário obrigatória")
        if principal.session:
            principal.session.revoked = True
            audit_event(db, principal.tenant_id, principal.actor_id, "auth.logout", principal.actor_id)
            db.commit()
        response.delete_cookie("fattech_session", path="/")
        return {"ok": True}

    @app.post("/api/v1/auth/password")
    def password_change(payload: PasswordChange, principal=Depends(require_auth), db=Depends(get_db)):
        if not principal.session:
            raise HTTPException(403, "Sessão de usuário obrigatória")
        rate_limit(db, f"password:{principal.actor_id}", 5, 300)
        user = db.scalar(select(User).where(User.id == principal.actor_id,
                                            User.tenant_id == principal.tenant_id).with_for_update()
                         .execution_options(populate_existing=True))
        if not user or not user.active:
            raise HTTPException(401, "Conta inativa")
        if not verify_password(user.password_hash, payload.current_password):
            raise HTTPException(401, "Senha atual incorreta")
        user.password_hash = hasher.hash(payload.new_password)
        db.execute(update(LoginSession).where(LoginSession.user_id == user.id,
                       LoginSession.token_hash != principal.session.token_hash).values(revoked=True))
        audit_event(db, principal.tenant_id, user.id, "auth.password_changed", user.id)
        db.commit()
        return {"ok": True, "other_sessions_revoked": True}

    @app.get("/api/v1/auth/sessions")
    def sessions(principal=Depends(require_auth), db=Depends(get_db)):
        if not principal.session:
            raise HTTPException(403, "Sessão de usuário obrigatória")
        items = [{"id": session.id, "expires_at": session.expires_at.isoformat(),
                  "current": session.token_hash == principal.session.token_hash}
                 for session in db.scalars(select(LoginSession).where(LoginSession.user_id == principal.actor_id,
                     LoginSession.revoked.is_(False), LoginSession.expires_at > now()))]
        return {"items": items, "total": len(items)}

    @app.delete("/api/v1/auth/sessions/{session_id}")
    def revoke_session(session_id: str, principal=Depends(require_auth), db=Depends(get_db)):
        if not principal.session:
            raise HTTPException(403, "Sessão de usuário obrigatória")
        session = db.scalar(select(LoginSession).where(LoginSession.id == session_id,
                                                       LoginSession.user_id == principal.actor_id))
        if session is None:
            raise HTTPException(404, "Sessão não encontrada")
        session.revoked = True
        audit_event(db, principal.tenant_id, principal.actor_id, "auth.session_revoked", session.id)
        db.commit()
        return {"revoked": True}

    @app.post("/api/v1/public/leads", status_code=202)
    def capture(payload: Lead, request: Request, db=Depends(get_db)):
        ip = request.client.host if request.client else "unknown"
        rate_limit(db, f"lead:{ip}", 10, 3600)
        tenant = db.scalar(select(Tenant).where(Tenant.slug == settings.public_tenant_slug))
        if not tenant:
            raise HTTPException(503, "Captação não configurada")
        set_tenant(db, tenant.id)
        lead = capture_lead(db, tenant.id, {
            "name": payload.name, "email": str(payload.email), "phone": payload.phone,
            "company": payload.company, "source": "website", "consent": True,
            "notes": f"Interesse: {payload.interest}\n{payload.message}".strip(),
        }, {key: value for key, value in payload.model_dump().items() if key.startswith("utm_")},
            promote=settings.capture_creates_deal)
        db.commit()
        return {"id": lead.id, "status": "accepted"}

    @app.get("/api/v1/dashboard")
    def dashboard(principal=Depends(require_auth), db=Depends(get_db), pipeline_id: str | None = None):
        principal.require("dashboard:read")
        # SQL aggregate operations avoid loading customer/message bodies into the dashboard.
        def count(kind, predicate=None):
            query = select(func.count()).select_from(Record).where(Record.tenant_id == principal.tenant_id,
                               Record.kind == kind, Record.deleted.is_(False))
            if predicate is not None:
                query = query.where(predicate)
            return db.scalar(query) or 0
        def money(kind, field, predicate=None):
            query = select(func.coalesce(func.sum(cast(Record.data[field].as_string(), BigInteger)), 0)).where(
                Record.tenant_id == principal.tenant_id, Record.kind == kind, Record.deleted.is_(False))
            if predicate is not None:
                query = query.where(predicate)
            return int(db.scalar(query) or 0)
        def weighted(predicate):
            # Sum the products first and divide once, so the forecast never accumulates per-row rounding.
            amount = cast(Record.data["value_cents"].as_string(), BigInteger)
            chance = cast(Record.data["probability"].as_string(), BigInteger)
            return int(db.scalar(select(func.coalesce(func.sum(amount * chance), 0)).where(
                Record.tenant_id == principal.tenant_id, Record.kind == "deals",
                Record.deleted.is_(False), predicate)) or 0) // 100
        funnel = (get_record(db, principal.tenant_id, "pipelines", pipeline_id) if pipeline_id
                  else default_pipeline(db, principal.tenant_id))
        def at(stage):
            return and_(Record.data["stage"].as_string() == stage,
                        Record.data["pipeline_id"].as_string() == funnel.id)
        pipeline = [{"stage": stage["key"], "label": stage["label"], "outcome": stage["outcome"],
                     "count": count("deals", at(stage["key"])),
                     "value_cents": money("deals", "value_cents", at(stage["key"])),
                     "weighted_cents": weighted(at(stage["key"]))}
                    for stage in (funnel.data["stages"] if funnel else [])]
        opened = [stage for stage in pipeline if stage["outcome"] == "open"]
        closed_won = sum(stage["count"] for stage in pipeline if stage["outcome"] == "won")
        total = sum(stage["count"] for stage in pipeline)
        activity = db.scalars(select(Audit).where(Audit.tenant_id == principal.tenant_id)
                              .order_by(Audit.created_at.desc()).limit(10))
        return {"contacts": count("contacts"), "open_deals": sum(x["count"] for x in opened),
                "pipeline_value_cents": sum(x["value_cents"] for x in opened),
                "weighted_pipeline_cents": sum(x["weighted_cents"] for x in opened),
                "revenue_cents": money("invoices", "amount_cents", Record.data["status"].as_string() == "paid"),
                "open_tasks": count("tasks", Record.data["status"].as_string() != "done"),
                "open_conversations": count("conversations", Record.data["status"].as_string() != "closed"),
                "pending_approvals": count("approvals", Record.data["status"].as_string() == "pending"),
                "active_automations": 0, "conversion_rate": round(closed_won / total * 100, 1) if total else 0,
                "pipeline": pipeline, "pipeline_id": funnel.id if funnel else None,
                "pipeline_name": funnel.data["name"] if funnel else "",
                "recent_activity": [audit_dict(item) for item in activity],
                "capabilities": CAPABILITIES}

    @app.get("/api/v1/integrations")
    def integrations(principal=Depends(require_auth)):
        principal.require("integrations:read")
        descriptions = {"n8n": "Gateway HMAC e API com escopos disponíveis; configure seu workflow n8n",
                        "whatsapp": "Requer conta Meta e adaptador de envio homologado",
                        "instagram": "Requer OAuth Meta e homologação",
                        "email": "Requer provedor de envio",
                        "ai": "Execução bloqueada até configurar runtime e orçamento",
                        "calendar": "Requer OAuth Google",
                        "payments": "Controle interno disponível; provedor de pagamentos pendente"}
        return {"items": [{"id": key, "name": key, "status": "available" if key == "n8n" and settings.webhook_secret else "not_configured",
                            "description": description} for key, description in descriptions.items()], "total": len(descriptions)}

    @app.get("/api/v1/team")
    def team(principal=Depends(require_auth), db=Depends(get_db)):
        principal.require("team:read")
        query = select(User).where(User.tenant_id == principal.tenant_id)
        if principal.role not in ADMIN_ROLES:
            query = query.where(User.active.is_(True))
        items = [{**user_dict(user), "active": user.active} for user in db.scalars(query)]
        return {"items": items, "total": len(items)}

    @app.post("/api/v1/team", status_code=201)
    def add_member(payload: TeamCreate, principal=Depends(require_auth), db=Depends(get_db)):
        principal.admin()
        actor, _ = lock_membership(db, principal)
        if not can_manage(actor.role, payload.role):
            raise HTTPException(403, "Você não pode conceder este nível de acesso")
        user = User(tenant_id=principal.tenant_id, name=payload.name, email=str(payload.email).lower(),
                    password_hash=hasher.hash(payload.password), role=payload.role)
        db.add(user)
        try:
            db.flush()
            audit_event(db, principal.tenant_id, principal.actor_id, "team.created", user.id, {"role": user.role})
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(409, "E-mail indisponível") from exc
        return user_dict(user)

    @app.patch("/api/v1/team/{user_id}")
    def update_member(user_id: str, payload: TeamUpdate, principal=Depends(require_auth), db=Depends(get_db)):
        principal.admin()
        # Serialize membership transitions to protect the last active owner from concurrent requests.
        actor, members = lock_membership(db, principal)
        user = next((member for member in members if member.id == user_id), None)
        if not user:
            raise HTTPException(404, "Usuário não encontrado")
        changes = payload.model_dump(exclude_none=True)
        loses_access = changes.get("active") is False
        next_role = changes.get("role", user.role)
        if user.active and user.role == "root" and (loses_access or next_role != "root"):
            if sum(member.active and member.role == "root" for member in members) <= 1:
                raise HTTPException(409, "Não é possível remover o último Root ativo")
        if user.active and user.role in ELEVATED_ROLES and (loses_access or next_role not in ELEVATED_ROLES):
            if sum(member.active and member.role in ELEVATED_ROLES for member in members) <= 1:
                raise HTTPException(409, "Não é possível remover o último proprietário ativo")
        own_name_only = user.id == actor.id and set(changes) <= {"name"}
        if not own_name_only and (not can_manage(actor.role, user.role) or not can_manage(actor.role, next_role)):
            raise HTTPException(403, "Você só pode administrar acessos subordinados ao seu papel")
        old_role = user.role
        for key, value in changes.items():
            setattr(user, key, value)
        if not user.active or old_role != user.role:
            db.execute(update(LoginSession).where(LoginSession.user_id == user.id).values(revoked=True))
            db.execute(update(ApiKey).where(ApiKey.created_by == user.id,
                                           ApiKey.tenant_id == principal.tenant_id).values(revoked=True))
        audit_event(db, principal.tenant_id, principal.actor_id, "team.updated", user.id, {"fields": sorted(changes)})
        db.commit()
        return {**user_dict(user), "active": user.active}

    @app.post("/api/v1/team/{user_id}/password")
    def reset_member_password(user_id: str, payload: PasswordReset, principal=Depends(require_auth), db=Depends(get_db)):
        principal.admin()
        actor, members = lock_membership(db, principal)
        target = next((member for member in members if member.id == user_id), None)
        if target is None:
            raise HTTPException(404, "Usuário não encontrado")
        if target.id == actor.id or not can_manage(actor.role, target.role):
            raise HTTPException(403, "Use a troca de senha pessoal ou selecione um acesso subordinado")
        target.password_hash = hasher.hash(payload.new_password)
        db.execute(update(LoginSession).where(LoginSession.user_id == target.id).values(revoked=True))
        db.execute(update(ApiKey).where(ApiKey.created_by == target.id, ApiKey.tenant_id == principal.tenant_id).values(revoked=True))
        audit_event(db, principal.tenant_id, actor.id, "team.password_reset", target.id)
        db.commit()
        return {"ok": True, "sessions_revoked": True, "api_keys_revoked": True}

    @app.get("/api/v1/audit")
    def audit(principal=Depends(require_auth), db=Depends(get_db), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
        principal.admin()
        records = db.scalars(select(Audit).where(Audit.tenant_id == principal.tenant_id)
                              .order_by(Audit.created_at.desc()).limit(limit).offset(offset))
        total = db.scalar(select(func.count()).select_from(Audit).where(Audit.tenant_id == principal.tenant_id))
        return {"items": [audit_dict(item) for item in records], "total": total}

    @app.post("/api/v1/api-keys", status_code=201)
    def create_key(payload: KeyCreate, principal=Depends(require_auth), db=Depends(get_db)):
        principal.admin()
        lock_membership(db, principal)
        allowed = {f"{kind}:{op}" for kind in RESOURCES for op in ("read", "write")}
        allowed |= {"webhooks:write", "events:read", "dashboard:read", "integrations:read", "team:read"}
        if not set(payload.scopes).issubset(allowed):
            raise HTTPException(422, "Escopo desconhecido")
        token = "fat_" + secrets.token_urlsafe(40)
        key = ApiKey(tenant_id=principal.tenant_id, created_by=principal.actor_id, name=payload.name,
                     key_hash=digest(token), prefix=token[:12], scopes=sorted(set(payload.scopes)),
                     expires_at=now() + timedelta(days=payload.expires_in_days))
        db.add(key)
        db.flush()
        audit_event(db, principal.tenant_id, principal.actor_id, "api_key.created", key.id, {"scopes": key.scopes})
        db.commit()
        return {**key_dict(key), "key": token}

    @app.get("/api/v1/api-keys")
    def keys(principal=Depends(require_auth), db=Depends(get_db)):
        principal.admin()
        creators = [user.id for user in db.scalars(select(User).where(User.tenant_id == principal.tenant_id))
                    if user.id == principal.actor_id or can_manage(principal.role, user.role)]
        items = [key_dict(key) for key in db.scalars(select(ApiKey).where(ApiKey.tenant_id == principal.tenant_id,
                                                                        ApiKey.created_by.in_(creators)))]
        return {"items": items, "total": len(items)}

    @app.delete("/api/v1/api-keys/{key_id}")
    def revoke_key(key_id: str, principal=Depends(require_auth), db=Depends(get_db)):
        principal.admin()
        actor, members = lock_membership(db, principal)
        key = db.scalar(select(ApiKey).where(ApiKey.id == key_id, ApiKey.tenant_id == principal.tenant_id))
        if not key:
            raise HTTPException(404, "Chave não encontrada")
        creator = next((member for member in members if member.id == key.created_by), None)
        if creator is None or (creator.id != actor.id and not can_manage(actor.role, creator.role)):
            raise HTTPException(404, "Chave não encontrada")
        key.revoked = True
        audit_event(db, principal.tenant_id, principal.actor_id, "api_key.revoked", key.id)
        db.commit()
        return {"revoked": True}

    @app.post("/api/v1/webhooks/n8n", status_code=202)
    async def webhook(request: Request, principal=Depends(require_auth), db=Depends(get_db)):
        if not principal.key:
            raise HTTPException(403, "Webhook requer chave de API com escopo")
        principal.require("webhooks:write")
        if not settings.webhook_secret:
            raise HTTPException(503, "Webhook não configurado")
        raw = await request.body()
        timestamp = request.headers.get("x-fattech-timestamp", "")
        try:
            valid_time = abs(time.time() - int(timestamp)) <= 300
        except ValueError:
            valid_time = False
        signature = request.headers.get("x-fattech-signature", "")
        expected = "sha256=" + hmac.new(settings.webhook_secret.encode(), timestamp.encode() + b"." + raw,
                                         hashlib.sha256).hexdigest()
        if not valid_time or not hmac.compare_digest(expected, signature):
            raise HTTPException(401, "Assinatura ou timestamp inválido")
        idempotency_key = request.headers.get("idempotency-key", "")
        if not 8 <= len(idempotency_key) <= 200:
            raise HTTPException(422, "Idempotency-Key de 8 a 200 caracteres obrigatória")
        rate_limit(db, f"webhook:{principal.key.id}", 120, 60)
        body_hash = hashlib.sha256(raw).hexdigest()
        previous = db.scalar(select(Idempotency).where(Idempotency.tenant_id == principal.tenant_id,
                                                        Idempotency.key == idempotency_key))
        if previous:
            if previous.body_hash != body_hash:
                raise HTTPException(409, "Chave idempotente reutilizada com outro conteúdo")
            return {**previous.response, "duplicate": True}
        try:
            payload = Webhook.model_validate_json(raw)
        except ValidationError as exc:
            raise HTTPException(422, "Envelope de evento inválido") from exc
        event_id = uid()
        result = {"id": event_id, "status": "accepted", "duplicate": False}
        db.add(Idempotency(tenant_id=principal.tenant_id, key=idempotency_key, body_hash=body_hash, response=result))
        db.add(Outbox(id=event_id, tenant_id=principal.tenant_id, event_type=payload.event_type,
                      payload=payload.payload, trace_id=payload.trace_id or uid(), hops=payload.hops))
        db.add(Audit(tenant_id=principal.tenant_id, actor_id=principal.actor_id, action="webhook.accepted",
                     resource_id=event_id, details={"event_type": payload.event_type}))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            previous = db.scalar(select(Idempotency).where(Idempotency.tenant_id == principal.tenant_id,
                                                            Idempotency.key == idempotency_key))
            if previous and previous.body_hash == body_hash:
                return {**previous.response, "duplicate": True}
            raise HTTPException(409, "Conflito idempotente")
        return result

    @app.get("/api/v1/events")
    def events(principal=Depends(require_auth), db=Depends(get_db), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
        principal.require("events:read")
        records = db.scalars(select(Outbox).where(Outbox.tenant_id == principal.tenant_id)
                              .order_by(Outbox.created_at.desc()).limit(limit).offset(offset))
        total = db.scalar(select(func.count()).select_from(Outbox).where(Outbox.tenant_id == principal.tenant_id))
        return {"items": [{"id": event.id, "event_type": event.event_type, "payload": event.payload,
                            "trace_id": event.trace_id, "hops": event.hops, "status": event.status,
                            "attempts": event.attempts, "created_at": event.created_at.isoformat()} for event in records],
                "total": total}

    @app.post("/api/v1/automations/{record_id}/simulate")
    def simulation(record_id: str, payload: Simulation, principal=Depends(require_auth), db=Depends(get_db)):
        principal.require("automations:read")
        record = get_record(db, principal.tenant_id, "automations", record_id)
        return simulate(record.data, payload.input)

    @app.post("/api/v1/events/{record_id}/retry")
    def retry_event(record_id: str, principal=Depends(require_auth), db=Depends(get_db)):
        principal.admin()
        result = db.execute(update(Outbox).where(Outbox.id == record_id,
            Outbox.tenant_id == principal.tenant_id, Outbox.status == "dead_letter")
            .values(status="pending", attempts=0, available_at=now(), last_error=None,
                    claim_token=None, locked_until=None))
        if result.rowcount != 1:
            raise HTTPException(409, "Evento não encontrado ou não está em dead letter")
        audit_event(db, principal.tenant_id, principal.actor_id, "event.retried", record_id)
        db.commit()
        return {"id": record_id, "status": "pending"}

    def message_decision(db, principal, record_id):
        """Shared by the preview and the send path, so the operator never sees a verdict the sender would not apply."""
        message = get_record(db, principal.tenant_id, "messages", record_id)
        conversation = get_record(db, principal.tenant_id, "conversations", message.data["conversation_id"])
        contact = (get_record(db, principal.tenant_id, "contacts", conversation.data["contact_id"])
                   if conversation.data.get("contact_id") else None)
        body = message.data["body"]
        if contact is not None and not contact.data.get("consent"):
            return message, compliance.Decision(False, "blocked", body, reason="no_consent")
        channel = conversation.data["channel"]
        if channel not in ("whatsapp", "instagram"):
            return message, compliance.Decision(True, "internal", body)
        evaluator = compliance.evaluate_whatsapp if channel == "whatsapp" else compliance.evaluate
        return message, evaluator(message=body, is_automated=False, blocklist=settings.blocklist,
                                  last_inbound_at=conversation.data.get("last_inbound_at"),
                                  opted_out_at=contact.data.get("opted_out_at") if contact else None)

    @app.post("/api/v1/messages/{record_id}/compliance")
    def message_compliance(record_id: str, principal=Depends(require_auth), db=Depends(get_db)):
        principal.require("messages:read")
        _, decision = message_decision(db, principal, record_id)
        return {**decision.as_dict(), "preview": decision.body, "explanation": COMPLIANCE_REASONS.get(decision.reason)}

    @app.post("/api/v1/messages/{record_id}/send")
    def send_message(record_id: str, payload: Version, principal=Depends(require_auth), db=Depends(get_db)):
        principal.require("messages:write")
        message, decision = message_decision(db, principal, record_id)
        if message.version != payload.version:
            raise HTTPException(409, "Versão desatualizada")
        if not decision.allowed:
            raise HTTPException(409, {"message": COMPLIANCE_REASONS.get(decision.reason, "Envio bloqueado."),
                                      "compliance": decision.as_dict()})
        if not settings.external_sends_enabled:
            raise HTTPException(503, "Envios externos estão desarmados neste ambiente; nenhuma mensagem saiu.")
        raise HTTPException(503, "Provedor de envio não configurado. A mensagem permanece como rascunho.")

    @app.get("/api/v1/crm/radar")
    def radar(principal=Depends(require_auth), db=Depends(get_db), pipeline_id: str | None = None):
        principal.require("deals:read")
        funnel = (get_record(db, principal.tenant_id, "pipelines", pipeline_id) if pipeline_id
                  else default_pipeline(db, principal.tenant_id))
        if funnel is None:
            return {"pipeline_id": None, "pipeline_name": "", "items": [], "total": 0,
                    "summary": {**{bucket: 0 for bucket in RISK_ORDER}, "needs_action": 0}}
        return build_radar(db, principal.tenant_id, funnel)

    @app.post("/api/v1/approvals/{record_id}/decision")
    def decision(record_id: str, payload: Decision, principal=Depends(require_auth), db=Depends(get_db)):
        principal.admin()
        record = get_record(db, principal.tenant_id, "approvals", record_id, lock=True)
        from datetime import datetime
        if record.data["status"] != "pending" or utc(datetime.fromisoformat(record.data["expires_at"])) <= now():
            raise HTTPException(409, "Solicitação encerrada ou expirada")
        if record.data.get("requested_by") == principal.actor_id:
            raise HTTPException(403, "Solicitante não pode aprovar a própria intenção")
        if record.data["gate"] in ("G1", "G2", "G3", "G5", "G6") and principal.role not in ELEVATED_ROLES:
            raise HTTPException(403, "Este gate requer o proprietário")
        data = {**record.data, "status": payload.decision, "decided_by": principal.actor_id,
                "decided_at": now().isoformat(), "reason": payload.reason, "execution_status": "not_executed"}
        result = db.execute(update(Record).where(Record.id == record_id, Record.tenant_id == principal.tenant_id,
                          Record.version == payload.version).values(data=data, version=payload.version + 1, updated_at=now()))
        if result.rowcount != 1:
            raise HTTPException(409, "Versão desatualizada")
        audit_event(db, principal.tenant_id, principal.actor_id, "approval.decided", record_id,
                    {"decision": payload.decision, "gate": data["gate"]})
        db.commit()
        db.refresh(record)
        return serialize(record)

    @app.post("/api/v1/agents/{record_id}/run")
    def run_agent(record_id: str, payload: Simulation, principal=Depends(require_auth), db=Depends(get_db)):
        principal.admin()
        record = get_record(db, principal.tenant_id, "agents", record_id)
        if record.data.get("budget_cents", 0) <= record.data.get("spent_cents", 0):
            raise HTTPException(409, "Agente bloqueado: orçamento disponível obrigatório")
        raise HTTPException(503, "Runtime de IA não configurado; nenhum crédito foi gasto")

    # Register every concrete route for an unambiguous OpenAPI operation catalog.
    for kind, schema in RESOURCES.items():
        register_resource(app, kind, schema)
    return app


def lock_membership(db, principal):
    """Recheck the actor after locking the tenant's membership in a stable order."""
    if db.bind.dialect.name == "sqlite":
        db.execute(text("UPDATE users SET active=active WHERE 1=0"))
    members = list(db.scalars(select(User).where(User.tenant_id == principal.tenant_id)
                             .order_by(User.id).with_for_update().execution_options(populate_existing=True)))
    actor = next((member for member in members if member.id == principal.actor_id), None)
    if not actor or not actor.active or actor.role not in ADMIN_ROLES:
        raise HTTPException(403, "Permissão de administração revogada")
    if not principal.session:
        raise HTTPException(403, "Sessão de usuário obrigatória")
    db.refresh(principal.session)
    if principal.session.revoked or utc(principal.session.expires_at) <= now():
        raise HTTPException(401, "Sessão expirada. Entre novamente.")
    principal.role = actor.role
    return actor, members


def audit_dict(item):
    return {"id": item.id, "action": item.action, "resource_id": item.resource_id,
            "actor_id": item.actor_id, "details": item.details, "created_at": item.created_at.isoformat()}


def key_dict(key):
    return {"id": key.id, "name": key.name, "prefix": key.prefix, "scopes": key.scopes,
            "revoked": key.revoked, "expires_at": key.expires_at.isoformat()}


def register_resource(app, kind, schema):
    def listing(principal=Depends(require_auth), db=Depends(get_db), q: str = Query("", max_length=200),
                status: str | None = None, stage: str | None = None, contact_id: str | None = None,
                conversation_id: str | None = None, project_id: str | None = None, owner_id: str | None = None,
                pipeline_id: str | None = None,
                limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
        principal.require(f"{kind}:read")
        return list_records(db, principal.tenant_id, kind, locals())

    def retrieve(record_id: str, principal=Depends(require_auth), db=Depends(get_db)):
        principal.require(f"{kind}:read")
        return serialize(get_record(db, principal.tenant_id, kind, record_id))

    def create(payload: schema, principal=Depends(require_auth), db=Depends(get_db)):
        principal.require(f"{kind}:write")
        if kind in PRIVILEGED and kind != "approvals":
            principal.admin()
        record = create_record(db, principal.tenant_id, principal.actor_id, kind, payload.model_dump(mode="json"))
        db.commit()
        return serialize(record)

    def patch(record_id: str, payload: dict = Body(...), principal=Depends(require_auth), db=Depends(get_db)):
        principal.require(f"{kind}:write")
        if kind in PRIVILEGED:
            principal.admin()
        record = update_record(db, principal, kind, record_id, payload)
        db.commit()
        return serialize(record)

    def remove(record_id: str, version: int = Query(..., ge=1), principal=Depends(require_auth), db=Depends(get_db)):
        principal.require(f"{kind}:write")
        if kind in PRIVILEGED:
            principal.admin()
        delete_record(db, principal, kind, record_id, version)
        db.commit()
        return {"deleted": True}

    for endpoint, method, suffix, status in [(listing, "GET", "", 200), (retrieve, "GET", "/{record_id}", 200),
               (create, "POST", "", 201), (patch, "PATCH", "/{record_id}", 200), (remove, "DELETE", "/{record_id}", 200)]:
        app.add_api_route(f"/api/v1/{kind}{suffix}", endpoint, methods=[method], status_code=status,
                          name=f"{kind}_{endpoint.__name__}", tags=[kind])


app = create_app()
