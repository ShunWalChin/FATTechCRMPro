from datetime import timedelta
import hashlib
import re

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import Integer, cast, func, or_, select, text, update
from sqlalchemy.orm import Session

from . import lead_scoring
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


def lock_pipeline_configuration(db, tenant_id):
    """Acquire before pipeline row locks, including first/default creation in an empty tenant."""
    if db.bind.dialect.name == "postgresql":
        key = int.from_bytes(hashlib.sha256(f"fattech:pipelines:{tenant_id}".encode()).digest()[:8], "big", signed=True)
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
    else:
        db.execute(update(Record).where(Record.id == "").values(version=Record.version))


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
    matches = find_contact_matches(db, tenant_id, data, exclude_id)
    if matches:
        raise HTTPException(409, {"message": "Já existe um contato com este e-mail ou telefone.",
                                  "contact_id": matches[0].id,
                                  "contact_name": matches[0].data.get("name", "")})


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
    record = db.scalar(statement.execution_options(populate_existing=lock or share))
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
            next_version = other.version + 1
            db.execute(update(Record).where(Record.id == other.id, Record.tenant_id == tenant_id)
                       .values(data={**other.data, "is_default": False}, version=next_version, updated_at=now()))
            audit_event(db, tenant_id, None, "pipelines.default_replaced", other.id,
                        {"replacement_id": record_id, "version": next_version})


def guard_stage_removal(db, tenant_id, pipeline_id, before, after):
    """A stage still holding deals cannot be renamed away or dropped without orphaning them."""
    remaining = {stage["key"]: stage for stage in after}
    for stage in before:
        if stage["key"] in remaining and remaining[stage["key"]]["outcome"] == stage["outcome"]:
            continue
        occupied = db.scalar(select(Record.id).where(Record.tenant_id == tenant_id, Record.kind == "deals",
            Record.deleted.is_(False), Record.data["pipeline_id"].as_string() == pipeline_id,
            Record.data["stage"].as_string() == stage["key"]).limit(1))
        if occupied:
            raise HTTPException(409, f"A etapa {stage['label']} possui oportunidades ativas; mova-as antes de removê-la ou mudar seu desfecho")


def apply_deal_rules(db, tenant_id, data, keep_probability, previous=None, previous_reason=None, before=None):
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
        pipeline = get_record(db, tenant_id, "pipelines", pipeline.id, share=True)
        if pipeline.data.get("status") != "active":
            raise HTTPException(409, "O funil padrão foi desativado; atualize e escolha outro funil")
        data["pipeline_id"] = pipeline.id
    stage = next((item for item in pipeline.data["stages"] if item["key"] == data["stage"]), None)
    if stage is None:
        raise HTTPException(422, "Etapa desconhecida neste funil")
    required_labels = {"contact_id": "Contato", "company_id": "Empresa cadastrada", "owner_id": "Responsável",
                       "value_cents": "Valor maior que zero", "expected_close": "Previsão de fechamento",
                       "next_action_at": "Próxima ação"}
    missing = [field for field in stage.get("required_fields", []) if not data.get(field)]
    if missing:
        raise HTTPException(422, {"message": "Complete os campos exigidos na etapa " + stage["label"] + ": "
                                  + ", ".join(required_labels[field] for field in missing),
                                  "required_fields": missing, "stage": stage["key"]})
    if stage["outcome"] == "lost" and not data.get("lost_reason", "").strip():
        raise HTTPException(422, "Informe o motivo da perda para encerrar a oportunidade")
    reasons = pipeline.data.get("loss_reasons", [])
    if (stage["outcome"] == "lost" and reasons and data.get("lost_reason") not in reasons
            and not (previous == pipeline.id and previous_reason == data.get("lost_reason"))):
        raise HTTPException(422, "Escolha um motivo de perda configurado no funil")
    if stage["outcome"] != "lost":
        data["lost_reason"] = ""
    if stage["outcome"] != "open":
        data["probability"] = 100 if stage["outcome"] == "won" else 0
    elif not keep_probability:
        data["probability"] = stage["probability"]
    prior_outcome = before.get("outcome") if before else None
    if before and prior_outcome is None:
        # Legacy records have no trustworthy closing instant. Resolve their old outcome without inventing one.
        old_pipeline = pipeline if previous == pipeline.id else get_record(db, tenant_id, "pipelines", previous, share=True)
        prior_outcome = next((s["outcome"] for s in old_pipeline.data["stages"] if s["key"] == before.get("stage")), None)
    outcome = stage["outcome"]
    data["outcome"] = outcome
    data["closed_at"] = (None if outcome == "open" else
                         before.get("closed_at") if before and prior_outcome == outcome else now().isoformat())
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


