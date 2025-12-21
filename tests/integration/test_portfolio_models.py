import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.models import User
from src.modules.portfolio.models import Asset, AssetType, Portfolio


@pytest.mark.asyncio
async def test_create_portfolio_relationship(get_db: AsyncSession, user_factory):
    """
    Test creation of portfolio and bidirectional relationship with User.
    """
    user = await user_factory("portfolio_owner@example.com")

    portfolio = Portfolio(name="Retirement Fund", description="Long term holding", user_id=user.id)
    get_db.add(portfolio)
    await get_db.commit()
    await get_db.refresh(portfolio)

    assert portfolio.id is not None
    assert portfolio.user_id == user.id

    stmt_p = select(Portfolio).where(Portfolio.user_id == user.id)
    result_p = await get_db.execute(stmt_p)
    user_portfolios = result_p.scalars().all()

    assert len(user_portfolios) == 1
    assert user_portfolios[0].name == "Retirement Fund"


@pytest.mark.asyncio
async def test_unique_portfolio_name_constraint(get_db: AsyncSession, user_factory):
    """
    Test that a user cannot have two portfolios with the same name.
    """
    user = await user_factory("unique_check@example.com")

    p1 = Portfolio(name="Crypto", user_id=user.id)
    get_db.add(p1)
    await get_db.commit()

    p2 = Portfolio(name="Crypto", user_id=user.id)
    get_db.add(p2)

    with pytest.raises(IntegrityError):
        await get_db.commit()

    await get_db.rollback()


@pytest.mark.asyncio
async def test_unique_asset_ticker_constraint(get_db: AsyncSession, user_factory):
    """
    Test that a portfolio cannot have duplicate tickers (should be aggregated).
    """
    user = await user_factory("asset_check@example.com")

    portfolio = Portfolio(name="Stocks", user_id=user.id)
    get_db.add(portfolio)
    await get_db.commit()
    await get_db.refresh(portfolio)

    a1 = Asset(
        ticker="BTC", quantity=1.5, avg_buy_price=50000.00, asset_type=AssetType.CRYPTO, portfolio_id=portfolio.id
    )
    get_db.add(a1)
    await get_db.commit()

    a2 = Asset(
        ticker="BTC", quantity=0.5, avg_buy_price=60000.00, asset_type=AssetType.CRYPTO, portfolio_id=portfolio.id
    )
    get_db.add(a2)

    with pytest.raises(IntegrityError):
        await get_db.commit()

    await get_db.rollback()


@pytest.mark.asyncio
async def test_cascade_delete_user(get_db: AsyncSession, user_factory):
    """
    Test that deleting a User automatically removes their Portfolios and Assets.
    """
    user = await user_factory("delete_me@example.com")

    portfolio = Portfolio(name="Temp", user_id=user.id)
    get_db.add(portfolio)
    await get_db.commit()

    asset = Asset(ticker="ETH", quantity=10, avg_buy_price=2000, asset_type=AssetType.CRYPTO, portfolio_id=portfolio.id)
    get_db.add(asset)
    await get_db.commit()

    assert (await get_db.get(User, user.id)) is not None
    assert (await get_db.get(Portfolio, portfolio.id)) is not None

    await get_db.delete(user)
    await get_db.commit()

    assert (await get_db.get(User, user.id)) is None
    assert (await get_db.get(Portfolio, portfolio.id)) is None
