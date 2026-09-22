"""Transactional commercial installation of SYNAPSE; no external delivery or AI claims.

Configuration and enrollment receipts use the existing tenant-scoped records table.
Only this router can write them; generic resource CRUD cannot bypass the policies.
"""
from datetime import timedelta
from uuid import NAMESPACE_URL, uuid5

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field
from sqlalchemy import func, select, text, update

from .db import get_db
from .models import InstagramAccount, Record, User, now
from .schemas import Cents, Identifier, StrictModel
from .security import require_auth
from .services import audit_event, create_record, get_record, lock_contacts, scoped, serialize

router = APIRouter(prefix="/api/v1/synapse", tags=["SYNAPSE"])
CONFIG_KIND = "synapse_config"
RUN_KIND = "synapse_runs"
READ_SCOPES = ("contacts:read", "deals:read", "tasks:read", "pipelines:read", "products:read",
               "agents:read", "knowledge:read", "integrations:read")


class Setup(StrictModel):
    setup_cents: Cents = 326000
    monthly_cents: Cents = 49700
    sla_hours: int = Field(default=24, strict=True, ge=1, le=720)


class ConfigurationChange(StrictModel):
    version: int = Field(strict=True, ge=1)
    enabled: bool
    capture_enabled: bool
    owner_id: Identifier
    sla_hours: int = Field(strict=True, ge=1, le=720)


class Enrollment(StrictModel):
    contact_id: Identifier


def stable_id(tenant_id, purpose):
    return str(uuid5(NAMESPACE_URL, f"fattech:{tenant_id}:synapse:{purpose}"))


def lock_configuration(db, tenant_id):
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"),
                   {"scope": f"fattech:synapse:{tenant_id}"})
    else:
        db.execute(update(Record).where(Record.id == "").values(version=Record.version))


def configuration(db, tenant_id):
    return db.scalar(scoped(tenant_id, CONFIG_KIND).where(
        Record.id == stable_id(tenant_id, "configuration")).execution_options(populate_existing=True))


def valid_owner(db, tenant_id, owner_id):
    owner = db.scalar(select(User).where(User.id == owner_id, User.tenant_id == tenant_id,
                                        User.active.is_(True), User.role != "viewer"))
    if owner is None:
        raise HTTPException(422, "Escolha um responsável ativo da organização com permissão de operação.")
    return owner


def require_reads(principal):
    for scope in READ_SCOPES:
        principal.require(scope)


