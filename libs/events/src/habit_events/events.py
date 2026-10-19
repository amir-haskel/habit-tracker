"""Domain-event contracts shared between services.

These are the *public* wire format services agree on. Producers (habit-core)
and consumers (notifications) both import these models, so a change here is a
deliberate, reviewable contract change. Each event's ``event_type`` doubles as
the SNS ``event_type`` message attribute that subscription filter policies
match on (e.g. "habit.logged").
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

# Routing-key constants — import these instead of hardcoding strings.
HABIT_CREATED = "habit.created"
HABIT_ARCHIVED = "habit.archived"
HABIT_LOGGED = "habit.logged"
STREAK_MILESTONE = "streak.milestone"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BaseEvent(BaseModel):
    event_type: str
    occurred_at: datetime = Field(default_factory=_utcnow)


class HabitCreated(BaseEvent):
    event_type: Literal["habit.created"] = HABIT_CREATED
    habit_id: int
    name: str
    habit_type: str
    tracking_type: str


class HabitArchived(BaseEvent):
    event_type: Literal["habit.archived"] = HABIT_ARCHIVED
    habit_id: int


class HabitLogged(BaseEvent):
    event_type: Literal["habit.logged"] = HABIT_LOGGED
    habit_id: int
    date: date
    completed: bool | None = None
    value: float | None = None
    # Whether this log satisfied the habit's daily goal (computed by habit-core).
    goal_met: bool = False


class StreakMilestone(BaseEvent):
    event_type: Literal["streak.milestone"] = STREAK_MILESTONE
    habit_id: int
    streak_length: int


# Discriminated union for decoding an arbitrary event off the wire.
AnyEvent = Annotated[
    Union[HabitCreated, HabitArchived, HabitLogged, StreakMilestone],
    Field(discriminator="event_type"),
]

_EVENT_TYPES: dict[str, type[BaseEvent]] = {
    HABIT_CREATED: HabitCreated,
    HABIT_ARCHIVED: HabitArchived,
    HABIT_LOGGED: HabitLogged,
    STREAK_MILESTONE: StreakMilestone,
}


def parse_event(event_type: str, body: bytes | str) -> BaseEvent:
    """Decode a raw message body into the right typed event model."""
    model = _EVENT_TYPES.get(event_type)
    if model is None:
        raise ValueError(f"Unknown event_type: {event_type}")
    return model.model_validate_json(body)
