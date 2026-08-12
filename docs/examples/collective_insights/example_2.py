from datetime import UTC, datetime, timedelta

from psengine.collective_insights import CollectiveInsights

ci = CollectiveInsights()

last_week = (datetime.now(UTC) - timedelta(days=7)).isoformat()

events = ci.search(
    indicator_type='ip',
    submission_method=['api', 'integration'],
    malware_id='present',
    detection_time_from=last_week,
    max_results=5,
)

for event in sorted(events, reverse=True):
    print(event)
