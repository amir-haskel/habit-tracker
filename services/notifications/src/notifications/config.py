from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./notifications.db"

    # "memory" (tests/local) or "rabbitmq". When "rabbitmq", the API process
    # starts a background consumer thread on startup.
    event_bus: str = "memory"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    # Queue name this service consumes from (durable, so events buffer while down).
    consumer_queue: str = "notifications"


settings = Settings()
