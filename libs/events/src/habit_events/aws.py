"""AWS adapter for the EventBus: SNS for publishing, SQS for consuming.

Publisher: every event goes to one SNS topic as its JSON body, with the event's
``event_type`` attached as a String message attribute. SNS filter policies match
on attributes (not the body), which is how each queue subscription picks the
event types it cares about.

Consumer: a long-polling SQS loop. The queue is subscribed to the topic with
RawMessageDelivery=true, so the message body is the event JSON itself and the
``event_type`` attribute arrives as an SQS message attribute. A message is
deleted only after its handler succeeds; on failure it is left alone so SQS
redelivers it after the visibility timeout, and the queue's redrive policy
moves it to a dead-letter queue after maxReceiveCount attempts.

Credentials come from boto3's default chain (task role on ECS), and the standard
AWS_ENDPOINT_URL env var points boto3 at LocalStack locally. ``boto3`` is an
optional dependency — install with the "aws" extra. Import of this module is
deferred by callers so InMemory-only runs (tests, local) never require it.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from habit_events.bus import EventBus
from habit_events.events import BaseEvent, parse_event

logger = logging.getLogger(__name__)

EVENT_TYPE_ATTRIBUTE = "event_type"


class SnsEventBus(EventBus):
    """Publisher side. Publishes each event to a single SNS topic."""

    def __init__(self, topic_arn: str, region_name: str | None = None) -> None:
        self._topic_arn = topic_arn
        self._client = boto3.client("sns", region_name=region_name)

    def publish(self, event: BaseEvent) -> None:
        self._client.publish(
            TopicArn=self._topic_arn,
            Message=event.model_dump_json(),
            MessageAttributes={
                EVENT_TYPE_ATTRIBUTE: {"DataType": "String", "StringValue": event.event_type}
            },
        )


def _event_type(message: dict[str, Any]) -> str:
    """The message's event type: the message attribute, else the body's field."""
    attribute = message.get("MessageAttributes", {}).get(EVENT_TYPE_ATTRIBUTE)
    if attribute is not None:
        return attribute["StringValue"]
    return json.loads(message["Body"])["event_type"]


def poll_once(
    client: Any,
    queue_url: str,
    handler: Callable[[BaseEvent], None],
    *,
    wait_seconds: int = 20,
) -> int:
    """Receive one batch (long poll) and dispatch it. Returns messages received.

    Each message is deleted only after its handler succeeds. A handler (or
    decode) failure is logged and the message is left in the queue — it becomes
    visible again after the visibility timeout and, after maxReceiveCount
    receives, lands in the dead-letter queue. One bad message never blocks the
    rest of the batch.
    """
    response = client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=wait_seconds,
        MessageAttributeNames=[EVENT_TYPE_ATTRIBUTE],
    )
    messages = response.get("Messages", [])
    for message in messages:
        try:
            event = parse_event(_event_type(message), message["Body"])
            handler(event)
        except Exception:  # noqa: BLE001
            # Leave the message undeleted for redelivery/DLQ, but keep the
            # consumer alive — a handler bug must not crash-loop the service.
            logger.exception("Handler failed for message_id=%s; leaving it in the queue", message.get("MessageId"))
            continue
        client.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
    return len(messages)


def consume(
    queue_url: str,
    handler: Callable[[BaseEvent], None],
    *,
    region_name: str | None = None,
    retry_delay: float = 3.0,
    max_retry_delay: float = 60.0,
) -> None:
    """Resilient blocking consumer loop; never returns.

    Calls ``poll_once`` forever. Client and connection errors (queue not there
    yet, throttling, network blip, expired credentials) are logged and retried
    with exponential backoff capped at ``max_retry_delay``; the delay resets
    after a successful poll.
    """
    client = boto3.client("sqs", region_name=region_name)
    delay = retry_delay
    logger.info("Consuming queue=%s", queue_url)
    while True:
        try:
            poll_once(client, queue_url, handler)
            delay = retry_delay
        except (BotoCoreError, ClientError) as exc:
            logger.warning("SQS error (%s); retrying in %ss", exc, delay)
            time.sleep(delay)
            delay = min(delay * 2, max_retry_delay)
        except Exception:  # noqa: BLE001
            logger.exception("Unexpected consumer error; retrying in %ss", delay)
            time.sleep(delay)
            delay = min(delay * 2, max_retry_delay)
