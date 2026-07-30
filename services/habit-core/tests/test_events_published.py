from datetime import date, timedelta

from fastapi.testclient import TestClient
from habit_events import InMemoryEventBus

TODAY = date.today()


def _create_boolean_build(client: TestClient) -> dict:
    resp = client.post(
        "/habits",
        json={"name": "Meditate", "habit_type": "build", "tracking_type": "boolean"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_quantity_build(client: TestClient) -> dict:
    resp = client.post(
        "/habits",
        json={
            "name": "Water",
            "habit_type": "build",
            "tracking_type": "quantity",
            "target_value": 8,
            "unit": "glasses",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_publishes_habit_created(client: TestClient, bus: InMemoryEventBus) -> None:
    habit = _create_boolean_build(client)
    created = [e for e in bus.published if e.event_type == "habit.created"]
    assert len(created) == 1
    assert created[0].habit_id == habit["id"]
    assert created[0].habit_type == "build"


def test_archive_publishes_habit_archived(client: TestClient, bus: InMemoryEventBus) -> None:
    habit = _create_boolean_build(client)
    client.post(f"/habits/{habit['id']}/archive")
    archived = [e for e in bus.published if e.event_type == "habit.archived"]
    assert len(archived) == 1
    assert archived[0].habit_id == habit["id"]


def test_archive_twice_publishes_once(client: TestClient, bus: InMemoryEventBus) -> None:
    habit = _create_boolean_build(client)
    client.post(f"/habits/{habit['id']}/archive")
    client.post(f"/habits/{habit['id']}/archive")
    archived = [e for e in bus.published if e.event_type == "habit.archived"]
    assert len(archived) == 1


def test_log_publishes_habit_logged_with_goal_met(client: TestClient, bus: InMemoryEventBus) -> None:
    habit = _create_quantity_build(client)
    client.post(f"/habits/{habit['id']}/logs", json={"date": str(TODAY), "amount": 8})
    logged = [e for e in bus.published if e.event_type == "habit.logged"]
    assert len(logged) == 1
    assert logged[0].goal_met is True
    assert logged[0].value == 8


def test_log_below_target_reports_goal_not_met(client: TestClient, bus: InMemoryEventBus) -> None:
    habit = _create_quantity_build(client)
    client.post(f"/habits/{habit['id']}/logs", json={"date": str(TODAY), "amount": 3})
    logged = [e for e in bus.published if e.event_type == "habit.logged"]
    assert logged[0].goal_met is False


def test_streak_milestone_published_at_seven_days(
    client: TestClient, bus: InMemoryEventBus
) -> None:
    habit = _create_boolean_build(client)
    # Log 7 consecutive days ending today, oldest first.
    for i in range(6, -1, -1):
        day = TODAY - timedelta(days=i)
        client.post(f"/habits/{habit['id']}/logs", json={"date": str(day), "completed": True})

    milestones = [e for e in bus.published if e.event_type == "streak.milestone"]
    assert len(milestones) == 1
    assert milestones[0].streak_length == 7


def test_no_milestone_before_seven_days(client: TestClient, bus: InMemoryEventBus) -> None:
    habit = _create_boolean_build(client)
    for i in range(4, -1, -1):  # only 5 days
        day = TODAY - timedelta(days=i)
        client.post(f"/habits/{habit['id']}/logs", json={"date": str(day), "completed": True})
    milestones = [e for e in bus.published if e.event_type == "streak.milestone"]
    assert milestones == []
