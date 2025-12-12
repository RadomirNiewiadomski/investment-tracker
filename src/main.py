"""
Main application entry point.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Investment Portfolio Tracker",
    description="Backend API for tracking investments with real-time alerts.",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Basic health check endpoint.

    Returns:
        dict: Status message.
    """
    return {"status": "ok", "service": "investment-tracker"}