NOTICE_ORDER = {"critical": 3, "attention": 2, "info": 1}


def build_notifications(db, tenant_id, limit=25, allowed=None):
    """Derived at read time from the records themselves.

    A stored notification goes stale the moment someone resolves the thing it points at, and nobody
    reconciles it. Deriving means a closed task or a scheduled next action simply stops appearing.
    """
    from .compliance import instant
    allowed = {"tasks", "approvals", "deals"} if allowed is None else allowed
    moment = now()
    today = moment.date().isoformat()
    items = []
    for record in (db.scalars(scoped(tenant_id, "tasks")) if "tasks" in allowed else []):
        due = record.data.get("due_date")
        expired = bool(due and (due < today if len(due) == 10 else instant(due) and instant(due) < moment))
        if record.data.get("status") != "done" and expired:
            items.append({"kind": "task_overdue", "severity": "critical", "id": record.id,
                          "title": record.data.get("title", ""), "detail": f"Prazo venceu em {due}",
                          "href": f"/crm/tarefas?abrir={record.id}", "at": due})
    for record in (db.scalars(scoped(tenant_id, "approvals")) if "approvals" in allowed else []):
        expires = instant(record.data.get("expires_at"))
        if record.data.get("status") == "pending" and expires and expires > moment:
            items.append({"kind": "approval_pending", "severity": "attention", "id": record.id,
                          "title": record.data.get("title", ""),
                          "detail": f"Aguarda decisão no gate {record.data.get('gate', '')}".strip(),
                          "href": f"/crm/aprovacoes?abrir={record.id}",
                          "at": record.data.get("expires_at", "")})
    for pipeline in (db.scalars(scoped(tenant_id, "pipelines")) if "deals" in allowed else []):
        for entry in build_radar(db, tenant_id, pipeline)["items"]:
            bucket = entry["risk"]["bucket"]
            if bucket not in ("critico", "em_risco"):
                continue
            elapsed = entry["risk"]["elapsed_hours"]
            waited = "sem atividade registrada" if elapsed is None else f"parada há {round(elapsed / 24)} dias"
            items.append({"kind": "deal_at_risk", "severity": "critical" if bucket == "critico" else "attention",
                          "id": entry["id"], "title": entry["title"],
                          "detail": f"Etapa {entry['stage_label']}, {waited}",
                          "href": f"/crm/pipeline?abrir={entry['id']}",
                          "at": entry["last_activity_at"] or ""})
    items.sort(key=lambda item: (-NOTICE_ORDER[item["severity"]], item["at"] or ""))
    counts = {severity: sum(1 for item in items if item["severity"] == severity) for severity in NOTICE_ORDER}
    return {"items": items[:limit], "total": len(items), "counts": counts}


def regras_de_lead(db, tenant_id):
    """O conjunto ativo, ou None. Dois ativos seria ambiguo, entao o primeiro por criacao vence
    e a ambiguidade e resolvida na configuracao, nunca no calculo."""
    registro = next(iter(db.scalars(scoped(tenant_id, "lead_rules")
                                    .where(Record.data["status"].as_string() == "active")
                                    .order_by(Record.created_at).limit(1))), None)
    return registro.data if registro else None


def pontuar_contato(db, tenant_id, data, alterou_score, anterior=None):
    """Com regra ativa o score passa a ser do servidor; sem regra ativa continua sendo da pessoa.

    Sobrescrever em silencio um numero que alguem digitou seria a mentira que este sistema evita,
    entao a alteracao manual e recusada com motivo enquanto houver regra ativa.
    """
    regras = regras_de_lead(db, tenant_id)
    if regras is None:
        data.pop("score_breakdown", None)
        return data
    if alterou_score:
        raise HTTPException(409, {"message": "A pontuação é calculada pelas regras de qualificação ativas; "
                                             "edite as regras em vez do lead.",
                                  "rules_name": regras.get("name", "")})
    resultado = lead_scoring.avaliar(regras, data)
    data["score"] = resultado["score"]
    data["score_breakdown"] = resultado
    return data


