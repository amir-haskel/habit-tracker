from fastapi import APIRouter

from habit_tracker.api.deps import DbSession
from habit_tracker.schemas.streak import StreakRead
from habit_tracker.services.streak_service import StreakService

router = APIRouter(prefix="/habits/{habit_id}/streaks", tags=["streaks"])


@router.get("", response_model=StreakRead)
def get_streaks(habit_id: int, db: DbSession) -> StreakRead:
    result = StreakService(db).compute(habit_id)
    return StreakRead(current_streak=result.current_streak, longest_streak=result.longest_streak)
