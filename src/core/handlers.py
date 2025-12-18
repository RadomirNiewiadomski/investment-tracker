"""
Global exception handlers for the application.
"""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.exceptions import AppException


async def app_exception_handler(request: Request, exc: AppException) -> ORJSONResponse:
    """
    Handle custom application exceptions.
    """
    return ORJSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.payload,
            }
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> ORJSONResponse:
    """
    Handle Pydantic validation errors (422).
    Customizes the default ugly output.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"] if x not in ("body",))
        errors.append({"field": field, "message": error["msg"]})

    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "ValidationError",
                "message": "Input validation failed",
                "details": errors,
            }
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> ORJSONResponse:
    """
    Handle standard HTTP exceptions (like 404 from FastAPI router).
    """
    return ORJSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTPError",
                "message": str(exc.detail),
            }
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    """
    Catch-all handler for unhandled exceptions (500).
    """
    logger.exception("Unhandled exception occurred")

    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "InternalServerError",
                "message": "An unexpected error occurred. Please try again later.",
            }
        },
    )
