from psengine.enrich import LookupMgr
from psengine.playbook_alerts import PlaybookAlertMgr
from psengine.playbook_alerts.pa_category import PACategory

pba_mgr = PlaybookAlertMgr()
enrich_mgr = LookupMgr()

alerts = pba_mgr.fetch_bulk(
    category=PACategory.DOMAIN_ABUSE,
    statuses=["New"],
    priority="High",
    created_from="-1d",
)

domains = [
    alert.panel_status.entity_name for alert in alerts
]
enriched_domains = enrich_mgr.lookup_bulk(
    domains, "domain", fields=["links"]
)

for enriched in enriched_domains:
    print(enriched)
