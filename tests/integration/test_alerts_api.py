"""
Integration tests for Alerts API endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.portfolio.repository import AlertRepository


@pytest.mark.asyncio
async def test_create_alert(client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession):
    """
    Test creating a new price alert.
    """
    payload = {"ticker": "BTC", "target_price": 50000.00, "condition": "BELOW"}

    response = await client.post("/api/v1/portfolios/alerts", json=payload, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["ticker"] == "BTC"
    assert data["condition"] == "BELOW"
    assert data["target_price"] == "50000.00"
    assert data["is_active"] is True

    repo = AlertRepository(db_session)
    alerts = await repo.get_all_by_user(user_id=1)
    assert len(alerts) == 1
    assert alerts[0].ticker == "BTC"


@pytest.mark.asyncio
async def test_get_my_alerts(client: AsyncClient, auth_headers: dict[str, str]):
    """
    Test listing alerts for current user.
    """
    await client.post(
        "/api/v1/portfolios/alerts",
        json={"ticker": "ETH", "target_price": 3000, "condition": "ABOVE"},
        headers=auth_headers,
    )

    response = await client.get("/api/v1/portfolios/alerts", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["ticker"] == "ETH"


@pytest.mark.asyncio
async def test_update_alert(client: AsyncClient, auth_headers: dict[str, str]):
    """
    Test updating an alert (e.g. deactivate).
    """
    create_res = await client.post(
        "/api/v1/portfolios/alerts",
        json={"ticker": "SOL", "target_price": 100, "condition": "ABOVE"},
        headers=auth_headers,
    )
    alert_id = create_res.json()["id"]

    payload = {"is_active": False}
    response = await client.patch(f"/api/v1/portfolios/alerts/{alert_id}", json=payload, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_alert(client: AsyncClient, auth_headers: dict[str, str], db_session: AsyncSession):
    """
    Test deleting an alert.
    """
    create_res = await client.post(
        "/api/v1/portfolios/alerts",
        json={"ticker": "DOGE", "target_price": 1, "condition": "ABOVE"},
        headers=auth_headers,
    )
    alert_id = create_res.json()["id"]

    response = await client.delete(f"/api/v1/portfolios/alerts/{alert_id}", headers=auth_headers)
    assert response.status_code == 204

    repo = AlertRepository(db_session)
    alert = await repo.get_alert_by_id(alert_id)
    assert alert is None
