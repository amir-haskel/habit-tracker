from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from habit_tracker.exceptions import NotFoundError, ValidationError
from habit_tracker.models.habit import Habit, TrackingType
from habit_tracker.repositories.habit_repository import HabitRepository
from habit_tracker.schemas.habit import HabitCreate, HabitUpdate


class HabitService:
    def __init__(self, db: Session) -> None:
        self._repo = HabitRepository(db)

    def create_habit(self, data: HabitCreate) -> Habit:
        habit = Habit(
            name=data.name,
            description=data.description,
            habit_type=data.habit_type,
            tracking_type=data.tracking_type,
            target_value=data.target_value,
            unit=data.unit,
        )
        return self._repo.create(habit)

    def get_habit(self, habit_id: int) -> Habit:
        habit = self._repo.get(habit_id)
        if habit is None:
            raise NotFoundError(f"Habit {habit_id} not found")
        return habit

    def list_habits(self, include_archived: bool = False) -> list[Habit]:
        return self._repo.list(include_archived=include_archived)

    def update_habit(self, habit_id: int, data: HabitUpdate) -> Habit:
        habit = self.get_habit(habit_id)
        if habit.is_archived:
            raise ValidationError("Cannot edit an archived habit")

        updates = data.model_dump(exclude_unset=True)
        touches_quantity_fields = "target_value" in updates or "unit" in updates
        if touches_quantity_fields and habit.tracking_type != TrackingType.QUANTITY:
            raise ValidationError("target_value/unit only apply to quantity-tracked habits")

        for field, value in updates.items():
            setattr(habit, field, value)
        return self._repo.save(habit)

    def archive_habit(self, habit_id: int) -> Habit:
        habit = self.get_habit(habit_id)
        if not habit.is_archived:
            habit.archived_at = datetime.now(timezone.utc)
            self._repo.save(habit)
        return habit