def leads_por_responsavel(db, tenant_id, elegiveis):
    abertos = {usuario: 0 for usuario in elegiveis}
    for registro in db.scalars(scoped(tenant_id, "contacts")):
        dono = registro.data.get("owner_id")
        if dono in abertos and registro.data.get("lead_stage") in ("novo", "em_contato"):
            abertos[dono] += 1
    return abertos


def distribuir_lead(db, tenant_id, regras):
    """Menor carga, e nao ponteiro rotativo: um ponteiro guardado dessincroniza quando alguem sai
    da equipe ou um lead e reatribuido a mao, e a fila fica torta sem ninguem perceber.

    O desempate por id mantem a escolha reproduzivel: a mesma equipe com a mesma carga escolhe
    sempre a mesma pessoa, o que torna o comportamento testavel.
    """
    if not regras or regras.get("assignment", {}).get("strategy") != "menor_carga":
        return None
    papeis = set(regras["assignment"].get("roles") or [])
    elegiveis = [usuario.id for usuario in db.scalars(
        select(User).where(User.tenant_id == tenant_id, User.active.is_(True)))
        if usuario.role in papeis]
    if not elegiveis:
        return None
    carga = leads_por_responsavel(db, tenant_id, elegiveis)
    return min(elegiveis, key=lambda usuario: (carga[usuario], usuario))


def marcar_interacao(db, tenant_id, contact_id, *, por_pessoa):
    """Ultima interacao e primeira resposta sao do servidor: quem responde nao digita que respondeu."""
    registro = db.scalar(scoped(tenant_id, "contacts").where(Record.id == contact_id))
    if registro is None:
        return
    instante = now().isoformat()
    data = {**registro.data, "last_interaction_at": instante}
    if por_pessoa and not data.get("first_response_at"):
        data["first_response_at"] = instante
    # Sem tocar em version: registrar que houve contato nao e uma edicao que alguem precise resolver.
    db.execute(update(Record).where(Record.id == contact_id, Record.tenant_id == tenant_id)
               .values(data=data))


def create_record(db, tenant_id, actor_id, kind, payload):
    if kind == "pipelines":
        lock_pipeline_configuration(db, tenant_id)
    if kind == "contacts":
        lock_contacts(db, tenant_id)
    data = validate(kind, payload)
    if kind == "contacts":
        data = normalize_contact_identifiers(data)
        ensure_unique_contact(db, tenant_id, data)
        data = pontuar_contato(db, tenant_id, data, alterou_score=bool(payload.get("score")))
        if not data.get("owner_id"):
            data["owner_id"] = distribuir_lead(db, tenant_id, regras_de_lead(db, tenant_id))
    validate_relations(db, tenant_id, data)
    if kind == "automations":
        validate_flow(data)
    if kind == "deals":
        apply_deal_rules(db, tenant_id, data, "probability" in payload)
        if not data.get("position"):
            data["position"] = next_position(db, tenant_id, data["pipeline_id"], data["stage"])
    if kind == "approvals":
        data.update(requested_by=actor_id, expires_at=(now() + timedelta(hours=24)).isoformat())
    record = Record(tenant_id=tenant_id, kind=kind, data=data)
    db.add(record)
    db.flush()
    if kind == "pipelines" and data["is_default"]:
        promote_default_pipeline(db, tenant_id, record.id)
    details = {"version": 1}
    if kind == "deals":
        details.update(outcome=data["outcome"], closed_at=data["closed_at"])
    audit_event(db, tenant_id, actor_id, f"{kind}.created", record.id, details)
    return record


def open_stage_keys(db, tenant_id):
    return {record.id: {stage["key"] for stage in record.data["stages"] if stage["outcome"] == "open"}
            for record in db.scalars(scoped(tenant_id, "pipelines"))}


def next_position(db, tenant_id, pipeline_id, stage):
    """New cards land at the bottom of their column; gaps of 1000 leave room to drop between neighbours."""
    maximum = db.scalar(select(func.max(cast(Record.data["position"].as_string(), Integer))).where(
        Record.tenant_id == tenant_id, Record.kind == "deals", Record.deleted.is_(False),
        Record.data["pipeline_id"].as_string() == pipeline_id, Record.data["stage"].as_string() == stage)) or 0
    return min(maximum + 1000, 1_000_000_000)


