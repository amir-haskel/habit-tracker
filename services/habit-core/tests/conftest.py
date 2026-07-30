import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_habit_core.db")

import pytest
from fastapi.testclient import TestClient
from habit_events import InMemoryEventBus
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from habit_core.db import Base, get_db
from habit_core.events import get_event_bus
from habit_core.main import app


def _make_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture()
def bus() -> InMemoryEventBus:
    """Per-test in-memory event bus; tests assert on ``bus.published``."""
    return InMemoryEventBus()


@pytest.fixture()
def client(bus: InMemoryEventBus) -> TestClient:
    engine = _make_engine()
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_event_bus] = lambda: bus
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
