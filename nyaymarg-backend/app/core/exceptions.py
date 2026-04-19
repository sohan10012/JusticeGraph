"""
app/core/exceptions.py — Custom HTTP exceptions for NyayMarg.
"""
from __future__ import annotations

from fastapi import HTTPException, status


class NyayMargException(HTTPException):
    """Base class for all NyayMarg exceptions."""


class AuthenticationError(NyayMargException):
    def __init__(self, detail: str = "Authentication required") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthorizationError(NyayMargException):
    def __init__(self, detail: str = "Insufficient permissions") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class PIIDetectedError(NyayMargException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="PII detected in input — cannot process",
        )


class ModelNotReadyError(NyayMargException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML model not loaded — try again shortly",
        )


class NotFoundError(NyayMargException):
    def __init__(self, resource: str = "Resource") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} not found",
        )


class ConflictError(NyayMargException):
    def __init__(self, detail: str = "Resource already exists") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ValidationError(NyayMargException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class UploadError(NyayMargException):
    def __init__(self, detail: str = "File upload failed") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
