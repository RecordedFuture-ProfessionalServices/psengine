from pathlib import Path

from psengine.playbook_alerts import PlaybookAlertMgr
from psengine.playbook_alerts.pa_category import PACategory

OUTPUT_DIR = Path(__file__).parent / 'alerts'
OUTPUT_DIR.mkdir(exist_ok=True)

pba_mgr = PlaybookAlertMgr()

new_alerts = pba_mgr.fetch_bulk(
    category=PACategory.THIRD_PARTY_RISK,
    priority='High',
    statuses=['New'],
    created_from='-1d',
)

for alert in new_alerts:
    extra_context = []

    markdown = alert.markdown(html_tags=True)

    out_file = OUTPUT_DIR / f'{alert.playbook_alert_id}.md'
    out_file.write_text(markdown)
