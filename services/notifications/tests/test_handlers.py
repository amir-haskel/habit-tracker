from datetime import date

from habit_events import HabitArchived, HabitCreated, HabitLogged, StreakMilestone
from sqlalchemy.orm import Session

from notifications.handlers import dispatch
from notifications.models import HabitRef, Notification
from notifications.repository import NotificationRepository


def test_habit_created_builds_read_model_and_notification(session: Session) -> None:
    dispatch(
        session,
        HabitCreated(habit_id=1, name="Drink water", habit_type="build", tracking_type="quantity"),
    )

    ref = session.get(HabitRef, 1)
    assert ref is not None and ref.name == "Drink water"

    notes = NotificationRepository(session).list()
    assert len(notes) == 1
    assert notes[0].kind == "habit_created"
    assert "Drink water" in notes[0].title


def test_streak_milestone_uses_read_model_name(session: Session) -> None:
    dispatch(
        session,
        HabitCreated(habit_id=2, name="Meditate", habit_type="build", tracking_type="boolean"),
    )
    dispatch(session, StreakMilestone(habit_id=2, streak_length=7))

    milestone = [n for n in NotificationRepository(session).list() if n.kind == "streak_milestone"]
    assert len(milestone) == 1
    assert "Meditate" in milestone[0].body
    assert "7-day streak" in milestone[0].title


def test_streak_milestone_without_ref_falls_back(session: Session) -> None:
    dispatch(session, StreakMilestone(habit_id=99, streak_length=30))
    milestone = NotificationRepository(session).list()[0]
    assert "habit #99" in milestone.body


def test_habit_archived_marks_read_model(session: Session) -> None:
    dispatch(
        session,
        HabitCreated(habit_id=3, name="Run", habit_type="build", tracking_type="boolean"),
    )
    dispatch(session, HabitArchived(habit_id=3))
    ref = session.get(HabitRef, 3)
    assert ref is not None and ref.archived is True


def test_habit_logged_is_ignored(session: Session) -> None:
    # No handler registered for habit.logged — dispatch is a no-op, no rows.
    dispatch(session, HabitLogged(habit_id=1, date=date(2026, 7, 30), completed=True, goal_met=True))
    assert session.query(Notification).count() == 0
