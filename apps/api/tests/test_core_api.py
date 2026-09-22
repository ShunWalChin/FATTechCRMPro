from datetime import timedelta

from fastapi.testclient import TestClient

from fattech.core_models import CoreDelivery, CoreHeartbeat
from fattech.models import Outbox, now
from test_api import PASSWORD, post, system as system


def test_operations_are_tenant_scoped_and_require_admin(system):
    client, app, factory, tenant_id, second, *_ = system
    with factory() as db:
        source = Outbox(tenant_id=second, event_type="private.event", payload={"secret": "not visible"})
        db.add(source)
        db.flush()
        delivery = CoreDelivery(tenant_id=second, event_id=source.id, worker_role="bi",
                                status="dead_letter", attempts=3, cycle_attempts=3)
        db.add(delivery)
        db.commit()
    assert client.get("/api/v1/core/deliveries").json()["total"] == 0
    assert client.get(f"/api/v1/core/deliveries/{delivery.id}/failures").status_code == 404
    assert client.post(f"/api/v1/core/deliveries/{delivery.id}/retry",
                       json={"expected_attempts": 3}).status_code == 404
    before = client.get("/api/v1/core/overview").json()
    assert before["counts"]["dead_letter"] == 0
    assert all(row["status"] == "unknown" for row in before["workers"])
    with factory() as db:
        db.add(CoreHeartbeat(tenant_id=tenant_id, worker_role="bi", last_seen_at=now() - timedelta(hours=1)))
        db.commit()
    result = client.get("/api/v1/core/overview").json()
    assert result["workers"][0]["status"] == "stale"
    assert client.get("/api/v1/core/deliveries?limit=101").status_code == 422
    post(client, "team", {"name": "Viewer", "email": "core-viewer@example.com", "password": PASSWORD, "role": "viewer"})
    with TestClient(app) as viewer:
        login = viewer.post("/api/v1/auth/login", json={"email": "core-viewer@example.com", "password": PASSWORD})
        viewer.headers["X-CSRF-Token"] = login.json()["csrf_token"]
        for path in ("overview", "contract", "deliveries", "message-batches"):
            assert viewer.get(f"/api/v1/core/{path}").status_code == 403
        assert viewer.post(f"/api/v1/core/deliveries/{delivery.id}/retry",
                           json={"expected_attempts": 3}).status_code == 403
