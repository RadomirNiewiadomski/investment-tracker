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


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """
    Integration test: Login with valid credentials and receive JWT token.
    """
    email = f"login_{uuid.uuid4()}@example.com"
    password = "strong_password123"

    register_payload = {"email": email, "password": password, "first_name": "Login", "last_name": "Tester"}
    await client.post("/api/v1/auth/register", json=register_payload)

    login_payload = {"email": email, "password": password}
    response = await client.post("/api/v1/auth/login", json=login_payload)

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """
    Integration test: Login with wrong password should fail.
    """
    login_payload = {"email": "ghost@example.com", "password": "wrong_password"}

    response = await client.post("/api/v1/auth/login", json=login_payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_read_users_me_success(client: AsyncClient):
    """
    Integration test: Access protected endpoint /me with a valid token.
    """
    email = f"me_{uuid.uuid4()}@example.com"
    password = "strong_password123"

    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password, "first_name": "Me", "last_name": "User"}
    )

    login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["first_name"] == "Me"
    assert "password" not in data


@pytest.mark.asyncio
async def test_read_users_me_unauthorized(client: AsyncClient):
    """
    Integration test: Access /me without token should fail.
    """
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
