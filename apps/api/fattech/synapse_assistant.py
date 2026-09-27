"""Tenant-scoped, extractive copilot. Sources are data, never executable instructions.

The lexical provider quotes reviewed CRM documents. Optional generation is a separate,
human-reviewed draft; neither path sends a message or mutates a commercial stage.
"""
import hashlib
import re
import unicodedata
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import Field

from .db import get_db
from .ai_provider import GenerationFailed, generate_grounded
from .idempotency import creation_receipt
from .models import Record, now
from .schemas import Identifier, StrictModel
from .security import rate_limit, require_auth
from .services import audit_event, create_record, get_record, lock_contacts, scoped
from .synapse import CONFIG_KIND

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


def prepare_assistance(db, tenant_id, conversation_id, question="", *, actor_id=None,
                       source_batch_id=None, requested_by=None):
    """Prepare a grounded draft or a human handoff without contacting a provider.

    This is deliberately usable by both the authenticated copilot endpoint and the internal
    messaging worker.  The source batch is an idempotency boundary: a replayed worker event can
    never create a second draft or a second follow-up task for the same inbound batch.
    """
    configuration = db.scalar(scoped(tenant_id, CONFIG_KIND))
    if configuration is None or not configuration.data.get("enabled"):
        return None
    conversation = get_record(db, tenant_id, "conversations", conversation_id, lock=True)
    if conversation.data.get("status") == "closed":
        return None
    if source_batch_id:
        previous = db.scalar(scoped(tenant_id, "synapse_assists").where(
            Record.data["source_batch_id"].as_string() == source_batch_id).limit(1))
        if previous is not None:
            return {"id": previous.id, **previous.data}
    contact_id = conversation.data.get("contact_id")
    contact = get_record(db, tenant_id, "contacts", contact_id) if contact_id else None
    incoming = db.scalar(scoped(tenant_id, "messages").where(
        Record.data["conversation_id"].as_string() == conversation.id,
        Record.data["direction"].as_string() == "inbound").order_by(
            Record.created_at.desc(), Record.id).limit(1))
    question = question.strip() or (str(incoming.data.get("body") or "")[:500] if incoming else "")
    reason = None
    if contact and contact.data.get("opted_out_at"):
        reason = "opted_out"
    elif len(question) < 2:
        reason = "missing_question"
    citations = retrieve(db, tenant_id, question) if reason is None else []
    if not citations and reason is None:
        reason = "no_evidence"
    status = "draft" if citations else "handoff"
    body = "\n\n".join(f"{item['title']}:\n{item['excerpt']}" for item in citations)
    task_id = None
    if status == "handoff" and reason != "opted_out":
        task = db.scalar(scoped(tenant_id, "tasks").where(
            Record.data["synapse_conversation_id"].as_string() == conversation.id,
            Record.data["status"].as_string() != "done").limit(1))
        if task is None:
            task = create_record(db, tenant_id, actor_id, "tasks", {
                "title": f"Revisar atendimento · {conversation.data['title']}"[:200],
                "description": "SYNAPSE precisa de orientação humana. Consulte a conversa e revise a base de conhecimento.",
                "priority": "high", "contact_id": contact_id,
                "owner_id": actor_id or configuration.data.get("owner_id"),
                "due_date": (now() + timedelta(hours=configuration.data.get("sla_hours", 24))).isoformat()},
                role="system")
            task.data = {**task.data, "synapse_conversation_id": conversation.id}
        task_id = task.id
        conversation.data = {**conversation.data, "status": "pending"}
        conversation.version += 1
        conversation.updated_at = now()
    result = {"conversation_id": conversation.id, "status": status, "body": body,
              "citations": citations, "provider": "lexical", "sent": False,
              "reason": reason, "task_id": task_id, "question": question,
              "requested_by": requested_by or actor_id or "core-engine"}
    if source_batch_id:
        result.update({"source_batch_id": source_batch_id, "trigger": "message_batch"})
    run = Record(tenant_id=tenant_id, kind="synapse_assists", data=result)
    db.add(run)
    db.flush()
    result = {"id": run.id, **result}
    audit_event(db, tenant_id, actor_id, "synapse.auto_assisted" if source_batch_id else "synapse.assisted",
                run.id, {"conversation_id": conversation.id, "status": status, "reason": reason,
                         "task_id": task_id, "source_ids": [item["id"] for item in citations],
                         "source_batch_id": source_batch_id, "sent": False})
    return result


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
    configuration = db.scalar(scoped(principal.tenant_id, CONFIG_KIND))
    if configuration is None or not configuration.data.get("enabled"):
        raise HTTPException(409, "Ative o SYNAPSE antes de consultar a base.")
    result = prepare_assistance(db, principal.tenant_id, payload.conversation_id, payload.question,
                                actor_id=principal.actor_id, requested_by=principal.actor_id)
    if result is None:
        raise HTTPException(409, "A conversa não está disponível para o SYNAPSE.")
    if receipt:
        receipt.response = result
    db.commit()
    return result


