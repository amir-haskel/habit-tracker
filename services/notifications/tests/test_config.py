import pytest
from sqlalchemy.engine import make_url

from notifications.config import Settings

ENV_VARS = [
    "DATABASE_URL",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_SSLMODE",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def make_settings(monkeypatch, **env: str) -> Settings:
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return Settings(_env_file=None)


COMPONENTS = {
    "DB_HOST": "db.internal",
    "DB_NAME": "notifications",
    "DB_USER": "master",
    "DB_PASSWORD": "s3cret",
}


def test_no_env_falls_back_to_sqlite(monkeypatch):
    assert make_settings(monkeypatch).database_url == "sqlite:///./notifications.db"


def test_explicit_database_url_is_used_as_is(monkeypatch):
    settings = make_settings(monkeypatch, DATABASE_URL="postgresql+psycopg://a:b@h:5432/d")
    assert settings.database_url == "postgresql+psycopg://a:b@h:5432/d"


def test_explicit_database_url_wins_over_components(monkeypatch):
    settings = make_settings(monkeypatch, DATABASE_URL="sqlite://", **COMPONENTS)
    assert settings.database_url == "sqlite://"


def test_explicit_database_url_wins_even_if_components_incomplete(monkeypatch):
    settings = make_settings(monkeypatch, DATABASE_URL="sqlite://", DB_HOST="db.internal")
    assert settings.database_url == "sqlite://"


def test_components_build_url(monkeypatch):
    settings = make_settings(monkeypatch, **COMPONENTS)
    assert settings.database_url == "postgresql+psycopg://master:s3cret@db.internal:5432/notifications"


def test_custom_port(monkeypatch):
    settings = make_settings(monkeypatch, DB_PORT="6543", **COMPONENTS)
    assert make_url(settings.database_url).port == 6543


def test_sslmode_added_only_when_set(monkeypatch):
    without = make_settings(monkeypatch, **COMPONENTS)
    assert "sslmode" not in without.database_url
    with_ssl = make_settings(monkeypatch, DB_SSLMODE="require", **COMPONENTS)
    assert make_url(with_ssl.database_url).query == {"sslmode": "require"}


def test_special_characters_in_password_round_trip(monkeypatch):
    password = "p@ss/w:rd%40#?&= x"
    settings = make_settings(monkeypatch, **{**COMPONENTS, "DB_PASSWORD": password})
    url = make_url(settings.database_url)
    assert url.password == password
    assert (url.username, url.host, url.port, url.database) == ("master", "db.internal", 5432, "notifications")


@pytest.mark.parametrize("missing", ["DB_NAME", "DB_USER", "DB_PASSWORD"])
def test_missing_component_raises(monkeypatch, missing):
    env = {k: v for k, v in COMPONENTS.items() if k != missing}
    with pytest.raises(ValueError, match=missing):
        make_settings(monkeypatch, **env)


def test_missing_components_are_all_named(monkeypatch):
    with pytest.raises(ValueError, match="DB_NAME, DB_USER, DB_PASSWORD"):
        make_settings(monkeypatch, DB_HOST="db.internal")


def test_error_does_not_leak_password(monkeypatch):
    env = {k: v for k, v in COMPONENTS.items() if k != "DB_NAME"}
    env["DB_PASSWORD"] = "hunter2-hunter2"
    with pytest.raises(ValueError) as excinfo:
        make_settings(monkeypatch, **env)
    assert "hunter2" not in str(excinfo.value)


def test_password_not_in_repr(monkeypatch):
    settings = make_settings(monkeypatch, DB_HOST="db.internal", DB_NAME="x", DB_USER="u", DB_PASSWORD="hunter2-hunter2")
    assert "hunter2" not in repr(settings).replace(settings.database_url, "")
