from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from habit_core.models.habit import Habit, HabitType, TrackingType
from habit_core.schemas.habit_log import HabitLogCreate
from habit_core.services.logging_service import LoggingService
from habit_core.services.stats_service import StatsService

TODAY = date.today()


def _make_habit(
    session: Session,
    *,
    habit_type: HabitType,
    tracking_type: TrackingType,
    created_days_ago: int,
) -> Habit:
    habit = Habit(
        name="Test habit",
        habit_type=habit_type,
        tracking_type=tracking_type,
        target_value=2 if tracking_type == TrackingType.QUANTITY else None,
        unit="units" if tracking_type == TrackingType.QUANTITY else None,
        created_at=datetime.now(timezone.utc) - timedelta(days=created_days_ago),
    )
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


def _log(session: Session, habit: Habit, days_ago: int, **kwargs) -> None:
    LoggingService(session).log(habit.id, HabitLogCreate(date=TODAY - timedelta(days=days_ago), **kwargs))


def test_build_habit_completion_rate_and_window_clipping(session: Session) -> None:
    habit = _make_habit(
        session, habit_type=HabitType.BUILD, tracking_type=TrackingType.BOOLEAN, created_days_ago=10
    )
    for days_ago in [6, 5, 4, 2, 1, 0]:
        _log(session, habit, days_ago, completed=True)
    _log(session, habit, 3, completed=False)
    # days -10..-7 (4 days) have no log at all -> failure by build convention

    results = {r.window_days: r for r in StatsService(session).completion_rates(habit.id, today=TODAY)}

    seven = results[7]
    assert seven.scheduled_days == 7
    assert seven.successful_days == 6
    assert seven.completion_rate == 6 / 7

    # habit only existed 11 days, so 30- and 90-day windows both clip to the same 11 days
    thirty = results[30]
    ninety = results[90]
    assert thirty.scheduled_days == 11
    assert thirty.successful_days == 6
    assert thirty.completion_rate == 6 / 11
    assert (ninety.scheduled_days, ninety.successful_days, ninety.completion_rate) == (
        thirty.scheduled_days,
        thirty.successful_days,
        thirty.completion_rate,
    )


def test_quit_habit_no_log_counts_as_success_in_rate(session: Session) -> None:
    habit = _make_habit(
        session, habit_type=HabitType.QUIT, tracking_type=TrackingType.BOOLEAN, created_days_ago=5
    )
    _log(session, habit, 2, completed=True)  # one relapse
    # every other day (including today) has no log -> success by quit convention

    results = {r.window_days: r for r in StatsService(session).completion_rates(habit.id, today=TODAY)}
    seven = results[7]
    assert seven.scheduled_days == 6  # clipped to habit lifetime (created 5 days ago)
    assert seven.successful_days == 5
    assert seven.completion_rate == 5 / 6


def test_habit_with_no_history_has_zero_rate(session: Session) -> None:
    habit = _make_habit(
        session, habit_type=HabitType.BUILD, tracking_type=TrackingType.BOOLEAN, created_days_ago=0
    )
    results = StatsService(session).completion_rates(habit.id, today=TODAY)
    for r in results:
        assert r.scheduled_days == 0
        assert r.successful_days == 0
        assert r.completion_rate == 0.0
