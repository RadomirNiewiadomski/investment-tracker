"""
Integration tests for Portfolio API endpoints.
Tests the full request-response cycle including authentication and DB persistence.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_portfolio_api(client: AsyncClient, auth_headers: dict[str, str]):
    """
    Test POST /api/v1/portfolios/
    Should create a new portfolio and return 201 Created.
    """
    payload = {"name": "My API Portfolio", "description": "Created via integration test"}

    response = await client.post("/api/v1/portfolios/", json=payload, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert "id" in data
    assert data["assets"] == []


@pytest.mark.asyncio
async def test_list_portfolios_api(client: AsyncClient, auth_headers: dict[str, str]):
    """
    Test GET /api/v1/portfolios/
    Should return a list of user's portfolios.
    """
    await client.post("/api/v1/portfolios/", json={"name": "Portfolio A"}, headers=auth_headers)
    await client.post("/api/v1/portfolios/", json={"name": "Portfolio B"}, headers=auth_headers)

    response = await client.get("/api/v1/portfolios/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [p["name"] for p in data]
    assert "Portfolio A" in names
    assert "Portfolio B" in names


@pytest.mark.asyncio
async def test_add_asset_api(client: AsyncClient, auth_headers: dict[str, str]):
    """
    Test POST /api/v1/portfolios/{id}/assets
    Should add an asset and calculate averages correctly.
    """
    create_resp = await client.post("/api/v1/portfolios/", json={"name": "Crypto Bag"}, headers=auth_headers)
    portfolio_id = create_resp.json()["id"]

    asset1_payload = {
        "ticker": "BTC",
        "quantity": "1.0",
        "avg_buy_price": "20000.00",
        "asset_type": "CRYPTO",
    }
    resp1 = await client.post(f"/api/v1/portfolios/{portfolio_id}/assets", json=asset1_payload, headers=auth_headers)
    assert resp1.status_code == 201
    assert resp1.json()["quantity"] == "1.00000000"

    asset2_payload = {"ticker": "BTC", "quantity": "1.0", "avg_buy_price": "40000.00", "asset_type": "CRYPTO"}
    resp2 = await client.post(f"/api/v1/portfolios/{portfolio_id}/assets", json=asset2_payload, headers=auth_headers)

    assert resp2.status_code == 201
    data = resp2.json()

    assert str(data["quantity"]) == "2.00000000"
    assert float(data["avg_buy_price"]) == 30000.0


@pytest.mark.asyncio
async def test_update_portfolio_api(client: AsyncClient, auth_headers: dict[str, str]):
    """
    Test PATCH /api/v1/portfolios/{id}
    Should update name/description.
    """
    create_resp = await client.post(
        "/api/v1/portfolios/", json={"name": "Old Name", "description": "Old Desc"}, headers=auth_headers
    )
    p_id = create_resp.json()["id"]

    patch_payload = {"name": "New Name"}
    response = await client.patch(f"/api/v1/portfolios/{p_id}", json=patch_payload, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "Old Desc"


@pytest.mark.asyncio
async def test_delete_portfolio_api(client: AsyncClient, auth_headers: dict[str, str]):
    """
    Test DELETE /api/v1/portfolios/{id}
    Should remove the resource.
    """
    create_resp = await client.post("/api/v1/portfolios/", json={"name": "To Delete"}, headers=auth_headers)
    p_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/portfolios/{p_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/portfolios/{p_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_get_portfolio_detail_with_assets(client: AsyncClient, auth_headers: dict[str, str]):
    """
    Test GET /api/v1/portfolios/{id}
    Should return portfolio details WITH assets included (Eager Loading check).
    """
    create_resp = await client.post("/api/v1/portfolios/", json={"name": "Details Test"}, headers=auth_headers)
    p_id = create_resp.json()["id"]

    await client.post(
        f"/api/v1/portfolios/{p_id}/assets",
        json={"ticker": "ETH", "quantity": "10", "avg_buy_price": "1500", "asset_type": "CRYPTO"},
        headers=auth_headers,
    )

    response = await client.get(f"/api/v1/portfolios/{p_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Details Test"
    assert len(data["assets"]) == 1
    assert data["assets"][0]["ticker"] == "ETH"


@pytest.mark.asyncio
async def test_delete_asset_api(client: AsyncClient, auth_headers: dict[str, str]):
    """
    Test DELETE /api/v1/portfolios/{id}/assets/{ticker}
    Should remove the asset from the portfolio.
    """
    create_resp = await client.post("/api/v1/portfolios/", json={"name": "Temp Portfolio"}, headers=auth_headers)
    p_id = create_resp.json()["id"]

    await client.post(
        f"/api/v1/portfolios/{p_id}/assets",
        json={"ticker": "BTC", "quantity": "1.0", "avg_buy_price": "20000.00", "asset_type": "CRYPTO"},
        headers=auth_headers,
    )

    del_resp = await client.delete(f"/api/v1/portfolios/{p_id}/assets/BTC", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/portfolios/{p_id}", headers=auth_headers)
    data = get_resp.json()
    assert len(data["assets"]) == 0
