import json
import pytest

from datetime import datetime, timedelta, timezone

from app.config import config
from app.events.event_service import EventService

def test_find_events_by_tenant_ordered(tmp_path, monkeypatch):
    service = prepare_service_with_data(tmp_path, monkeypatch)

    events = service.find_events(tenant_id="tenant1")

    assert isinstance(events, list)
    assert len(events) == 3
    assert all(event.tenant_id == "tenant1" for event in events)
    assert events[0].timestamp <= events[1].timestamp <= events[2].timestamp

def test_find_events_returns_empty_list_for_unknown_tenant(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="Invalid tenant identifier: unknown"):
        service = prepare_service_with_data(tmp_path, monkeypatch) 
        service.find_events(tenant_id="unknown")

def test_find_events_avoids_duplicates(tmp_path, monkeypatch):
    lines = [
        '{"event_id":"evt1","tenant_id":"tenant1","action":"install","package":"pkgA","version":"1.0.0","timestamp":"2024-01-01T00:00:00","actor":"user1"}',
        '{"event_id":"evt1","tenant_id":"tenant1","action":"install","package":"pkgA","version":"1.0.0","timestamp":"2024-01-01T00:00:00","actor":"user1"}',
    ]
    test_file = write_test_events_file(tmp_path, lines)
    monkeypatch.setattr(config, "EVENTS_FILE", str(test_file))

    service = EventService()
    events = service.find_events(tenant_id="tenant1")

    assert isinstance(events, list)
    assert len(events) == 1
    assert events[0].event_id == "evt1"

def test_find_events_avoids_malformed_json_entries(tmp_path, monkeypatch):
    lines = [        
        '{"":}',
        '   ',
        '{"event_id":"evt2","tenant_id":"tenant1","action":"update","package":"pkgB","version":"1.1.0","timestamp":"2024-01-01T01:00:00","actor":"user2"}',
    ]
    test_file = write_test_events_file(tmp_path, lines)
    monkeypatch.setattr(config, "EVENTS_FILE", str(test_file))

    service = EventService()
    events = service.find_events(tenant_id="tenant1")

    assert isinstance(events, list)
    assert len(events) == 1
    assert {event.event_id for event in events} == {"evt2"} 

def test_find_events_handles_missing_file(monkeypatch):
    monkeypatch.setattr(config, "EVENTS_FILE", "non_existent_file.jsonl")

    with pytest.raises(ValueError, match="Invalid tenant identifier: any_tenant"):
        service = EventService()
        service.find_events(tenant_id="any_tenant")

@pytest.mark.parametrize("tenant_id, expected_count, expected_event_ids", [
    ("tenant1", 2, {"evt2", "evt3"}),
    ("tenant2", 0, set()), 
])
def test_find_events_with_filters_start_dt(tmp_path, monkeypatch, tenant_id, expected_count, expected_event_ids):
    service = prepare_service_with_data(tmp_path, monkeypatch)

    start_dt = datetime(2024, 1, 1, 1, 1, tzinfo=timezone.utc)
    events = service.find_events(tenant_id=tenant_id, start_dt=start_dt)

    assert isinstance(events, list)
    assert len(events) == expected_count
    if expected_count > 0:
        assert {event.tenant_id for event in events} == {tenant_id}
        assert {event.event_id for event in events} == expected_event_ids
        assert {event.timestamp.isoformat() for event in events} == {"2024-02-01T01:00:00+00:00", "2024-03-01T02:00:00+00:00"}

@pytest.mark.parametrize("tenant_id, expected_count, expected_event_ids", [
    ("tenant1", 2, {"evt1", "evt2"}),
    ("tenant2", 1, {"evt4"}),
])
def test_find_events_with_filters_end_dt(tmp_path, monkeypatch, tenant_id, expected_count, expected_event_ids):
    service = prepare_service_with_data(tmp_path, monkeypatch)
    end_dt = datetime(2024, 2, 2, 0, 0, tzinfo=timezone.utc)
    events = service.find_events(tenant_id=tenant_id, end_dt=end_dt)

    assert isinstance(events, list)
    assert len(events) == expected_count
    if expected_count > 0:
        assert {event.tenant_id for event in events} == {tenant_id}
        assert {event.event_id for event in events} == expected_event_ids   



@pytest.mark.parametrize("tenant_id, action, expected_count, expected_event_ids", [
    ("tenant1", "install", 2, {"evt1", "evt3"}),
    ("tenant2", "install", 1, {"evt4"}),
])
def test_find_events_with_filters_action(tmp_path, monkeypatch, tenant_id, action, expected_count, expected_event_ids):
    service = prepare_service_with_data(tmp_path, monkeypatch)
    events = service.find_events(tenant_id=tenant_id, action=action)

    assert isinstance(events, list)
    assert len(events) == expected_count
    if expected_count > 0:
        assert {event.tenant_id for event in events} == {tenant_id}
        assert {event.event_id for event in events} == expected_event_ids
        assert {event.action for event in events} == {action}


