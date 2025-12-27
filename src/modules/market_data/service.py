"""
Service layer for Market Data.
Handles caching and fetching of asset prices.
"""

from redis.asyncio import Redis

from src.modules.market_data.client import CoinGeckoClient


class MarketDataService:
    """
    Service to provide asset prices with caching strategy.
    """

    CACHE_EXPIRE_SECONDS = 300

    def __init__(self, redis: Redis):
        self.redis = redis
        self.client = CoinGeckoClient()

    async def get_price(self, ticker: str) -> float | None:
        """
        Get price from Cache. If missing, fetch from API and cache it.
        """
        cache_key = f"price:{ticker.upper()}"
        cached_price = await self.redis.get(cache_key)
        if cached_price:
            return float(cached_price)
        price = await self.client.get_current_price(ticker)
        if price is not None:
            await self.redis.set(cache_key, str(price), ex=self.CACHE_EXPIRE_SECONDS)

        return price
