"""
API Router for Portfolio module.
Exposes endpoints for managing portfolios and assets.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import User
from src.modules.portfolio.dependencies import get_alert_service, get_portfolio_service
from src.modules.portfolio.models import Alert, Asset, Portfolio
from src.modules.portfolio.schemas import (
    AlertCreate,
    AlertResponse,
    AlertUpdate,
    AssetCreate,
    AssetResponse,
    PortfolioCreate,
    PortfolioListResponse,
    PortfolioResponse,
    PortfolioUpdate,
)
from src.modules.portfolio.service import AlertService, PortfolioService

router = APIRouter(tags=["Portfolios"])

CurrentUser = Annotated[User, Depends(get_current_user)]
PortfolioSvc = Annotated[PortfolioService, Depends(get_portfolio_service)]
AlertSvc = Annotated[AlertService, Depends(get_alert_service)]


@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_in: PortfolioCreate,
    current_user: CurrentUser,
    service: PortfolioSvc,
) -> Portfolio:
    """
    Create a new investment portfolio.
    """
    return await service.create_portfolio(user_id=current_user.id, portfolio_in=portfolio_in)


@router.get("/", response_model=list[PortfolioListResponse])
async def list_portfolios(
    current_user: CurrentUser,
    service: PortfolioSvc,
) -> list[Portfolio]:
    """
    List all portfolios belonging to the current user.
    """
    return await service.get_user_portfolios(user_id=current_user.id)


@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_in: AlertCreate,
    current_user: CurrentUser,
    service: AlertSvc,
) -> Alert:
    """
    Create a new price alert.
    """
    return await service.create_alert(user_id=current_user.id, alert_in=alert_in)


@router.get("/alerts", response_model=list[AlertResponse])
async def get_my_alerts(
    current_user: CurrentUser,
    service: AlertSvc,
) -> list[Alert]:
    """
    List all alerts created by the current user.
    """
    return await service.get_user_alerts(user_id=current_user.id)


@router.patch("/alerts/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_update: AlertUpdate,
    current_user: CurrentUser,
    service: AlertSvc,
) -> Alert:
    """
    Update an alert (e.g. change price, re-activate).
    """
    return await service.update_alert(user_id=current_user.id, alert_id=alert_id, update_data=alert_update)


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    current_user: CurrentUser,
    service: AlertSvc,
) -> None:
    """
    Delete an alert.
    """
    await service.delete_alert(user_id=current_user.id, alert_id=alert_id)


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: int,
    current_user: CurrentUser,
    service: PortfolioSvc,
) -> Portfolio:
    """
    Get details of a specific portfolio (including assets).
    """
    return await service.get_portfolio(user_id=current_user.id, portfolio_id=portfolio_id)


@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: int,
    update_data: PortfolioUpdate,
    current_user: CurrentUser,
    service: PortfolioSvc,
) -> Portfolio:
    """
    Update portfolio name or description.
    """
    return await service.update_portfolio(user_id=current_user.id, portfolio_id=portfolio_id, update_data=update_data)


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: int,
    current_user: CurrentUser,
    service: PortfolioSvc,
) -> None:
    """
    Delete a portfolio and all its assets.
    """
    await service.delete_portfolio(user_id=current_user.id, portfolio_id=portfolio_id)


@router.post("/{portfolio_id}/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def add_asset(
    portfolio_id: int,
    asset_in: AssetCreate,
    current_user: CurrentUser,
    service: PortfolioSvc,
) -> Asset:
    """
    Add an asset to a portfolio (or update existing one).
    Automatically calculates weighted average price if asset exists.
    """
    return await service.add_asset_to_portfolio(user_id=current_user.id, portfolio_id=portfolio_id, asset_in=asset_in)


@router.delete("/{portfolio_id}/assets/{ticker}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    portfolio_id: int,
    ticker: str,
    current_user: CurrentUser,
    service: PortfolioSvc,
) -> None:
    """
    Remove an asset from the portfolio completely.
    """
    await service.remove_asset(user_id=current_user.id, portfolio_id=portfolio_id, ticker=ticker)
