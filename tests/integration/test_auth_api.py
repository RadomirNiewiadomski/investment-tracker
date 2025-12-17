import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """
    Integration test: Register a user successfully via API.
    """
    random_email = f"user_{uuid.uuid4()}@example.com"

    payload = {
        "email": random_email,
        "password": "strong_password123",
        "first_name": "Integration",
        "last_name": "Test",
    }

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert data["email"] == random_email
    assert data["first_name"] == "Integration"
    assert "id" in data
    assert "uuid" in data

    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """
    Integration test: Try to register twice with the same email. t
    """
    email = f"dup_{uuid.uuid4()}@example.com"
    payload = {"email": email, "password": "strong_password123"}

    resp1 = await client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 400
    assert resp2.json()["detail"] == "Email already registered"
