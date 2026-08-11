import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    unique_email = f"newuser_{uuid.uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": "password123", "full_name": "New User"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == unique_email
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    unique_email = f"duplicate_{uuid.uuid4().hex[:8]}@example.com"
    payload = {"email": unique_email, "password": "password123"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    unique_email = f"logintest_{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register", json={"email": unique_email, "password": "password123"}
    )
    response = await client.post(
        "/api/v1/auth/login", data={"username": unique_email, "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    unique_email = f"wrongpass_{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register", json={"email": unique_email, "password": "password123"}
    )
    response = await client.post(
        "/api/v1/auth/login", data={"username": unique_email, "password": "wrongpassword"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert "email" in response.json()
    assert "hashed_password" not in response.json()