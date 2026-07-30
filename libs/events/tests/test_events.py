from datetime import date

from habit_events import (
    HABIT_LOGGED,
    HabitCreated,
    HabitLogged,
    InMemoryEventBus,
    parse_event,
)


def test_in_memory_bus_records_published_events() -> None:
    bus = InMemoryEventBus()
    event = HabitCreated(habit_id=1, name="Water", habit_type="build", tracking_type="quantity")
    bus.publish(event)
    assert bus.published == [event]


def test_in_memory_bus_dispatches_to_subscribers() -> None:
    bus = InMemoryEventBus()
    received: list[int] = []
    bus.subscribe(HABIT_LOGGED, lambda e: received.append(e.habit_id))

    bus.publish(HabitLogged(habit_id=7, date=date(2026, 7, 30), completed=True, goal_met=True))
    # A different event type must not reach this subscriber.
    bus.publish(HabitCreated(habit_id=9, name="X", habit_type="build", tracking_type="boolean"))

    assert received == [7]


def test_parse_event_round_trip() -> None:
    original = HabitLogged(habit_id=3, date=date(2026, 7, 30), value=5.0, goal_met=False)
    decoded = parse_event(original.event_type, original.model_dump_json())
    assert isinstance(decoded, HabitLogged)
    assert decoded.habit_id == 3
    assert decoded.value == 5.0


def test_parse_unknown_event_raises() -> None:
    try:
        parse_event("nope.unknown", b"{}")
    except ValueError as exc:
        assert "Unknown event_type" in str(exc)
    else:
        raise AssertionError("expected ValueError")
