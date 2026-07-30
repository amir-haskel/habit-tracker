"""RabbitMQ adapter for the EventBus.

Uses a single topic exchange ("habits.events"); each event is published with
its ``event_type`` as the routing key. Consumers bind a queue with routing-key
patterns (e.g. "habit.*", "streak.milestone") to receive the subset they care
about.

``pika`` is an optional dependency — install with the "rabbitmq" extra. Import
of this module is deferred by callers so that InMemory-only runs (tests, local)
never require pika to be present.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

import pika

from habit_events.bus import EventBus
from habit_events.events import BaseEvent, parse_event

EXCHANGE = "habits.events"


class RabbitMQEventBus(EventBus):
    """Publisher side. Holds one connection/channel and declares the exchange."""

    def __init__(self, url: str) -> None:
        self._params = pika.URLParameters(url)
        self._connection: pika.BlockingConnection | None = None
        self._channel = None

    def _ensure_channel(self):
        if self._connection is None or self._connection.is_closed:
            self._connection = pika.BlockingConnection(self._params)
            self._channel = self._connection.channel()
            self._channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
        return self._channel

    def publish(self, event: BaseEvent) -> None:
        channel = self._ensure_channel()
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=event.event_type,
            body=event.model_dump_json(),
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
        )

    def close(self) -> None:
        if self._connection is not None and self._connection.is_open:
            self._connection.close()


def consume(
    url: str,
    queue: str,
    routing_keys: Iterable[str],
    handler: Callable[[BaseEvent], None],
) -> None:
    """Blocking consumer loop. Binds ``queue`` to ``routing_keys`` and dispatches
    each decoded event to ``handler``. Messages are ack'd only after the handler
    returns without raising, so a crash re-delivers rather than drops.
    """
    connection = pika.BlockingConnection(pika.URLParameters(url))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    channel.queue_declare(queue=queue, durable=True)
    for key in routing_keys:
        channel.queue_bind(exchange=EXCHANGE, queue=queue, routing_key=key)

    def _on_message(ch, method, properties, body):
        try:
            event = parse_event(method.routing_key, body)
            handler(event)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:  # noqa: BLE001 — requeue once for at-least-once delivery
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            raise

    channel.basic_qos(prefetch_count=10)
    channel.basic_consume(queue=queue, on_message_callback=_on_message)
    channel.start_consuming()
