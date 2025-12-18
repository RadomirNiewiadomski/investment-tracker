"""
Health check router for monitoring service status.
"""

from fastapi import APIRouter, status

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Endpoint used by Docker/K8s to verify if the service is up and running.",
)
async def health_check() -> dict[str, str]:
    """
    Simple health check.
    """
    return {"status": "ok", "service": "investment-tracker"}
