from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./habit_core.db"

    # Event bus: "memory" (default, no broker) or "rabbitmq".
    event_bus: str = "memory"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"


settings = Settings()
