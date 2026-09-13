"""Previewable, atomic contact batches. CSV columns never grant consent or ownership."""
from fastapi import Depends, Header, HTTPException, Response

from .db import get_db
from .idempotency import creation_receipt
from .models import Record
from .schemas import ContactImport
from .security import require_auth
from .services import audit_event, lock_contacts, normalize_contact_identifiers, scoped, validate

FIELDS = frozenset(("name", "email", "phone", "company", "source", "notes"))


def import_contacts(db, tenant_id, actor_id, rows, commit):
    lock_contacts(db, tenant_id)
    index = {}
    for record in db.scalars(scoped(tenant_id, "contacts")):
        try:
            identifiers = normalize_contact_identifiers(record.data)
        except HTTPException:
            identifiers = normalize_contact_identifiers({**record.data, "phone": ""})
        for field in ("email", "phone"):
            if identifiers.get(field):
                index.setdefault((field, identifiers[field]), (record.id, record.data.get("name", "")))
    report = {"total": len(rows), "ready": 0, "created": 0, "invalid": [], "duplicates": [], "committed": False}
    ready = []
    for line, row in enumerate(rows, start=1):
        try:
            if set(row) - FIELDS:
                raise HTTPException(422, "Colunas não permitidas: " + ", ".join(sorted(set(row) - FIELDS)))
            data = normalize_contact_identifiers(validate("contacts", {**row, "source": row.get("source") or "import",
                                                       "owner_id": actor_id, "consent": False}))
            keys = [(field, data[field]) for field in ("email", "phone") if data.get(field)]
            if not keys:
                raise HTTPException(422, "Informe e-mail ou telefone para evitar duplicatas")
        except HTTPException as exc:
            report["invalid"].append({"line": line, "errors": exc.detail})
            continue
        clash = next((index[key] for key in keys if key in index), None)
        if clash is not None:
            report["duplicates"].append({"line": line, "contact_id": clash[0], "contact_name": clash[1],
                                         "reason": "Identificador já cadastrado" if clash[0] else "Linha repetida no arquivo"})
            continue
        ready.append((line, data))
        for key in keys:
            index[key] = ("", data["name"])
    report["ready"] = len(ready)
    if commit and report["invalid"]:
        raise HTTPException(422, {"message": "Corrija as linhas inválidas. Nenhum contato foi importado.", "report": report})
    if commit:
        for line, data in ready:
            record = Record(tenant_id=tenant_id, kind="contacts", data=data)
            db.add(record)
            db.flush()
            audit_event(db, tenant_id, actor_id, "contacts.imported", record.id, {"line": line})
        report.update(created=len(ready), committed=True)
    return report


def contact_import(payload: ContactImport, response: Response,
                   idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
                   principal=Depends(require_auth), db=Depends(get_db)):
    principal.require("contacts:write")
    principal.require("contacts:read")  # Duplicate reports disclose the existing contact's identity.
    receipt = None
    if payload.commit:
        if idempotency_key is None:
            raise HTTPException(422, "Idempotency-Key obrigatória para confirmar a importação")
        receipt, replayed = creation_receipt(db, principal, "contact_import", idempotency_key, {"rows": payload.rows})
        response.headers["Idempotency-Replayed"] = str(replayed).lower()
        if replayed:
            report = receipt.response
            db.commit()
            return report
    report = import_contacts(db, principal.tenant_id, principal.actor_id, payload.rows, payload.commit)
    if receipt is not None:
        receipt.response = report
        db.commit()
    else:
        db.rollback()
    return report
