from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from fattech.models import Audit, Record, User
from test_access import signed_in
from test_api import PASSWORD, post, system as system


@pytest.fixture
def sales_system(system):
    _, app, *_ = system
    # The application must expose these routes itself; mounting them here would hide an unmounted router.
    assert any(route.path == "/api/v1/sales/proposals" for route in app.routes), "router de vendas não montado"
    return system


def proposal_input(client, **overrides):
    deal = post(client, "deals", {"title": "Oportunidade de proposta", "value_cents": 1000})
    product = post(client, "products", {"name": "Consultoria", "sku": "CONS", "price_cents": 333})
    return {"title": "Proposta comercial", "deal_id": deal["id"],
            "items": [{"product_id": product["id"], "quantity": 3}], **overrides}, product


def test_proposal_prices_are_server_snapshots_and_acceptance_is_immutable(sales_system):
    client, _, factory, _, _, _, _ = sales_system
    payload, product = proposal_input(client, discount_cents=99)
    proposal = post(client, "sales/proposals", payload)
    assert proposal["subtotal_cents"] == 999 and proposal["total_cents"] == 900
    assert proposal["status"] == "draft" and proposal["currency"] == "BRL"
    assert proposal["items"] == [{"product_id": product["id"], "name": "Consultoria", "sku": "CONS",
                                  "quantity": 3, "unit_price_cents": 333, "line_total_cents": 999}]
    assert client.patch("/api/v1/products/" + product["id"], json={"version": 1, "price_cents": 777}).status_code == 200
    url = "/api/v1/sales/proposals/" + proposal["id"]
    assert client.get(url).json()["items"][0]["unit_price_cents"] == 333
    assert client.patch(url, json={"version": 1, "status": "accepted"}).status_code == 409
    issued = client.patch(url, json={"version": 1, "status": "issued"})
    assert issued.status_code == 200 and "issued_at" in issued.json()
    assert client.patch(url, json={"version": 1, "status": "accepted"}).status_code == 409
    accepted = client.patch(url, json={"version": 2, "status": "accepted"})
    assert accepted.status_code == 200 and accepted.json()["total_cents"] == 900
    for status in ("draft", "issued", "rejected", "accepted"):
        assert client.patch(url, json={"version": 3, "status": status}).status_code == 409
    assert client.patch(url, json={"version": 3, "status": "accepted", "items": []}).status_code == 422
    assert client.get("/api/v1/deals/" + payload["deal_id"]).json()["stage"] == "lead"
    assert client.get("/api/v1/sales/proposals", params={"status": "accepted"}).json()["total"] == 1
    assert client.delete(f"/api/v1/deals/{payload['deal_id']}?version=1").status_code == 409
    audit = client.get("/api/v1/audit").json()["items"]
    decision = next(event for event in audit if event["action"] == "sales_proposals.accepted")
    assert decision["label"] == "Registrou o aceite da proposta"
    assert decision["resource_name"] == payload["title"]
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Audit).where(Audit.action == "sales_proposals.accepted")) == 1


@pytest.mark.parametrize("change", [
    {"discount_cents": -1}, {"discount_cents": 1000}, {"discount_cents": 1.5},
    {"discount_cents": True}, {"total_cents": 1}, {"status": "accepted"},
])
def test_proposal_rejects_forged_or_invalid_money(sales_system, change):
    client, _, factory, _, _, _, _ = sales_system
    payload, _ = proposal_input(client)
    response = client.post("/api/v1/sales/proposals", json={**payload, **change})
    assert response.status_code == 422, response.text
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Record).where(Record.kind == "sales_proposals")) == 0


@pytest.mark.parametrize("quantity", [0, -1, 1.5, True, "3", 10001])
def test_proposal_quantity_is_a_bounded_positive_integer(sales_system, quantity):
    client, *_ = sales_system
    payload, product = proposal_input(client)
    payload["items"] = [{"product_id": product["id"], "quantity": quantity}]
    assert client.post("/api/v1/sales/proposals", json=payload).status_code == 422


def test_proposal_catalog_guards_duplicates_overflow_and_inactive_items(sales_system):
    client, *_ = sales_system
    payload, product = proposal_input(client)
    assert client.post("/api/v1/sales/proposals", json={**payload, "items": payload["items"] * 2}).status_code == 422
    client.patch("/api/v1/products/" + product["id"], json={"version": 1, "price_cents": 100_000_000_000})
    assert client.post("/api/v1/sales/proposals", json=payload).status_code == 422
    client.patch("/api/v1/products/" + product["id"], json={"version": 2, "price_cents": 100, "status": "inactive"})
    assert client.post("/api/v1/sales/proposals", json=payload).status_code == 409


