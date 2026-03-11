import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from .api import ApiMeta


class Project(BaseModel):
    id: UUID
    title: str
    scanning_enabled: Optional[bool] = None
    last_scanned_at: Optional[datetime.datetime] = None
    inserted_at: Optional[datetime.datetime] = None
    max_exposure_score: Optional[int] = None


class ProjectListResponse(BaseModel):
    data: list[Project]
    meta: ApiMeta
