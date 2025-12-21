"""
Unit tests for PortfolioService.
Tests business logic using mocked repository.
"""

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.modules.portfolio.models import Asset, AssetType, Portfolio
from src.modules.portfolio.schemas import AssetCreate, PortfolioCreate
from src.modules.portfolio.service import PortfolioService


@pytest.fixture
def mock_repo():
    """Mocks the PortfolioRepository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def service(mock_repo):
    """Creates PortfolioService with mocked repo."""
    return PortfolioService(mock_repo)


@pytest.mark.asyncio
async def test_create_portfolio_success(service, mock_repo):
    """
    Test creating a portfolio successfully when name is unique.
    """
    user_id = 1
    schema = PortfolioCreate(name="My Crypto", description="Test")
    mock_repo.get_all_by_user.return_value = []
    mock_repo.create_portfolio.return_value = Portfolio(id=1, user_id=user_id, **schema.model_dump())

    result = await service.create_portfolio(user_id, schema)

    assert result.name == "My Crypto"
    mock_repo.create_portfolio.assert_awaited_once_with(user_id=user_id, name="My Crypto", description="Test")


@pytest.mark.asyncio
async def test_create_portfolio_duplicate_name(service, mock_repo):
    user_id = 1
    schema = PortfolioCreate(name="Duplicate", description="Test")
    mock_repo.get_all_by_user.return_value = [Portfolio(id=2, user_id=user_id, name="Duplicate")]

    with pytest.raises(HTTPException) as exc:
        await service.create_portfolio(user_id, schema)

    assert exc.value.status_code == 409
    assert "already exists" in exc.value.detail


@pytest.mark.asyncio
async def test_add_asset_new_creation(service, mock_repo):
    """
    Test adding an asset that DOES NOT exist in the portfolio.
    Should create a new entry.
    """
    user_id = 1
    portfolio_id = 10
    asset_in = AssetCreate(
        ticker="BTC", quantity=Decimal("1.0"), avg_buy_price=Decimal("50000"), asset_type=AssetType.CRYPTO
    )

    mock_portfolio = Portfolio(id=portfolio_id, user_id=user_id)
    mock_repo.get_portfolio_by_id.return_value = mock_portfolio

    mock_repo.get_asset_by_ticker.return_value = None

    created_asset = Asset(id=100, portfolio_id=portfolio_id, **asset_in.model_dump())
    mock_repo.create_asset.return_value = created_asset

    result = await service.add_asset_to_portfolio(user_id, portfolio_id, asset_in)

    assert result.ticker == "BTC"
    mock_repo.create_asset.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_asset_aggregation(service, mock_repo):
    """
    Test adding an asset that ALREADY exists.
    Should update quantity and calculate Weighted Average Price.
    """
    user_id = 1
    portfolio_id = 10

    existing_asset = Asset(
        id=100, ticker="BTC", quantity=Decimal("1.0"), avg_buy_price=Decimal("20000.00"), portfolio_id=portfolio_id
    )

    asset_in = AssetCreate(
        ticker="BTC", quantity=Decimal("1.0"), avg_buy_price=Decimal("40000.00"), asset_type=AssetType.CRYPTO
    )

    mock_portfolio = Portfolio(id=portfolio_id, user_id=user_id)
    mock_repo.get_portfolio_by_id.return_value = mock_portfolio
    mock_repo.get_asset_by_ticker.return_value = existing_asset

    result = await service.add_asset_to_portfolio(user_id, portfolio_id, asset_in)

    assert result.quantity == Decimal("2.0")
    assert result.avg_buy_price == Decimal("30000.00")

    mock_repo.commit.assert_awaited_once()
    mock_repo.create_asset.assert_not_awaited()
