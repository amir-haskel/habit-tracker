from pydantic import BaseModel


class CompletionRateRead(BaseModel):
    window_days: int
    scheduled_days: int
    successful_days: int
    completion_rate: float


class StatsRead(BaseModel):
    windows: list[CompletionRateRead]
