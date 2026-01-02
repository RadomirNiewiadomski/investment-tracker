"""
Notification Service.
Currently mocks email sending by logging to console.
"""

from loguru import logger


class NotificationService:
    """
    Service responsible for sending notifications to users.
    """

    async def send_price_alert_email(
        self, user_id: int, ticker: str, price: float, condition: str, target: float
    ) -> None:
        """
        Mocks sending an email when a price alert is triggered.
        """

        subject = f"Price Alert: {ticker} is {condition} {target}"
        body = f"Hello User #{user_id}, your alert for {ticker} was triggered! Current price: {price}"

        logger.success(f"~~~~~~~~~~~~[MOCK EMAIL]~~~~~~~~~~~~~~ To User: {user_id} | Subject: {subject} | Body: {body}")
