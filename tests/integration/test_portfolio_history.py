"""
Integration tests for Portfolio History logic.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.portfolio.models import PortfolioHistory
from src.modules.portfolio.repository import PortfolioRepository


@pytest.mark.asyncio
async def test_snapshot_upsert_flow(db_session: AsyncSession, user_factory):
    """
    End-to-end test for creating snapshots.
    Verifies that saving a snapshot for the same day twice
    UPDATES the existing record instead of creating a duplicate or error.
    """
    user = await user_factory("history_tester@example.com")

    repo = PortfolioRepository(db_session)
    portfolio = await repo.create_portfolio(user_id=user.id, name="Snapshot Portfolio")

    test_date = date.today()

    history_entry_1 = PortfolioHistory(
        date=test_date, total_value=Decimal("1000.00"), total_pnl_percentage=Decimal("10.0"), portfolio_id=portfolio.id
    )

    await repo.create_portfolio_history(history_entry_1)
    await db_session.commit()

    stmt = select(PortfolioHistory).where(PortfolioHistory.portfolio_id == portfolio.id)
    result = await db_session.execute(stmt)
    history_in_db = result.scalars().all()

    assert len(history_in_db) == 1
    assert history_in_db[0].total_value == Decimal("1000.00")
    assert history_in_db[0].date == test_date

    history_entry_2 = PortfolioHistory(
        date=test_date,  # Same date
        portfolio_id=portfolio.id,  # Same portfolio
        total_value=Decimal("2500.00"),  # New value
        total_pnl_percentage=Decimal("25.0"),
    )

    await repo.create_portfolio_history(history_entry_2)
    await db_session.commit()

    db_session.expire_all()

    result_after = await db_session.execute(stmt)
    history_final = result_after.scalars().all()

    assert len(history_final) == 1

    # Value should be updated
    assert history_final[0].total_value == Decimal("2500.00")
    assert history_final[0].total_pnl_percentage == Decimal("25.0")
