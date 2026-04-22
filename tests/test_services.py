from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.metadata import fetch_and_store, get_stored_metadata


class TestFetchAndStore:

    @patch("app.services.metadata.get_database")
    @patch("app.services.metadata.httpx.AsyncClient")
    async def test_fetches_and_saves(self, mock_client_cls, mock_get_db):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html", "server": "nginx"}
        mock_response.cookies = {}
        mock_response.text = "<html>test</html>"

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        mock_collection = AsyncMock()
        mock_get_db.return_value = {"metadata": mock_collection}

        result = await fetch_and_store("https://example.com")

        assert result["url"] == "https://example.com"
        assert result["status_code"] == 200
        assert result["headers"]["content-type"] == "text/html"
        assert result["page_source"] == "<html>test</html>"
        mock_collection.find_one_and_replace.assert_called_once()

    @patch("app.services.metadata.get_database")
    @patch("app.services.metadata.httpx.AsyncClient")
    async def test_timeout_propagates(self, mock_client_cls, mock_get_db):
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException(
            "timed out", request=httpx.Request("GET", "https://slow.com")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(httpx.TimeoutException):
            await fetch_and_store("https://slow.com")


class TestGetStoredMetadata:

    @patch("app.services.metadata.get_database")
    async def test_returns_record(self, mock_get_db):
        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = {"url": "https://example.com", "status_code": 200}
        mock_get_db.return_value = {"metadata": mock_collection}

        result = await get_stored_metadata("https://example.com")
        assert result["url"] == "https://example.com"

    @patch("app.services.metadata.get_database")
    async def test_returns_none_when_not_found(self, mock_get_db):
        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = None
        mock_get_db.return_value = {"metadata": mock_collection}

        result = await get_stored_metadata("https://notfound.com")
        assert result is None
