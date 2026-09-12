from datetime import timedelta
import hashlib
import re

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, or_, select, text, update
from sqlalchemy.orm import Session

from .models import Audit, Outbox, Record, User, now, uid
from .schemas import DEFAULT_STAGE_HOURS, RESOURCES

RELATIONS = {"contact_id": "contacts", "company_id": "companies", "deal_id": "deals",
             "project_id": "projects", "conversation_id": "conversations"}
# Configuration parents are read by every deal write, so they are guarded without an exclusive row lock.
SHARED_RELATIONS = {"pipeline_id": "pipelines"}
PRIVILEGED = {"agents", "approvals", "automations", "invoices", "pipelines"}


def lock_contacts(db, tenant_id):
    """Serialize every contact writer before reading rows; lock survives until outer commit/rollback."""
    if db.bind.dialect.name == "postgresql":
        key = int.from_bytes(hashlib.sha256(f"fattech:contacts:{tenant_id}".encode()).digest()[:8], "big", signed=True)
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
    else:
        # SQLite has one writer per database. A no-op write reserves it before a read/write upgrade can race.
        db.execute(update(Record).where(Record.tenant_id == tenant_id, Record.id == "")
                   .values(version=Record.version).execution_options(synchronize_session=False))


def find_contact_matches(db, tenant_id, data, exclude_id=None):
    """Caller holds lock_contacts. Returns only this tenant's active matches; never merges historical rows."""
    identifiers = normalize_contact_identifiers(data)
    if not identifiers.get("email") and not identifiers.get("phone"):
        return []
    query = scoped(tenant_id, "contacts")
    if exclude_id:
        query = query.where(Record.id != exclude_id)
    matches = []
    # ponytail: scan normalizes legacy formats without rewriting history; indexed keys need a backfill migration.
    for record in db.scalars(query.execution_options(populate_existing=True)):
        try:
            candidate = normalize_contact_identifiers(record.data)
        except HTTPException:
            # Existing malformed phone data must not hide an otherwise matching valid email.
            candidate = normalize_contact_identifiers({**record.data, "phone": ""})
        if any(identifiers.get(field) and identifiers[field] == candidate.get(field) for field in ("email", "phone")):
            matches.append(record)
    return matches


def ensure_unique_contact(db, tenant_id, data, exclude_id=None):
    if find_contact_matches(db, tenant_id, data, exclude_id):
        raise HTTPException(409, "Já existe um contato com este e-mail ou telefone nesta empresa")


def normalize_contact_identifiers(data):
    """Canonical CRM identifiers; local 10/11-digit phones are Brazilian, other countries need + or 00."""
    normalized = dict(data)
    email = normalized.get("email")
    normalized["email"] = email.strip().lower() if email else None
    phone = (normalized.get("phone") or "").strip()
    if not phone:
        normalized["phone"] = ""
        return normalized
    if not re.fullmatch(r"\+?[0-9()\s.\-]+", phone):
        raise HTTPException(422, "Telefone inválido; informe DDD e número, sem ramal ou letras")
    digits = re.sub(r"[^0-9]", "", phone)
    international = phone.startswith("+") or digits.startswith("00")
    if digits.startswith("00") and not phone.startswith("+"):
        digits = digits[2:]
    if not international:
        if len(digits) in (10, 11):
            digits = "55" + digits
        elif not (digits.startswith("55") and len(digits) in (12, 13)):
            raise HTTPException(422, "Telefone inválido; informe DDD ou prefixo internacional +")
    if not 8 <= len(digits) <= 15 or digits.startswith("0"):
        raise HTTPException(422, "Telefone inválido; use de 8 a 15 dígitos com código do país")
    if digits.startswith("55") and (len(digits) not in (12, 13) or digits[2] == "0"):
        raise HTTPException(422, "Telefone brasileiro inválido; informe DDD e número completo")
    normalized["phone"] = "+" + digits
    return normalized


def scoped(tenant_id: str, kind: str):
    return select(Record).where(Record.tenant_id == tenant_id, Record.kind == kind, Record.deleted.is_(False))


