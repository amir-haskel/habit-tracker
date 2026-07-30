"""RabbitMQ consumer wiring.

Can run two ways:
  * embedded — ``start_consumer_thread()`` is called from the API's lifespan so
    a single process owns the (SQLite) DB. Simplest for this phase.
  * standalone — ``python -m notifications.consumer`` runs a dedicated consumer
    process. Split it out like this once the store moves to Postgres and you
    want to scale consumption independently of the API.
"""

from __future__ import annotations

import threading

from habit_events import BaseEvent

from notifications.config import settings
from notifications.db import Base, SessionLocal, engine
from notifications.handlers import ROUTING_KEYS, dispatch


def _handle(event: BaseEvent) -> None:
    db = SessionLocal()
    try:
        dispatch(db, event)
    finally:
        db.close()


def run_consumer() -> None:
    """Blocking consume loop against RabbitMQ."""
    from habit_events.rabbitmq import consume

    consume(settings.rabbitmq_url, settings.consumer_queue, ROUTING_KEYS, _handle)


def start_consumer_thread() -> threading.Thread:
    thread = threading.Thread(target=run_consumer, name="notif-consumer", daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    run_consumer()
