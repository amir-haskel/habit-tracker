"""EventBus abstraction.

Business code depends only on this interface, never on a concrete broker. That
keeps the broker a swappable detail: InMemoryEventBus for tests and local runs,
SnsEventBus (SNS publish, SQS consume) on AWS and in the LocalStack compose
stack — none of which the service/handler code needs to know about.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable

from habit_events.events import BaseEvent

Handler = Callable[[BaseEvent], None]


class EventBus(ABC):
    @abstractmethod
    def publish(self, event: BaseEvent) -> None:
        """Publish a domain event. Fire-and-forget from the caller's view."""


class InMemoryEventBus(EventBus):
    """Synchronous in-process bus. Publishing invokes subscribers immediately.

    Used by tests (assert on ``published``) and as a no-broker local default.
    """

    def __init__(self) -> None:
        self.published: list[BaseEvent] = []
        self._subscribers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, event: BaseEvent) -> None:
        self.published.append(event)
        for handler in self._subscribers[event.event_type]:
            handler(event)
