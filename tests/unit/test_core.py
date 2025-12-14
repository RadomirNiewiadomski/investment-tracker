"""
Unit tests for core infrastructure logic.
"""

from sqlalchemy.orm import Mapped, mapped_column

from src.core.config import Settings
from src.core.database import Base


def test_config_sqlalchemy_uri_generation() -> None:
    """
    Test that SQLALCHEMY_DATABASE_URI is correctly computed from components.
    """
    settings = Settings(
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="secret_password",
        POSTGRES_SERVER="localhost",
        POSTGRES_PORT=5432,
        POSTGRES_DB="testdb",
        REDIS_HOST="localhost",
        REDIS_PORT=6379,
        PROJECT_NAME="Test",
        API_V1_STR="/api",
        SECRET_KEY="secret",
    )

    uri = str(settings.SQLALCHEMY_DATABASE_URI)

    assert uri == "postgresql+asyncpg://testuser:secret_password@localhost:5432/testdb"


def test_database_tablename_generation() -> None:
    """
    Test automatic snake_case table name generation from class name.
    """

    # Create some temporary models
    class User(Base):
        id: Mapped[int] = mapped_column(primary_key=True)

    class UserPortfolio(Base):
        id: Mapped[int] = mapped_column(primary_key=True)

    class AssetManager(Base):
        id: Mapped[int] = mapped_column(primary_key=True)

    assert User.__tablename__ == "user"
    assert UserPortfolio.__tablename__ == "user_portfolio"
    assert AssetManager.__tablename__ == "asset_manager"