def promote_lead(db, tenant_id, contact, interest):
    """WEB-03: a captured lead becomes a tracked opportunity and a next action, not just a row in contacts.

    A resubmission never opens a second opportunity; it attaches the follow-up to the one already running,
    so repeat form fills cannot inflate the pipeline the sales team reads.
    """
    pipeline = default_pipeline(db, tenant_id)
    if pipeline:
        pipeline = get_record(db, tenant_id, "pipelines", pipeline.id, share=True)
    stage = next((item for item in (pipeline.data["stages"] if pipeline else []) if item["outcome"] == "open"), None)
    opened = open_stage_keys(db, tenant_id)
    deal = next((record for record in db.scalars(scoped(tenant_id, "deals").where(
        Record.data["contact_id"].as_string() == contact.id))
        if record.data.get("stage") in opened.get(record.data.get("pipeline_id"), set())), None)
    if deal is None and stage and pipeline.data.get("status") == "active":
        candidate = {
            "title": f"{contact.data['name']} · {interest or 'Contato pelo site'}"[:200],
            "contact_id": contact.id, "pipeline_id": pipeline.id, "stage": stage["key"],
            "position": next_position(db, tenant_id, pipeline.id, stage["key"])}
        missing = [field for field in stage.get("required_fields", []) if not candidate.get(field)]
        if missing:
            # Capture remains durable while qualification awaits a person; never bypass stage requirements.
            audit_event(db, tenant_id, None, "contacts.qualification_pending", contact.id,
                        {"pipeline_id": pipeline.id, "required_fields": missing})
        else:
            deal = create_record(db, tenant_id, None, "deals", candidate)
    # One open next action per contact: ten form fills must not become ten identical reminders.
    pending = any(record.data.get("status") != "done" for record in db.scalars(
        scoped(tenant_id, "tasks").where(Record.data["contact_id"].as_string() == contact.id)))
    if not pending:
        create_record(db, tenant_id, None, "tasks", {
            "title": f"Responder {contact.data['name']}"[:200],
            "description": f"Lead recebido pelo site.\n{interest}".strip()[:20000],
            "priority": "high", "due_date": (now() + timedelta(days=1)).date().isoformat(),
            "contact_id": contact.id, "deal_id": deal.id if deal else None})
    return deal


def capture_lead(db, tenant_id, payload, attribution, promote=True):
    """Public resubmission enriches the existing contact instead of failing.

    A resend must not duplicate a contact. Conflicting identities require review rather than guessing
    which person submitted the form. First-touch attribution and consent decisions stay intact;
    an unauthenticated submission cannot undo a refusal or an opt-out.
    """
    lock_contacts(db, tenant_id)
    submitted_notes = payload.get("notes", "")
    payload = {**payload, "notes": submitted_notes[:20000]}
    identifiers = normalize_contact_identifiers(validate("contacts", payload))
    existing = find_contact_matches(db, tenant_id, identifiers)
    if len(existing) > 1:
        raise HTTPException(409, "Não foi possível processar o cadastro. Entre em contato com a equipe.")
    if not existing:
        record = create_record(db, tenant_id, None, "contacts", payload)
        record.data = {**record.data, "attribution": attribution, "consented_at": now().isoformat()}
        capture_activity(db, tenant_id, record.id, submitted_notes, attribution)
        if promote:
            promote_lead(db, tenant_id, record, payload.get("notes", ""))
        return record
    record = existing[0]
    entry = f"{now().date().isoformat()} · {payload['notes']}".strip()
    history = str(record.data.get("notes") or "").strip()
    merged = {**record.data,
              "notes": (f"{history}\n\n{entry}" if history else entry)[:20000]}
    merged.setdefault("attribution", attribution)
    if merged.get("consent") and not merged.get("opted_out_at"):
        merged.setdefault("consented_at", now().isoformat())
    db.execute(update(Record).where(Record.id == record.id, Record.tenant_id == tenant_id)
               .values(data=merged, version=record.version + 1, updated_at=now()))
    audit_event(db, tenant_id, None, "contacts.recaptured", record.id, {"version": record.version + 1})
    db.refresh(record)
    capture_activity(db, tenant_id, record.id, submitted_notes, attribution)
    if promote:
        promote_lead(db, tenant_id, record, payload.get("notes", ""))
    return record


