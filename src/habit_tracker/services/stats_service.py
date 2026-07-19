from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from habit_tracker.models.habit import Habit, HabitType
from habit_tracker.models.habit_log import HabitLog
from habit_tracker.repositories.habit_log_repository import HabitLogRepository
from habit_tracker.services.habit_service import HabitService
from habit_tracker.services.scheduling import iter_scheduled_days
from habit_tracker.services.success import day_status

WINDOWS = (7, 30, 90)


@dataclass(frozen=True)
class CompletionStats:
    window_days: int
    scheduled_days: int
    successful_days: int
    completion_rate: float


def _completion_rate(
    habit: Habit, logs_by_date: dict[date, HabitLog], today: date, window_days: int
) -> CompletionStats:
    window_start = today - timedelta(days=window_days - 1)
    start = max(window_start, habit.created_at.date())
    if start > today:
        return CompletionStats(window_days, 0, 0, 0.0)

    scheduled = 0
    successes = 0
    for day in iter_scheduled_days(habit, start, today):
        log = logs_by_date.get(day)
        if day == today and log is None and habit.habit_type == HabitType.BUILD:
            continue  # day isn't over yet; don't count it either way
        scheduled += 1
        if day_status(habit, log):
            successes += 1

    rate = successes / scheduled if scheduled else 0.0
    return CompletionStats(window_days, scheduled, successes, rate)


class StatsService:
    def __init__(self, db: Session) -> None:
        self._habits = HabitService(db)
        self._logs = HabitLogRepository(db)

    def completion_rates(self, habit_id: int, today: date | None = None) -> list[CompletionStats]:
        habit = self._habits.get_habit(habit_id)
        today = today or datetime.now(timezone.utc).date()
        earliest_window_start = today - timedelta(days=max(WINDOWS) - 1)
        start = max(earliest_window_start, habit.created_at.date())
        logs_by_date = {
            log.date: log
            for log in self._logs.list_for_habit(habit_id, start_date=start, end_date=today)
        }
        return [_completion_rate(habit, logs_by_date, today, window) for window in WINDOWS]