def test_proposal_tenant_relations_and_replay_are_protected(sales_system):
    client, app, factory, _, _, _, _ = sales_system
    payload, product = proposal_input(client)
    headers = {"Idempotency-Key": "proposal-retry-001"}
    first = client.post("/api/v1/sales/proposals", json=payload, headers=headers)
    assert first.status_code == 201
    client.patch("/api/v1/products/" + product["id"], json={"version": 1, "price_cents": 100})
    replay = client.post("/api/v1/sales/proposals", json=payload, headers=headers)
    assert replay.json() == first.json() and replay.headers["Idempotency-Replayed"] == "true"
    assert client.post("/api/v1/sales/proposals", json={**payload, "discount_cents": 1}, headers=headers).status_code == 409
    with signed_in(app, "other@example.com") as other:
        assert other.get("/api/v1/sales/proposals").json()["total"] == 0
        assert other.get("/api/v1/sales/proposals/" + first.json()["id"]).status_code == 404
        assert other.patch("/api/v1/sales/proposals/" + first.json()["id"], json={"version": 1, "status": "issued"}).status_code == 404
        assert other.post("/api/v1/sales/proposals", json=payload).status_code == 404
        own_deal = post(other, "deals", {"title": "Outro tenant"})
        assert other.post("/api/v1/sales/proposals", json={**payload, "deal_id": own_deal["id"]}).status_code == 404
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Record).where(Record.kind == "sales_proposals")) == 1


def test_goals_are_unique_versioned_admin_managed_and_personally_visible(sales_system):
    client, app, factory, _, _, owner_id, foreign_owner = sales_system
    member = post(client, "team", {"name": "Vendedor", "email": "seller@example.com", "password": PASSWORD, "role": "member"})
    payload = {"owner_id": member["id"], "period": "2026-09", "target_cents": 10000}
    goal = post(client, "sales/goals", payload)
    owner_goal = post(client, "sales/goals", {**payload, "owner_id": owner_id})
    assert client.post("/api/v1/sales/goals", json=payload).status_code == 409
    assert client.post("/api/v1/sales/goals", json={**payload, "owner_id": foreign_owner}).status_code == 404
    assert client.post("/api/v1/sales/goals", json={**payload, "period": "2026-13"}).status_code == 422
    url = "/api/v1/sales/goals/" + goal["id"]
    assert client.patch(url, json={"version": 1, "target_cents": 20000}).status_code == 200
    assert client.patch(url, json={"version": 1, "target_cents": 30000}).status_code == 409
    assert client.patch(url, json={"version": 2, "target_cents": 30000, "owner_id": owner_id}).status_code == 422
    with signed_in(app, member["email"]) as seller:
        assert seller.get("/api/v1/sales/goals").json()["items"][0]["id"] == goal["id"]
        assert seller.get("/api/v1/sales/goals").json()["total"] == 1
        assert seller.get("/api/v1/sales/goals", params={"owner_id": owner_id}).status_code == 403
        assert seller.post("/api/v1/sales/goals", json={**payload, "period": "2026-10"}).status_code == 403
        assert seller.patch(url, json={"version": 2, "target_cents": 1}).status_code == 403
    with signed_in(app, "other@example.com") as other:
        assert other.get("/api/v1/sales/goals").json()["total"] == 0
        assert other.patch("/api/v1/sales/goals/" + owner_goal["id"], json={"version": 1, "target_cents": 1}).status_code == 404
    with factory() as db:
        db.get(User, member["id"]).active = False
        db.commit()
    assert client.post("/api/v1/sales/goals", json={**payload, "period": "2026-10"}).status_code == 404


