from datetime import date

from fastapi import APIRouter, status

from habit_tracker.api.deps import DbSession
from habit_tracker.exceptions import NotFoundError
from habit_tracker.schemas.habit_log import HabitLogCreate, HabitLogRead
from habit_tracker.services.logging_service import LoggingService

router = APIRouter(prefix="/habits/{habit_id}/logs", tags=["logs"])


@router.post("", response_model=HabitLogRead, status_code=status.HTTP_201_CREATED)
def log_habit(habit_id: int, data: HabitLogCreate, db: DbSession) -> HabitLogRead:
    log = LoggingService(db).log(habit_id, data)
    return HabitLogRead.model_validate(log)


@router.get("", response_model=list[HabitLogRead])
def list_logs(
    habit_id: int,
    db: DbSession,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[HabitLogRead]:
    logs = LoggingService(db).list_logs(habit_id, start_date, end_date)
    return [HabitLogRead.model_validate(log) for log in logs]


@router.get("/{log_date}", response_model=HabitLogRead)
def get_log(habit_id: int, log_date: date, db: DbSession) -> HabitLogRead:
    log = LoggingService(db).get_log(habit_id, log_date)
    if log is None:
        raise NotFoundError(f"No log for habit {habit_id} on {log_date}")
    return HabitLogRead.model_validate(log)
