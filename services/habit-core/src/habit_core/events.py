"""Event-bus provider for habit-core.

A process-wide singleton chosen by config: InMemory by default (tests, local
without a broker) or RabbitMQ when EVENT_BUS=rabbitmq. Exposed as the FastAPI
dependency ``get_event_bus`` so tests can override it via dependency_overrides.
"""

from __future__ import annotations

from functools import lru_cache

from habit_events import EventBus, InMemoryEventBus

from habit_core.config import settings


@lru_cache
def _singleton() -> EventBus:
    if settings.event_bus == "rabbitmq":
        from habit_events.rabbitmq import RabbitMQEventBus

        return RabbitMQEventBus(settings.rabbitmq_url)
    return InMemoryEventBus()


def get_event_bus() -> EventBus:
    return _singleton()
