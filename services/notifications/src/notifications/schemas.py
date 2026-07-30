from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    habit_id: int
    kind: str
    title: str
    body: str | None
    read: bool
    created_at: datetime
