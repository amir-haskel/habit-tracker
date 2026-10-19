from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./notifications.db"

    # "memory" (tests/local) or "aws". When "aws", the API process starts a
    # background SQS consumer thread on startup. Credentials and
    # AWS_ENDPOINT_URL (LocalStack) come from boto3's own chain.
    event_bus: str = "memory"
    # URL of the SQS queue this service consumes from (subscribed to the SNS topic).
    sqs_queue_url: str = ""
    aws_region: str | None = None


settings = Settings()
