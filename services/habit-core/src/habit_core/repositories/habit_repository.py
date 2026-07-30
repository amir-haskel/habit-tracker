from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from habit_core.models.habit import Habit


class HabitRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, habit: Habit) -> Habit:
        self._db.add(habit)
        self._db.commit()
        self._db.refresh(habit)
        return habit

    def get(self, habit_id: int) -> Habit | None:
        return self._db.get(Habit, habit_id)

    def list(self, include_archived: bool = False) -> list[Habit]:
        stmt = select(Habit).order_by(Habit.id)
        if not include_archived:
            stmt = stmt.where(Habit.archived_at.is_(None))
        return list(self._db.scalars(stmt))

    def save(self, habit: Habit) -> Habit:
        self._db.commit()
        self._db.refresh(habit)
        return habit
