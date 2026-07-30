from datetime import date, timedelta

from fastapi.testclient import TestClient

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)


def _create_habit(client: TestClient, **overrides) -> dict:
    payload = {
        "name": "Drink water",
        "habit_type": "build",
        "tracking_type": "quantity",
        "target_value": 8,
        "unit": "glasses",
    }
    payload.update(overrides)
    response = client.post("/habits", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _create_boolean_habit(client: TestClient, **overrides) -> dict:
    return _create_habit(
        client,
        name="Meditate",
        tracking_type="boolean",
        target_value=None,
        unit=None,
        **overrides,
    )


def test_log_boolean_habit_done(client: TestClient) -> None:
    habit = _create_boolean_habit(client)
    response = client.post(
        f"/habits/{habit['id']}/logs", json={"date": str(TODAY), "completed": True}
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["completed"] is True
    assert body["value"] is None
    assert body["date"] == str(TODAY)


def test_log_boolean_habit_overwrites_same_day(client: TestClient) -> None:
    habit = _create_boolean_habit(client)
    client.post(f"/habits/{habit['id']}/logs", json={"date": str(TODAY), "completed": True})
    response = client.post(
        f"/habits/{habit['id']}/logs", json={"date": str(TODAY), "completed": False}
    )
    assert response.status_code == 201
    assert response.json()["completed"] is False

    logs = client.get(f"/habits/{habit['id']}/logs").json()
    assert len(logs) == 1


def test_log_quantity_increments_across_calls(client: TestClient) -> None:
    habit = _create_habit(client)
    client.post(f"/habits/{habit['id']}/logs", json={"date": str(TODAY), "amount": 3})
    response = client.post(f"/habits/{habit['id']}/logs", json={"date": str(TODAY), "amount": 2})
    assert response.status_code == 201
    assert response.json()["value"] == 5


def test_log_quantity_set_mode_overwrites(client: TestClient) -> None:
    habit = _create_habit(client)
    client.post(f"/habits/{habit['id']}/logs", json={"date": str(TODAY), "amount": 3})
    response = client.post(
        f"/habits/{habit['id']}/logs",
        json={"date": str(TODAY), "amount": 10, "mode": "set"},
    )
    assert response.status_code == 201
    assert response.json()["value"] == 10


def test_backfill_past_date(client: TestClient) -> None:
    habit = _create_habit(client)
    response = client.post(
        f"/habits/{habit['id']}/logs", json={"date": str(YESTERDAY), "amount": 8}
    )
    assert response.status_code == 201
    assert response.json()["date"] == str(YESTERDAY)


def test_future_date_rejected(client: TestClient) -> None:
    habit = _create_habit(client)
    future = TODAY + timedelta(days=1)
    response = client.post(f"/habits/{habit['id']}/logs", json={"date": str(future), "amount": 1})
    assert response.status_code == 400


def test_completed_rejected_for_quantity_habit(client: TestClient) -> None:
    habit = _create_habit(client)
    response = client.post(
        f"/habits/{habit['id']}/logs", json={"date": str(TODAY), "completed": True}
    )
    assert response.status_code == 400


def test_amount_rejected_for_boolean_habit(client: TestClient) -> None:
    habit = _create_boolean_habit(client)
    response = client.post(f"/habits/{habit['id']}/logs", json={"date": str(TODAY), "amount": 1})
    assert response.status_code == 400


def test_both_completed_and_amount_rejected(client: TestClient) -> None:
    habit = _create_habit(client)
    response = client.post(
        f"/habits/{habit['id']}/logs",
        json={"date": str(TODAY), "completed": True, "amount": 1},
    )
    assert response.status_code == 422


def test_logging_against_archived_habit_rejected(client: TestClient) -> None:
    habit = _create_habit(client)
    client.post(f"/habits/{habit['id']}/archive")
    response = client.post(f"/habits/{habit['id']}/logs", json={"date": str(TODAY), "amount": 1})
    assert response.status_code == 400


def test_logging_against_missing_habit_returns_404(client: TestClient) -> None:
    response = client.post("/habits/999/logs", json={"date": str(TODAY), "amount": 1})
    assert response.status_code == 404


def test_get_log_for_missing_date_returns_404(client: TestClient) -> None:
    habit = _create_habit(client)
    response = client.get(f"/habits/{habit['id']}/logs/{TODAY}")
    assert response.status_code == 404


def test_list_logs_with_date_range(client: TestClient) -> None:
    habit = _create_habit(client)
    two_days_ago = TODAY - timedelta(days=2)
    client.post(f"/habits/{habit['id']}/logs", json={"date": str(two_days_ago), "amount": 1})
    client.post(f"/habits/{habit['id']}/logs", json={"date": str(YESTERDAY), "amount": 2})
    client.post(f"/habits/{habit['id']}/logs", json={"date": str(TODAY), "amount": 3})

    response = client.get(
        f"/habits/{habit['id']}/logs",
        params={"start_date": str(YESTERDAY), "end_date": str(TODAY)},
    )
    dates = [entry["date"] for entry in response.json()]
    assert dates == [str(YESTERDAY), str(TODAY)]
