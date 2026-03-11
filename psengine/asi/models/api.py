from typing import Optional

from pydantic import BaseModel


class PaginationResponse(BaseModel):
    next_cursor: Optional[str] = None
    limit: Optional[int] = 50
    total: Optional[int] = None
    sort: Optional[list[list[str]]] = None


class ApiCount(BaseModel):
    returned: int
    total: Optional[int] = None


class ApiMeta(BaseModel):
    counts: Optional[ApiCount] = None
    pagination: Optional[PaginationResponse] = None
    request_id: Optional[str] = None


class Pagination(BaseModel):
    next_cursor: Optional[str] = None
    limit: Optional[int] = 50
