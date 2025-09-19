import os

from pydantic import BaseModel

from psengine.config import Config, ConfigModel, get_config
from psengine.enrich import LookupMgr
from psengine.playbook_alerts import PlaybookAlertMgr

CONFIG_PATH = os.path.join(os.getcwd(), "int_config.toml")


class PBAConfig(BaseModel):
    """Config for playbook alerts."""

    category: str
    statuses: list[str]
    priority: str
    lookback: str


class EnrichConfig(BaseModel):
    """Config for IOC enrichment."""

    fields: list[str]


class IntegrationConfig(ConfigModel):
    """The main integration config."""

    pba: PBAConfig
    enrich: EnrichConfig


Config.init(
    config_class=IntegrationConfig, config_path=CONFIG_PATH
)
config = get_config()

pba_mgr = PlaybookAlertMgr()
enrich_mgr = LookupMgr()

alerts = pba_mgr.fetch_bulk(
    category=config.pba.category,
    statuses=config.pba.statuses,
    priority=config.pba.priority,
    created_from=config.pba.lookback,
)

domains = [
    alert.panel_status.entity_name for alert in alerts
]
enriched_domains = enrich_mgr.lookup_bulk(
    domains, "domain", fields=config.enrich.fields
)

for enriched in enriched_domains:
    print(enriched)
