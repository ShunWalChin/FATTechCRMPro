"""Closing cohorts must not masquerade as creation cohorts or invent legacy dates."""
from datetime import datetime, timezone

from fattech.db import set_tenant
from fattech.models import Record
from test_api import post, system as system
from test_backend_refinement import refined as refined


def test_closed_report_uses_authoritative_outcome_utc_boundaries_and_discloses_legacy(refined):
    client, _, factory, tenant_id, _, owner_id, _ = refined
    contact = post(client, "contacts", {"name": "Origem fechamento", "source": "closing"})
    rows = []
    for title in ("Início", "Final", "Próximo dia", "Legado", "Aberta"):
        rows.append(post(client, "deals", {"title": title, "value_cents": 100_000_000_000,
            "owner_id": owner_id, "contact_id": contact["id"], "stage": "lead"}))
    with factory() as db:
        set_tenant(db, tenant_id)
        for index, deal in enumerate(rows):
            record = db.get(Record, deal["id"])
            record.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
            if index < 3:
                stamp = ["2026-09-01T00:00:00+00:00", "2026-09-01T23:59:59.999999+00:00",
                         "2026-09-02T00:00:00+00:00"][index]
                # A stored outcome remains authoritative even when stage configuration differs.
                record.data = {**record.data, "outcome": "won", "closed_at": stamp}
            elif index == 3:
                record.data = {key: value for key, value in record.data.items() if key not in {"outcome", "closed_at"}}
                record.data = {**record.data, "stage": "won"}
        db.commit()
    query = {"source": "closing", "owner_id": owner_id, "date_from": "2026-09-01", "date_to": "2026-09-01"}
    created = client.get("/api/v1/sales/report", params=query).json()
    assert created["deal_count"] == 0 and created["date_basis"] == "deal_created_at_utc"
    closed = client.get("/api/v1/sales/report", params={**query, "date_basis": "closed"})
    assert closed.status_code == 200, closed.text
    report = closed.json()
    assert report["date_basis"] == "deal_closed_at_utc"
    assert report["deal_count"] == report["won_count"] == 2
    assert report["won_cents"] == 200_000_000_000
    assert report["open_count"] == report["weighted_pipeline_cents"] == 0
    assert report["excluded_missing_closed_at"] == 1
    assert client.get("/api/v1/sales/report", params={**query, "date_basis": "closed", "source": "other"}).json()["excluded_missing_closed_at"] == 0
    assert client.get("/api/v1/sales/report", params={"date_basis": "expected"}).status_code == 422


def test_real_close_reopen_and_legacy_edit_do_not_fabricate_history(refined):
    client, _, factory, tenant_id, *_ = refined
    deal = post(client, "deals", {"title": "Ciclo comercial", "value_cents": 101})
    assert deal["outcome"] == "open" and deal.get("closed_at") is None
    path = "/api/v1/deals/" + deal["id"]
    closed = client.patch(path, json={"version": 1, "stage": "won"}).json()
    assert closed["outcome"] == "won" and closed["closed_at"]
    edited = client.patch(path, json={"version": 2, "notes": "Anotação após fechamento"}).json()
    assert edited["closed_at"] == closed["closed_at"]
    reopened = client.patch(path, json={"version": 3, "stage": "lead"}).json()
    assert reopened["outcome"] == "open" and reopened.get("closed_at") is None
    assert client.get("/api/v1/sales/report", params={"date_basis": "closed"}).json()["deal_count"] == 0
    legacy = post(client, "deals", {"title": "Histórico anterior", "stage": "won"})
    with factory() as db:
        set_tenant(db, tenant_id)
        record = db.get(Record, legacy["id"])
        record.data = {key: value for key, value in record.data.items() if key not in {"outcome", "closed_at"}}
        db.commit()
    edited = client.patch("/api/v1/deals/" + legacy["id"], json={"version": 1, "notes": "Revisado"}).json()
    assert edited["outcome"] == "won" and edited.get("closed_at") is None
    assert client.get("/api/v1/sales/report", params={"date_basis": "closed"}).json()["excluded_missing_closed_at"] == 1
