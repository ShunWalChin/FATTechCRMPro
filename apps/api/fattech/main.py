import hashlib
import hmac
import json
import pathlib
import secrets
import time
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy import BigInteger, and_, cast, func, select, text, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .config import Settings, get_settings
from .db import Base, get_db, make_engine, session_factory, set_tenant
from .models import AgentRun, AgentStep, ApiKey, Audit, Idempotency, KnowledgeChunk, LoginSession, Outbox, Record, Tenant, User, now, uid
from .schemas import (RESOURCES, Decision, KeyCreate, Lead, Login, PasswordChange, PasswordReset,
                      Simulation, TeamCreate,
                      TeamUpdate, Version, Webhook)
from .security import (DUMMY_HASH, digest, hasher, rate_limit, require_auth, user_dict, utc,
                       verify_password)
from .permissions import ADMIN_ROLES, ELEVATED_ROLES, RANK, can_manage
from .idempotency import creation_receipt
from .imports import contact_import
from .json_input import validate_json_body
from .record_views import register_record_views
from .instagram_webhook import register_instagram_webhook
from .content_ops import register_content_ops
from .agent_api import register_agent_api
from .audit_chain import verificar as verificar_trilha
from .sales_operations import router as sales_router
from . import compliance
from .services import (PRIVILEGED, RISK_ORDER, audit_event, build_notifications, build_radar,
                       capture_lead, create_record,
                       default_pipeline, delete_record, get_record, list_records, serialize, simulate,
                       update_record)

# One declaration; the health endpoint and the OpenAPI catalogue must never disagree.
APP_VERSION = "0.5.1"

RESOURCE_NOUNS = {"contacts": ("contato", "o"), "companies": ("empresa", "a"), "pipelines": ("funil", "o"),
                  "deals": ("oportunidade", "a"), "tasks": ("tarefa", "a"), "conversations": ("conversa", "a"),
                  "messages": ("mensagem", "a"), "campaigns": ("campanha", "a"), "automations": ("automação", "a"),
                  "knowledge": ("documento", "o"), "approvals": ("solicitação", "a"), "agents": ("agente", "o"),
                  "projects": ("projeto", "o"), "invoices": ("lançamento", "o"), "products": ("produto", "o"),
                  "sales_proposals": ("proposta", "a"), "sales_goals": ("meta", "a")}
ACTION_VERBS = {"created": "Criou", "updated": "Alterou", "deleted": "Excluiu"}
ACTION_LABELS = {
    "pipelines.default_replaced": "Substituiu o funil padrão",
    "activities.created": "Registrou uma atividade",
    "sales_proposals.issued": "Emitiu a proposta internamente",
    "sales_proposals.accepted": "Registrou o aceite da proposta",
    "sales_proposals.rejected": "Registrou a recusa da proposta",
    "auth.login": "Entrou no sistema", "auth.logout": "Saiu do sistema",
    "auth.password_changed": "Alterou a própria senha", "auth.session_revoked": "Encerrou uma sessão",
    "team.created": "Cadastrou um integrante", "team.updated": "Alterou um integrante",
    "team.operator_provisioned": "Provisionou um acesso", "team.password_reset": "Redefiniu a senha de um integrante",
    "api_key.created": "Criou uma chave de API", "api_key.revoked": "Revogou uma chave de API",
    "webhook.accepted": "Recebeu um evento externo", "event.retried": "Reprocessou um evento",
    "approval.decided": "Decidiu uma solicitação", "contacts.recaptured": "Recebeu um contato pelo site",
    "synapse.assisted": "Consultou a base de conhecimento do SYNAPSE",
    "synapse.capture_pending": "Registrou captação aguardando configuração do SYNAPSE",
    "synapse.installed": "Preparou a operação comercial SYNAPSE",
    "synapse.configured": "Alterou a configuração do SYNAPSE",
    "synapse.enrolled": "Vinculou um lead à operação SYNAPSE",
    "core.delivery.retried": "Recolocou uma entrega interna na fila de processamento",
    "messages.received": "Registrou uma mensagem recebida",
    "contacts.opted_out": "Registrou pedido de interrupção de mensagens",
}


