"""
Celery tasks for Market Data module.
"""

import asyncio

from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.celery_app import celery_app
from src.core.database import create_engine
from src.core.redis import init_redis_pool
from src.modules.market_data.service import MarketDataService
from src.modules.portfolio.models import Asset

logger = get_task_logger(__name__)


async def _update_prices_logic() -> None:
    """
    Async logic to fetch unique tickers and update their prices in cache.
    """
    logger.info("Starting background price update...")

    redis_client = await init_redis_pool()
    local_engine = create_engine()
    local_session_maker = async_sessionmaker(
        bind=local_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    market_service = MarketDataService(redis_client)

    try:
        async with local_session_maker() as session:
            # Get all unique tickers from DB
            stmt = select(Asset.ticker).distinct()
            result = await session.execute(stmt)
            tickers = result.scalars().all()

            logger.info(f"Found {len(tickers)} unique assets to update: {tickers}")

            if not tickers:
                return

            # Fetch & Cache prices (FORCE REFRESH)
            logger.info(f"Updating prices for tickers: {tickers}")
            tasks = [market_service.get_price(ticker, force_refresh=True) for ticker in tickers]
            await asyncio.gather(*tasks)

    finally:
        await redis_client.aclose()
        await local_engine.dispose()

    logger.info("Background price update completed.")


@celery_app.task  # type: ignore
def update_asset_prices() -> None:
    """
    Celery wrapper for the async logic.
    """
    async_to_sync(_update_prices_logic)()
