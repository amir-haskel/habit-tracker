from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    # Validation errors must not echo input values (DB_PASSWORD) into logs.
    model_config = SettingsConfigDict(hide_input_in_errors=True)

    # Precedence: an explicit DATABASE_URL wins; else, if DB_HOST is set, the URL
    # is built from the DB_* components below (AWS: ECS injects them separately,
    # the password from Secrets Manager); else the SQLite default. After
    # validation, `database_url` is always the final URL string.
    database_url: str = "sqlite:///./habit_core.db"
    db_host: str = ""
    db_port: int = 5432
    db_name: str = ""
    db_user: str = ""
    # SecretStr keeps it out of reprs and pydantic validation-error messages.
    db_password: SecretStr = SecretStr("")
    # e.g. "require" for RDS. Empty = no sslmode in the URL.
    db_sslmode: str = ""

    # Event bus: "memory" (default, no broker) or "aws" (publish to SNS).
    # Credentials and AWS_ENDPOINT_URL (LocalStack) come from boto3's own chain.
    event_bus: str = "memory"
    sns_topic_arn: str = ""
    aws_region: str | None = None

    @model_validator(mode="after")
    def _build_database_url(self) -> "Settings":
        if "database_url" in self.model_fields_set or not self.db_host:
            return self
        required = {"DB_NAME": self.db_name, "DB_USER": self.db_user, "DB_PASSWORD": self.db_password.get_secret_value()}
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"DB_HOST is set but missing: {', '.join(missing)}")
        url = URL.create(
            "postgresql+psycopg",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"sslmode": self.db_sslmode} if self.db_sslmode else {},
        )
        # hide_password=False: the engine needs the real password (escaped by SQLAlchemy).
        self.database_url = url.render_as_string(hide_password=False)
        return self


settings = Settings()
