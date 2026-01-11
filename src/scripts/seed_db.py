"""
Script to seed the database with sample data.
Usage: uv run python -m src.scripts.seed_db
"""

import asyncio
import sys
from decimal import Decimal

from loguru import logger
from sqlalchemy import select

from src.core.database import async_session_maker
from src.core.security import get_password_hash
from src.modules.auth.models import User
from src.modules.portfolio.models import Alert, AlertCondition, Asset, AssetType
from src.modules.portfolio.repository import AlertRepository, PortfolioRepository

logger.remove()
logger.add(sys.stderr, level="INFO")


async def seed_data() -> None:
    logger.info("🌱 Starting database seeding...")

    async with async_session_maker() as session:
        stmt = select(User).where(User.email == "demo@example.com")
        result = await session.execute(stmt)
        existing_user = result.scalars().first()

        if existing_user:
            logger.warning("⚠️  Demo user already exists. Skipping seeding.")
            return

        logger.info("👤 Creating demo user (demo@example.com / password)...")
        hashed_pw = get_password_hash("password")
        user = User(
            email="demo@example.com",
            hashed_password=hashed_pw,
            first_name="Demo",
            last_name="User",
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        logger.info("Creating 'Main Crypto' portfolio...")
        portfolio_repo = PortfolioRepository(session)
        portfolio = await portfolio_repo.create_portfolio(
            user_id=user.id, name="Main Crypto", description="My long-term holding strategy"
        )

        logger.info("💰 Adding assets (BTC, ETH, SOL, DOGE)")

        assets_data = [
            {
                "ticker": "BTC",
                "quantity": Decimal("1.5"),
                "avg_buy_price": Decimal("25000.00"),
                "asset_type": AssetType.CRYPTO,
            },
            {
                "ticker": "ETH",
                "quantity": Decimal("10.0"),
                "avg_buy_price": Decimal("1500.00"),
                "asset_type": AssetType.CRYPTO,
            },
            {
                "ticker": "SOL",
                "quantity": Decimal("100.0"),
                "avg_buy_price": Decimal("20.00"),
                "asset_type": AssetType.CRYPTO,
            },
            {
                "ticker": "DOGE",
                "quantity": Decimal("5000.0"),
                "avg_buy_price": Decimal("0.05"),
                "asset_type": AssetType.CRYPTO,
            },
        ]

        for asset_in in assets_data:
            asset = Asset(
                ticker=asset_in["ticker"],
                quantity=asset_in["quantity"],
                avg_buy_price=asset_in["avg_buy_price"],
                asset_type=asset_in["asset_type"],
                portfolio_id=portfolio.id,
            )
            await portfolio_repo.create_asset(asset)

        logger.info("🔔 Adding sample alerts...")
        alert_repo = AlertRepository(session)

        alerts_data = [
            {"ticker": "BTC", "target_price": Decimal("100000.00"), "condition": AlertCondition.ABOVE},
            {"ticker": "ETH", "target_price": Decimal("2000.00"), "condition": AlertCondition.BELOW},
        ]

        for alert_in in alerts_data:
            alert = Alert(
                ticker=alert_in["ticker"],
                target_price=alert_in["target_price"],
                condition=alert_in["condition"],
                user_id=user.id,
                is_active=True,
            )
            await alert_repo.create_alert(alert)

        await session.commit()
        logger.success("✅ Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())
