"""Event handlers: translate domain events into notifications + read-model updates.

Pure functions of (db, event) so they can be unit-tested without a broker. The
consumer (and the in-process subscriptions) route decoded events here.
"""

from __future__ import annotations

from habit_events import (
    HABIT_ARCHIVED,
    HABIT_CREATED,
    STREAK_MILESTONE,
    BaseEvent,
    HabitArchived,
    HabitCreated,
    StreakMilestone,
)
from sqlalchemy.orm import Session

from notifications.models import Notification
from notifications.repository import NotificationRepository


def handle_habit_created(db: Session, event: HabitCreated) -> None:
    repo = NotificationRepository(db)
    repo.upsert_habit_ref(event.habit_id, event.name)
    repo.add(
        Notification(
            habit_id=event.habit_id,
            kind="habit_created",
            title=f"Now tracking “{event.name}”",
            body="We'll help you keep the streak going.",
        )
    )


def handle_habit_archived(db: Session, event: HabitArchived) -> None:
    NotificationRepository(db).mark_habit_archived(event.habit_id)


def handle_streak_milestone(db: Session, event: StreakMilestone) -> None:
    repo = NotificationRepository(db)
    name = repo.habit_name(event.habit_id)
    repo.add(
        Notification(
            habit_id=event.habit_id,
            kind="streak_milestone",
            title=f"\U0001f525 {event.streak_length}-day streak!",
            body=f"You've kept “{name}” going for {event.streak_length} days straight.",
        )
    )


_DISPATCH = {
    HABIT_CREATED: handle_habit_created,
    HABIT_ARCHIVED: handle_habit_archived,
    STREAK_MILESTONE: handle_streak_milestone,
}

# Event types this service handles. The SNS subscription's filter policy
# (see docs/messaging.md) must list the same types.
EVENT_TYPES = tuple(_DISPATCH.keys())


def dispatch(db: Session, event: BaseEvent) -> None:
    handler = _DISPATCH.get(event.event_type)
    if handler is not None:
        handler(db, event)