@router.post("/setup")
def setup(payload: Setup, principal=Depends(require_auth), db=Depends(get_db)):
    principal.admin()
    lock_contacts(db, principal.tenant_id)
    lock_configuration(db, principal.tenant_id)
    previous = configuration(db, principal.tenant_id)
    if previous:
        return {"created": False, "configuration": serialize(previous)}
    valid_owner(db, principal.tenant_id, principal.actor_id)
    pipeline = create_record(db, principal.tenant_id, principal.actor_id, "pipelines", {
        "name": "SYNAPSE · Vendas", "description": "Da entrada ao fechamento do produto SYNAPSE.",
        "is_default": False,
        "stages": [
            {"key": "lead", "label": "Entrada", "probability": 10, "expected_duration_hours": payload.sla_hours},
            {"key": "qualification", "label": "Qualificação", "probability": 25},
            {"key": "diagnosis", "label": "Diagnóstico", "probability": 45},
            {"key": "proposal", "label": "Proposta", "probability": 65},
            {"key": "negotiation", "label": "Negociação", "probability": 85},
            {"key": "won", "label": "Ganho", "outcome": "won"},
            {"key": "lost", "label": "Perdido", "outcome": "lost"},
        ],
        "loss_reasons": ["Sem orçamento", "Fora do perfil", "Momento inadequado", "Concorrente", "Sem retorno"],
    }, role=principal.role)
    installation = create_record(db, principal.tenant_id, principal.actor_id, "products", {
        "name": "SYNAPSE · Implantação", "sku": "SYNAPSE-SETUP", "price_cents": payload.setup_cents,
        "unit": "projeto", "recurrence": "nenhuma", "category": "SYNAPSE",
        "description": "Implantação do CRM e acompanhamento de configuração por 60 dias.",
    }, role=principal.role)
    license_product = create_record(db, principal.tenant_id, principal.actor_id, "products", {
        "name": "SYNAPSE · Licença mensal", "sku": "SYNAPSE-MONTHLY", "price_cents": payload.monthly_cents,
        "unit": "mes", "recurrence": "mensal", "category": "SYNAPSE",
        "description": "Licença mensal. Cobrança e pagamento dependem de contratação e provedor configurado.",
    }, role=principal.role)
    agent = create_record(db, principal.tenant_id, principal.actor_id, "agents", {
        "name": "SYNAPSE · Copiloto comercial", "squad": "Comercial", "role": "Qualificação assistida",
        "status": "paused", "autonomy": "A0", "budget_cents": 0,
        "description": "Preparar contexto e respostas fundamentadas para revisão humana. Sem envio automático.",
    }, role=principal.role)
    record = Record(id=stable_id(principal.tenant_id, "configuration"), tenant_id=principal.tenant_id,
                    kind=CONFIG_KIND, data={
                        "pipeline_id": pipeline.id, "setup_product_id": installation.id,
                        "license_product_id": license_product.id, "agent_id": agent.id,
                        "owner_id": principal.actor_id, "enabled": True, "capture_enabled": False,
                        "sla_hours": payload.sla_hours, "setup_cents": payload.setup_cents,
                        "monthly_cents": payload.monthly_cents,
                    })
    db.add(record)
    db.flush()
    audit_event(db, principal.tenant_id, principal.actor_id, "synapse.installed", record.id,
                {"pipeline_id": pipeline.id, "agent_id": agent.id})
    db.commit()
    return {"created": True, "configuration": serialize(record)}


@router.post("/settings")
def settings(payload: ConfigurationChange, principal=Depends(require_auth), db=Depends(get_db)):
    principal.admin()
    lock_contacts(db, principal.tenant_id)
    lock_configuration(db, principal.tenant_id)
    record = configuration(db, principal.tenant_id)
    if record is None:
        raise HTTPException(409, "Instale o SYNAPSE antes de configurar a operação.")
    if record.version != payload.version:
        raise HTTPException(409, "Versão desatualizada; recarregue a configuração.")
    valid_owner(db, principal.tenant_id, payload.owner_id)
    if payload.capture_enabled and not payload.enabled:
        raise HTTPException(422, "Ative a operação SYNAPSE antes de ativar a captura automática.")
    if payload.enabled:
        pipeline = get_record(db, principal.tenant_id, "pipelines", record.data["pipeline_id"], share=True)
        if pipeline.data.get("status") != "active" or not any(
                stage["outcome"] == "open" for stage in pipeline.data["stages"]):
            raise HTTPException(409, "O funil SYNAPSE precisa estar ativo e ter uma etapa aberta.")
    record.data = {**record.data, **payload.model_dump(exclude={"version"})}
    record.version += 1
    record.updated_at = now()
    audit_event(db, principal.tenant_id, principal.actor_id, "synapse.configured", record.id,
                {"version": record.version, "enabled": payload.enabled, "capture_enabled": payload.capture_enabled})
    db.commit()
    return serialize(record)


