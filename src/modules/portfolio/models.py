"""
Database models for the Portfolio module.
"""

import enum
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models import TimestampMixin, UUIDMixin

# to avoid Circular Imports problem for mypy and IDE
if TYPE_CHECKING:
    from src.modules.auth.models import User


class AssetType(str, enum.Enum):
    """
    Type of the asset.
    Stored as string in DB for better compatibility.
    """

    CRYPTO = "CRYPTO"
    STOCK = "STOCK"
    ETF = "ETF"
    FOREX = "FOREX"
    COMMODITY = "COMMODITY"


class Portfolio(Base, UUIDMixin, TimestampMixin):
    """
    Represents a collection of investments owned by a user.
    """

    __tablename__ = "portfolios"
    __allow_unmapped__ = True

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="portfolios")
    assets: Mapped[list["Asset"]] = relationship("Asset", back_populates="portfolio", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_portfolio_user_name"),)

    # --- TRANSIENT FIELDS (Not stored in DB, used for runtime valuation) ---
    total_value: float | None = None
    total_pnl_percentage: float | None = None

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"


class Asset(Base, UUIDMixin, TimestampMixin):
    """
    Represents a specific holding (position) within a portfolio.
    """

    __tablename__ = "assets"
    __allow_unmapped__ = True

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    ticker: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. BTC, AAPL
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    avg_buy_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    asset_type: Mapped[AssetType] = mapped_column(String(20), nullable=False)

    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    portfolio: Mapped["Portfolio"] = relationship("Portfolio", back_populates="assets")

    __table_args__ = (UniqueConstraint("portfolio_id", "ticker", name="uq_asset_portfolio_ticker"),)

    # --- TRANSIENT FIELDS (Not stored in DB, used for runtime valuation) ---
    current_price: float | None = None
    current_value: float | None = None
    pnl_percentage: float | None = None

    def __str__(self) -> str:
        return f"{self.ticker} - {self.quantity}"
