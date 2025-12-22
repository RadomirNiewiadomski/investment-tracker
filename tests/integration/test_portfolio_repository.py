"""
Integration tests for PortfolioRepository.
Verifies database operations for Portfolios and Assets using a real DB session.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.portfolio.models import Asset, AssetType
from src.modules.portfolio.repository import PortfolioRepository


@pytest.mark.asyncio
async def test_repository_create_and_get_portfolio(db_session: AsyncSession, user_factory):
    """
    Test creating a new portfolio via repository and retrieving it by ID.
    Ensures that data persistence works correctly.
    """
    repo = PortfolioRepository(db_session)
    user = await user_factory("repo_test@example.com")

    new_portfolio = await repo.create_portfolio(user_id=user.id, name="My Repository Fund", description="Testing repo")

    assert new_portfolio.id is not None
    assert new_portfolio.name == "My Repository Fund"
    assert new_portfolio.user_id == user.id

    fetched = await repo.get_portfolio_by_id(new_portfolio.id)

    assert fetched is not None
    assert fetched.id == new_portfolio.id
    assert fetched.description == "Testing repo"


@pytest.mark.asyncio
async def test_repository_list_user_portfolios(db_session: AsyncSession, user_factory):
    """
    Test retrieving all portfolios belonging to a specific user.
    Should return a list of Portfolio objects.
    """
    repo = PortfolioRepository(db_session)
    user = await user_factory("list_test@example.com")

    await repo.create_portfolio(user.id, "Portfolio A")
    await repo.create_portfolio(user.id, "Portfolio B")

    portfolios = await repo.get_all_by_user(user.id)

    assert len(portfolios) == 2
    names = {p.name for p in portfolios}
    assert "Portfolio A" in names
    assert "Portfolio B" in names


@pytest.mark.asyncio
async def test_repository_update_portfolio(db_session: AsyncSession, user_factory):
    """
    Test updating an existing portfolio.
    """
    repo = PortfolioRepository(db_session)
    user = await user_factory("update_test@example.com")
    portfolio = await repo.create_portfolio(user.id, "Old Name", "Old Desc")

    updated = await repo.update_portfolio(portfolio, name="New Name")

    assert updated.name == "New Name"
    assert updated.description == "Old Desc"
    assert updated.id == portfolio.id


@pytest.mark.asyncio
async def test_repository_delete_portfolio(db_session: AsyncSession, user_factory):
    """
    Test deleting a portfolio.
    Verifies that the portfolio is removed from the database.
    """
    repo = PortfolioRepository(db_session)
    user = await user_factory("delete_test@example.com")
    portfolio = await repo.create_portfolio(user.id, "To Delete")

    await repo.delete_portfolio(portfolio)

    fetched = await repo.get_portfolio_by_id(portfolio.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_repository_delete_asset(db_session: AsyncSession, user_factory):
    """
    Test deleting a specific asset from the repository.
    """
    repo = PortfolioRepository(db_session)
    user = await user_factory("repo_asset_del@example.com")
    portfolio = await repo.create_portfolio(user.id, "Asset Delete Test")

    asset = Asset(ticker="SOL", quantity=10, avg_buy_price=20, asset_type=AssetType.CRYPTO, portfolio_id=portfolio.id)
    created_asset = await repo.create_asset(asset)

    await repo.delete_asset(created_asset)

    fetched_asset = await repo.get_asset_by_ticker(portfolio.id, "SOL")
    assert fetched_asset is None

    fetched_portfolio = await repo.get_portfolio_by_id(portfolio.id)
    assert fetched_portfolio is not None
