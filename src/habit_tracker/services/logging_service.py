from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from habit_tracker.exceptions import ValidationError
from habit_tracker.models.habit import TrackingType
from habit_tracker.models.habit_log import HabitLog
from habit_tracker.repositories.habit_log_repository import HabitLogRepository
from habit_tracker.schemas.habit_log import HabitLogCreate
from habit_tracker.services.habit_service import HabitService


class LoggingService:
    def __init__(self, db: Session) -> None:
        self._repo = HabitLogRepository(db)
        self._habits = HabitService(db)

    def log(self, habit_id: int, data: HabitLogCreate) -> HabitLog:
        habit = self._habits.get_habit(habit_id)
        if habit.is_archived:
            raise ValidationError("Cannot log against an archived habit")
        if data.date > datetime.now(timezone.utc).date():
            raise ValidationError("Cannot log a future date")

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

        return self._repo.save(entry)

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