def _current_sources(db, tenant_id, citations):
    """A citation is valid only while the exact tenant document and version still exist."""
    if not citations or len(citations) > 3:
        return False
    for source in citations:
        record = db.scalar(scoped(tenant_id, "knowledge").where(Record.id == source.get("id")))
        if (record is None or record.version != source.get("version") or
                hashlib.sha256(str(record.data.get("content") or "").encode()).hexdigest()
                != source.get("content_hash")):
            return False
    return True


def _generation_allowed(db, tenant_id, run):
    config = db.scalar(scoped(tenant_id, CONFIG_KIND))
    if not config or not config.data.get("enabled") or not config.data.get("ai_enabled"):
        raise HTTPException(409, "O copiloto generativo não está habilitado nesta organização.")
    conversation = get_record(db, tenant_id, "conversations", run.data["conversation_id"])
    if conversation.data.get("status") == "closed":
        raise HTTPException(409, "A conversa foi encerrada; prepare um novo atendimento.")
    if conversation.data.get("contact_id"):
        contact = get_record(db, tenant_id, "contacts", conversation.data["contact_id"])
        if contact.data.get("opted_out_at"):
            raise HTTPException(409, "O contato pediu para não receber mensagens.")
    if not _current_sources(db, tenant_id, run.data.get("citations") or []):
        raise HTTPException(409, "Uma fonte mudou ou foi removida; consulte a base novamente.")


@router.post("/assists/{assist_id}/generate")
def generate_assist(assist_id: Identifier, request: Request, principal=Depends(require_auth), db=Depends(get_db)):
    """Manual model draft, with a durable claim and no database transaction during inference."""
    for scope in ("agents:write", "knowledge:read", "conversations:read", "contacts:read"):
        principal.require(scope)
    settings = request.app.state.settings
    if not settings.ai_provider_ready:
        raise HTTPException(503, "Nenhum provedor de IA está configurado no servidor.")
    rate_limit(db, f"synapse-ai-user:{principal.tenant_id}:{principal.actor_id}", 10, 60)
    rate_limit(db, f"synapse-ai-tenant:{principal.tenant_id}", 100, 86_400)
    run = get_record(db, principal.tenant_id, "synapse_assists", assist_id, lock=True)
    if run.data.get("provider") == "openai-compatible" and run.data.get("generation_state") == "complete":
        _generation_allowed(db, principal.tenant_id, run)
        return {"id": run.id, **run.data}
    if run.data.get("status") != "draft" or run.data.get("sent"):
        raise HTTPException(409, "Só um rascunho não enviado pode ser aprimorado com IA.")
    _generation_allowed(db, principal.tenant_id, run)
    started = run.data.get("generation_started_at")
    if run.data.get("generation_state") == "running" and started:
        try:
            if now() - datetime.fromisoformat(started) < timedelta(seconds=90):
                raise HTTPException(409, "A geração já está em andamento.")
        except (TypeError, ValueError):
            pass
    claim = str(uuid4())
    question, citations = run.data["question"], run.data["citations"]
    run.data = {**run.data, "generation_state": "running", "generation_token": claim,
                "generation_started_at": now().isoformat()}
    run.version += 1
    run.updated_at = now()
    db.commit()  # No open transaction, row lock, or database connection during the model call.

    try:
        generated = generate_grounded(question, citations, settings)
    except GenerationFailed as exc:
        db.rollback()
        current = get_record(db, principal.tenant_id, "synapse_assists", assist_id, lock=True)
        if current.data.get("generation_token") == claim:
            current.data = {**current.data, "generation_state": "failed", "generation_error": str(exc)}
            current.version += 1
            current.updated_at = now()
            db.commit()
        raise HTTPException(502, "O modelo não produziu um rascunho fundamentado. A resposta da base foi preservada.") from exc

    current = get_record(db, principal.tenant_id, "synapse_assists", assist_id, lock=True)
    if current.data.get("generation_token") != claim:
        raise HTTPException(409, "Outra geração assumiu este rascunho.")
    try:
        _generation_allowed(db, principal.tenant_id, current)
    except HTTPException:
        current.data = {**current.data, "generation_state": "stale"}
        current.version += 1
        current.updated_at = now()
        db.commit()
        raise
    current.data = {**current.data, "lexical_body": current.data["body"],
                    "body": generated["body"], "provider": "openai-compatible",
                    "model": generated["model"], "usage": generated["usage"],
                    "generation_state": "complete", "generated_at": now().isoformat(),
                    "generated_by": principal.actor_id, "sent": False}
    current.data.pop("generation_token", None)
    current.version += 1
    current.updated_at = now()
    audit_event(db, principal.tenant_id, principal.actor_id, "synapse.ai_generated", current.id,
                {"conversation_id": current.data["conversation_id"], "model": generated["model"],
                 "source_ids": [source["id"] for source in citations], "sent": False,
                 "usage": generated["usage"]})
    db.commit()
    return {"id": current.id, **current.data}
