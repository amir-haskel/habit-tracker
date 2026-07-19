from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta

from habit_tracker.models.habit import FrequencyType, Habit


def is_scheduled(habit: Habit, day: date) -> bool:
    """Whether `day` is a day this habit is expected on. Only DAILY exists today;
    other frequency_type values will get their own branch once real scheduling lands."""
    if habit.frequency_type == FrequencyType.DAILY:
        return True
    raise NotImplementedError(f"Unsupported frequency_type: {habit.frequency_type}")


def iter_scheduled_days(habit: Habit, start: date, end: date) -> Iterator[date]:
    current = start
    while current <= end:
        if is_scheduled(habit, current):
            yield current
        current += timedelta(days=1)
