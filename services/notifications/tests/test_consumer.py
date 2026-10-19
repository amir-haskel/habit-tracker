import pytest

from notifications import consumer
from notifications.config import settings


def test_consumer_requires_queue_url(monkeypatch) -> None:
    monkeypatch.setattr(settings, "sqs_queue_url", "")
    with pytest.raises(RuntimeError, match="SQS_QUEUE_URL"):
        consumer.start_consumer_thread()
