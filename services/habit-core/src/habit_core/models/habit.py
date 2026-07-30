from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from habit_core.db import Base

if TYPE_CHECKING:
    from habit_core.models.habit_log import HabitLog


class HabitType(str, enum.Enum):
    BUILD = "build"
    QUIT = "quit"


class TrackingType(str, enum.Enum):
    BOOLEAN = "boolean"
    QUANTITY = "quantity"


class FrequencyType(str, enum.Enum):
    """Only DAILY is implemented today; other values will land with real scheduling later."""

    DAILY = "daily"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    habit_type: Mapped[HabitType] = mapped_column(Enum(HabitType, native_enum=False, length=20))
    tracking_type: Mapped[TrackingType] = mapped_column(
        Enum(TrackingType, native_enum=False, length=20)
    )
    target_value: Mapped[float | None] = mapped_column(Float, default=None)
    unit: Mapped[str | None] = mapped_column(String(50), default=None)
    frequency_type: Mapped[FrequencyType] = mapped_column(
        Enum(FrequencyType, native_enum=False, length=20), default=FrequencyType.DAILY
    )
    frequency_config: Mapped[dict | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    logs: Mapped[list["HabitLog"]] = relationship(
        back_populates="habit", cascade="all, delete-orphan"
    )

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None
