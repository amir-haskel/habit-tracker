from __future__ import annotations

from datetime import date, datetime, timezone

from habit_events import EventBus, HabitLogged, StreakMilestone
from sqlalchemy.orm import Session

from habit_core.events import get_event_bus
from habit_core.exceptions import ValidationError
from habit_core.models.habit import TrackingType
from habit_core.models.habit_log import HabitLog
from habit_core.repositories.habit_log_repository import HabitLogRepository
from habit_core.schemas.habit_log import HabitLogCreate
from habit_core.services.habit_service import HabitService
from habit_core.services.streak_service import StreakService
from habit_core.services.success import day_status

# Streak lengths worth celebrating with a notification.
MILESTONES = frozenset({7, 14, 21, 30, 50, 75, 100, 150, 200, 365})


class LoggingService:
    def __init__(self, db: Session, bus: EventBus | None = None) -> None:
        self._repo = HabitLogRepository(db)
        self._bus = bus or get_event_bus()
        self._habits = HabitService(db, self._bus)
        self._streaks = StreakService(db)

    def log(self, habit_id: int, data: HabitLogCreate) -> HabitLog:
        habit = self._habits.get_habit(habit_id)
        if habit.is_archived:
            raise ValidationError("Cannot log against an archived habit")
        if data.date > datetime.now(timezone.utc).date():
            raise ValidationError("Cannot log a future date")

        # Streak before this log, to detect a freshly-crossed milestone.
        streak_before = self._streaks.compute(habit_id).current_streak

        entry = self._repo.get_by_date(habit_id, data.date) or HabitLog(
            habit_id=habit_id, date=data.date
        )

        if habit.tracking_type == TrackingType.BOOLEAN:
            if data.completed is None:
                raise ValidationError("boolean-tracked habits require `completed`")
            entry.completed = data.completed
        else:
            if data.amount is None:
                raise ValidationError("quantity-tracked habits require `amount`")
            entry.value = data.amount if data.mode == "set" else (entry.value or 0) + data.amount

        entry = self._repo.save(entry)

        self._bus.publish(
            HabitLogged(
                habit_id=habit_id,
                date=entry.date,
                completed=entry.completed,
                value=entry.value,
                goal_met=day_status(habit, entry),
            )
        )

        streak_after = self._streaks.compute(habit_id).current_streak
        if streak_after > streak_before and streak_after in MILESTONES:
            self._bus.publish(StreakMilestone(habit_id=habit_id, streak_length=streak_after))

        return entry

    def get_log(self, habit_id: int, log_date: date) -> HabitLog | None:
        self._habits.get_habit(habit_id)
        return self._repo.get_by_date(habit_id, log_date)

    def list_logs(
        self,
        habit_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[HabitLog]:
        self._habits.get_habit(habit_id)
        return self._repo.list_for_habit(habit_id, start_date, end_date)
