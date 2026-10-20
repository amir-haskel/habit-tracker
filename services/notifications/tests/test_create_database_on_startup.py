import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from notifications.config import Settings
from notifications.main import app, settings


def test_flag_requires_db_components() -> None:
    with pytest.raises(ValidationError) as exc:
        Settings(_env_file=None, create_database_on_startup=True, db_host="db.example")
    message = str(exc.value)
    assert "CREATE_DATABASE_ON_STARTUP" in message
    assert "DB_NAME" in message and "DB_USER" in message and "DB_PASSWORD" in message


def test_flag_off_does_not_touch_the_database(monkeypatch) -> None:
    calls: list[object] = []
    monkeypatch.setattr("notifications.bootstrap_db.ensure_app_database", lambda s: calls.append(s))
    monkeypatch.setattr(settings, "create_database_on_startup", False)
    with TestClient(app):
        pass
    assert calls == []


def test_flag_on_creates_database_before_startup_completes(monkeypatch) -> None:
    calls: list[object] = []
    monkeypatch.setattr("notifications.bootstrap_db.ensure_app_database", lambda s: calls.append(s))
    monkeypatch.setattr(settings, "create_database_on_startup", True)
    with TestClient(app):
        pass
    assert calls == [settings]
