from datetime import timedelta

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from .models import Audit, Outbox, Record, User, now, uid
from .schemas import RESOURCES

RELATIONS = {"contact_id": "contacts", "company_id": "companies", "deal_id": "deals",
             "project_id": "projects", "conversation_id": "conversations"}
PRIVILEGED = {"agents", "approvals", "automations", "invoices"}


def scoped(tenant_id: str, kind: str):
    return select(Record).where(Record.tenant_id == tenant_id, Record.kind == kind, Record.deleted.is_(False))


def get_record(db: Session, tenant_id: str, kind: str, record_id: str, *, lock=False):
    statement = scoped(tenant_id, kind).where(Record.id == record_id)
    record = db.scalar(statement.with_for_update() if lock else statement)
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


def create_record(db, tenant_id, actor_id, kind, payload):
    data = validate(kind, payload)
    validate_relations(db, tenant_id, data)
    if kind == "automations":
        validate_flow(data)
    if kind == "approvals":
        data.update(requested_by=actor_id, expires_at=(now() + timedelta(hours=24)).isoformat())
    record = Record(tenant_id=tenant_id, kind=kind, data=data)
    db.add(record)
    db.flush()
    audit_event(db, tenant_id, actor_id, f"{kind}.created", record.id, {"version": 1})
    return record


def update_record(db, principal, kind, record_id, payload):
    record = get_record(db, principal.tenant_id, kind, record_id, lock=True)
    changes = dict(payload)
    version = changes.pop("version", None)
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise HTTPException(422, "version inteira obrigatória")
    if kind == "approvals":
        raise HTTPException(409, "Intenções são imutáveis; use a decisão ou crie nova solicitação")
    editable = {key: value for key, value in record.data.items() if key in RESOURCES[kind].model_fields}
    protected = {key: value for key, value in record.data.items() if key not in RESOURCES[kind].model_fields}
    data = {**validate(kind, {**editable, **changes}), **protected}
    validate_relations(db, principal.tenant_id, data)
    if kind == "automations":
        validate_flow(data)
    result = db.execute(update(Record).where(Record.id == record_id, Record.tenant_id == principal.tenant_id,
                                           Record.version == version, Record.deleted.is_(False))
                        .values(data=data, version=version + 1, updated_at=now()))
    if result.rowcount != 1:
        raise HTTPException(409, "O registro foi alterado por outra pessoa. Atualize e tente novamente.")
    audit_event(db, principal.tenant_id, principal.actor_id, f"{kind}.updated", record_id,
                {"version": version + 1, "fields": sorted(changes)})
    db.flush()
    db.refresh(record)
    return record


def delete_record(db, principal, kind, record_id, version):
    get_record(db, principal.tenant_id, kind, record_id, lock=True)
    # Prevent dangling relationships rather than silently hiding parent records.
    for field, related_kind in RELATIONS.items():
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
    for field in ("status", "stage", "contact_id", "conversation_id", "project_id", "owner_id"):
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
