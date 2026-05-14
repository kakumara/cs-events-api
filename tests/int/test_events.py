from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_find_events_by_tenant_valid():
    response = client.get("/events", headers={"X-Tenant-ID": "tenent_1"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 4
    assert all(event.get("tenant_id") == "tenent_1" for event in response.json())


def test_find_events_by_tenant_invalid():
    # invalid tenant identifier
    response = client.get("/events", headers={"X-Tenant-ID": "invalid_tenant"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Invalid tenant identifier: invalid_tenant"}

    # missing tenant identifier header
    response = client.get("/events")
    assert response.status_code == 422
    error = response.json().get("detail")[0]
    assert error.get("loc") == ["header", "x-tenant-id"]
    assert error.get("msg") == "Field required"
    assert error.get("type") == "missing"


def test_find_events_by_tenant_with_invalid_date_range():
    response = client.get(
        "/events?start_dt=2026-05-15T00:00:00Z&end_dt=2026-05-14T23:59:59Z",
        headers={"X-Tenant-ID": "tenent_1"},
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "start_dt must be less than or equal to end_dt"
    }


def test_find_events_by_tenant_with_filters():
    response = client.get(
        "/events?start_dt=2026-05-14T00:00:00Z&end_dt=2026-05-15T23:59:59Z&action=download&package=numpy",
        headers={"X-Tenant-ID": "tenent_1"},
    )
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) == 1
    assert_event_data(
        events[0], "tenent_1", "download", "numpy", "1.24.0", "release-bot"
    )

    response = client.get(
        "/events?start_dt=2026-05-14T00:00:00Z&end_dt=2026-05-15T23:59:59Z&action=upload&package=numpy",
        headers={"X-Tenant-ID": "tenent_1"},
    )
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) == 1
    assert_event_data(
        events[0], "tenent_1", "upload", "numpy", "1.25.0", "ci-agent-042"
    )

    # filters and sorted by timestamp
    response = client.get(
        "/events?start_dt=2026-05-14T00:00:00Z&end_dt=2026-05-15T23:59:59Z&action=download&package=globex-api",
        headers={"X-Tenant-ID": "tenent_2"},
    )
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    assert len(events) == 2
    assert_event_data(
        events[0],
        "tenent_2",
        "download",
        "globex-api",
        "3.2.0",
        "ci-runner-02",
        "2026-05-14T14:56:58.143410Z",
    )
    assert_event_data(
        events[1],
        "tenent_2",
        "download",
        "globex-api",
        "3.1.0",
        "ci-runner-03",
        "2026-05-15T10:41:45.022022Z",
    )


def assert_event_data(
    event, tenant_id, action, package, version, actor, timestamp=None
):
    assert event.get("tenant_id") == tenant_id
    assert event.get("action") == action
    assert event.get("package") == package
    assert event.get("version") == version
    assert event.get("actor") == actor
    if timestamp is not None:
        assert event.get("timestamp") == timestamp
