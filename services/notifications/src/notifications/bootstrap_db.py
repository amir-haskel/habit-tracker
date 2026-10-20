"""One-off job: create the notifications database if it does not exist.

RDS creates only one initial database (habit_core), so this runs once per
environment (ECS run-task command override, notifications image):

    python -m notifications.bootstrap_db

Connects to the maintenance database `postgres` with the master credentials from
DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_SSLMODE (DB_NAME is not used) and
creates BOOTSTRAP_DB_NAME (default `notifications`) if missing. Idempotent.
"""

import os
import sys

MAINTENANCE_DB = "postgres"
DEFAULT_TARGET_DB = "notifications"


def connect_kwargs(env: "os._Environ[str] | dict[str, str]") -> dict[str, object]:
    """psycopg connection arguments for the maintenance database, from DB_* variables."""
    required = ["DB_HOST", "DB_USER", "DB_PASSWORD"]
    missing = [name for name in required if not env.get(name)]
    if missing:
        raise ValueError(f"missing required environment variables: {', '.join(missing)}")
    kwargs: dict[str, object] = {
        "host": env["DB_HOST"],
        "port": int(env.get("DB_PORT") or 5432),
        "user": env["DB_USER"],
        "password": env["DB_PASSWORD"],
        "dbname": MAINTENANCE_DB,
        "connect_timeout": 10,
    }
    if env.get("DB_SSLMODE"):
        kwargs["sslmode"] = env["DB_SSLMODE"]
    return kwargs


def ensure_database(conn, name: str) -> bool:
    """Create database `name` unless it exists. Returns True if it was created.

    `conn` must be an autocommit psycopg connection (CREATE DATABASE cannot run
    inside a transaction block).
    """
    from psycopg import errors, sql

    exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone()
    if exists:
        return False
    try:
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    except errors.DuplicateDatabase:  # created by a concurrent run since the check
        return False
    return True


def ensure_app_database(settings) -> bool:
    """Create `settings.db_name` if missing, using the app's own DB_* settings.

    Used for CREATE_DATABASE_ON_STARTUP. Returns True if it was created.
    """
    import psycopg

    env = {
        "DB_HOST": settings.db_host,
        "DB_PORT": str(settings.db_port),
        "DB_USER": settings.db_user,
        "DB_PASSWORD": settings.db_password.get_secret_value(),
        "DB_SSLMODE": settings.db_sslmode,
    }
    with psycopg.connect(**connect_kwargs(env), autocommit=True) as conn:
        return ensure_database(conn, settings.db_name)


def main() -> int:
    target = os.environ.get("BOOTSTRAP_DB_NAME") or DEFAULT_TARGET_DB
    try:
        import psycopg

        # Never print kwargs/exception text wholesale: they can carry the password.
        with psycopg.connect(**connect_kwargs(os.environ), autocommit=True) as conn:
            created = ensure_database(conn, target)
    except Exception as exc:
        print(f"bootstrap_db: failed to ensure database {target!r}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"bootstrap_db: database {target!r} {'created' if created else 'already exists'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
