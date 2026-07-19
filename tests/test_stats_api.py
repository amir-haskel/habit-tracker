from datetime import date

from fastapi.testclient import TestClient

TODAY = date.today()


def test_stats_endpoint_returns_all_windows(client: TestClient) -> None:
    response = client.post(
        "/habits",
        json={"name": "Meditate", "habit_type": "build", "tracking_type": "boolean"},
    )
    habit = response.json()
    client.post(f"/habits/{habit['id']}/logs", json={"date": str(TODAY), "completed": True})

    response = client.get(f"/habits/{habit['id']}/stats")
    assert response.status_code == 200
    windows = {w["window_days"]: w for w in response.json()["windows"]}
    assert set(windows) == {7, 30, 90}
    assert windows[7]["scheduled_days"] == 1
    assert windows[7]["successful_days"] == 1
    assert windows[7]["completion_rate"] == 1.0


def test_stats_for_missing_habit_returns_404(client: TestClient) -> None:
    response = client.get("/habits/999/stats")
    assert response.status_code == 404