def action_label(action: str) -> str:
    """Falls back to the raw key rather than inventing wording for an action nobody mapped."""
    if action in ACTION_LABELS:
        return ACTION_LABELS[action]
    kind, _, verb = action.partition(".")
    noun = RESOURCE_NOUNS.get(kind)
    if noun and verb in ACTION_VERBS:
        return f"{ACTION_VERBS[verb]} {noun[1]} {noun[0]}"
    return action


def integration_status(key, settings, contas_instagram):
    """O estado vem do que existe, nao de um dicionario escrito a mao que envelhece sozinho."""
    if key == "n8n":
        return "available" if settings.webhook_secret else "not_configured"
    if key == "instagram":
        return "available" if contas_instagram else ("ready" if settings.credential_key else "not_configured")
    return "not_configured"


def api_scopes():
    return {f"{kind}:{op}" for kind in RESOURCES for op in ("read", "write")} | {
        "webhooks:write", "events:read", "dashboard:read", "integrations:read",
        "integrations:write", "team:read",
        # contracts vive fora de RESOURCES porque tem transicoes que o PATCH generico burlaria;
        # o escopo precisa existir aqui ou nenhuma chave de API jamais poderia recebe-lo.
        "contracts:read", "contracts:write",
        # O agente opera o proprio ciclo de corrida com este escopo. Ele e deliberadamente distinto
        # de `agents:write`, que escreve o registro de configuracao de um agente: operar a si mesmo
        # e reconfigurar a si mesmo sao coisas diferentes, e so a primeira e do agente.
        "agent:operate"}


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
                from .migrate import TENANT_TABLES
                secured = connection.execute(text("SELECT count(*) FROM pg_class c JOIN pg_namespace n "
                    "ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relname = ANY(:tabelas) "
                    "AND c.relrowsecurity AND c.relforcerowsecurity"), {"tabelas": list(TENANT_TABLES)}).scalar_one()
                if secured != len(TENANT_TABLES):
                    raise RuntimeError("Tenant tables require ENABLE and FORCE ROW LEVEL SECURITY")
                connection.execute(text("SELECT 1 FROM schema_migrations WHERE version = '0008'" )).scalar_one()
        yield

    app = FastAPI(title="FAT Tech CRM API", version=APP_VERSION, lifespan=lifespan,
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
        def protected(response):
            response.headers.update({"X-Request-ID": trace, "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "strict-origin-when-cross-origin", "Cache-Control": "no-store"})
            return response
        try:
            length = int(request.headers.get("content-length", "0"))
            if length < 0:
                raise ValueError
        except ValueError:
            return protected(JSONResponse({"detail": "Content-Length inválido"}, 400))
        if length > settings.max_body_bytes:
            return protected(JSONResponse({"detail": "Corpo excede o limite"}, 413))
        # Count actual chunks too; Content-Length is attacker-controlled.
        if request.method in ("POST", "PATCH", "PUT"):
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > settings.max_body_bytes:
                    return protected(JSONResponse({"detail": "Corpo excede o limite"}, 413))
            request._body = bytes(body)
            media_type = request.headers.get("content-type", "application/json").split(";")[0].strip().lower()
            if body and (media_type == "application/json" or media_type.endswith("+json")):
                try:
                    validate_json_body(bytes(body))
                except (ValueError, RecursionError):
                    return protected(JSONResponse({"detail": "JSON inválido: use chaves únicas, valores finitos e estrutura de até 64 níveis"}, 422))
        response = await call_next(request)
        return protected(response)

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
        return {"status": "ok", "version": APP_VERSION, "environment": settings.env}

    @app.post("/api/v1/auth/login")
    def login(payload: Login, request: Request, response: Response, db=Depends(get_db)):
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") not in settings.origins:
            raise HTTPException(403, "Origem não autorizada")
        ip = request.client.host if request.client else "unknown"
        rate_limit(db, f"login:ip:{ip}", settings.login_attempts_per_ip, 300)
        rate_limit(db, f"login:email:{payload.email.lower()}", settings.login_attempts_per_email, 300)
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
        utm = {key: value for key, value in payload.model_dump().items() if key.startswith("utm_")}
        from .synapse import enroll_contact
        configuration = db.scalar(select(Record).where(Record.tenant_id == tenant.id,
            Record.kind == "synapse_config", Record.deleted.is_(False)))
        synapse_capture = bool(configuration and configuration.data.get("enabled")
                               and configuration.data.get("capture_enabled"))
        lead = capture_lead(db, tenant.id, {
            "name": payload.name, "email": str(payload.email), "phone": payload.phone,
            "company": payload.company, "source": "website", "consent": True,
            "notes": f"Interesse: {payload.interest}\n{payload.message}".strip(),
            # UTM vira campo do contato, nao so um dicionario guardado: e o que deixa agrupar por origem.
            **utm,
        }, utm,
            promote=settings.capture_creates_deal and not synapse_capture)
        if synapse_capture:
            try:
                with db.begin_nested():
                    enroll_contact(db, tenant.id, None, lead)
            except HTTPException as exc:
                if exc.status_code not in (404, 409, 422):
                    raise
                # A subsequently edited funnel must never discard the public lead.
                audit_event(db, tenant.id, None, "synapse.capture_pending", lead.id,
                            {"reason": "configuration_requires_review", "status_code": exc.status_code})
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
                "recent_activity": describe_audit(db, principal.tenant_id, list(activity)),
                "capabilities": CAPABILITIES}

    @app.get("/api/v1/integrations")
    def integrations(principal=Depends(require_auth), db=Depends(get_db)):
        principal.require("integrations:read")
        from .models import InstagramAccount
        conectadas = db.scalar(select(func.count()).select_from(InstagramAccount).where(
            InstagramAccount.tenant_id == principal.tenant_id, InstagramAccount.status == "connected")) or 0
        descriptions = {"n8n": "Gateway HMAC e API com escopos disponíveis; configure seu workflow n8n",
                        "whatsapp": "Requer conta Meta e adaptador de envio homologado",
                        "instagram": (f"{conectadas} conta(s) conectada(s); o webhook resolve a organização pela conta"
                                      if conectadas else "Conecte uma conta em Integrações; o token fica cifrado no servidor"),
                        "email": "Requer provedor de envio",
                        "ai": "Execução bloqueada até configurar runtime e orçamento",
                        "calendar": "Requer OAuth Google",
                        "payments": "Controle interno disponível; provedor de pagamentos pendente"}
        names = {"n8n": "n8n", "whatsapp": "WhatsApp", "instagram": "Instagram", "email": "E-mail",
                 "ai": "Inteligência artificial", "calendar": "Google Agenda", "payments": "Pagamentos"}
        # The scope catalogue is served from the same set the key endpoint validates against, so they cannot drift.
        scopes = sorted(api_scopes())
        return {"items": [{"id": key, "name": names.get(key, key),
                            "status": integration_status(key, settings, conectadas),
                            "description": description} for key, description in descriptions.items()],
                "total": len(descriptions), "scopes": scopes}

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
        records = list(db.scalars(select(Audit).where(Audit.tenant_id == principal.tenant_id)
                                  .order_by(Audit.created_at.desc()).limit(limit).offset(offset)))
        total = db.scalar(select(func.count()).select_from(Audit).where(Audit.tenant_id == principal.tenant_id))
        return {"items": describe_audit(db, principal.tenant_id, records), "total": total}

    @app.get("/api/v1/audit/verify")
    def audit_verify(principal=Depends(require_auth), db=Depends(get_db),
                     recentes: int = Query(0, ge=0, le=5000)):
        """Percorre a cadeia de integridade da trilha e devolve o veredito com o denominador.

        `recentes` confere só a cauda — barato o bastante para rodar de hora em hora. Sem ele, a
        cadeia inteira, que é o que uma auditoria externa pede. Um resultado sem o número de linhas
        conferidas não diria nada: quem não lê nada também não acha problema nenhum.
        """
        principal.admin()
        return verificar_trilha(db, principal.tenant_id, recentes or None)

    @app.post("/api/v1/api-keys", status_code=201)
    def create_key(payload: KeyCreate, principal=Depends(require_auth), db=Depends(get_db)):
        principal.admin()
        lock_membership(db, principal)
        allowed = api_scopes()
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
        if not valid_time or not hmac.compare_digest(expected.encode(), signature.encode()):
            raise HTTPException(401, "Assinatura ou timestamp inválido")
        idempotency_key = request.headers.get("idempotency-key", "")
        if not 8 <= len(idempotency_key) <= 200:
            raise HTTPException(422, "Idempotency-Key de 8 a 200 caracteres obrigatória")
        if idempotency_key.startswith("create:"):
            raise HTTPException(422, "Prefixo reservado de Idempotency-Key")
        # Validate even on replay: a CRUD receipt is never a valid webhook envelope.
        try:
            payload = Webhook.model_validate_json(raw)
        except ValidationError as exc:
            raise HTTPException(422, "Envelope de evento inválido") from exc
        rate_limit(db, f"webhook:{principal.key.id}", 120, 60)
        body_hash = hashlib.sha256(raw).hexdigest()
        previous = db.scalar(select(Idempotency).where(Idempotency.tenant_id == principal.tenant_id,
                                                        Idempotency.key == idempotency_key))
        if previous:
            if previous.body_hash != body_hash:
                raise HTTPException(409, "Chave idempotente reutilizada com outro conteúdo")
            return {**previous.response, "duplicate": True}
        event_id = uid()
        result = {"id": event_id, "status": "accepted", "duplicate": False}
        db.add(Idempotency(tenant_id=principal.tenant_id, key=idempotency_key, body_hash=body_hash, response=result))
        db.add(Outbox(id=event_id, tenant_id=principal.tenant_id, event_type=payload.event_type,
                      payload=payload.payload, trace_id=payload.trace_id or uid(), hops=payload.hops,
                      origin="integration", actor={"type": "webhook", "id": principal.actor_id or "integration"}))
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

    app.add_api_route("/api/v1/contacts/import", contact_import, methods=["POST"])

    # A base de conhecimento e o grafo curado que acompanha a aplicacao. Ele e lido do pacote, nao
    # montado em tempo de execucao: a producao precisa responder o mesmo que o repositorio afirma.
    knowledge_graph = json.loads((pathlib.Path(__file__).parent / "knowledge_graph.json")
                                 .read_text(encoding="utf-8"))

    @app.get("/api/v1/knowledge/graph")
    def knowledge(principal=Depends(require_auth)):
        principal.require("knowledge:read")
        return knowledge_graph

    @app.get("/api/v1/knowledge/search")
    def knowledge_search(q: str = Query(..., min_length=2, max_length=500), limit: int = Query(10, ge=1, le=50),
                         principal=Depends(require_auth), db=Depends(get_db)):
        """Deterministic first-stage retrieval over CRM knowledge and the curated graph.

        This is intentionally provider-neutral: it gives the future RAG adapter a stable, tenant-scoped
        contract and citations before embeddings or an external NVIDIA deployment are enabled.
        """
        principal.require("knowledge:read")
        terms = {part.casefold() for part in q.split() if len(part) > 1}
        candidates = []
        for record in db.scalars(select(Record).where(Record.tenant_id == principal.tenant_id,
                                                       Record.kind == "knowledge", Record.deleted.is_(False))):
            data = record.data
            text_value = " ".join(str(data.get(key, "")) for key in ("title", "content", "category", "tags", "source"))
            score = sum(text_value.casefold().count(term) for term in terms)
            if score:
                candidates.append({"id": record.id, "kind": "knowledge", "title": data.get("title", ""),
                                   "text": data.get("content", ""), "source": data.get("source", ""),
                                   "score": score, "citation": {"kind": "knowledge", "id": record.id}})
        for node in knowledge_graph.get("nodes", []):
            text_value = " ".join(str(node.get(key, "")) for key in ("label", "summary", "why", "where", "source"))
            score = sum(text_value.casefold().count(term) for term in terms)
            if score:
                candidates.append({"id": node.get("id"), "kind": "graph", "title": node.get("label", ""),
                                   "text": node.get("summary", ""), "source": node.get("source", ""),
                                   "score": score, "citation": {"kind": "graph", "id": node.get("id")}})
        candidates.sort(key=lambda item: (-item["score"], item["title"]))
        return {"query": q, "items": candidates[:limit], "total": len(candidates), "provider": "lexical"}

    @app.post("/api/v1/knowledge/{record_id}/index")
    def index_knowledge(record_id: str, principal=Depends(require_auth), db=Depends(get_db)):
        """Create deterministic retrieval chunks; embeddings are added by a provider adapter later."""
        principal.require("knowledge:write")
        record = get_record(db, principal.tenant_id, "knowledge", record_id, lock=True)
        content = str(record.data.get("content", "")).strip()
        if not content:
            raise HTTPException(422, "Documento sem conteúdo para indexação")
        db.query(KnowledgeChunk).filter(KnowledgeChunk.tenant_id == principal.tenant_id,
                                        KnowledgeChunk.knowledge_id == record_id).delete(synchronize_session=False)
        words, chunks = content.split(), []
        for start in range(0, len(words), 180):
            chunk = " ".join(words[start:start + 180])
            chunks.append(KnowledgeChunk(tenant_id=principal.tenant_id, knowledge_id=record_id,
                chunk_index=len(chunks), content=chunk,
                meta={"title": record.data.get("title", ""), "category": record.data.get("category", "general"),
                          "source": record.data.get("source", "")},
                content_hash=hashlib.sha256(chunk.encode("utf-8")).hexdigest()))
        db.add_all(chunks)
        audit_event(db, principal.tenant_id, principal.actor_id, "knowledge.indexed", record_id,
                    {"chunks": len(chunks), "provider": "lexical"})
        db.commit()
        return {"knowledge_id": record_id, "chunks": len(chunks), "provider": "lexical"}

    @app.get("/api/v1/notifications")
    def notifications(principal=Depends(require_auth), db=Depends(get_db)):
        principal.require("dashboard:read")
        # A lista fixa aqui foi o que manteve contratos fora dos avisos mesmo depois de o
        # construtor passar a deriva-los: um conjunto escrito em dois lugares diverge no primeiro.
        allowed = {kind for kind in ("tasks", "approvals", "deals", "contracts")
                   if not principal.key or f"{kind}:read" in principal.key.scopes}
        return build_notifications(db, principal.tenant_id, allowed=allowed)

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

    # Proposals, goals and reports live in their own router; mounting it is what makes them exist.
    app.include_router(sales_router)
    from .work_queue import router as work_queue_router
    app.include_router(work_queue_router)
    from .instagram_accounts import router as instagram_router
    app.include_router(instagram_router)
    from .lead_queue import router as lead_router
    app.include_router(lead_router)
    from .synapse import router as synapse_router
    from .synapse_assistant import router as synapse_assistant_router
    app.include_router(synapse_router)
    app.include_router(synapse_assistant_router)
    from .core_api import router as core_router
    app.include_router(core_router)
    # Antes do laco de RESOURCES: /contacts/duplicates precisa vencer /contacts/{record_id}.
    from .merge import register_merge
    register_merge(app)
    from .contracts import register_contracts
    register_contracts(app)
    register_content_ops(app)
    register_agent_api(app)
    # Register every concrete route for an unambiguous OpenAPI operation catalog.
    for kind, schema in RESOURCES.items():
        register_resource(app, kind, schema)
    register_record_views(app)
    register_instagram_webhook(app, settings)
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


def describe_audit(db, tenant_id, records):
    """Resolve actor and subject names in two batched queries; an audit nobody can read is not a control."""
    actors = {item.actor_id for item in records if item.actor_id}
    subjects = {item.resource_id for item in records if item.resource_id}
    people = {user.id: user.name for user in db.scalars(select(User).where(
        User.tenant_id == tenant_id, User.id.in_(actors | subjects)))} if (actors or subjects) else {}
    titles = {record.id: (record.data.get("name") or record.data.get("title") or "")
              for record in db.scalars(select(Record).where(
                  Record.tenant_id == tenant_id, Record.id.in_(subjects)))} if subjects else {}
    described = []
    for item in records:
        actor = people.get(item.actor_id) or ("Sistema" if not item.actor_id else "Conta indisponível")
        subject = titles.get(item.resource_id) or people.get(item.resource_id, "")
        # Signing in names the actor twice; the subject only adds information when it differs.
        described.append({**audit_dict(item), "label": action_label(item.action), "actor_name": actor,
                          "resource_name": "" if subject == actor else subject})
    return described


def audit_dict(item):
    return {"id": item.id, "action": item.action, "resource_id": item.resource_id,
            "actor_id": item.actor_id, "details": item.details, "created_at": item.created_at.isoformat()}


def key_dict(key):
    return {"id": key.id, "name": key.name, "prefix": key.prefix, "scopes": key.scopes,
            "revoked": key.revoked, "expires_at": key.expires_at.isoformat()}


def redact(db, principal, kind, corpo):
    """Campo restrito nao sai da API para quem nao pode ve-lo. Esconder so na tela seria enfeite."""
    from .custom_fields import ocultar
    return ocultar(db, principal.tenant_id, kind, corpo, principal.role)


def register_resource(app, kind, schema):
    def listing(principal=Depends(require_auth), db=Depends(get_db), q: str = Query("", max_length=200),
                status: str | None = None, stage: str | None = None, contact_id: str | None = None,
                conversation_id: str | None = None, project_id: str | None = None, owner_id: str | None = None,
                pipeline_id: str | None = None,
                limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
        principal.require(f"{kind}:read")
        pagina = list_records(db, principal.tenant_id, kind, locals())
        return {**pagina, "items": [redact(db, principal, kind, item) for item in pagina["items"]]}

    def retrieve(record_id: str, principal=Depends(require_auth), db=Depends(get_db)):
        principal.require(f"{kind}:read")
        return redact(db, principal, kind, serialize(get_record(db, principal.tenant_id, kind, record_id)))

    def create(payload: schema, response: Response,
               idempotency_key: str | None = Header(default=None, alias="Idempotency-Key",
                   description="Optional stable operation key. Repeat the same key and body to recover the original creation result."),
               principal=Depends(require_auth), db=Depends(get_db)):
        principal.require(f"{kind}:write")
        if kind in PRIVILEGED and kind != "approvals":
            principal.admin()
        data = payload.model_dump(mode="json")
        # Keep legacy receipt hashes for omitted defaults; explicit zero now has its own meaning.
        explicit_zero = kind == "deals" and "probability" in payload.model_fields_set and data["probability"] == 0
        receipt_data = {**data, "_explicit_probability_zero": True} if explicit_zero else data
        key = idempotency_key
        receipt = None
        if key is not None:
            receipt, replayed = creation_receipt(db, principal, kind, key, receipt_data)
            response.headers["Idempotency-Replayed"] = str(replayed).lower()
            if replayed:
                result = receipt.response
                db.commit()
                return result
        if kind == "deals" and "probability" not in payload.model_fields_set:
            data = {name: value for name, value in data.items() if name != "probability"}
        record = create_record(db, principal.tenant_id, principal.actor_id, kind, data, role=principal.role)
        result = redact(db, principal, kind, serialize(record))
        if receipt is not None:
            receipt.response = result
        db.commit()
        return result

    def patch(record_id: str, payload: dict = Body(...), principal=Depends(require_auth), db=Depends(get_db)):
        principal.require(f"{kind}:write")
        if kind in PRIVILEGED:
            principal.admin()
        record = update_record(db, principal, kind, record_id, payload)
        db.commit()
        return redact(db, principal, kind, serialize(record))

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
