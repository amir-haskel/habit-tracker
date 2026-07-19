import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_habit_tracker.db")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from habit_tracker.db import Base, get_db
from habit_tracker.main import app


def _make_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture()
def client() -> TestClient:
    engine = _make_engine()
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def session() -> Session:
    """Direct DB session for service-level tests that need to control created_at/log dates precisely."""
    engine = _make_engine()
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = testing_session_local()
    try:
        yield db
    finally:
        db.close()
