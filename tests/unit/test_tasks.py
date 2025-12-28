"""
Unit tests for Celery Tasks logic.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.market_data.tasks import _update_prices_logic


@pytest.mark.asyncio
async def test_update_prices_logic_flow():
    """
    Test that the background task logic:
    1. Connects to Redis & DB.
    2. Fetches unique tickers.
    3. Calls market_service with force_refresh=True.
    4. Cleans up resources.
    """
    mock_redis = AsyncMock()
    mock_engine = AsyncMock()
    mock_session = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalars().all.return_value = ["BTC", "ETH"]
    mock_session.execute.return_value = mock_result

    mock_session_maker = MagicMock()
    mock_session_maker.return_value.__aenter__.return_value = mock_session
    mock_session_maker.return_value.__aexit__.return_value = None

    mock_market_service = AsyncMock()

    with (
        patch("src.modules.market_data.tasks.init_redis_pool", return_value=mock_redis),
        patch("src.modules.market_data.tasks.create_engine", return_value=mock_engine),
        patch("src.modules.market_data.tasks.async_sessionmaker", return_value=mock_session_maker),
        patch("src.modules.market_data.tasks.MarketDataService", return_value=mock_market_service),
    ):
        await _update_prices_logic()

        mock_session.execute.assert_awaited_once()

        assert mock_market_service.get_price.await_count == 2
        mock_market_service.get_price.assert_any_await("BTC", force_refresh=True)
        mock_market_service.get_price.assert_any_await("ETH", force_refresh=True)

        mock_redis.aclose.assert_awaited_once()
        mock_engine.dispose.assert_awaited_once()
