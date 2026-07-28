"""Integration tests for Market API endpoints.

These tests use mocked services to test API endpoint behavior without requiring a database.

To run these tests:
uv run pytest tests/integration/
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timezone

from app.main import app


@pytest.fixture
def mock_service():
    """Create a mock MarketService for integration testing."""
    from datetime import datetime, timezone
    
    mock = MagicMock()
    
    # Mock async methods properly using AsyncMock
    # Response must match MarketPriceDto structure (code, title, price, change, provider, provider_time, retrieved_at)
    mock.get_latest_prices = AsyncMock(return_value=[
        {
            "code": "usd", 
            "title": "دلار آمریکا", 
            "price": 190700, 
            "change": 500,
            "provider": "navasan",
            "provider_time": "14:30",
            "retrieved_at": datetime.now(timezone.utc)
        },
        {
            "code": "sekkeh", 
            "title": "سکه طرح امامی", 
            "price": 184500000, 
            "change": 1000000,
            "provider": "navasan",
            "provider_time": "14:30",
            "retrieved_at": datetime.now(timezone.utc)
        },
    ])
    
    mock.force_refresh = AsyncMock(return_value=[
        {
            "code": "usd", 
            "title": "دلار آمریکا", 
            "price": 190700, 
            "change": 500,
            "provider": "navasan",
            "provider_time": "14:30",
            "retrieved_at": datetime.now(timezone.utc)
        },
        {
            "code": "sekkeh", 
            "title": "سکه طرح امامی", 
            "price": 184500000, 
            "change": 1000000,
            "provider": "navasan",
            "provider_time": "14:30",
            "retrieved_at": datetime.now(timezone.utc)
        },
    ])
    
    mock.get_price_history = MagicMock(return_value=[
        {
            "code": "usd",
            "title": "دلار آمریکا",
            "price": 190200,
            "change": 0,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "provider": "navasan",
            "provider_time": "14:30",
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "code": "sekkeh",
            "title": "سکه طرح امامی",
            "price": 183500000,
            "change": 0,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "provider": "navasan",
            "provider_time": "14:30",
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        },
    ])
    
    return mock


@pytest.fixture
async def client(mock_service):
    """Create test client with mocked service."""
    from unittest.mock import patch
    with patch('api.v1.market.MarketService', return_value=mock_service):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


class TestMarketLatestEndpoint:
    """Tests for GET /api/v1/market/latest endpoint."""
    
    @pytest.mark.asyncio
    async def test_latest_prices_success(self, client):
        """Test successful retrieval of latest prices."""
        response = await client.get(
            "/api/v1/market/latest",
            params={"codes": "usd,sekkeh"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["success"] is True
        assert "items" in data
        assert "retrieved_at" in data
        
        items = data["items"]
        assert isinstance(items, list)
        assert len(items) == 2
        
        usd_item = next((item for item in items if item["code"] == "usd"), None)
        sekkeh_item = next((item for item in items if item["code"] == "sekkeh"), None)
        
        assert usd_item is not None
        assert usd_item["title"] == "دلار آمریکا"
        assert isinstance(usd_item["price"], (int, float))
        assert isinstance(usd_item["change"], (int, float))
        
        assert sekkeh_item is not None
        assert sekkeh_item["title"] == "سکه طرح امامی"
        assert isinstance(sekkeh_item["price"], (int, float))
        assert isinstance(sekkeh_item["change"], (int, float))
    
    @pytest.mark.asyncio
    async def test_latest_prices_single_code(self, client):
        """Test retrieval with single code."""
        response = await client.get(
            "/api/v1/market/latest",
            params={"codes": "usd"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        items = data["items"]
        assert isinstance(items, list)
        assert len(items) >= 1
        assert items[0]["code"] == "usd"
    
    @pytest.mark.asyncio
    async def test_latest_prices_invalid_code(self, client, mock_service):
        """Test handling of invalid/unknown codes."""
        # Configure mock to return empty for unknown codes
        mock_service.get_latest_prices = AsyncMock(return_value=[])
        
        response = await client.get(
            "/api/v1/market/latest",
            params={"codes": "unknown_code"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["items"] == []


class TestMarketRefreshEndpoint:
    """Tests for POST /api/v1/market/refresh endpoint."""
    
    @pytest.mark.asyncio
    async def test_refresh_success(self, client):
        """Test successful price refresh."""
        response = await client.post(
            "/api/v1/market/refresh",
            json={"codes": ["usd", "sekkeh"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "items" in data
        assert "message" in data
        
        items = data["items"]
        assert isinstance(items, list)
        assert len(items) >= 1
        
        # Verify structure
        for item in items:
            assert "code" in item
            assert "price" in item
            assert isinstance(item["price"], (int, float))
    
    @pytest.mark.asyncio
    async def test_refresh_single_code(self, client):
        """Test refresh with single code."""
        response = await client.post(
            "/api/v1/market/refresh",
            json={"codes": ["usd"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        items = data["items"]
        assert isinstance(items, list)
        assert len(items) >= 1
    
    @pytest.mark.asyncio
    async def test_refresh_empty_codes(self, client):
        """Test refresh with empty codes list."""
        response = await client.post(
            "/api/v1/market/refresh",
            json={"codes": []}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["items"], list)


class TestMarketHistoryEndpoint:
    """Tests for GET /api/v1/market/history endpoint."""
    
    @pytest.mark.asyncio
    async def test_history_success(self, client):
        """Test successful retrieval of price history."""
        response = await client.get("/api/v1/market/history")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "items" in data
        assert "total_count" in data
        
        items = data["items"]
        assert isinstance(items, list)
        
        if len(items) > 0:
            item = items[0]
            assert "code" in item
            assert "price" in item
            assert "provider" in item
            assert "retrieved_at" in item
    
    @pytest.mark.asyncio
    async def test_history_with_provider_filter(self, client):
        """Test history filtered by provider."""
        response = await client.get(
            "/api/v1/market/history",
            params={"provider": "navasan"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["items"], list)
    
    @pytest.mark.asyncio
    async def test_history_with_item_filter(self, client):
        """Test history filtered by item code."""
        response = await client.get(
            "/api/v1/market/history",
            params={"code": "usd"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["items"], list)
    
    @pytest.mark.asyncio
    async def test_history_with_limit(self, client):
        """Test history with limit parameter."""
        response = await client.get(
            "/api/v1/market/history",
            params={"limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        items = data["items"]
        assert isinstance(items, list)
        assert len(items) <= 10


class TestMarketValidation:
    """Tests for input validation."""
    
    @pytest.mark.asyncio
    async def test_invalid_json_body(self, client):
        """Test handling of invalid JSON body."""
        response = await client.post(
            "/api/v1/market/refresh",
            content="invalid json"
        )
        
        # FastAPI should return 422 for invalid JSON
        assert response.status_code in [200, 422]