@pytest.mark.parametrize("tenant_id, package, expected_event_ids", [
    ("tenant1", "pkgA", {"evt1", "evt3"}),
    ("tenant1", "pkgB", {"evt2"}),
    ("tenant1", "unknown_pkg", set()),
])
def test_find_events_with_filters_package(tmp_path, monkeypatch, tenant_id, package, expected_event_ids):
    service = prepare_service_with_data(tmp_path, monkeypatch)
    events = service.find_events(tenant_id=tenant_id, package=package)

    assert isinstance(events, list)
    assert {event.event_id for event in events} == expected_event_ids    
    assert all(event.tenant_id == tenant_id for event in events)
    if expected_event_ids:        
        assert events[0].timestamp <= events[-1].timestamp      

@pytest.mark.parametrize("tenant_id, start_dt, end_dt, action, package, expected_event_ids", [
    ("tenant1", datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), datetime(2024, 2, 15, 0, 0, tzinfo=timezone.utc), "install", "pkgA", {"evt1"}),
    ("tenant1", datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), datetime(2024, 3, 2, 0, 0, tzinfo=timezone.utc), "install", "pkgA", {"evt1", "evt3"}),
    ("tenant1", datetime(2024, 2, 1, 0, 0, tzinfo=timezone.utc), datetime(2024, 3, 2, 0, 0, tzinfo=timezone.utc), "install", "pkgA", {"evt3"}),
    ("tenant1", datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), datetime(2024, 1, 2, 0, 0, tzinfo=timezone.utc), "install", "pkgA", {"evt1"}),
    ("tenant1", datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), "install", "pkgB", set()),
    ("tenant1", datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), datetime(2024, 3, 1, 0, tzinfo=timezone.utc), "update", "pkgB", {"evt2"}), 
    ("tenant2", datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc), datetime(2024, 2, 15, 0, 0, tzinfo=timezone.utc), "install", "pkgA", {"evt4"}),
])
def test_find_events_with_filters_combined(tmp_path, monkeypatch, tenant_id, start_dt, end_dt, action, package, expected_event_ids):
    service = prepare_service_with_data(tmp_path, monkeypatch)
    events = service.find_events(tenant_id=tenant_id, start_dt=start_dt, end_dt=end_dt, action=action, package=package)

    assert isinstance(events, list)
    assert len(events) == len(expected_event_ids)
    for event in events:
        assert event.event_id in expected_event_ids
        assert event.tenant_id == tenant_id
        assert event.action == action
        assert event.package == package

def test_cleanup_old_events(tmp_path, monkeypatch):
    now = datetime.now(timezone.utc)
    day1 = now - timedelta(hours=1)
    day2 = now - timedelta(days=2)
    lines = [
        json.dumps({
            "event_id": "evt1",
            "tenant_id": "tenant1",
            "action": "install",
            "package": "pkgA",
            "version": "1.0.0",
            "timestamp": day1.isoformat(),
            "actor": "user1",
        }),
        json.dumps({
            "event_id": "evt2",
            "tenant_id": "tenant1",
            "action": "update",
            "package": "pkgB",
            "version": "1.1.0",
            "timestamp": day2.isoformat(),
            "actor": "user2",
        }),
        json.dumps({
            "event_id": "evt3",
            "tenant_id": "tenant2",
            "action": "install",
            "package": "pkgA",
            "version": "1.0.0",
            "timestamp": day1.isoformat(),
            "actor": "user3",
        }),
        json.dumps({
            "event_id": "evt4",
            "tenant_id": "tenant2",
            "action": "install",
            "package": "pkgB",
            "version": "1.2.0",
            "timestamp": day2.isoformat(),
            "actor": "user4",
        }),
    ]
    test_file = write_test_events_file(tmp_path, lines)
    monkeypatch.setattr(config,("EVENTS_FILE"), str(test_file))
    monkeypatch.setattr(config,("RETENTION_DAYS"), 1)

    service = EventService()

    service.cleanup_old_events()

    tenant1_events = service.find_events("tenant1")
    tenant2_events = service.find_events("tenant2")

    assert isinstance(tenant1_events, list)
    assert len(tenant1_events) == 1
    assert {event.event_id for event in tenant1_events} == {"evt1"}

    assert isinstance(tenant2_events, list)
    assert len(tenant2_events) == 1
    assert {event.event_id for event in tenant2_events} == {"evt3"}

def prepare_service_with_data(tmp_path, monkeypatch):
    # intentionally out of order to test sorting by timestamp in find_events
    lines = [
        '{"event_id": "evt3", "tenant_id": "tenant1", "action": "install", "package": "pkgA", "version": "1.0.0", "timestamp": "2024-03-01T02:00:00Z", "actor": "user3"}',
        '{"event_id": "evt1", "tenant_id": "tenant1", "action": "install", "package": "pkgA", "version": "1.0.0", "timestamp": "2024-01-01T00:30:00Z", "actor": "user1"}',
        '{"event_id": "evt2", "tenant_id": "tenant1", "action": "update", "package": "pkgB", "version": "1.1.0", "timestamp": "2024-02-01T01:00:00Z", "actor": "user2"}',        
        '{"event_id": "evt4", "tenant_id": "tenant2", "action": "install", "package": "pkgA", "version": "1.0.0", "timestamp": "2024-01-01T00:30:00Z", "actor": "user4"}',
    ]
    test_file = write_test_events_file(tmp_path, lines)
    monkeypatch.setattr(config, "EVENTS_FILE", str(test_file))

    service = EventService()
    return service

def write_test_events_file(tmp_path, lines):
    file_path = tmp_path / "events.jsonl"
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return file_path
