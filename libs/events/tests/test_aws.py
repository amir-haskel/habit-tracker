"""SNS publisher + SQS consumer, run against moto (no real AWS calls).

The fixture mirrors the real resources: a topic, a queue subscribed with
RawMessageDelivery=true and an event_type filter policy, and a dead-letter
queue behind a redrive policy. See docs/messaging.md.
"""

import json
from datetime import date
from types import SimpleNamespace

import boto3
import pytest
from moto import mock_aws

from habit_events import (
    HabitArchived,
    HabitCreated,
    HabitLogged,
    StreakMilestone,
    BaseEvent,
)
from habit_events.aws import SnsEventBus, consume, poll_once

REGION = "us-east-1"
FILTERED_TYPES = ["habit.created", "habit.archived", "streak.milestone"]


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)


def _subscribe(sns, sqs, topic_arn: str, queue_url: str) -> None:
    queue_arn = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=["QueueArn"])[
        "Attributes"
    ]["QueueArn"]
    sns.subscribe(
        TopicArn=topic_arn,
        Protocol="sqs",
        Endpoint=queue_arn,
        Attributes={
            "RawMessageDelivery": "true",
            "FilterPolicy": json.dumps({"event_type": FILTERED_TYPES}),
        },
    )


@pytest.fixture()
def aws():
    with mock_aws():
        sns = boto3.client("sns", region_name=REGION)
        sqs = boto3.client("sqs", region_name=REGION)

        topic_arn = sns.create_topic(Name="habit-tracker-events")["TopicArn"]
        dlq_url = sqs.create_queue(QueueName="habit-tracker-notifications-dlq")["QueueUrl"]
        dlq_arn = sqs.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=["QueueArn"])[
            "Attributes"
        ]["QueueArn"]
        # VisibilityTimeout=0 makes an undeleted message reappear immediately,
        # standing in for "the visibility timeout elapsed".
        queue_url = sqs.create_queue(
            QueueName="habit-tracker-notifications",
            Attributes={
                "VisibilityTimeout": "0",
                "RedrivePolicy": json.dumps(
                    {"deadLetterTargetArn": dlq_arn, "maxReceiveCount": "3"}
                ),
            },
        )["QueueUrl"]
        _subscribe(sns, sqs, topic_arn, queue_url)

        yield SimpleNamespace(
            sns=sns, sqs=sqs, topic_arn=topic_arn, queue_url=queue_url, dlq_url=dlq_url
        )


def _poll(aws, handler) -> int:
    return poll_once(aws.sqs, aws.queue_url, handler, wait_seconds=0)


def test_published_event_reaches_handler_as_typed_event(aws) -> None:
    bus = SnsEventBus(aws.topic_arn, REGION)
    event = HabitCreated(habit_id=1, name="Water", habit_type="build", tracking_type="quantity")
    bus.publish(event)

    received: list[BaseEvent] = []
    assert _poll(aws, received.append) == 1

    assert received == [event]
    assert isinstance(received[0], HabitCreated)


def test_message_is_raw_json_with_event_type_attribute(aws) -> None:
    SnsEventBus(aws.topic_arn, REGION).publish(StreakMilestone(habit_id=4, streak_length=7))

    message = aws.sqs.receive_message(
        QueueUrl=aws.queue_url, MessageAttributeNames=["All"], WaitTimeSeconds=0
    )["Messages"][0]

    # RawMessageDelivery: the body is the event itself, not an SNS envelope.
    assert json.loads(message["Body"])["streak_length"] == 7
    assert message["MessageAttributes"]["event_type"]["StringValue"] == "streak.milestone"


def test_event_outside_filter_policy_does_not_arrive(aws) -> None:
    bus = SnsEventBus(aws.topic_arn, REGION)
    bus.publish(HabitLogged(habit_id=1, date=date(2026, 7, 30), completed=True, goal_met=True))

    received: list[BaseEvent] = []
    assert _poll(aws, received.append) == 0
    assert received == []

    # A matching event published afterwards still flows.
    bus.publish(HabitArchived(habit_id=1))
    assert _poll(aws, received.append) == 1
    assert [e.event_type for e in received] == ["habit.archived"]


