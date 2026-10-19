"""Event-bus provider for habit-core.

A process-wide singleton chosen by config: InMemory by default (tests, local
without a broker) or SNS when EVENT_BUS=aws. Exposed as the FastAPI dependency
``get_event_bus`` so tests can override it via dependency_overrides.
"""

from __future__ import annotations

from functools import lru_cache

from habit_events import EventBus, InMemoryEventBus

from habit_core.config import settings


@lru_cache
def _singleton() -> EventBus:
    if settings.event_bus == "aws":
        from habit_events.aws import SnsEventBus

        if not settings.sns_topic_arn:
            raise RuntimeError("EVENT_BUS=aws requires SNS_TOPIC_ARN")
        return SnsEventBus(settings.sns_topic_arn, settings.aws_region)
    return InMemoryEventBus()


def get_event_bus() -> EventBus:
    return _singleton()
