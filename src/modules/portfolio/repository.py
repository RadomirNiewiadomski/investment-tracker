"""
Repository layer for Portfolio module.
Handles database access logic for Portfolios and Assets.
"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.portfolio.models import Portfolio


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
        await self.session.refresh(portfolio)
        return portfolio

    async def get_portfolio_by_id(self, portfolio_id: int) -> Portfolio | None:
        """
        Retrieves a portfolio by its ID.
        """
        return await self.session.get(Portfolio, portfolio_id)

    async def get_all_by_user(self, user_id: int) -> Sequence[Portfolio]:
        """
        Retrieves all portfolios belonging to a specific user.
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
