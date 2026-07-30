from datetime import date

from fastapi.testclient import TestClient

TODAY = date.today()


def test_streaks_endpoint(client: TestClient) -> None:
    response = client.post(
        "/habits",
        json={
            "name": "Meditate",
            "habit_type": "build",
            "tracking_type": "boolean",
        },
    )
    habit = response.json()

    client.post(f"/habits/{habit['id']}/logs", json={"date": str(TODAY), "completed": True})

    response = client.get(f"/habits/{habit['id']}/streaks")
    assert response.status_code == 200
    body = response.json()
    assert body["current_streak"] == 1
    assert body["longest_streak"] == 1


def test_streaks_for_missing_habit_returns_404(client: TestClient) -> None:
    response = client.get("/habits/999/streaks")
    assert response.status_code == 404