def enroll_contact(db, tenant_id, actor_id, contact):
    """Enroll exactly once for this installation, committing with the caller's contact transaction.

    Lock order starts at contacts, also used by public capture and generic contact writers.
    The persistent run is the receipt: request headers, retries and different operators cannot
    create a second opportunity. No provider call belongs in this transaction.
    """
    lock_contacts(db, tenant_id)
    lock_configuration(db, tenant_id)
    config = configuration(db, tenant_id)
    if config is None or not config.data.get("enabled"):
        raise HTTPException(409, "A operação SYNAPSE está desativada ou ainda não foi instalada.")
    contact = get_record(db, tenant_id, "contacts", contact.id, lock=True)
    receipt_id = stable_id(tenant_id, f"enrollment:{config.id}:{contact.id}")
    previous = db.scalar(scoped(tenant_id, RUN_KIND).where(Record.id == receipt_id))
    if previous:
        return {**serialize(previous), "duplicate": True}
    owner = valid_owner(db, tenant_id, config.data["owner_id"])
    actor_role = valid_owner(db, tenant_id, actor_id).role if actor_id else ""
    pipeline = get_record(db, tenant_id, "pipelines", config.data["pipeline_id"], share=True)
    if pipeline.data.get("status") != "active":
        raise HTTPException(409, "O funil SYNAPSE está inativo.")
    stage = next((item for item in pipeline.data["stages"] if item["outcome"] == "open"), None)
    if stage is None:
        raise HTTPException(409, "O funil SYNAPSE não possui etapa aberta.")
    deadline = (now() + timedelta(hours=config.data["sla_hours"])).isoformat()
    product = get_record(db, tenant_id, "products", config.data["setup_product_id"], share=True)
    if product.data.get("status") != "active":
        raise HTTPException(409, "O produto de implantação SYNAPSE está inativo.")
    deal = create_record(db, tenant_id, actor_id, "deals", {
        "title": f"SYNAPSE · {contact.data['name']}"[:200], "contact_id": contact.id,
        "company_id": contact.data.get("company_id"),
        "pipeline_id": pipeline.id, "stage": stage["key"], "owner_id": owner.id,
        "value_cents": product.data["price_cents"], "next_action_at": deadline,
        "notes": "Valor da implantação. Mensalidade será discriminada na proposta; não foi cobrada.",
    }, role=actor_role)
    task = create_record(db, tenant_id, actor_id, "tasks", {
        "title": f"Qualificar SYNAPSE · {contact.data['name']}"[:200],
        "description": "Revisar perfil, interesse e consentimento; registrar diagnóstico e próxima ação.",
        "priority": "high", "due_date": deadline, "contact_id": contact.id,
        "deal_id": deal.id, "owner_id": owner.id,
    })
    receipt = Record(id=receipt_id, tenant_id=tenant_id, kind=RUN_KIND, data={
        "status": "enrolled", "configuration_id": config.id, "configuration_version": config.version,
        "contact_id": contact.id, "deal_id": deal.id, "task_id": task.id,
        "owner_id": owner.id, "due_at": deadline, "source": "website" if actor_id is None else "manual",
        "setup_cents": product.data["price_cents"],
    })
    db.add(receipt)
    db.flush()
    audit_event(db, tenant_id, actor_id, "synapse.enrolled", receipt.id,
                {"contact_id": contact.id, "deal_id": deal.id, "task_id": task.id})
    return {**serialize(receipt), "duplicate": False}


@router.post("/enroll")
def enroll(payload: Enrollment, principal=Depends(require_auth), db=Depends(get_db)):
    # The workflow writes multiple resources and returns their identifiers; scoped API keys
    # must have every corresponding read/write grant, not just contact access.
    for scope in ("contacts:read", "deals:write", "deals:read", "tasks:write", "tasks:read", "pipelines:read",
                  "products:read"):
        principal.require(scope)
    contact = get_record(db, principal.tenant_id, "contacts", payload.contact_id)
    result = enroll_contact(db, principal.tenant_id, principal.actor_id, contact)
    db.commit()
    return result


def count(db, tenant_id, kind, *conditions):
    return db.scalar(select(func.count()).select_from(Record).where(
        Record.tenant_id == tenant_id, Record.kind == kind, Record.deleted.is_(False), *conditions)) or 0


def run_page(db, tenant_id, limit, offset):
    records = db.scalars(scoped(tenant_id, RUN_KIND).order_by(Record.created_at.desc(), Record.id)
                         .limit(limit).offset(offset))
    return {"items": [serialize(record) for record in records], "total": count(db, tenant_id, RUN_KIND)}


@router.get("/runs")
def runs(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
         principal=Depends(require_auth), db=Depends(get_db)):
    require_reads(principal)
    return run_page(db, principal.tenant_id, limit, offset)


