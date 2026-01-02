"""
Celery tasks for Market Data module.
"""

import asyncio

from asgiref.sync import async_to_sync
from celery.utils.log import get_task_logger
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.celery_app import celery_app
from src.core.database import create_engine
from src.core.redis import init_redis_pool
from src.modules.market_data.service import MarketDataService
from src.modules.notifications.service import NotificationService
from src.modules.portfolio.models import Alert, AlertCondition, Asset
from src.modules.portfolio.repository import AlertRepository

logger = get_task_logger(__name__)


async def _process_alerts(session: AsyncSession, redis_client: Redis) -> int:
    """
    Checks all active alerts against current cache prices.
    Returns number of triggered alerts.
    """
    alert_repo = AlertRepository(session)
    notification_service = NotificationService()

    active_alerts = await alert_repo.get_all_active()

    triggered_count = 0

    for alert in active_alerts:
        cache_key = f"price:{alert.ticker}"
        cached_price_str = await redis_client.get(cache_key)

        if not cached_price_str:
            continue

        current_price = float(cached_price_str)
        target_price = float(alert.target_price)

        is_triggered = False

        if (alert.condition == AlertCondition.ABOVE and current_price > target_price) or (
            alert.condition == AlertCondition.BELOW and current_price < target_price
        ):
            is_triggered = True

        if is_triggered:
            logger.info(f"Alert triggered! ID: {alert.id}, Ticker: {alert.ticker}, Condition: {alert.condition}")

            await notification_service.send_price_alert_email(
                user_id=alert.user_id,
                ticker=alert.ticker,
                price=current_price,
                condition=str(alert.condition),
                target=target_price,
            )

            alert.is_active = False
            triggered_count += 1

    if triggered_count > 0:
        await session.commit()

    return triggered_count


async def _update_prices_logic() -> None:
    """
    Async logic to fetch unique tickers, update their prices in cache,
    and check user alerts.
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
            stmt_assets = select(Asset.ticker).distinct()
            stmt_alerts = select(Alert.ticker).where(Alert.is_active == True).distinct()  # noqa

            res_assets = await session.execute(stmt_assets)
            res_alerts = await session.execute(stmt_alerts)

            tickers = set(res_assets.scalars().all()) | set(res_alerts.scalars().all())

            if tickers:
                logger.info(f"Updating prices for {len(tickers)} tickers: {tickers}")
                tasks = [market_service.get_price(ticker, force_refresh=True) for ticker in tickers]
                await asyncio.gather(*tasks)

            triggered = await _process_alerts(session, redis_client)
            logger.info(f"Alert check finished. Triggered: {triggered}")

    finally:
        await redis_client.aclose()
        await local_engine.dispose()

    logger.info("Background job completed.")


@celery_app.task  # type: ignore
def update_asset_prices() -> None:
    """
    Celery wrapper for the async logic.
    """
    async_to_sync(_update_prices_logic)()
