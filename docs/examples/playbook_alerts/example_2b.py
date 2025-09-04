from pathlib import Path

from psengine.enrich.lookup_mgr import LookupMgr
from psengine.enrich.soar_mgr import SoarMgr
from psengine.playbook_alerts import PlaybookAlertMgr
from psengine.playbook_alerts.pa_category import PACategory

OUTPUT_DIR = Path(__file__).parent / "alerts"
OUTPUT_DIR.mkdir(exist_ok=True)

pba_mgr = PlaybookAlertMgr()
soar_mgr = SoarMgr()
lookup_mgr = LookupMgr()

new_alerts = pba_mgr.fetch_bulk(
    category=PACategory.THIRD_PARTY_RISK,
    priority="High",
    statuses=["New"],
    created_from="-1d",
)

for alert in new_alerts:
    extra_context = []

    ips = alert.all_ip_addresses
    if ips:
        extra_context = soar_mgr.soar(ip=ips)

    extra_context.append(
        lookup_mgr.lookup(
            alert.panel_status.entity_id,
            "company",
            ["aiInsights", "timestamps", "intelCard"],
        )
    )
    markdown = alert.markdown(
        extra_context=extra_context, html_tags=True
    )

    out_file = OUTPUT_DIR / f"{alert.playbook_alert_id}.md"
    out_file.write_text(markdown)
