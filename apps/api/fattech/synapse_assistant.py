"""Tenant-scoped, extractive copilot. Sources are data, never executable instructions.

This first provider quotes reviewed CRM documents; it does not claim to run an LLM.
No send, payment, provider request or commercial stage mutation occurs here.
"""
import hashlib
import re
import unicodedata
from datetime import timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import Field

from .db import get_db
from .idempotency import creation_receipt
from .models import Record, now
from .schemas import Identifier, StrictModel
from .security import rate_limit, require_auth
from .services import audit_event, create_record, get_record, lock_contacts, scoped

router = APIRouter(prefix="/api/v1/synapse", tags=["SYNAPSE"])
STOP_WORDS = frozenset("a o as os de da do das dos em no na nos nas e ou um uma com para por que qual quais como quanto quando sobre meu minha seu sua voce voces gostaria saber preciso quero tem pode poderia".split())


def normalized(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(c))


def terms_of(value):
    return {term for term in re.findall(r"[a-z0-9]+", normalized(value))
            if len(term) > 2 and term not in STOP_WORDS}


def retrieve(db, tenant_id, question):
    """Read current active sources, so stale indexes/deleted documents cannot be cited.

    A bounded corpus prevents a request loading an unbounded knowledge base. Ranking
    is deliberately lexical and explainable; semantic retrieval remains a separate adapter.
    """
    terms = terms_of(question)
    if not terms:
        return []
    ranked = []
    for record in db.scalars(scoped(tenant_id, "knowledge").order_by(
            Record.updated_at.desc(), Record.id).limit(200)):
        title = str(record.data.get("title") or "Documento")
        content = str(record.data.get("content") or "").strip()
        if not content:
            continue
        words = terms_of(title + " " + content)
        matched = terms & words
        # A single incidental word must not produce a confident answer to a complex question.
        if not matched or len(matched) / len(terms) < 0.5:
            continue
        paragraphs = [p.strip() for p in content.splitlines() if p.strip()]
        paragraph = max(paragraphs, key=lambda p: len(terms & terms_of(p)))
        ranked.append({"id": record.id, "title": title, "version": record.version,
                       "excerpt": paragraph[:1200],
                       "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                       "matched_terms": sorted(matched), "score": len(matched)})
    return sorted(ranked, key=lambda x: (-x["score"], x["id"]))[:3]


class AssistInput(StrictModel):
    conversation_id: Identifier
    question: str = Field(default="", max_length=500)


@router.post("/assist")
def assist(payload: AssistInput, principal=Depends(require_auth), db=Depends(get_db),
           idempotency_key: str | None = Header(default=None)):
    for scope in ("agents:write", "knowledge:read", "conversations:read", "conversations:write",
                  "messages:read", "contacts:read", "tasks:write"):
        principal.require(scope)
    # Count rejected requests too. This commit must precede receipt/business locks.
    rate_limit(db, f"synapse-assist:{principal.tenant_id}:{principal.actor_id}", 30, 60)
    lock_contacts(db, principal.tenant_id)
    receipt = None
    if idempotency_key:
        receipt, replay = creation_receipt(db, principal, "synapse_assist", idempotency_key,
                                           payload.model_dump())
        if replay:
            return receipt.response
    configuration = db.scalar(scoped(principal.tenant_id, "synapse_config"))
    if configuration is None or not configuration.data.get("enabled"):
        raise HTTPException(409, "Ative o SYNAPSE antes de consultar a base.")
    conversation = get_record(db, principal.tenant_id, "conversations", payload.conversation_id, lock=True)
    if conversation.data.get("status") == "closed":
        raise HTTPException(409, "Reabra a conversa antes de preparar o atendimento.")
    contact_id = conversation.data.get("contact_id")
    contact = get_record(db, principal.tenant_id, "contacts", contact_id) if contact_id else None
    incoming = db.scalar(scoped(principal.tenant_id, "messages").where(
        Record.data["conversation_id"].as_string() == conversation.id,
        Record.data["direction"].as_string() == "inbound").order_by(Record.created_at.desc(), Record.id).limit(1))
    question = payload.question.strip() or (str(incoming.data.get("body") or "")[:500] if incoming else "")
    reason = None
    if contact and contact.data.get("opted_out_at"):
        reason = "opted_out"
    elif len(question) < 2:
        reason = "missing_question"
    citations = retrieve(db, principal.tenant_id, question) if reason is None else []
    if not citations and reason is None:
        reason = "no_evidence"
    status = "draft" if citations else "handoff"
    body = "\n\n".join(f"{item['title']}:\n{item['excerpt']}" for item in citations)
    task_id = None
    if status == "handoff" and reason != "opted_out":
        # Row lock on conversation serializes concurrent requests even with different receipt keys.
        task = db.scalar(scoped(principal.tenant_id, "tasks").where(
            Record.data["synapse_conversation_id"].as_string() == conversation.id,
            Record.data["status"].as_string() != "done").limit(1))
        if task is None:
            task = create_record(db, principal.tenant_id, principal.actor_id, "tasks", {
                "title": f"Revisar atendimento · {conversation.data['title']}"[:200],
                "description": "SYNAPSE precisa de orientação humana. Consulte a conversa e revise a base de conhecimento.",
                "priority": "high", "contact_id": contact_id, "owner_id": principal.actor_id,
                "due_date": (now() + timedelta(hours=configuration.data.get("sla_hours", 24))).isoformat()},
                role=principal.role)
            task.data = {**task.data, "synapse_conversation_id": conversation.id}
        task_id = task.id
        conversation.data = {**conversation.data, "status": "pending"}
        conversation.version += 1
        conversation.updated_at = now()
    result = {"conversation_id": conversation.id, "status": status, "body": body,
              "citations": citations, "provider": "lexical", "sent": False,
              "reason": reason, "task_id": task_id,
              "question": question, "requested_by": principal.actor_id}
    run = Record(tenant_id=principal.tenant_id, kind="synapse_assists", data=result)
    db.add(run)
    db.flush()
    result = {"id": run.id, **result}
    audit_event(db, principal.tenant_id, principal.actor_id, "synapse.assisted", run.id,
                {"conversation_id": conversation.id, "status": status, "reason": reason,
                 "task_id": task_id, "source_ids": [item["id"] for item in citations], "sent": False})
    if receipt:
        receipt.response = result
    db.commit()
    return result
