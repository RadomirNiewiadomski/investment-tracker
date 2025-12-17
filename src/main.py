from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.core.config import settings
from src.core.logging import setup_logging
from src.modules.auth.router import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for the FastAPI application.
    Handles startup and shutdown logic.
    """
    # Startup logic
    setup_logging()
    yield
    # Shutdown logic


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    application = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG,
        version="0.1.0",
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
    )
    application.include_router(auth_router, prefix="/api/v1/auth")

    @application.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """
        Health check endpoint to verify service status.
        """
        return {"status": "ok", "service": "investment-tracker"}

    return application


app = create_application()
