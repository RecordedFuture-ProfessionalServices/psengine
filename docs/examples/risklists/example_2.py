import json
import os
from pathlib import Path
from typing import Annotated, Union

from pydantic import BeforeValidator, Field, field_validator

from psengine.common_models import RFBaseModel
from psengine.risklists import RisklistMgr

OUTPUT_DIR = os.path.join(os.getcwd(), "risklists")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class TADetail(RFBaseModel):
    """Threat actor details."""

    id_: str = Field(alias="id")
    value: Union[list[str], str]


def arrange_data(data) -> list[dict]:
    """Unpacking fields as a list of dictionaries."""
    data = json.loads(data)
    return [{"id": k, "value": v} for k, v in data.items()]


class TARisklist(RFBaseModel):
    """Custom TA Risklist validator."""

    ioc: str = Field(validation_alias="Name")
    risk_score: int = Field(validation_alias="Risk")
    risk_string: str = Field(validation_alias="RiskString")
    ta_ids: list[str] = Field(
        validation_alias="ThreatActorIDs"
    )
    ta_names: Annotated[
        list[TADetail], BeforeValidator(arrange_data)
    ] = Field(validation_alias="ThreatActorNames")
    ta_aliases: Annotated[
        list[TADetail], BeforeValidator(arrange_data)
    ] = Field(validation_alias="ThreatActorAliases")
    ta_categories: Annotated[
        list[TADetail], BeforeValidator(arrange_data)
    ] = Field(validation_alias="ThreatActorCategories")

    @field_validator("ta_ids", mode="before")
    @classmethod
    def parse_ta_ids(cls, field: str) -> list[str]:
        """ta_ids field from string to list."""
        return json.loads(field)


mgr = RisklistMgr()
risklist = list(
    mgr.fetch_risklist(
        "/public/risklists/ta_ip_risklist_v2.csv",
        validate=TARisklist,
    )
)

out_file = Path(os.path.join(OUTPUT_DIR, "ta_risklist_ip.json"))
out_file.write_text(
    json.dumps(
        [entry.json() for entry in risklist], indent=4
    )
)
