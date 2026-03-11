from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WHOISContact(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    organization: Optional[str] = None
    is_current: Optional[bool] = True


class WHOISRecord(BaseModel):
    registrar: Optional[str] = None
    expires_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    is_private: Optional[bool] = None
    is_from_parent: Optional[bool] = False
    contacts: Optional[list[WHOISContact]] = None
    name_servers: Optional[list[str]] = None
