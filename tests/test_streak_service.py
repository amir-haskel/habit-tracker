from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from habit_tracker.models.habit import Habit, HabitType, TrackingType
from habit_tracker.schemas.habit_log import HabitLogCreate
from habit_tracker.services.logging_service import LoggingService
from habit_tracker.services.streak_service import StreakService

TODAY = date.today()


def _make_habit(
    session: Session,
    *,
    habit_type: HabitType,
    tracking_type: TrackingType,
    target_value: float | None = None,
    unit: str | None = None,
    created_days_ago: int = 0,
) -> Habit:
    habit = Habit(
        name="Test habit",
        habit_type=habit_type,
        tracking_type=tracking_type,
        target_value=target_value,
        unit=unit,
        created_at=datetime.now(timezone.utc) - timedelta(days=created_days_ago),
    )
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


def _log(session: Session, habit: Habit, days_ago: int, **kwargs) -> None:
    LoggingService(session).log(habit.id, HabitLogCreate(date=TODAY - timedelta(days=days_ago), **kwargs))


def test_build_boolean_streak_breaks_on_miss_and_ignores_pending_today(session: Session) -> None:
    habit = _make_habit(
        session, habit_type=HabitType.BUILD, tracking_type=TrackingType.BOOLEAN, created_days_ago=4
    )
    _log(session, habit, 4, completed=True)
    _log(session, habit, 3, completed=True)
    _log(session, habit, 2, completed=False)
    _log(session, habit, 1, completed=True)
    # today intentionally not logged

    result = StreakService(session).compute(habit.id, today=TODAY)
    assert result.current_streak == 1
    assert result.longest_streak == 2


def test_build_quantity_streak_uses_target_threshold(session: Session) -> None:
    habit = _make_habit(
        session,
        habit_type=HabitType.BUILD,
        tracking_type=TrackingType.QUANTITY,
        target_value=8,
        unit="glasses",
        created_days_ago=2,
    )
    _log(session, habit, 2, amount=8)
    _log(session, habit, 1, amount=5)
    _log(session, habit, 0, amount=10)

    result = StreakService(session).compute(habit.id, today=TODAY)
    assert result.current_streak == 1
    assert result.longest_streak == 1


def test_quit_boolean_no_log_defaults_to_success(session: Session) -> None:
    habit = _make_habit(
        session, habit_type=HabitType.QUIT, tracking_type=TrackingType.BOOLEAN, created_days_ago=3
    )
    _log(session, habit, 1, completed=True)  # relapse
    # day-3, day-2, today: no logs at all -> success by convention, including today

    result = StreakService(session).compute(habit.id, today=TODAY)
    assert result.current_streak == 1
    assert result.longest_streak == 2


def test_quit_quantity_streak_uses_max_threshold(session: Session) -> None:
    habit = _make_habit(
        session,
        habit_type=HabitType.QUIT,
        tracking_type=TrackingType.QUANTITY,
        target_value=2,
        unit="cigarettes",
        created_days_ago=2,
    )
    _log(session, habit, 2, amount=1)
    _log(session, habit, 1, amount=5)
    # today: no log -> success by convention

    result = StreakService(session).compute(habit.id, today=TODAY)
    assert result.current_streak == 1
    assert result.longest_streak == 1


def test_brand_new_habit_with_no_logs_has_zero_streaks(session: Session) -> None:
    habit = _make_habit(
        session, habit_type=HabitType.BUILD, tracking_type=TrackingType.BOOLEAN, created_days_ago=0
    )
    result = StreakService(session).compute(habit.id, today=TODAY)
    assert result.current_streak == 0
    assert result.longest_streak == 0


def test_logging_today_extends_current_streak(session: Session) -> None:
    habit = _make_habit(
        session, habit_type=HabitType.BUILD, tracking_type=TrackingType.BOOLEAN, created_days_ago=2
    )
    _log(session, habit, 2, completed=True)
    _log(session, habit, 1, completed=True)
    _log(session, habit, 0, completed=True)

    result = StreakService(session).compute(habit.id, today=TODAY)
    assert result.current_streak == 3
    assert result.longest_streak == 3
