"""
Pydantic schemas for the Portfolio module.
Handles data validation and serialization.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.modules.portfolio.models import AssetType


class AssetBase(BaseModel):
    """
    Shared properties for Asset.
    """

    ticker: str = Field(min_length=1, max_length=20, pattern="^[A-Z0-9]+$")
    quantity: Annotated[Decimal, Field(gt=0)]
    avg_buy_price: Annotated[Decimal, Field(gt=0, decimal_places=2)]
    asset_type: AssetType


class AssetCreate(AssetBase):
    """
    Payload for adding an asset to a portfolio.
    """

    pass


class AssetResponse(AssetBase):
    """
    Response model for Asset.
    """

    id: int
    portfolio_id: int
    created_at: datetime

    current_price: float | None = None
    current_value: float | None = None
    pnl_percentage: float | None = None  # 'pnl' - Profit and Loss

    model_config = ConfigDict(from_attributes=True)


class PortfolioBase(BaseModel):
    """
    Shared properties for Portfolio.
    """

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class PortfolioCreate(PortfolioBase):
    """
    Payload for creating a new portfolio.
    """

    pass


class PortfolioUpdate(BaseModel):
    """
    Payload for updating a portfolio.
    All fields are optional.
    """

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class PortfolioListResponse(PortfolioBase):
    """
    Lightweight response for list views (no assets).
    """

    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PortfolioResponse(PortfolioBase):
    """
    Response model for Portfolio.
    Includes list of assets.
    """

    id: int
    user_id: int
    created_at: datetime

    total_value: float | None = None
    total_pnl_percentage: float | None = None

    assets: list[AssetResponse] = []

    model_config = ConfigDict(from_attributes=True)
