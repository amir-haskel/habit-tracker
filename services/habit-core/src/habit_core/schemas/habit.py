from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from habit_core.models.habit import FrequencyType, HabitType, TrackingType


class HabitBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    habit_type: HabitType
    tracking_type: TrackingType
    target_value: float | None = Field(default=None, gt=0)
    unit: str | None = None

    @model_validator(mode="after")
    def _validate_tracking_fields(self) -> HabitBase:
        if self.tracking_type == TrackingType.QUANTITY:
            if self.target_value is None or self.unit is None:
                raise ValueError("quantity-tracked habits require target_value and unit")
        elif self.target_value is not None or self.unit is not None:
            raise ValueError("boolean-tracked habits must not set target_value or unit")
        return self


class HabitCreate(HabitBase):
    pass


class HabitUpdate(BaseModel):
    """Fields a habit can be edited to. habit_type/tracking_type are immutable after creation."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    target_value: float | None = Field(default=None, gt=0)
    unit: str | None = None


class HabitRead(HabitBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    frequency_type: FrequencyType
    created_at: datetime
    archived_at: datetime | None
    is_archived: bool
