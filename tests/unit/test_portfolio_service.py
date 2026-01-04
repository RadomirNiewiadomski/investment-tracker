"""
Unit tests for PortfolioService.
Tests business logic using mocked repository.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status

from src.core.exceptions import PermissionDeniedException
from src.modules.market_data.service import MarketDataService
from src.modules.portfolio.models import Asset, AssetType, Portfolio
from src.modules.portfolio.repository import PortfolioRepository
from src.modules.portfolio.schemas import AssetCreate, PortfolioCreate
from src.modules.portfolio.service import PortfolioService


@pytest.fixture
def mock_repo():
    """Mocks the PortfolioRepository."""
    return AsyncMock(spec=PortfolioRepository)


@pytest.fixture
def mock_market_data():
    """
    Creates a mock for MarketDataService.
    """
    return AsyncMock(spec=MarketDataService)


@pytest.fixture
def service(mock_repo, mock_market_data):
    """Creates PortfolioService with mocked dependencies."""
    return PortfolioService(mock_repo, mock_market_data)


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


@pytest.mark.asyncio
async def test_remove_asset_success(service, mock_repo):
    """
    Test removing an asset successfully.
    """
    user_id = 1
    portfolio_id = 10
    ticker = "BTC"

    mock_portfolio = Portfolio(id=portfolio_id, user_id=user_id)
    mock_asset = Asset(id=100, ticker=ticker, portfolio_id=portfolio_id)

    mock_repo.get_portfolio_by_id.return_value = mock_portfolio
    mock_repo.get_asset_by_ticker.return_value = mock_asset

    await service.remove_asset(user_id, portfolio_id, ticker)

    mock_repo.get_asset_by_ticker.assert_awaited_once_with(portfolio_id, ticker)
    mock_repo.delete_asset.assert_awaited_once_with(mock_asset)


@pytest.mark.asyncio
async def test_remove_asset_not_found(service, mock_repo):
    """
    Test removing a non-existent asset raises 404.
    """
    user_id = 1
    portfolio_id = 10
    ticker = "GHOST"

    mock_portfolio = Portfolio(id=portfolio_id, user_id=user_id)

    mock_repo.get_portfolio_by_id.return_value = mock_portfolio
    mock_repo.get_asset_by_ticker.return_value = None

    with pytest.raises(HTTPException) as exc:
        await service.remove_asset(user_id, portfolio_id, ticker)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    mock_repo.delete_asset.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_portfolio_with_valuation(service, mock_repo, mock_market_data):
    """
    Test retrieving a portfolio and calculating its value (PnL).
    Scenario:
    - User has 1 BTC bought at $20,000.
    - Current price is $50,000.
    - Expected Total Value: $50,000.
    - Expected PnL: 150%.
    """
    user_id = 1
    portfolio_id = 10

    asset = Asset(
        id=100, ticker="BTC", quantity=Decimal("1.0"), avg_buy_price=Decimal("20000.00"), asset_type=AssetType.CRYPTO
    )
    portfolio = Portfolio(id=portfolio_id, user_id=user_id, assets=[asset])

    mock_repo.get_portfolio_by_id.return_value = portfolio

    # Mock Market Data (BTC price = 50k)
    mock_market_data.get_price.return_value = 50000.0

    result = await service.get_portfolio(user_id, portfolio_id)

    mock_repo.get_portfolio_by_id.assert_awaited_once_with(portfolio_id)
    mock_market_data.get_price.assert_awaited_once_with("BTC")

    assert result.assets[0].current_price == 50000.0
    assert result.assets[0].current_value == 50000.0
    assert result.assets[0].pnl_percentage == 150.0
    assert result.total_value == 50000.0
    assert result.total_pnl_percentage == 150.0


@pytest.mark.asyncio
async def test_get_portfolio_not_found(service, mock_repo):
    """
    Test getting a non-existent portfolio raises 404.
    """
    mock_repo.get_portfolio_by_id.return_value = None

    with pytest.raises(HTTPException) as exc:
        await service.get_portfolio(user_id=1, portfolio_id=999)

    assert exc.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_portfolio_permission_denied(service, mock_repo):
    """
    Test accessing someone else's portfolio raises 403.
    """
    wrong_user_id = 1
    owner_id = 2
    portfolio = Portfolio(id=10, user_id=owner_id)

    mock_repo.get_portfolio_by_id.return_value = portfolio

    with pytest.raises(PermissionDeniedException):
        await service.get_portfolio(wrong_user_id, portfolio_id=10)


@pytest.mark.asyncio
async def test_create_daily_snapshots_calculates_pnl_correctly():
    """
    Test that daily snapshot logic correctly calculates Total Value and PnL %.
    Scenario:
      - Asset: BTC
      - Quantity: 2.0
      - Avg Buy Price: 20,000 USD (Total Cost = 40,000)
      - Current Price: 30,000 USD (Total Value = 60,000)
      - Expected PnL: ((60k - 40k) / 40k) * 100 = 50%
    """
    mock_repo = AsyncMock()
    mock_market_data = AsyncMock()
    service = PortfolioService(mock_repo, mock_market_data)

    mock_asset = MagicMock(spec=Asset)
    mock_asset.ticker = "BTC"
    mock_asset.quantity = Decimal("2.0")
    mock_asset.avg_buy_price = Decimal("20000.00")

    mock_portfolio = MagicMock(spec=Portfolio)
    mock_portfolio.id = 1
    mock_portfolio.assets = [mock_asset]

    mock_repo.get_all_portfolios_system.return_value = [mock_portfolio]

    mock_market_data.get_price.return_value = 30000.00

    count = await service.create_daily_snapshots()

    assert count == 1

    mock_repo.create_portfolio_history.assert_called_once()

    call_args = mock_repo.create_portfolio_history.call_args[0][0]

    assert call_args.portfolio_id == 1
    assert call_args.date == date.today()
    assert call_args.total_value == Decimal("60000.00")
    assert call_args.total_pnl_percentage == Decimal("50.0")

    mock_repo.commit.assert_awaited_once()
