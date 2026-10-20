import pytest

from notifications.bootstrap_db import connect_kwargs, ensure_database, main

ENV = {"DB_HOST": "db.internal", "DB_USER": "master", "DB_PASSWORD": "p@ss/w:rd"}


def test_connect_kwargs_targets_maintenance_db_and_defaults():
    assert connect_kwargs(ENV) == {
        "host": "db.internal",
        "port": 5432,
        "user": "master",
        "password": "p@ss/w:rd",
        "dbname": "postgres",
        "connect_timeout": 10,
    }


def test_connect_kwargs_port_and_sslmode_and_ignores_db_name():
    kwargs = connect_kwargs({**ENV, "DB_PORT": "6543", "DB_SSLMODE": "require", "DB_NAME": "habit_core"})
    assert kwargs["port"] == 6543
    assert kwargs["sslmode"] == "require"
    assert kwargs["dbname"] == "postgres"


def test_connect_kwargs_omits_empty_sslmode():
    assert "sslmode" not in connect_kwargs({**ENV, "DB_SSLMODE": ""})


@pytest.mark.parametrize("missing", ["DB_HOST", "DB_USER", "DB_PASSWORD"])
def test_connect_kwargs_missing_variable(missing):
    env = {k: v for k, v in ENV.items() if k != missing}
    with pytest.raises(ValueError, match=missing):
        connect_kwargs(env)


class FakeConn:
    """Records statements; `existing` simulates the pg_database lookup result."""

    def __init__(self, existing: bool):
        self.existing = existing
        self.statements: list = []

    def execute(self, query, params=None):
        self.statements.append((query, params))
        return self

    def fetchone(self):
        return (1,) if self.existing else None


def test_ensure_database_skips_when_present():
    pytest.importorskip("psycopg")
    conn = FakeConn(existing=True)
    assert ensure_database(conn, "notifications") is False
    assert len(conn.statements) == 1
    assert conn.statements[0][1] == ("notifications",)


def test_ensure_database_creates_when_missing_with_quoted_identifier():
    sql = pytest.importorskip("psycopg.sql")
    conn = FakeConn(existing=False)
    assert ensure_database(conn, 'we"ird; DROP DATABASE x; --') is True
    create = conn.statements[1][0]
    assert create.as_string(None) == 'CREATE DATABASE "we""ird; DROP DATABASE x; --"'
    assert isinstance(create, sql.Composed)


def test_main_fails_without_credentials(monkeypatch, capsys):
    for name in ("DB_HOST", "DB_USER", "DB_PASSWORD", "BOOTSTRAP_DB_NAME"):
        monkeypatch.delenv(name, raising=False)
    assert main() == 1
    err = capsys.readouterr().err
    assert "DB_HOST" in err
