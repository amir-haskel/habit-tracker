from __future__ import annotations

from datetime import date as date_
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from habit_core.db import Base

if TYPE_CHECKING:
    from habit_core.models.habit import Habit


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HabitLog(Base):
    __tablename__ = "habit_logs"
    __table_args__ = (UniqueConstraint("habit_id", "date", name="uq_habit_log_habit_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id"))
    date: Mapped[date_] = mapped_column(Date)
    completed: Mapped[bool | None] = mapped_column(default=None)
    value: Mapped[float | None] = mapped_column(Float, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    habit: Mapped["Habit"] = relationship(back_populates="logs")
