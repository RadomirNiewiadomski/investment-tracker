"""
Repository layer for Portfolio module.
Handles database access logic for Portfolios and Assets.
"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.portfolio.models import Asset, Portfolio


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
