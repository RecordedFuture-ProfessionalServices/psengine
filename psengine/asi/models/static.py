from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Optional
import datetime
from .core import AssetState, MembershipType


class StaticType(str, Enum):
    HOSTNAME = 'hostname'
    IPV4 = 'ipv4'
    WILDCARD = 'wildcard'


class StaticAsset(BaseModel):
    asset: str
    membership_type: MembershipType
    static_type: StaticType
    global_state: AssetState
    project_state: AssetState
    inserted_at: Optional[datetime.datetime] = None
    last_applied_at: Optional[datetime.datetime] = None
    delete_requested_at: Optional[datetime.datetime] = None
    deleted_at: Optional[datetime.datetime] = None
    additional_properties: dict[str, Any] = Field(default_factory=dict)


class StaticAssetRule(BaseModel):
    asset: str
    membership_type: MembershipType
    static_type: StaticType
    additional_properties: dict[str, Any] = Field(default_factory=dict)


class StaticAssetRuleError(BaseModel):
    rule: Optional[StaticAssetRule] = None
    failed: Optional[bool] = None
    messages: Optional[list[str]] = None
    additional_properties: dict[str, Any] = Field(default_factory=dict)


class StaticAssetsOperations(BaseModel):
    add_rules: Optional[list[StaticAssetRule]] = None
    remove_rules: Optional[list[StaticAssetRule]] = None
    additional_properties: dict[str, Any] = Field(default_factory=dict)


class StaticAssetsResult(BaseModel):
    added: Optional[list[StaticAssetRule]] = None
    removed: Optional[list[StaticAssetRule]] = None
    errors: Optional[list[StaticAssetRuleError]] = None
    additional_properties: dict[str, Any] = Field(default_factory=dict)
