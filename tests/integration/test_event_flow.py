"""End-to-end event-contract test across services.

Wires habit-core's publisher to notifications' handlers through a single
InMemoryEventBus — the same typed events SNS/SQS would carry — and asserts the
notifications service reacts correctly. Requires both packages installed
(editable): pip install -e libs/events -e services/habit-core -e services/notifications
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from habit_events import InMemoryEventBus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# habit-core (producer)
import habit_core.models  # noqa: F401 — register models
from habit_core.db import Base as HabitBase
from habit_core.schemas.habit import HabitCreate
from habit_core.schemas.habit_log import HabitLogCreate
from habit_core.services.habit_service import HabitService
from habit_core.services.logging_service import LoggingService

# notifications (consumer)
import notifications.models  # noqa: F401 — register models
from notifications.db import Base as NotifBase
from notifications.handlers import EVENT_TYPES, dispatch
from notifications.repository import NotificationRepository


def _in_memory_session(base):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


@pytest.fixture()
def wired():
    """A shared bus with notifications' handlers subscribed to habit-core events."""
    bus = InMemoryEventBus()
    habit_db = _in_memory_session(HabitBase)
    notif_db = _in_memory_session(NotifBase)

    for event_type in EVENT_TYPES:
        bus.subscribe(event_type, lambda event: dispatch(notif_db, event))

    return bus, habit_db, notif_db


def test_create_then_streak_flows_into_notifications(wired) -> None:
    bus, habit_db, notif_db = wired
    habits = HabitService(habit_db, bus)
    logging = LoggingService(habit_db, bus)

    habit = habits.create_habit(
        HabitCreate(name="Meditate", habit_type="build", tracking_type="boolean")
    )

    # A "habit created" notification and the read-model entry both exist.
    notes = NotificationRepository(notif_db)
    created = notes.list()
    assert any(n.kind == "habit_created" and "Meditate" in n.title for n in created)

    # Build a 7-day streak; the milestone event should produce a notification
    # whose body uses the name from the notifications read-model.
    today = date.today()
    for i in range(6, -1, -1):
        logging.log(habit.id, HabitLogCreate(date=today - timedelta(days=i), completed=True))

    milestones = [n for n in notes.list() if n.kind == "streak_milestone"]
    assert len(milestones) == 1
    assert "Meditate" in milestones[0].body
    assert "7-day streak" in milestones[0].title


def test_archive_marks_read_model_across_services(wired) -> None:
    bus, habit_db, notif_db = wired
    habits = HabitService(habit_db, bus)

    habit = habits.create_habit(
        HabitCreate(name="Run", habit_type="build", tracking_type="boolean")
    )
    habits.archive_habit(habit.id)

    from notifications.models import HabitRef

    ref = notif_db.get(HabitRef, habit.id)
    assert ref is not None and ref.archived is True
