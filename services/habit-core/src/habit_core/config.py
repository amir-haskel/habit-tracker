from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./habit_core.db"

    # Event bus: "memory" (default, no broker) or "aws" (publish to SNS).
    # Credentials and AWS_ENDPOINT_URL (LocalStack) come from boto3's own chain.
    event_bus: str = "memory"
    sns_topic_arn: str = ""
    aws_region: str | None = None


settings = Settings()
