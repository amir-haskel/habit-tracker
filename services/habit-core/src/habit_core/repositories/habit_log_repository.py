from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from habit_core.models.habit_log import HabitLog


class HabitLogRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_date(self, habit_id: int, log_date: date) -> HabitLog | None:
        stmt = select(HabitLog).where(HabitLog.habit_id == habit_id, HabitLog.date == log_date)
        return self._db.scalars(stmt).first()

    def list_for_habit(
        self,
        habit_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[HabitLog]:
        stmt = select(HabitLog).where(HabitLog.habit_id == habit_id)
        if start_date is not None:
            stmt = stmt.where(HabitLog.date >= start_date)
        if end_date is not None:
            stmt = stmt.where(HabitLog.date <= end_date)
        stmt = stmt.order_by(HabitLog.date)
        return list(self._db.scalars(stmt))

    def save(self, log: HabitLog) -> HabitLog:
        self._db.add(log)
        self._db.commit()
        self._db.refresh(log)
        return log
