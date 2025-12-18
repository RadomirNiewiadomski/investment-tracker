"""
Application configuration settings using Pydantic.
"""

from pydantic import computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application settings.
    Variables are loaded from environment variables and .env file.
    """

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    # --- App Config ---
    PROJECT_NAME: str = "Investment Tracker"
    DEBUG: bool = False
    ALLOWED_HOSTS: list[str] = ["*"]
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- Postgres Database ---
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> MultiHostUrl:
        """
        Construct the SQLAlchemy Async Database URI.
        Uses postgresql+asyncpg:// scheme.
        """
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    # --- Redis (Cache & Broker) ---
    REDIS_HOST: str
    REDIS_PORT: int = 6379

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_URL(self) -> MultiHostUrl:
        """
        Construct the Redis URI.
        """
        return MultiHostUrl.build(
            scheme="redis",
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
        )


settings = Settings()
