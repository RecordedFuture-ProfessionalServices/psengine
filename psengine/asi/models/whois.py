from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Optional
import datetime


class WHOISContact(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    organization: Optional[str] = None
    is_current: Optional[bool] = True
    additional_properties: dict[str, Any] = Field(default_factory=dict)


class WHOISRecord(BaseModel):
    registrar: Optional[str] = None
    expires_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    created_at: Optional[datetime.datetime] = None
    is_private: Optional[bool] = None
    is_from_parent: Optional[bool] = False
    contacts: Optional[list[WHOISContact]] = None
    name_servers: Optional[list[str]] = None
    additional_properties: dict[str, Any] = Field(default_factory=dict)
