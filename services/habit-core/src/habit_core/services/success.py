from __future__ import annotations

from habit_core.models.habit import Habit, HabitType, TrackingType
from habit_core.models.habit_log import HabitLog


def day_status(habit: Habit, log: HabitLog | None) -> bool:
    """Whether a given day counts as a success for this habit.

    Missing-log convention: for `quit` habits, no log means the behavior wasn't
    logged as happening, so it defaults to success. For `build` habits, no log
    means the action wasn't done, so it defaults to failure.
    """
    if log is None:
        return habit.habit_type == HabitType.QUIT

    if habit.tracking_type == TrackingType.BOOLEAN:
        occurred = bool(log.completed)
    else:
        value = log.value if log.value is not None else 0.0
        target = habit.target_value or 0.0
        if habit.habit_type == HabitType.BUILD:
            return value >= target
        return value <= target

    if habit.habit_type == HabitType.BUILD:
        return occurred
    return not occurred
