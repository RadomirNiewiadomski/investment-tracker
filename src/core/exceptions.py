"""
Custom exception classes for the application.
"""

from typing import Any

from fastapi import status


class AppException(Exception):
    """
    Base exception class for all application-specific errors.
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    """
    Exception raised when a resource is not found.
    """

    def __init__(self, resource: str, resource_id: Any) -> None:
        super().__init__(
            message=f"{resource} with id {resource_id} not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class PermissionDeniedException(AppException):
    """
    Exception raised when a user does not have permission.
    """

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class BadRequestException(AppException):
    """
    Exception raised for bad requests/validation logic.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
