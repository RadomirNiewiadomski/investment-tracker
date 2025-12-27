"""
Dependencies for the Portfolio module.
Handles dependency injection for services.
"""

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.redis import get_redis_client
from src.modules.market_data.service import MarketDataService
from src.modules.portfolio.repository import PortfolioRepository
from src.modules.portfolio.service import PortfolioService


def get_market_data_service(redis: Redis = Depends(get_redis_client)) -> MarketDataService:
    """
    Dependency to create MarketDataService with Redis connection.
    """
    return MarketDataService(redis)


def get_portfolio_service(
    session: AsyncSession = Depends(get_db),
    market_data: MarketDataService = Depends(get_market_data_service),
) -> PortfolioService:
    """
    Dependency that provides a PortfolioService instance with DB and Market Data.
    """
    repository = PortfolioRepository(session)
    return PortfolioService(repository, market_data)
