"""Bounded task queue: database filters, UTC deadlines and scoped relationship labels."""
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import DateTime, and_, case, cast, extract, func, or_, select

from .db import get_db
from .models import Record, User, now
from .record_views import readable
from .security import require_auth
from .services import scoped, serialize

router = APIRouter(prefix="/api/v1", tags=["work queue"])


@router.get("/work-queue")
def work_queue(principal=Depends(require_auth), db=Depends(get_db),
               q: str = Query("", max_length=200), owner_id: str = Query("", max_length=36),
               status: Literal["all", "open", "todo", "in_progress", "done"] = "open",
               priority: Literal["all", "low", "medium", "high", "urgent"] = "all",
               due: Literal["all", "overdue", "today", "upcoming", "undated"] = "all",
               limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0, le=10000)):
    principal.require("tasks:read")
    reference = now()
    midnight = reference.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = midnight + timedelta(days=1)
    statement = scoped(principal.tenant_id, "tasks")
    data = Record.data
    if q.strip():
        term = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        statement = statement.where(or_(*[data[key].as_string().ilike(f"%{term}%", escape="\\")
                                          for key in ("title", "description")]))
    if owner_id:
        owner = data["owner_id"].as_string()
        statement = statement.where(or_(owner.is_(None), owner == "") if owner_id == "unassigned"
                                    else owner == (principal.actor_id if owner_id == "me" else owner_id))
    if status != "all":
        statement = statement.where(data["status"].as_string().in_(["todo", "in_progress"])
                                    if status == "open" else data["status"].as_string() == status)
    if priority != "all":
        statement = statement.where(data["priority"].as_string() == priority)
    raw = func.nullif(data["due_date"].as_string(), "")
    # SQL epoch comparisons respect offsets; unzoned deadlines are interpreted as UTC.
    if db.bind.dialect.name == "postgresql":
        zoned = case((func.length(raw) == 10, raw + "T00:00:00Z"),
                     (raw.op("~")(r"(Z|[+-][0-9]{2}(:?[0-9]{2})?)$"), raw), else_=raw + "Z")
        moment = extract("epoch", cast(zoned, DateTime(timezone=True)))
    else:
        moment = (func.julianday(raw) - 2440587.5) * 86400.0
    day_only = func.length(raw) == 10
    expired = or_(and_(day_only, moment < midnight.timestamp()),
                  and_(~day_only, moment < reference.timestamp()))
    if due == "overdue":
        statement = statement.where(expired, data["status"].as_string() != "done")
    elif due == "today":
        statement = statement.where(moment >= midnight.timestamp(), moment < tomorrow.timestamp())
    elif due == "upcoming":
        statement = statement.where(moment >= tomorrow.timestamp())
    elif due == "undated":
        statement = statement.where(raw.is_(None))
    total = db.scalar(select(func.count()).select_from(statement.subquery()))
    rows = list(db.scalars(statement.order_by(moment.asc().nulls_last(), Record.id).limit(limit).offset(offset)))
    items = [serialize(record) for record in rows]
    for kind, field in (("contacts", "contact"), ("deals", "deal")):
        if readable(principal, kind):
            ids = {item.get(field + "_id") for item in items} - {None, ""}
            names = {record.id: record.data.get("name") or record.data.get("title", "")
                     for record in db.scalars(scoped(principal.tenant_id, kind).where(Record.id.in_(ids)))}
            for item in items:
                item[field + "_name"] = names.get(item.get(field + "_id"))
    if readable(principal, "team"):
        ids = {item.get("owner_id") for item in items} - {None, ""}
        names = dict(db.execute(select(User.id, User.name).where(User.tenant_id == principal.tenant_id,
                                                                User.id.in_(ids))).all())
        for item in items:
            item["owner_name"] = names.get(item.get("owner_id"))
    return {"items": items, "total": total, "limit": limit, "offset": offset,
            "reference_at": reference.isoformat(), "timezone": "UTC"}
