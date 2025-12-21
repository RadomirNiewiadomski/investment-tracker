"""
Dependencies for the Portfolio module.
Handles dependency injection for services.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.portfolio.repository import PortfolioRepository
from src.modules.portfolio.service import PortfolioService


def get_portfolio_service(session: AsyncSession = Depends(get_db)) -> PortfolioService:
    """
    Dependency that provides a PortfolioService instance with a database session.
    """
    repository = PortfolioRepository(session)
    return PortfolioService(repository)