@router.get("/overview")
def overview(principal=Depends(require_auth), db=Depends(get_db)):
    require_reads(principal)
    tenant_id = principal.tenant_id
    config = configuration(db, tenant_id)
    pipeline_id = config.data["pipeline_id"] if config else ""
    pipeline_deals = scoped(tenant_id, "deals").where(Record.data["pipeline_id"].as_string() == pipeline_id)
    deal_ids = pipeline_deals.with_only_columns(Record.id)
    pipeline_filter = Record.data["pipeline_id"].as_string() == pipeline_id
    metrics = {
        "leads": count(db, tenant_id, RUN_KIND),
        "deals": count(db, tenant_id, "deals", pipeline_filter),
        "open_deals": count(db, tenant_id, "deals", pipeline_filter, Record.data["outcome"].as_string() == "open"),
        "won_deals": count(db, tenant_id, "deals", pipeline_filter, Record.data["outcome"].as_string() == "won"),
        "pending_tasks": count(db, tenant_id, "tasks", Record.data["deal_id"].as_string().in_(deal_ids),
                               Record.data["status"].as_string() != "done"),
    }
    connected_instagram = db.scalar(select(func.count()).select_from(InstagramAccount).where(
        InstagramAccount.tenant_id == tenant_id, InstagramAccount.status == "connected")) or 0
    has_knowledge = bool(count(db, tenant_id, "knowledge", Record.data["content"].as_string() != ""))
    assets = []
    if config:
        for field, kind in (("pipeline_id", "pipelines"), ("setup_product_id", "products"),
                            ("license_product_id", "products"), ("agent_id", "agents")):
            assets.append(db.scalar(scoped(tenant_id, kind).where(Record.id == config.data[field])))
    commercial_ready = bool(config and config.data.get("enabled") and len(assets) == 4
                            and all(assets) and all(asset.data.get("status") == "active" for asset in assets[:3]))
    readiness = [
        {"key": "commercial", "label": "Operação comercial", "status": "ready" if commercial_ready else "pending",
         "detail": "Funil e catálogo ativos; cadastro do agente disponível." if commercial_ready
         else "Prepare a operação e revise os vínculos do funil, catálogo e agente.",
         "href": "/crm/synapse"},
        {"key": "capture", "label": "Captura do site", "status": "ready" if config and config.data.get("enabled")
         and config.data.get("capture_enabled") else "pending",
         "detail": "Adesão automática ao SYNAPSE controlada pela configuração da organização.", "href": "/crm/synapse"},
        {"key": "knowledge", "label": "Conhecimento", "status": "ready" if has_knowledge else "pending",
         "detail": "Recuperação lexical com fontes; embeddings e LLM externo dependem de integração.",
         "href": "/crm/conhecimento"},
        {"key": "instagram", "label": "Conta Instagram", "status": "ready" if connected_instagram else "pending",
         "detail": f"{connected_instagram} conta(s) conectada(s). Conexão não comprova envio externo.",
         "href": "/crm/integracoes"},
        {"key": "whatsapp", "label": "WhatsApp oficial", "status": "pending",
         "detail": "Provedor de envio e credenciais da organização ainda precisam ser integrados.", "href": "/crm/integracoes"},
        {"key": "autonomy", "label": "Agentes autônomos", "status": "pending",
         "detail": "Cadastro pausado. Executor autônomo e envio externo não estão ativos.", "href": "/crm/ia"},
        {"key": "calendar", "label": "Agenda e Google Calendar", "status": "pending",
         "detail": "Reserva de horários e sincronização externa ainda não implementadas.", "href": "/crm/tarefas"},
        {"key": "subscriptions", "label": "Assinaturas de clientes", "status": "pending",
         "detail": "O catálogo registra recorrência; cobrança automática e liberação de módulos por plano ainda não existem.",
         "href": "/crm/produtos"},
        {"key": "customer_activation", "label": "Ativação do cliente", "status": "pending",
         "detail": "Preparar este workspace não cria um ambiente isolado para um cliente comprador.",
         "href": "/crm/projetos"},
    ]
    return {"id": "synapse", "installed": config is not None,
            "configuration": serialize(config) if config else None, "metrics": metrics,
            "readiness": readiness, "recent_runs": run_page(db, tenant_id, 10, 0)["items"]}
