from pydantic import BaseModel, Field
from typing import Optional, List, TypeVar, Generic

T = TypeVar('T')


class ErrorResponse(BaseModel):
    message: str = Field(description="Human-readable error message")
    code: Optional[int] = Field(default=None, description="Application-specific error code")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"message": "Not implemented", "code": 501},
                {"message": "Subscription not found", "code": 404},
            ]
        }
    }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model"""
    items: List[T] = Field(description="List of items in the current page")
    total: int = Field(description="Total number of items across all pages")
    page: int = Field(description="Current page number (1-indexed)")
    limit: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [],
                    "total": 100,
                    "page": 1,
                    "limit": 20,
                    "total_pages": 5,
                    "has_next": True,
                    "has_prev": False
                }
            ]
        }
    }

