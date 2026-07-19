from fastapi.testclient import TestClient


def _create(client: TestClient, **overrides) -> dict:
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


def test_create_quantity_habit(client: TestClient) -> None:
    habit = _create(client)
    assert habit["name"] == "Drink water"
    assert habit["tracking_type"] == "quantity"
    assert habit["target_value"] == 8
    assert habit["unit"] == "glasses"
    assert habit["frequency_type"] == "daily"
    assert habit["is_archived"] is False


def test_create_boolean_habit(client: TestClient) -> None:
    habit = _create(
        client,
        name="Meditate",
        tracking_type="boolean",
        target_value=None,
        unit=None,
    )
    assert habit["tracking_type"] == "boolean"
    assert habit["target_value"] is None
    assert habit["unit"] is None


def test_create_quit_habit(client: TestClient) -> None:
    habit = _create(
        client,
        name="No smoking",
        habit_type="quit",
        tracking_type="boolean",
        target_value=None,
        unit=None,
    )
    assert habit["habit_type"] == "quit"


def test_quantity_habit_requires_target_and_unit(client: TestClient) -> None:
    response = client.post(
        "/habits",
        json={
            "name": "Read",
            "habit_type": "build",
            "tracking_type": "quantity",
        },
    )
    assert response.status_code == 422


def test_boolean_habit_rejects_target_and_unit(client: TestClient) -> None:
    response = client.post(
        "/habits",
        json={
            "name": "Meditate",
            "habit_type": "build",
            "tracking_type": "boolean",
            "target_value": 10,
            "unit": "minutes",
        },
    )
    assert response.status_code == 422


def test_get_habit(client: TestClient) -> None:
    created = _create(client)
    response = client.get(f"/habits/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_missing_habit_returns_404(client: TestClient) -> None:
    response = client.get("/habits/999")
    assert response.status_code == 404


def test_list_habits_excludes_archived_by_default(client: TestClient) -> None:
    active = _create(client, name="Active habit")
    archived = _create(client, name="Archived habit")
    client.post(f"/habits/{archived['id']}/archive")

    response = client.get("/habits")
    ids = [h["id"] for h in response.json()]
    assert active["id"] in ids
    assert archived["id"] not in ids

    response = client.get("/habits", params={"include_archived": True})
    ids = [h["id"] for h in response.json()]
    assert active["id"] in ids
    assert archived["id"] in ids


def test_update_habit_name_and_description(client: TestClient) -> None:
    habit = _create(client)
    response = client.patch(
        f"/habits/{habit['id']}",
        json={"name": "Drink more water", "description": "8+ glasses a day"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Drink more water"
    assert body["description"] == "8+ glasses a day"


def test_update_quantity_fields_on_boolean_habit_rejected(client: TestClient) -> None:
    habit = _create(client, name="Meditate", tracking_type="boolean", target_value=None, unit=None)
    response = client.patch(f"/habits/{habit['id']}", json={"target_value": 10})
    assert response.status_code == 400


def test_archive_habit(client: TestClient) -> None:
    habit = _create(client)
    response = client.post(f"/habits/{habit['id']}/archive")
    assert response.status_code == 200
    assert response.json()["is_archived"] is True
    assert response.json()["archived_at"] is not None


def test_cannot_edit_archived_habit(client: TestClient) -> None:
    habit = _create(client)
    client.post(f"/habits/{habit['id']}/archive")
    response = client.patch(f"/habits/{habit['id']}", json={"name": "New name"})
    assert response.status_code == 400