def get_record(db: Session, tenant_id: str, kind: str, record_id: str, *, lock=False, share=False):
    statement = scoped(tenant_id, kind).where(Record.id == record_id)
    if lock or share:
        # FOR SHARE lets concurrent deals read the same pipeline while still blocking its removal.
        statement = statement.with_for_update(read=share and not lock)
    record = db.scalar(statement)
    if record is None:
        raise HTTPException(404, "Registro não encontrado")
    return record


def serialize(record: Record):
    return {**record.data, "id": record.id, "tenant_id": record.tenant_id, "version": record.version,
            "created_at": record.created_at.isoformat(), "updated_at": record.updated_at.isoformat()}


def audit_event(db, tenant_id, actor_id, action, resource_id, details=None):
    metadata = details or {}
    db.add(Audit(tenant_id=tenant_id, actor_id=actor_id, action=action, resource_id=resource_id, details=metadata))
    db.add(Outbox(tenant_id=tenant_id, event_type=action,
                  payload={"resource_id": resource_id, **metadata}, trace_id=uid()))


def validate(kind, data):
    try:
        return RESOURCES[kind].model_validate(data).model_dump(mode="json")
    except ValidationError as exc:
        # Never echo supplied secrets/input in a validation response.
        raise HTTPException(422, [{"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
                                  for error in exc.errors()]) from exc


def validate_relations(db, tenant_id, data):
    for field, kind in RELATIONS.items():
        if data.get(field):
            get_record(db, tenant_id, kind, data[field], lock=True)
    if data.get("owner_id"):
        owner = db.scalar(select(User).where(User.id == data["owner_id"], User.tenant_id == tenant_id,
                                            User.active.is_(True)))
        if owner is None:
            raise HTTPException(422, "Responsável inválido")


def validate_flow(data):
    nodes = data.get("nodes", [])
    ids = {node["id"] for node in nodes}
    if len(ids) != len(nodes):
        raise HTTPException(422, "IDs de nós duplicados")
    adjacency = {node_id: [] for node_id in ids}
    for edge in data.get("edges", []):
        if edge["source"] not in ids or edge["target"] not in ids:
            raise HTTPException(422, "Aresta referencia nó inexistente")
        adjacency[edge["source"]].append(edge["target"])
    visiting, visited = set(), set()
    def visit(node):
        if node in visiting:
            raise HTTPException(422, "Ciclo no fluxo; utilize atraso e novo evento")
        if node in visited:
            return
        visiting.add(node)
        for target in adjacency[node]:
            visit(target)
        visiting.remove(node)
        visited.add(node)
    for node in ids:
        visit(node)


def default_pipeline(db, tenant_id):
    active = [record for record in db.scalars(scoped(tenant_id, "pipelines").order_by(Record.created_at))
              if record.data.get("status") == "active"]
    return next((record for record in active if record.data.get("is_default")), active[0] if active else None)


def promote_default_pipeline(db, tenant_id, record_id):
    """One default funnel per tenant; demoting the previous one keeps its version and audit trail honest."""
    for other in db.scalars(scoped(tenant_id, "pipelines").where(Record.id != record_id).with_for_update()):
        if other.data.get("is_default"):
            db.execute(update(Record).where(Record.id == other.id, Record.tenant_id == tenant_id)
                       .values(data={**other.data, "is_default": False}, version=other.version + 1, updated_at=now()))


def guard_stage_removal(db, tenant_id, pipeline_id, before, after):
    """A stage still holding deals cannot be renamed away or dropped without orphaning them."""
    remaining = {stage["key"] for stage in after}
    for stage in before:
        if stage["key"] in remaining:
            continue
        occupied = db.scalar(select(Record.id).where(Record.tenant_id == tenant_id, Record.kind == "deals",
            Record.deleted.is_(False), Record.data["pipeline_id"].as_string() == pipeline_id,
            Record.data["stage"].as_string() == stage["key"]).limit(1))
        if occupied:
            raise HTTPException(409, f"A etapa {stage['label']} possui oportunidades ativas; mova-as antes de removê-la")


def apply_deal_rules(db, tenant_id, data, keep_probability, previous=None):
    """Stage vocabulary is tenant configuration, so it is resolved here rather than by a static schema literal."""
    if data.get("pipeline_id"):
        pipeline = get_record(db, tenant_id, "pipelines", data["pipeline_id"], share=True)
        # An archived funnel stops receiving deals but must not strand the ones already in it.
        if pipeline.data.get("status") != "active" and data["pipeline_id"] != previous:
            raise HTTPException(422, "Funil inativo; escolha um funil ativo")
    else:
        pipeline = default_pipeline(db, tenant_id)
        if pipeline is None:
            raise HTTPException(409, "Cadastre um funil ativo antes de registrar oportunidades")
        data["pipeline_id"] = pipeline.id
    stage = next((item for item in pipeline.data["stages"] if item["key"] == data["stage"]), None)
    if stage is None:
        raise HTTPException(422, "Etapa desconhecida neste funil")
    if stage["outcome"] == "lost" and not data.get("lost_reason", "").strip():
        raise HTTPException(422, "Informe o motivo da perda para encerrar a oportunidade")
    if stage["outcome"] != "lost":
        data["lost_reason"] = ""
    if not keep_probability:
        data["probability"] = stage["probability"]
    # Server-owned and deliberately outside the schema, so it survives edits and no client can forge it.
    data["last_activity_at"] = now().isoformat()


RISK_ORDER = {"critico": 4, "em_risco": 3, "em_voo": 2, "em_dia": 1}


def classify_risk(last_activity, next_action, expected_hours, moment):
    """A scheduled next action holds a deal in flight: whoever already booked the next step is not stalled."""
    elapsed = float("inf") if last_activity is None else max(0.0, (moment - last_activity).total_seconds() / 3600)
    ratio = elapsed / max(1, expected_hours)
    if next_action and next_action > moment and ratio < 1.5:
        bucket = "em_voo"
    elif ratio >= 2:
        bucket = "critico"
    elif ratio >= 1:
        bucket = "em_risco"
    else:
        bucket = "em_dia"
    finite = elapsed if elapsed != float("inf") else None
    return {"bucket": bucket, "elapsed_hours": None if finite is None else round(finite, 1),
            "ratio": None if finite is None else round(ratio, 2)}


def score_band(probability):
    """Shared vocabulary between interface, report and automation; probability now comes from the stage."""
    if probability is None:
        return None
    return "quente" if probability >= 65 else "morno" if probability >= 35 else "frio"


def build_radar(db, tenant_id, pipeline):
    """Open deals ranked by commercial risk, with the summary the operator would otherwise count by hand."""
    from .compliance import instant
    moment = now()
    stages = {stage["key"]: stage for stage in pipeline.data["stages"]}
    items = []
    for record in db.scalars(scoped(tenant_id, "deals").where(
            Record.data["pipeline_id"].as_string() == pipeline.id)):
        stage = stages.get(record.data.get("stage"))
        if stage is None or stage["outcome"] != "open":
            continue
        activity = instant(record.data.get("last_activity_at")) or instant(record.updated_at)
        action = instant(record.data.get("next_action_at"))
        risk = classify_risk(activity, action, int(stage.get("expected_duration_hours", DEFAULT_STAGE_HOURS)), moment)
        items.append({"id": record.id, "title": record.data.get("title"), "stage": stage["key"],
                      "stage_label": stage["label"], "value_cents": record.data.get("value_cents", 0),
                      "probability": record.data.get("probability", 0),
                      "band": score_band(record.data.get("probability")),
                      "contact_id": record.data.get("contact_id"), "owner_id": record.data.get("owner_id"),
                      "last_activity_at": activity.isoformat() if activity else None,
                      "next_action_at": record.data.get("next_action_at"), "version": record.version,
                      "risk": risk, "needs_action": not action or action <= moment})
    # Worst risk first, then the deal untouched for longest inside that bucket.
    items.sort(key=lambda item: (-RISK_ORDER[item["risk"]["bucket"]], item["last_activity_at"] or ""))
    summary = {bucket: sum(1 for item in items if item["risk"]["bucket"] == bucket) for bucket in RISK_ORDER}
    summary["needs_action"] = sum(1 for item in items if item["needs_action"])
    return {"pipeline_id": pipeline.id, "pipeline_name": pipeline.data["name"],
            "items": items, "total": len(items), "summary": summary}


def create_record(db, tenant_id, actor_id, kind, payload):
    if kind == "contacts":
        lock_contacts(db, tenant_id)
    data = validate(kind, payload)
    if kind == "contacts":
        data = normalize_contact_identifiers(data)
        ensure_unique_contact(db, tenant_id, data)
    validate_relations(db, tenant_id, data)
    if kind == "automations":
        validate_flow(data)
    if kind == "deals":
        apply_deal_rules(db, tenant_id, data, bool(payload.get("probability")))
    if kind == "approvals":
        data.update(requested_by=actor_id, expires_at=(now() + timedelta(hours=24)).isoformat())
    record = Record(tenant_id=tenant_id, kind=kind, data=data)
    db.add(record)
    db.flush()
    if kind == "pipelines" and data["is_default"]:
        promote_default_pipeline(db, tenant_id, record.id)
    audit_event(db, tenant_id, actor_id, f"{kind}.created", record.id, {"version": 1})
    return record


def capture_lead(db, tenant_id, payload, attribution):
    """Public resubmission enriches the existing contact instead of failing.

    WEB-03 asks that a resend not duplicate, not that it error: a visitor filling the form twice must
    not receive a conflict, which would also disclose that the address is already in the CRM. First-touch
    attribution and the original consent instant are never overwritten by a later submission.
    """
    lock_contacts(db, tenant_id)
    identifiers = normalize_contact_identifiers(validate("contacts", payload))
    existing = find_contact_matches(db, tenant_id, identifiers)
    if not existing:
        record = create_record(db, tenant_id, None, "contacts", payload)
        record.data = {**record.data, "attribution": attribution, "consented_at": now().isoformat()}
        return record
    record = existing[0]
    entry = f"{now().date().isoformat()} · {payload['notes']}".strip()
    history = str(record.data.get("notes") or "").strip()
    merged = {**record.data, "consent": True,
              "notes": f"{history}\n\n{entry}"[-20000:] if history else entry[:20000]}
    merged.setdefault("attribution", attribution)
    merged.setdefault("consented_at", now().isoformat())
    db.execute(update(Record).where(Record.id == record.id, Record.tenant_id == tenant_id)
               .values(data=merged, version=record.version + 1, updated_at=now()))
    audit_event(db, tenant_id, None, "contacts.recaptured", record.id, {"version": record.version + 1})
    db.refresh(record)
    return record


def update_record(db, principal, kind, record_id, payload):
    if kind == "contacts":
        lock_contacts(db, principal.tenant_id)
    record = get_record(db, principal.tenant_id, kind, record_id, lock=True)
    if kind == "contacts":
        db.refresh(record)
    changes = dict(payload)
    version = changes.pop("version", None)
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise HTTPException(422, "version inteira obrigatória")
    if kind == "approvals":
        raise HTTPException(409, "Intenções são imutáveis; use a decisão ou crie nova solicitação")
    editable = {key: value for key, value in record.data.items() if key in RESOURCES[kind].model_fields}
    protected = {key: value for key, value in record.data.items() if key not in RESOURCES[kind].model_fields}
    data = {**validate(kind, {**editable, **changes}), **protected}
    if kind == "contacts":
        data = normalize_contact_identifiers(data)
        ensure_unique_contact(db, principal.tenant_id, data, record_id)
    validate_relations(db, principal.tenant_id, data)
    if kind == "automations":
        validate_flow(data)
    if kind == "deals":
        apply_deal_rules(db, principal.tenant_id, data, "probability" in changes, record.data.get("pipeline_id"))
    if kind == "pipelines":
        guard_stage_removal(db, principal.tenant_id, record_id, record.data["stages"], data["stages"])
    result = db.execute(update(Record).where(Record.id == record_id, Record.tenant_id == principal.tenant_id,
                                           Record.version == version, Record.deleted.is_(False))
                        .values(data=data, version=version + 1, updated_at=now()))
    if result.rowcount != 1:
        raise HTTPException(409, "O registro foi alterado por outra pessoa. Atualize e tente novamente.")
    if kind == "pipelines" and data["is_default"]:
        promote_default_pipeline(db, principal.tenant_id, record_id)
    audit_event(db, principal.tenant_id, principal.actor_id, f"{kind}.updated", record_id,
                {"version": version + 1, "fields": sorted(changes)})
    db.flush()
    db.refresh(record)
    return record


def delete_record(db, principal, kind, record_id, version):
    if kind == "contacts":
        lock_contacts(db, principal.tenant_id)
    get_record(db, principal.tenant_id, kind, record_id, lock=True)
    # Prevent dangling relationships rather than silently hiding parent records.
    for field, related_kind in {**RELATIONS, **SHARED_RELATIONS}.items():
        if related_kind == kind:
            exists = db.scalar(select(Record.id).where(Record.tenant_id == principal.tenant_id,
                                Record.deleted.is_(False), Record.data[field].as_string() == record_id).limit(1))
            if exists:
                raise HTTPException(409, "Registro possui vínculos ativos")
    result = db.execute(update(Record).where(Record.id == record_id, Record.tenant_id == principal.tenant_id,
                                           Record.version == version, Record.deleted.is_(False))
                        .values(deleted=True, version=version + 1, updated_at=now()))
    if result.rowcount != 1:
        raise HTTPException(409, "Versão desatualizada")
    audit_event(db, principal.tenant_id, principal.actor_id, f"{kind}.deleted", record_id, {"version": version + 1})


def list_records(db, tenant_id, kind, filters):
    statement = scoped(tenant_id, kind)
    for field in ("status", "stage", "contact_id", "conversation_id", "project_id", "owner_id", "pipeline_id"):
        if filters.get(field):
            statement = statement.where(Record.data[field].as_string() == filters[field])
    if filters.get("q"):
        term = filters["q"].replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")[:200]
        statement = statement.where(or_(*[Record.data[field].as_string().ilike(f"%{term}%", escape="\\")
                                          for field in ("name", "title", "email", "body")]))
    total = db.scalar(select(func.count()).select_from(statement.subquery()))
    records = db.scalars(statement.order_by(Record.created_at.desc()).limit(filters["limit"]).offset(filters["offset"]))
    return {"items": [serialize(record) for record in records], "total": total}


def simulate(data, supplied):
    validate_flow(data)
    nodes = {node["id"]: node for node in data["nodes"]}
    incoming = {edge["target"] for edge in data["edges"]}
    queue = sorted(node_id for node_id in nodes if node_id not in incoming)
    context = dict(supplied)
    steps, visited = [], set()
    while queue:
        node_id = queue.pop(0)
        if node_id in visited:
            continue
        visited.add(node_id)
        node = nodes[node_id]
        kind, config = node["type"], node["config"]
        result = {"node_id": node_id, "type": kind, "status": "simulated"}
        branch = None
        if kind == "condition":
            branch = "true" if context.get(str(config.get("field", ""))) == config.get("equals") else "false"
            result["branch"] = branch
        elif kind == "set":
            context[str(config.get("key", "value"))] = config.get("value")
        elif kind == "message":
            result["preview"] = str(config.get("body", ""))[:10000]
        elif kind in ("ai", "webhook"):
            result["status"] = "blocked_external_side_effect"
        steps.append(result)
        if kind == "end":
            continue
        queue.extend(edge["target"] for edge in data["edges"] if edge["source"] == node_id
                     and (branch is None or edge.get("condition", "") in ("", branch)))
    return {"mode": "simulation", "sent": False, "steps": steps, "output": context}
