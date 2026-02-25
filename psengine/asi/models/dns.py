from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Optional, Union
import datetime

class DNSValueValueType1(BaseModel):

    additional_properties: dict[str, Any] = Field(default_factory=dict)

class DNSValue(BaseModel):

    value: Union[DNSValueValueType1, str]
    last_resolved_at: Optional[datetime.datetime]
    seen_from: Optional[list[str]] = None
    first_seen_at: Optional[datetime.datetime] = None
    additional_properties: dict[str, Any] = Field(default_factory=dict)

class DNSRecord(BaseModel):

    record_type: str
    value: Optional[list[DNSValue]]
    is_virtual: Optional[bool] = False
    additional_properties: dict[str, Any] = Field(default_factory=dict)
