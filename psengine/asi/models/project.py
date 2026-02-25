from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Optional
from uuid import UUID
import datetime
from .api import ApiMeta

class Project(BaseModel):

    id: UUID
    title: str
    scanning_enabled: Optional[bool] = None
    last_scanned_at: Optional[datetime.datetime] = None
    inserted_at: Optional[datetime.datetime] = None
    max_exposure_score: Optional[int] = None
    additional_properties: dict[str, Any] = Field(default_factory=dict)

class ProjectListResponse(BaseModel):

    data: list[Project]
    meta: ApiMeta
    additional_properties: dict[str, Any] = Field(default_factory=dict)
