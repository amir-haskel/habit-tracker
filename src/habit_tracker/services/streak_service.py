from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from habit_tracker.models.habit import Habit, HabitType
from habit_tracker.models.habit_log import HabitLog
from habit_tracker.repositories.habit_log_repository import HabitLogRepository
from habit_tracker.services.habit_service import HabitService
from habit_tracker.services.scheduling import iter_scheduled_days
from habit_tracker.services.success import day_status


@dataclass(frozen=True)
class StreakResult:
    current_streak: int
    longest_streak: int


def compute_streaks(habit: Habit, logs_by_date: dict[date, HabitLog], today: date) -> StreakResult:
    start = habit.created_at.date()
    if logs_by_date:
        start = min(start, min(logs_by_date))
    if start > today:
        return StreakResult(current_streak=0, longest_streak=0)

    running = 0
    longest = 0
    for day in iter_scheduled_days(habit, start, today):
        log = logs_by_date.get(day)
        if day == today and log is None and habit.habit_type == HabitType.BUILD:
            continue  # day isn't over yet; don't conclude a miss

        if day_status(habit, log):
            running += 1
            longest = max(longest, running)
        else:
            running = 0

    return StreakResult(current_streak=running, longest_streak=longest)


class StreakService:
    def __init__(self, db: Session) -> None:
        self._habits = HabitService(db)
        self._logs = HabitLogRepository(db)

    def compute(self, habit_id: int, today: date | None = None) -> StreakResult:
        habit = self._habits.get_habit(habit_id)
        today = today or datetime.now(timezone.utc).date()
        logs_by_date = {log.date: log for log in self._logs.list_for_habit(habit_id)}
        return compute_streaks(habit, logs_by_date, today)
