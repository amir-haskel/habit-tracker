from fastapi import APIRouter

from habit_core.api.deps import DbSession
from habit_core.schemas.stats import CompletionRateRead, StatsRead
from habit_core.services.stats_service import StatsService

router = APIRouter(prefix="/habits/{habit_id}/stats", tags=["stats"])


@router.get("", response_model=StatsRead)
def get_stats(habit_id: int, db: DbSession) -> StatsRead:
    results = StatsService(db).completion_rates(habit_id)
    return StatsRead(
        windows=[
            CompletionRateRead(
                window_days=result.window_days,
                scheduled_days=result.scheduled_days,
                successful_days=result.successful_days,
                completion_rate=result.completion_rate,
            )
            for result in results
        ]
    )