def test_report_filters_cohort_owner_source_and_isolates_tenants(sales_system):
    client, app, factory, _, _, owner_id, _ = sales_system
    member = post(client, "team", {"name": "Vendedor", "email": "reporter@example.com", "password": PASSWORD, "role": "member"})
    contact = post(client, "contacts", {"name": "Origem site", "source": "website"})
    deals = []
    for value, stage, reason in [(101, "qualified", ""), (101, "qualified", ""), (500, "won", ""), (99, "lost", "Preço")]:
        deals.append(post(client, "deals", {"title": "Coorte", "value_cents": value, "stage": stage,
                     "lost_reason": reason, "owner_id": member["id"], "contact_id": contact["id"]}))
    outside_date = post(client, "deals", {"title": "Fora do período", "value_cents": 700, "stage": "won", "owner_id": member["id"]})
    post(client, "deals", {"title": "Outro vendedor", "value_cents": 800, "stage": "won", "owner_id": owner_id})
    post(client, "sales/goals", {"owner_id": member["id"], "period": "2026-09", "target_cents": 1000})
    with factory() as db:
        for deal in deals:
            db.get(Record, deal["id"]).created_at = datetime(2026, 9, 1, tzinfo=timezone.utc)
        db.get(Record, outside_date["id"]).created_at = datetime(2026, 8, 31, tzinfo=timezone.utc)
        db.commit()
    query = {"owner_id": member["id"], "source": "website", "date_from": "2026-09-01", "date_to": "2026-09-01", "period": "2026-09"}
    report = client.get("/api/v1/sales/report", params=query).json()
    assert report["deal_count"] == 4 and report["open_count"] == 2
    assert report["pipeline_cents"] == 202 and report["weighted_pipeline_cents"] == 61
    assert report["won_cents"] == 500 and report["won_count"] == 1 and report["lost_count"] == 1
    assert report["lost_reasons"] == {"Preço": 1} and report["goals"][0]["target_cents"] == 1000
    assert report["date_basis"] == "deal_created_at_utc"
    assert client.get("/api/v1/sales/report", params={**query, "source": "ads"}).json()["deal_count"] == 0
    assert client.get("/api/v1/sales/report", params={"date_from": "2026-10-01", "date_to": "2026-09-01"}).status_code == 422
    with signed_in(app, member["email"]) as seller:
        assert seller.get("/api/v1/sales/report", params={"source": "website"}).json()["deal_count"] == 4
        assert seller.get("/api/v1/sales/report", params={"owner_id": owner_id}).status_code == 403
    with signed_in(app, "other@example.com") as other:
        report = other.get("/api/v1/sales/report").json()
        assert report["deal_count"] == 0 and report["goals"] == []


def test_proposals_honor_viewer_and_key_scopes_but_members_can_operate(sales_system):
    client, app, _, _, _, _, _ = sales_system
    payload, _ = proposal_input(client)
    member = post(client, "team", {"name": "Vendedor", "email": "operator@example.com", "password": PASSWORD, "role": "member"})
    viewer = post(client, "team", {"name": "Leitor", "email": "readsales@example.com", "password": PASSWORD, "role": "viewer"})
    with signed_in(app, member["email"]) as seller:
        proposal = post(seller, "sales/proposals", payload)
    with signed_in(app, viewer["email"]) as reader:
        assert reader.get("/api/v1/sales/proposals/" + proposal["id"]).status_code == 200
        assert reader.post("/api/v1/sales/proposals", json=payload).status_code == 403
        assert reader.patch("/api/v1/sales/proposals/" + proposal["id"], json={"version": 1, "status": "issued"}).status_code == 403
    key = post(client, "api-keys", {"name": "Leitura comercial", "scopes": ["deals:read"]})
    with TestClient(app) as external:
        external.headers["Authorization"] = "Bearer " + key["key"]
        assert external.get("/api/v1/sales/proposals").status_code == 200
        assert external.post("/api/v1/sales/proposals", json=payload).status_code == 403
        assert external.post("/api/v1/sales/goals", json={"owner_id": member["id"], "period": "2026-09", "target_cents": 1}).status_code == 403


def test_simultaneous_proposal_decisions_commit_only_one_outcome(sales_system):
    client, app, factory, _, _, _, _ = sales_system
    payload, _ = proposal_input(client)
    proposal = post(client, "sales/proposals", payload)
    url = "/api/v1/sales/proposals/" + proposal["id"]
    assert client.patch(url, json={"version": 1, "status": "issued"}).status_code == 200
    barrier = Barrier(2)
    def decide(status):
        with TestClient(app) as peer:
            peer.cookies.update(client.cookies)
            peer.headers["X-CSRF-Token"] = client.headers["X-CSRF-Token"]
            barrier.wait(timeout=10)
            return peer.patch(url, json={"version": 2, "status": status})
    with ThreadPoolExecutor(max_workers=2) as workers:
        responses = list(workers.map(decide, ["accepted", "rejected"]))
    assert sorted(response.status_code for response in responses) == [200, 409]
    assert client.get(url).json()["version"] == 3
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Audit).where(
            Audit.action.in_(["sales_proposals.accepted", "sales_proposals.rejected"]))) == 1
