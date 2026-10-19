import pytest
from habit_events import InMemoryEventBus

from habit_core import events
from habit_core.config import settings


@pytest.fixture(autouse=True)
def fresh_singleton():
    events._singleton.cache_clear()
    yield
    events._singleton.cache_clear()


def test_defaults_to_in_memory_bus() -> None:
    assert isinstance(events.get_event_bus(), InMemoryEventBus)


def test_aws_bus_requires_topic_arn(monkeypatch) -> None:
    monkeypatch.setattr(settings, "event_bus", "aws")
    monkeypatch.setattr(settings, "sns_topic_arn", "")
    with pytest.raises(RuntimeError, match="SNS_TOPIC_ARN"):
        events.get_event_bus()


def test_aws_bus_is_sns_publisher(monkeypatch) -> None:
    pytest.importorskip("boto3")
    from habit_events.aws import SnsEventBus

    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.setattr(settings, "event_bus", "aws")
    monkeypatch.setattr(settings, "sns_topic_arn", "arn:aws:sns:us-east-1:123456789012:t")
    monkeypatch.setattr(settings, "aws_region", "us-east-1")
    assert isinstance(events.get_event_bus(), SnsEventBus)