def capture_activity(db, tenant_id, contact_id, body, attribution):
    """Keep each submission separately; the legacy notes field is only a bounded summary."""
    # O lead falando conosco e interacao, nao resposta: por_pessoa fica falso de proposito.
    marcar_interacao(db, tenant_id, contact_id, por_pessoa=False)
    activity = Record(tenant_id=tenant_id, kind="activities", data={"type": "note", "body": body,
        "contact_id": contact_id, "author_id": None, "author_name": "Site FAT Tech", "source": "website",
        "attribution": attribution})
    db.add(activity)
    db.flush()
    audit_event(db, tenant_id, None, "activities.created", activity.id,
                {"parent_kind": "contacts", "parent_id": contact_id, "source": "website"})


def update_record(db, principal, kind, record_id, payload):
    if kind == "pipelines":
        lock_pipeline_configuration(db, principal.tenant_id)
    if kind == "contacts":
        lock_contacts(db, principal.tenant_id)
    record = get_record(db, principal.tenant_id, kind, record_id, lock=True)
    if kind == "contacts":
        db.refresh(record)
    changes = dict(payload)
    version = changes.pop("version", None)
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise HTTPException(422, "version inteira obrigatória")
    if record.version != version:
        raise HTTPException(409, "O registro foi alterado por outra pessoa. Atualize e tente novamente.")
    if kind == "approvals":
        raise HTTPException(409, "Intenções são imutáveis; use a decisão ou crie nova solicitação")
    editable = {key: value for key, value in record.data.items() if key in RESOURCES[kind].model_fields}
    protected = {key: value for key, value in record.data.items() if key not in RESOURCES[kind].model_fields}
    data = {**validate(kind, {**editable, **changes}), **protected}
    if kind == "contacts":
        data = normalize_contact_identifiers(data)
        ensure_unique_contact(db, principal.tenant_id, data, record_id)
        data = pontuar_contato(db, principal.tenant_id, data,
                               alterou_score="score" in changes and changes["score"] != record.data.get("score"))
    validate_relations(db, principal.tenant_id, data)
    if kind == "automations":
        validate_flow(data)
    if kind == "deals":
        same_stage = data.get("pipeline_id") == record.data.get("pipeline_id") and data["stage"] == record.data["stage"]
        apply_deal_rules(db, principal.tenant_id, data, "probability" in changes or same_stage,
                         record.data.get("pipeline_id"), record.data.get("lost_reason"), before=record.data)
    if kind == "pipelines":
        guard_stage_removal(db, principal.tenant_id, record_id, record.data["stages"], data["stages"])
    details = {"version": version + 1, "fields": sorted(changes)}
    if kind == "deals":
        details.update(previous_outcome=record.data.get("outcome"), outcome=data["outcome"],
                       closed_at=data["closed_at"], previous_closed_at=record.data.get("closed_at"))
    result = db.execute(update(Record).where(Record.id == record_id, Record.tenant_id == principal.tenant_id,
                                           Record.version == version, Record.deleted.is_(False))
                        .values(data=data, version=version + 1, updated_at=now()))
    if result.rowcount != 1:
        raise HTTPException(409, "O registro foi alterado por outra pessoa. Atualize e tente novamente.")
    if kind == "pipelines" and data["is_default"]:
        promote_default_pipeline(db, principal.tenant_id, record_id)
    audit_event(db, principal.tenant_id, principal.actor_id, f"{kind}.updated", record_id, details)
    db.flush()
    db.refresh(record)
    return record


def delete_record(db, principal, kind, record_id, version):
    if kind == "pipelines":
        lock_pipeline_configuration(db, principal.tenant_id)
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
    # A board is read top to bottom, so its column order is the operator's priority, not the creation date.
    order = ((func.coalesce(cast(Record.data["position"].as_string(), Integer), 0), Record.created_at.desc())
             if kind == "deals" else (Record.created_at.desc(),))
    records = db.scalars(statement.order_by(*order).limit(filters["limit"]).offset(filters["offset"]))
    items = [serialize(record) for record in records]
    if kind == "deals":
        attach_related_names(db, tenant_id, items)
    return {"items": items, "total": total}


def attach_related_names(db, tenant_id, items):
    """One extra query for the page being returned, so the board shows who the deal is with."""
    ids = {item[field] for item in items for field in ("contact_id", "company_id") if item.get(field)}
    if not ids:
        return
    names = {record.id: record.data.get("name", "") for record in db.scalars(
        select(Record).where(Record.tenant_id == tenant_id, Record.id.in_(ids), Record.deleted.is_(False)))}
    for item in items:
        item["contact_name"] = names.get(item.get("contact_id"), "")
        item["company_name"] = names.get(item.get("company_id"), "")


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
