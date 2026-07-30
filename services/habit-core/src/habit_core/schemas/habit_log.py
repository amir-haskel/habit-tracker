from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HabitLogCreate(BaseModel):
    date: date
    completed: bool | None = None
    amount: float | None = Field(default=None, ge=0)
    mode: Literal["increment", "set"] = "increment"

    @model_validator(mode="after")
    def _validate_exactly_one_kind(self) -> HabitLogCreate:
        if (self.completed is None) == (self.amount is None):
            raise ValueError("provide exactly one of `completed` or `amount`")
        return self


class HabitLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    habit_id: int
    date: date
    completed: bool | None
    value: float | None
    created_at: datetime
    updated_at: datetime
