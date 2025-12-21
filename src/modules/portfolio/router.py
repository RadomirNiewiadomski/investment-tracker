"""
API Router for Portfolio module.
Exposes endpoints for managing portfolios and assets.
"""

from fastapi import APIRouter, Depends, status

from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import User
from src.modules.portfolio.dependencies import get_portfolio_service
from src.modules.portfolio.schemas import (
    AssetCreate,
    AssetResponse,
    PortfolioCreate,
    PortfolioListResponse,
    PortfolioResponse,
    PortfolioUpdate,
)
from src.modules.portfolio.service import PortfolioService

# All routes here require authentication
router = APIRouter(tags=["Portfolios"], dependencies=[Depends(get_current_user)])


@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_in: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Create a new investment portfolio.
    """
    return await service.create_portfolio(user_id=current_user.id, portfolio_in=portfolio_in)


@router.get("/", response_model=list[PortfolioListResponse])
async def list_portfolios(
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    List all portfolios belonging to the current user.
    """
    return await service.get_user_portfolios(user_id=current_user.id)


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Get details of a specific portfolio (including assets).
    """
    return await service.get_portfolio(user_id=current_user.id, portfolio_id=portfolio_id)


@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: int,
    update_data: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Update portfolio name or description.
    """
    return await service.update_portfolio(user_id=current_user.id, portfolio_id=portfolio_id, update_data=update_data)


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Delete a portfolio and all its assets.
    """
    await service.delete_portfolio(user_id=current_user.id, portfolio_id=portfolio_id)


@router.post("/{portfolio_id}/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def add_asset(
    portfolio_id: int,
    asset_in: AssetCreate,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """
    Add an asset to a portfolio (or update existing one).
    Automatically calculates weighted average price if asset exists.
    """
    return await service.add_asset_to_portfolio(user_id=current_user.id, portfolio_id=portfolio_id, asset_in=asset_in)
