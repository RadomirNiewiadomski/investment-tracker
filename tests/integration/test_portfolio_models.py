import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.models import User
from src.modules.portfolio.models import Asset, AssetType, Portfolio


@pytest.mark.asyncio
async def test_create_portfolio_relationship(db_session: AsyncSession, user_factory):
    """
    Test creation of portfolio and bidirectional relationship with User.
    """
    user = await user_factory("portfolio_owner@example.com")

    portfolio = Portfolio(name="Retirement Fund", description="Long term holding", user_id=user.id)
    db_session.add(portfolio)
    await db_session.commit()
    await db_session.refresh(portfolio)

    assert portfolio.id is not None
    assert portfolio.user_id == user.id

    stmt_p = select(Portfolio).where(Portfolio.user_id == user.id)
    result_p = await db_session.execute(stmt_p)
    user_portfolios = result_p.scalars().all()

    assert len(user_portfolios) == 1
    assert user_portfolios[0].name == "Retirement Fund"


@pytest.mark.asyncio
async def test_unique_portfolio_name_constraint(db_session: AsyncSession, user_factory):
    """
    Test that a user cannot have two portfolios with the same name.
    """
    user = await user_factory("unique_check@example.com")

    p1 = Portfolio(name="Crypto", user_id=user.id)
    db_session.add(p1)
    await db_session.commit()

    p2 = Portfolio(name="Crypto", user_id=user.id)
    db_session.add(p2)

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_unique_asset_ticker_constraint(db_session: AsyncSession, user_factory):
    """
    Test that a portfolio cannot have duplicate tickers (should be aggregated).
    """
    user = await user_factory("asset_check@example.com")

    portfolio = Portfolio(name="Stocks", user_id=user.id)
    db_session.add(portfolio)
    await db_session.commit()
    await db_session.refresh(portfolio)

    a1 = Asset(
        ticker="BTC", quantity=1.5, avg_buy_price=50000.00, asset_type=AssetType.CRYPTO, portfolio_id=portfolio.id
    )
    db_session.add(a1)
    await db_session.commit()

    a2 = Asset(
        ticker="BTC", quantity=0.5, avg_buy_price=60000.00, asset_type=AssetType.CRYPTO, portfolio_id=portfolio.id
    )
    db_session.add(a2)

    with pytest.raises(IntegrityError):
        await db_session.commit()

    await db_session.rollback()


@pytest.mark.asyncio
async def test_cascade_delete_user(db_session: AsyncSession, user_factory):
    """
    Test that deleting a User automatically removes their Portfolios and Assets.
    """
    user = await user_factory("delete_me@example.com")

    portfolio = Portfolio(name="Temp", user_id=user.id)
    db_session.add(portfolio)
    await db_session.commit()

    asset = Asset(ticker="ETH", quantity=10, avg_buy_price=2000, asset_type=AssetType.CRYPTO, portfolio_id=portfolio.id)
    db_session.add(asset)
    await db_session.commit()

    assert (await db_session.get(User, user.id)) is not None
    assert (await db_session.get(Portfolio, portfolio.id)) is not None

    await db_session.delete(user)
    await db_session.commit()

    assert (await db_session.get(User, user.id)) is None
    assert (await db_session.get(Portfolio, portfolio.id)) is None