def test_message_is_deleted_after_handler_succeeds(aws) -> None:
    SnsEventBus(aws.topic_arn, REGION).publish(HabitArchived(habit_id=2))

    assert _poll(aws, lambda event: None) == 1
    # Visibility timeout is 0, so anything undeleted would be received again.
    assert _poll(aws, lambda event: None) == 0


def test_handler_failure_leaves_message_for_redelivery(aws) -> None:
    SnsEventBus(aws.topic_arn, REGION).publish(HabitArchived(habit_id=2))

    def boom(event: BaseEvent) -> None:
        raise RuntimeError("handler bug")

    assert _poll(aws, boom) == 1  # logged, not raised

    redelivered: list[BaseEvent] = []
    assert _poll(aws, redelivered.append) == 1
    assert [e.habit_id for e in redelivered] == [2]


def test_repeated_failure_ends_up_in_dead_letter_queue(aws) -> None:
    SnsEventBus(aws.topic_arn, REGION).publish(HabitArchived(habit_id=2))

    def boom(event: BaseEvent) -> None:
        raise RuntimeError("handler bug")

    for _ in range(4):  # maxReceiveCount is 3
        _poll(aws, boom)

    dead = aws.sqs.receive_message(QueueUrl=aws.dlq_url, WaitTimeSeconds=0).get("Messages", [])
    assert len(dead) == 1
    assert json.loads(dead[0]["Body"])["habit_id"] == 2


def test_one_failing_message_does_not_block_the_batch(aws) -> None:
    bus = SnsEventBus(aws.topic_arn, REGION)
    bus.publish(HabitArchived(habit_id=1))
    bus.publish(HabitArchived(habit_id=2))

    handled: list[int] = []

    def handler(event: BaseEvent) -> None:
        if event.habit_id == 1:
            raise RuntimeError("handler bug")
        handled.append(event.habit_id)

    assert _poll(aws, handler) == 2
    assert handled == [2]
    # Only the failed message comes back.
    remaining: list[int] = []
    assert _poll(aws, lambda e: remaining.append(e.habit_id)) == 1
    assert remaining == [1]


def test_event_type_falls_back_to_body_without_attribute(aws) -> None:
    event = HabitArchived(habit_id=5)
    aws.sqs.send_message(QueueUrl=aws.queue_url, MessageBody=event.model_dump_json())

    received: list[BaseEvent] = []
    assert _poll(aws, received.append) == 1
    assert received == [event]


def test_undecodable_message_is_left_in_the_queue(aws) -> None:
    aws.sqs.send_message(QueueUrl=aws.queue_url, MessageBody="not json")

    received: list[BaseEvent] = []
    assert _poll(aws, received.append) == 1
    assert received == []
    # Not deleted: it is received again (and would reach the DLQ eventually).
    assert _poll(aws, received.append) == 1


class _Stop(BaseException):
    """Ends the otherwise-infinite consume loop; not an Exception, so it escapes it."""


def test_consume_survives_client_errors_and_keeps_polling(aws, monkeypatch) -> None:
    # Point the consumer at a queue that does not exist yet: every poll raises a
    # ClientError until the "infrastructure" appears during the backoff sleep.
    late_url = "https://sqs.us-east-1.amazonaws.com/123456789012/late-queue"
    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        if len(sleeps) == 2:
            queue_url = aws.sqs.create_queue(QueueName="late-queue")["QueueUrl"]
            assert queue_url == late_url
            aws.sqs.send_message(
                QueueUrl=queue_url, MessageBody=HabitArchived(habit_id=9).model_dump_json()
            )

    monkeypatch.setattr("habit_events.aws.time", SimpleNamespace(sleep=fake_sleep))

    received: list[BaseEvent] = []

    def handler(event: BaseEvent) -> None:
        received.append(event)
        raise _Stop

    with pytest.raises(_Stop):
        consume(late_url, handler, region_name=REGION, retry_delay=1.0, max_retry_delay=60.0)

    assert sleeps == [1.0, 2.0]  # exponential backoff between failed polls
    assert [e.habit_id for e in received] == [9]
