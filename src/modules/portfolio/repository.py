"""
Repository layer for Portfolio module.
Handles database access logic for Portfolios, Assets and Allerts.
"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.portfolio.models import Alert, Asset, Portfolio, PortfolioHistory
from src.modules.portfolio.schemas import AlertUpdate


class PortfolioRepository:
    """
    Repository for performing database operations on Portfolio resources.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_portfolio(self, user_id: int, name: str, description: str | None = None) -> Portfolio:
        """
        Creates a new portfolio for a specific user.
        """
        portfolio = Portfolio(user_id=user_id, name=name, description=description)
        self.session.add(portfolio)
        await self.session.commit()
        await self.session.refresh(portfolio, attribute_names=["assets"])
        return portfolio

    async def get_portfolio_by_id(self, portfolio_id: int) -> Portfolio | None:
        """
        Retrieves a portfolio by its ID including its assets (Eager Load).
        Forces refresh from DB to ensure up-to-date assets list.
        """
        stmt = (
            select(Portfolio)
            .options(selectinload(Portfolio.assets))
            .where(Portfolio.id == portfolio_id)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all_by_user(self, user_id: int) -> Sequence[Portfolio]:
        """
        Retrieves all portfolios belonging to a specific user.
        Lightweight query - fetches ONLY portfolio data, NO assets.
        """
        stmt = select(Portfolio).where(Portfolio.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_portfolio(
        self, portfolio: Portfolio, name: str | None = None, description: str | None = None
    ) -> Portfolio:
        """
        Updates portfolio details.
        Only updates fields that are provided (not None).
        """
        if name is not None:
            portfolio.name = name

        if description is not None:
            portfolio.description = description

        await self.session.commit()
        await self.session.refresh(portfolio)
        return portfolio

    async def delete_portfolio(self, portfolio: Portfolio) -> None:
        """
        Deletes a portfolio from the database.
        """
        await self.session.delete(portfolio)
        await self.session.commit()

    async def get_asset_by_ticker(self, portfolio_id: int, ticker: str) -> Asset | None:
        """
        Retrieves a specific asset from a portfolio by its ticker.
        """
        stmt = select(Asset).where(Asset.portfolio_id == portfolio_id, Asset.ticker == ticker)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_asset(self, asset: Asset) -> Asset:
        """
        Adds a new asset to the database.
        """
        self.session.add(asset)
        await self.session.commit()
        await self.session.refresh(asset)
        return asset

    async def commit(self) -> None:
        """
        Commits changes to the database.
        Useful for updates where we modified the object directly.
        """
        await self.session.commit()

    async def delete_asset(self, asset: Asset) -> None:
        """
        Deletes an asset from the database.
        """
        await self.session.delete(asset)
        await self.session.commit()

    async def get_all_portfolios_system(self) -> Sequence[Portfolio]:
        """
        Retrieves ALL portfolios in the system (for background worker).
        Eager loads assets to calculate value.
        """
        stmt = select(Portfolio).options(selectinload(Portfolio.assets))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_portfolio_history(self, history: PortfolioHistory) -> PortfolioHistory:
        """
        Saves or updates a daily snapshot.
        Commit is handled at the end of service/task.
        """
        stmt = select(PortfolioHistory).where(
            PortfolioHistory.portfolio_id == history.portfolio_id, PortfolioHistory.date == history.date
        )
        result = await self.session.execute(stmt)
        existing = result.scalars().first()

        if existing:
            # Update
            existing.total_value = history.total_value
            existing.total_pnl_percentage = history.total_pnl_percentage
            return existing
        else:
            # Insert
            self.session.add(history)
            return history


class AlertRepository:
    """
    Repository for handling Alert database operations.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_alert(self, alert: Alert) -> Alert:
        """
        Saves a new alert to the database.
        """
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def get_alert_by_id(self, alert_id: int) -> Alert | None:
        """
        Retrieves an alert by ID.
        """
        stmt = select(Alert).where(Alert.id == alert_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all_by_user(self, user_id: int) -> Sequence[Alert]:
        """
        Retrieves all alerts created by a specific user.
        """
        stmt = select(Alert).where(Alert.user_id == user_id).order_by(Alert.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_active(self) -> Sequence[Alert]:
        """
        Retrieves ALL active alerts in the system.
        Used by the Background Worker to check conditions.
        """
        stmt = select(Alert).where(Alert.is_active == True)  # noqa: E712
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_alert(self, alert: Alert, update_data: AlertUpdate) -> Alert:
        """
        Updates an existing alert.
        """
        update_dict = update_data.model_dump(exclude_unset=True)

        for key, value in update_dict.items():
            setattr(alert, key, value)

        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def delete_alert(self, alert: Alert) -> None:
        """
        Deletes an alert.
        """
        await self.session.delete(alert)
        await self.session.commit()
