##################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. Recorded Future makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. Recorded Future shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #
##############################################################################################

from pathlib import Path

from psengine.analyst_notes import AnalystNoteMgr
from psengine.classic_alerts import ClassicAlertMgr
from psengine.enrich import SoarMgr
from psengine.enrich.lookup_mgr import LookupMgr
from psengine.logger import RFLogger
from psengine.playbook_alerts.playbook_alert_mgr import PlaybookAlertMgr

LOG = RFLogger().get_logger()

OUTPUT_DIR = Path(__file__).parent / 'md'


def markdown_analyst_note():
    note_id = 'wazc3I'
    mgr = AnalystNoteMgr()
    note = mgr.lookup(note_id)

    LOG.info(f'Writing to file Analyst Note {note_id} with html_tags=False')
    (OUTPUT_DIR / f'analyst_note_{note_id}_html_False.md').write_text(note.markdown())

    LOG.info('Writing to file Analyst Note with html_tags=True')
    (OUTPUT_DIR / f'analyst_note_{note_id}_html_True.md').write_text(note.markdown(html_tags=True))


def markdown_classic_alert():
    mgr = ClassicAlertMgr()
    search_results = mgr.search(max_results=1)
    alert_id = search_results[0].id_
    alert = mgr.fetch(alert_id)

    LOG.info(f'Writing to file Classic Alert {alert_id} with html_tags=False')
    (OUTPUT_DIR / f'classic_alert_{alert_id}_html_False.md').write_text(alert.markdown())

    LOG.info('Writing to file Classic Alert with html_tags=True')
    (OUTPUT_DIR / f'classic_alert_{alert_id}_html_True.md').write_text(
        alert.markdown(html_tags=True)
    )

    LOG.info('Writing to file Classic Alert with defang_iocs=True')
    (OUTPUT_DIR / f'classic_alert_{alert_id}_defang_iocs.md').write_text(
        alert.markdown(defang_iocs=True)
    )


def markdown_standard_playbook_alert(pa_mgr: PlaybookAlertMgr, category):
    """Print the markdown of Playbook alerts that do not allow extra objects.

    This includes:
         - Domain Abuse
         - Code Repo
         - Geopol
         - Identity
    """
    LOG.info('Example of standard PBAs without extra_context specified when calling markdown()')
    search_result = pba_mgr.search(category=category, max_results=1)
    if search_result.counts.returned == 0:
        # The supplied token did not have access to this alert category
        # or the were no alerts in this category
        return

    alert_id = search_result.data[0].playbook_alert_id
    alert = pa_mgr.fetch(alert_id, category)
    LOG.info(f'Writing to file {category} PBA markdown for {alert_id}')
    # Please note html_tags are also supported here
    (OUTPUT_DIR / f'pba_{category}_standard.md').write_text(alert.markdown())


def markdown_tpr_advanced(pba_mgr: PlaybookAlertMgr, category):
    # Some alerts like the TPR can be improved by enriching:
    # - IPs from the alert
    # - the company that the alert is raised against
    LOG.info('Example of TPR enriched via SOAR and returning HTML output')
    alert_id = 'task:85743a62-fa26-43a4-aadf-cf3563dfa3a3'
    alert = pba_mgr.fetch(alert_id, category)
    soar_mgr = SoarMgr()
    lookup_mgr = LookupMgr()
    # Use the @property to get all IPs from the alert and enrich using SOAR
    ips = alert.all_ip_addresses
    extra_context = soar_mgr.soar(ip=ips)

    # Enrich the company that the alert is raised against
    extra_context.append(
        lookup_mgr.lookup(
            alert.panel_status.entity_id, 'company', ['aiInsights', 'timestamps', 'intelCard']
        )
    )
    LOG.info(f'Writing to file {category} PBA markdown with extra_context for {alert_id}')
    (OUTPUT_DIR / f'pba_{category}_tpr_advanced.md').write_text(
        alert.markdown(
            extra_context=extra_context,
            html_tags=True,
        )
    )


def markdown_cyber_vuln_advanced(pba_mgr, category):
    LOG.info('Example of Cyber Vulnerability enriched via lookup, with aiInsight and CVSS info.')

    search_result = pba_mgr.search(category=category, max_results=1)
    if search_result.counts.returned == 0:
        # The supplied token did not have access to this alert category
        # or the were no alerts in this category
        return

    alert_id = search_result.data[0].playbook_alert_id
    alert = pba_mgr.fetch(alert_id, category)
    lookup_mgr = LookupMgr()
    extra_context = [
        lookup_mgr.lookup(
            alert.panel_status.entity_name,
            'vulnerability',
            fields=['aiInsights', 'cvssv2', 'cvssv3'],
        )
    ]
    analyst_note_mgr = AnalystNoteMgr()
    insikt_notes = [analyst_note_mgr.lookup(id_) for id_ in alert.insikt_note_ids]
    extra_context.extend(insikt_notes)

    LOG.info(f'Writing to file {category} PBA markdown with extra_context for {alert_id}')
    (OUTPUT_DIR / f'pba_{category}_cyber_vuln_advanced.md').write_text(
        alert.markdown(
            extra_context=extra_context,
            html_tags=True,
        )
    )


if __name__ == '__main__':
    OUTPUT_DIR.mkdir(exist_ok=True)
    markdown_analyst_note()
    markdown_classic_alert()
    PBAS_CATEGORIES = [
        'domain_abuse',
        'code_repo_leakage',
        'identity_novel_exposures',
        # 'geopolitics_facility',
        'third_party_risk',
        'cyber_vulnerability',
    ]
    pba_mgr = PlaybookAlertMgr()

    for category in PBAS_CATEGORIES:
        markdown_standard_playbook_alert(pba_mgr, category)

    # The examples below are for PBAs for which the markdown output
    # can be extended with additional context
    markdown_tpr_advanced(pba_mgr, 'third_party_risk')
    markdown_cyber_vuln_advanced(pba_mgr, 'cyber_vulnerability')

    LOG.info(f'Please see {OUTPUT_DIR} for the markdown files.')
