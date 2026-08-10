import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_txt_document(client: AsyncClient, auth_headers: dict):
    content = b"This is a test document content for testing purposes."
    files = {"file": ("test_doc.txt", io.BytesIO(content), "text/plain")}
    response = await client.post("/api/v1/documents", headers=auth_headers, files=files)
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test_doc.txt"
    assert data["file_type"] == "txt"
    assert data["processing_status"] == "pending"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_upload_invalid_file_type(client: AsyncClient, auth_headers: dict):
    content = b"fake image content"
    files = {"file": ("image.png", io.BytesIO(content), "image/png")}
    response = await client.post("/api/v1/documents", headers=auth_headers, files=files)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/documents", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_unauthenticated_access(client: AsyncClient):
    response = await client.get("/api/v1/documents")
    assert response.status_code == 401