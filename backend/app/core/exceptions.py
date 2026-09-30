from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class StudioBaseException(Exception):
    """Base exception for all studio domain errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: Optional[Any] = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(message)


class EntityNotFoundException(StudioBaseException):
    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            message=f"{entity_name} with id '{entity_id}' not found.",
            code="NOT_FOUND",
            details={"entity": entity_name, "id": str(entity_id)},
        )


class PermissionDeniedException(StudioBaseException):
    def __init__(self, message: str = "You do not have permission to access this resource."):
        super().__init__(message=message, code="PERMISSION_DENIED")


class InvalidOperationException(StudioBaseException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="INVALID_OPERATION", details=details)


class PaymentVerificationException(StudioBaseException):
    def __init__(self, message: str = "Payment verification failed."):
        super().__init__(message=message, code="PAYMENT_VERIFICATION_FAILED")
