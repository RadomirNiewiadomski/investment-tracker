"""
Unit tests for Market Data Service.
Tests caching logic and integration with the client using mocks.
"""

from unittest.mock import AsyncMock

import pytest
from redis.asyncio import Redis

from src.modules.market_data.service import MarketDataService


@pytest.fixture
def mock_redis():
    """
    Creates a mocked Redis client.
    """
    redis = AsyncMock(spec=Redis)
    redis.get = AsyncMock()
    redis.set = AsyncMock()
    return redis


@pytest.fixture
def mock_client():
    """
    Creates a mocked CoinGeckoClient.
    We mock the entire class or specifically the get_current_price method inside the service.
    """
    pass


@pytest.mark.asyncio
async def test_get_price_cache_hit(mock_redis):
    """
    Scenario: Price is available in Redis.
    Expected: Return price from Redis, do NOT call external API.
    """
    ticker = "BTC"
    cached_price = "50000.0"

    # Mock Redis behavior: get returns a value
    mock_redis.get.return_value = cached_price

    service = MarketDataService(mock_redis)
    # Mock the internal client to ensure it's not called
    service.client.get_current_price = AsyncMock()

    price = await service.get_price(ticker)

    assert price == 50000.0
    mock_redis.get.assert_awaited_once_with("price:BTC")
    service.client.get_current_price.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_price_cache_miss_api_success(mock_redis):
    """
    Scenario: Price is NOT in Redis, API returns value.
    Expected: Call API, save to Redis, return price.
    """
    ticker = "ETH"
    api_price = 3000.0

    # Redis returns None (Cache Miss)
    mock_redis.get.return_value = None

    service = MarketDataService(mock_redis)
    # Mock API success
    service.client.get_current_price = AsyncMock(return_value=api_price)

    price = await service.get_price(ticker)

    assert price == 3000.0
    mock_redis.get.assert_awaited_once_with("price:ETH")
    service.client.get_current_price.assert_awaited_once_with("ETH")
    # Verify we saved to Redis with expiration
    mock_redis.set.assert_awaited_once_with("price:ETH", str(api_price), ex=service.CACHE_EXPIRE_SECONDS)


@pytest.mark.asyncio
async def test_get_price_cache_miss_api_failure(mock_redis):
    """
    Scenario: Price NOT in Redis, API returns None (error/not found).
    Expected: Call API, return None, DO NOT save to Redis.
    """
    ticker = "UNKNOWN"

    mock_redis.get.return_value = None

    service = MarketDataService(mock_redis)
    # Mock API failure (returns None)
    service.client.get_current_price = AsyncMock(return_value=None)

    price = await service.get_price(ticker)

    assert price is None
    mock_redis.get.assert_awaited_once()
    service.client.get_current_price.assert_awaited_once()
    # Verify we DID NOT save None to Redis
    mock_redis.set.assert_not_awaited()
