"""
Integration tests for Portfolio History API endpoints.
Tests retrieval of historical data created by background workers.
"""

from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_password_hash
from src.modules.auth.models import User
from src.modules.portfolio.models import PortfolioHistory
from src.modules.portfolio.repository import PortfolioRepository


@pytest.mark.asyncio
async def test_get_portfolio_history_api(client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession):
    """
    Test GET /api/v1/portfolios/{id}/history
    Should return a list of history snapshots for the portfolio.
    """
    create_resp = await client.post("/api/v1/portfolios/", json={"name": "History Test"}, headers=auth_headers)
    assert create_resp.status_code == 201
    portfolio_id = create_resp.json()["id"]

    repo = PortfolioRepository(db_session)

    history_entry = PortfolioHistory(
        date=date.today(),
        total_value=Decimal("5000.00"),
        total_pnl_percentage=Decimal("15.50"),
        portfolio_id=portfolio_id,
    )
    await repo.create_portfolio_history(history_entry)
    await db_session.commit()

    response = await client.get(f"/api/v1/portfolios/{portfolio_id}/history", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1

    entry = data[0]
    assert entry["total_value"] == "5000.00"
    assert entry["total_pnl_percentage"] == 15.5
    assert entry["date"] == str(date.today())


@pytest.mark.asyncio
async def test_get_history_not_found(client: AsyncClient, auth_headers: dict[str, str]):
    """
    Test GET /api/v1/portfolios/{id}/history
    Should return 404 if portfolio does not exist.
    """
    response = await client.get("/api/v1/portfolios/99999/history", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_history_forbidden(client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession):
    """
    Test GET /api/v1/portfolios/{id}/history
    Should return 403 Forbidden if accessing another user's portfolio.
    """
    other_user = User(email="victim@example.com", hashed_password=get_password_hash("secret"), is_active=True)
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    repo = PortfolioRepository(db_session)
    victim_portfolio = await repo.create_portfolio(user_id=other_user.id, name="Secret Portfolio")

    # Try to access it with "auth_headers" (which belongs to the Test User, not Victim)
    response = await client.get(f"/api/v1/portfolios/{victim_portfolio.id}/history", headers=auth_headers)

    assert response.status_code == 403
