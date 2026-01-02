"""
Service layer for the Portfolio module.
Contains business logic for managing portfolios, assets and alerts.
"""

import asyncio
from decimal import Decimal

from fastapi import HTTPException, status

from src.core.exceptions import PermissionDeniedException
from src.modules.market_data.service import MarketDataService
from src.modules.portfolio.models import Alert, Asset, Portfolio
from src.modules.portfolio.repository import AlertRepository, PortfolioRepository
from src.modules.portfolio.schemas import AlertCreate, AlertUpdate, AssetCreate, PortfolioCreate, PortfolioUpdate


class PortfolioService:
    """
    Handles business logic for Portfolios and Assets.
    Interacts with PortfolioRepository for data persistence.
    """

    def __init__(self, repository: PortfolioRepository, market_data: MarketDataService):
        self.repository = repository
        self.market_data = market_data

    async def create_portfolio(self, user_id: int, portfolio_in: PortfolioCreate) -> Portfolio:
        """
        Creates a new portfolio for the user.
        Raises error if name is not unique for the user.
        """
        portfolios = await self.repository.get_all_by_user(user_id)
        if any(p.name == portfolio_in.name for p in portfolios):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Portfolio with this name already exists.",
            )

        return await self.repository.create_portfolio(
            user_id=user_id, name=portfolio_in.name, description=portfolio_in.description
        )

    async def get_portfolio(self, user_id: int, portfolio_id: int) -> Portfolio:
        """
        Retrieves a portfolio and enriches it with current market prices.
        Fetches prices for all assets in parallel using asyncio.gather.
        """
        portfolio = await self.repository.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

        if portfolio.user_id != user_id:
            raise PermissionDeniedException()

        if not portfolio.assets:
            return portfolio

        tasks = [self.market_data.get_price(asset.ticker) for asset in portfolio.assets]

        current_prices = await asyncio.gather(*tasks)

        total_value = 0.0
        total_cost = 0.0

        for asset, price in zip(portfolio.assets, current_prices, strict=True):
            asset.current_price = price

            if price is not None:
                qty_float = float(asset.quantity)
                buy_price_float = float(asset.avg_buy_price)

                current_val = qty_float * price
                cost_val = qty_float * buy_price_float

                asset.current_value = current_val

                if cost_val > 0:
                    asset.pnl_percentage = ((current_val - cost_val) / cost_val) * 100.0

                total_value += current_val
                total_cost += cost_val

        portfolio.total_value = total_value
        if total_cost > 0:
            portfolio.total_pnl_percentage = ((total_value - total_cost) / total_cost) * 100.0

        return portfolio

    async def get_user_portfolios(self, user_id: int) -> list[Portfolio]:
        """
        Returns all portfolios for a user.
        """
        return list(await self.repository.get_all_by_user(user_id))

    async def update_portfolio(self, user_id: int, portfolio_id: int, update_data: PortfolioUpdate) -> Portfolio:
        """
        Updates portfolio details.
        """
        portfolio = await self.get_portfolio(user_id, portfolio_id)

        return await self.repository.update_portfolio(
            portfolio, name=update_data.name, description=update_data.description
        )

    async def delete_portfolio(self, user_id: int, portfolio_id: int) -> None:
        """
        Deletes a portfolio.
        """
        portfolio = await self.get_portfolio(user_id, portfolio_id)
        await self.repository.delete_portfolio(portfolio)

    async def add_asset_to_portfolio(self, user_id: int, portfolio_id: int, asset_in: AssetCreate) -> Asset:
        """
        Adds an asset to a portfolio.
        If the asset (ticker) already exists, it aggregates the quantity and recalculates
        the average buy price (Weighted Average).
        """
        portfolio = await self.get_portfolio(user_id, portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

        if portfolio.user_id != user_id:
            raise PermissionDeniedException()

        existing_asset = await self.repository.get_asset_by_ticker(portfolio.id, asset_in.ticker)

        if existing_asset:
            # Calculate new total value: (Old Qty * Old Price) + (New Qty * New Price)
            current_value = existing_asset.quantity * existing_asset.avg_buy_price
            new_addition_value = asset_in.quantity * asset_in.avg_buy_price

            total_quantity = existing_asset.quantity + asset_in.quantity

            new_avg_price = (current_value + new_addition_value) / total_quantity if total_quantity > 0 else Decimal(0)

            existing_asset.quantity = total_quantity
            existing_asset.avg_buy_price = new_avg_price

            await self.repository.commit()
            return existing_asset

        else:
            new_asset = Asset(
                ticker=asset_in.ticker,
                quantity=asset_in.quantity,
                avg_buy_price=asset_in.avg_buy_price,
                asset_type=asset_in.asset_type,
                portfolio_id=portfolio.id,
            )
            return await self.repository.create_asset(new_asset)

    async def remove_asset(self, user_id: int, portfolio_id: int, ticker: str) -> None:
        """
        Removes an asset (identified by ticker) from a user's portfolio.
        """
        portfolio = await self.get_portfolio(user_id, portfolio_id)
        if not portfolio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

        if portfolio.user_id != user_id:
            raise PermissionDeniedException()

        asset = await self.repository.get_asset_by_ticker(portfolio.id, ticker)
        if not asset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found in this portfolio")

        await self.repository.delete_asset(asset)


class AlertService:
    """
    Service for managing user alerts.
    """

    def __init__(self, repository: AlertRepository):
        self.repository = repository

    async def create_alert(self, user_id: int, alert_in: AlertCreate) -> Alert:
        """
        Creates a new alert for the user.
        """
        alert = Alert(**alert_in.model_dump(), user_id=user_id)
        return await self.repository.create_alert(alert)

    async def get_user_alerts(self, user_id: int) -> list[Alert]:
        """
        Gets all alerts for a user.
        """
        return list(await self.repository.get_all_by_user(user_id))

    async def update_alert(self, user_id: int, alert_id: int, update_data: AlertUpdate) -> Alert:
        """
        Updates an alert. Verifies ownership.
        """
        alert = await self.repository.get_alert_by_id(alert_id)
        if not alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

        if alert.user_id != user_id:
            raise PermissionDeniedException()

        return await self.repository.update_alert(alert, update_data)

    async def delete_alert(self, user_id: int, alert_id: int) -> None:
        """
        Deletes an alert. Verifies ownership.
        """
        alert = await self.repository.get_alert_by_id(alert_id)
        if not alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

        if alert.user_id != user_id:
            raise PermissionDeniedException()

        await self.repository.delete_alert(alert)
