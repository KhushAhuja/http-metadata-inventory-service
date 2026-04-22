from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


SAMPLE_RECORD = {
    "url": "https://example.com",
    "status_code": 200,
    "headers": {"content-type": "text/html"},
    "cookies": {},
    "page_source": "<html><body>Hello</body></html>",
    "fetched_at": datetime(2026, 4, 21, tzinfo=timezone.utc).isoformat(),
}


@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.fixture
async def client(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestPostMetadata:

    @patch("app.routes.metadata.fetch_and_store", new_callable=AsyncMock)
    async def test_success(self, mock_fetch, client):
        mock_fetch.return_value = SAMPLE_RECORD
        response = await client.post("/metadata", json={"url": "https://example.com"})
        assert response.status_code == 201
        data = response.json()
        assert data["url"] == "https://example.com"
        assert data["status_code"] == 200
        assert "headers" in data
        assert "page_source" in data

    async def test_invalid_url(self, client):
        response = await client.post("/metadata", json={"url": "not-a-url"})
        assert response.status_code == 422

    async def test_missing_url(self, client):
        response = await client.post("/metadata", json={})
        assert response.status_code == 422

    @patch("app.routes.metadata.fetch_and_store", new_callable=AsyncMock)
    async def test_timeout(self, mock_fetch, client):
        from httpx import TimeoutException, Request
        mock_fetch.side_effect = TimeoutException(
            "timed out", request=Request("GET", "https://example.com")
        )
        response = await client.post("/metadata", json={"url": "https://example.com"})
        assert response.status_code == 504

    @patch("app.routes.metadata.fetch_and_store", new_callable=AsyncMock)
    async def test_unreachable_url(self, mock_fetch, client):
        from httpx import ConnectError, Request
        mock_fetch.side_effect = ConnectError(
            "connection refused", request=Request("GET", "https://nope.invalid")
        )
        response = await client.post("/metadata", json={"url": "https://nope.invalid"})
        assert response.status_code == 400


class TestGetMetadata:

    @patch("app.routes.metadata.get_stored_metadata", new_callable=AsyncMock)
    async def test_cache_hit(self, mock_get, client):
        mock_get.return_value = SAMPLE_RECORD
        response = await client.get("/metadata", params={"url": "https://example.com"})
        assert response.status_code == 200
        assert response.json()["url"] == "https://example.com"

    @patch("app.routes.metadata.fetch_and_store", new_callable=AsyncMock)
    @patch("app.routes.metadata.get_stored_metadata", new_callable=AsyncMock)
    async def test_cache_miss_returns_202(self, mock_get, mock_fetch, client):
        mock_get.return_value = None
        response = await client.get("/metadata", params={"url": "https://new-url.com"})
        assert response.status_code == 202
        data = response.json()
        assert data["url"] == "https://new-url.com/"
        assert "scheduled" in data["message"].lower()

    @patch("app.routes.metadata.fetch_and_store", new_callable=AsyncMock)
    @patch("app.routes.metadata.get_stored_metadata", new_callable=AsyncMock)
    async def test_cache_miss_triggers_background_task(self, mock_get, mock_fetch, client):
        mock_get.return_value = None
        await client.get("/metadata", params={"url": "https://trigger-test.com"})
        mock_fetch.assert_called_once_with("https://trigger-test.com/")
