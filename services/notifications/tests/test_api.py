from fastapi.testclient import TestClient

from notifications.models import Notification


def _seed(client: TestClient) -> None:
    # Seed directly via the same session the API uses (dependency override).
    from notifications.db import get_db

    db = next(client.app.dependency_overrides[get_db]())
    db.add_all(
        [
            Notification(habit_id=1, kind="habit_created", title="A", read=False),
            Notification(habit_id=1, kind="streak_milestone", title="B", read=True),
        ]
    )
    db.commit()


def test_list_notifications(client: TestClient) -> None:
    _seed(client)
    resp = client.get("/notifications")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_unread_only(client: TestClient) -> None:
    _seed(client)
    resp = client.get("/notifications", params={"unread_only": True})
    titles = [n["title"] for n in resp.json()]
    assert titles == ["A"]


def test_unread_count(client: TestClient) -> None:
    _seed(client)
    resp = client.get("/notifications/unread-count")
    assert resp.json() == {"count": 1}


def test_mark_read(client: TestClient) -> None:
    _seed(client)
    target = client.get("/notifications", params={"unread_only": True}).json()[0]
    resp = client.post(f"/notifications/{target['id']}/read")
    assert resp.status_code == 200
    assert resp.json()["read"] is True
    assert client.get("/notifications/unread-count").json() == {"count": 0}


def test_mark_read_missing_returns_404(client: TestClient) -> None:
    resp = client.post("/notifications/999/read")
    assert resp.status_code == 404


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
