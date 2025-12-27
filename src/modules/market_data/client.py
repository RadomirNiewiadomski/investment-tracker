"""
Client for interacting with external Market Data APIs (e.g., CoinGecko).
"""

import httpx
from loguru import logger


class CoinGeckoClient:
    """
    Adapter for CoinGecko API.
    """

    BASE_URL = "https://api.coingecko.com/api/v3"

    async def get_current_price(self, ticker: str) -> float | None:
        """
        Fetches current price for a given ticker (e.g., 'BTC', 'ETH') in USD.
        Returns None if ticker is not found or API fails properly.
        """
        ticker_map = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "ADA": "cardano", "DOT": "polkadot"}

        coin_id = ticker_map.get(ticker.upper())
        if not coin_id:
            return None

        url = f"{self.BASE_URL}/simple/price"
        params = {"ids": coin_id, "vs_currencies": "usd"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                # Structure: {"bitcoin": {"usd": 50000}}
                if coin_id in data and "usd" in data[coin_id]:
                    return float(data[coin_id]["usd"])
                return None

            except httpx.HTTPError as e:
                logger.error(f"Error fetching price for {ticker}: {e}")
                return None
            except Exception:
                logger.exception(f"Unexpected error in CoinGeckoClient for {ticker}")
                return None
