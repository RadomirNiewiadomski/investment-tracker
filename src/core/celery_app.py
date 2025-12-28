"""
Celery application configuration.
"""

from celery import Celery

from src.core.config import settings

celery_app = Celery(
    "investment_tracker",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    imports=["src.modules.market_data.tasks"],
)

celery_app.conf.beat_schedule = {
    "update-prices-every-5-minutes": {
        "task": "src.modules.market_data.tasks.update_asset_prices",
        "schedule": 300.0,  # every 5 minutes
    },
}
