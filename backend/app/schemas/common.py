from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """Standard unified API response wrapper."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[DataT] = None


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard unified API error wrapper."""
    success: bool = False
    code: str = "ERROR"
    message: str
    details: Optional[List[ErrorDetail]] = None


class HealthResponse(BaseModel):
    """Health check status response."""
    status: str = "healthy"
    version: str
    environment: str
    database_connected: bool
    timestamp: str


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Standard paginated response wrapper."""
    success: bool = True
    data: List[DataT]
    pagination: PaginationMeta
