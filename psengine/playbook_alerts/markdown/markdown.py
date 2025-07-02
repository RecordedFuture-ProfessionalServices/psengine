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

from markdown_strings import bold, link

from ...constants import TIMESTAMP_STR, TRUNCATE_COMMENT
from ...markdown import (
    MarkdownMaker,
)
from ..pa_category import PACategory
from .markdown_code_repo import _code_repo_markdown
from .markdown_cyber_vulnerability import _cyber_vulnerability_markdown
from .markdown_domain_abuse import _domain_abuse_markdown
from .markdown_geopolitics_facility import _geopolitics_facility_markdown
from .markdown_identity_exposure import _identity_exposure_markdown
from .markdown_malware_report import _malware_report_markdown
from .markdown_third_party_risk import _third_party_risk_markdown

PORTAL_URL = 'https://app.recordedfuture.com/portal/playbook-alerts/{}'
API_URL = 'https://api.recordedfuture.com/playbook-alert/{}/{}'


MARKDOWN_BY_PBA_TYPE = {
    PACategory.CODE_REPO_LEAKAGE.value: _code_repo_markdown,
    PACategory.DOMAIN_ABUSE.value: _domain_abuse_markdown,
    PACategory.IDENTITY_NOVEL_EXPOSURES.value: _identity_exposure_markdown,
    PACategory.THIRD_PARTY_RISK.value: _third_party_risk_markdown,
    PACategory.GEOPOLITICS_FACILITY.value: _geopolitics_facility_markdown,
    PACategory.CYBER_VULNERABILITY.value: _cyber_vulnerability_markdown,
    PACategory.MALWARE_REPORT.value: _malware_report_markdown,
}


def _generic_pba_summary(pba, md_maker: MarkdownMaker):
    md_maker.add_title(pba.panel_status.case_rule_label)
    id_ = pba.playbook_alert_id
    general_info = [
        f'{bold("ID:")} {id_}  ',
        f'{bold("Created:")} {pba.panel_status.created.strftime(TIMESTAMP_STR)}  ',
        f'{bold("Updated:")} {pba.panel_status.updated.strftime(TIMESTAMP_STR)}  ',
        f'{bold("Status:")} {pba.panel_status.status}  ',
        f'{bold("Priority:")} {pba.panel_status.priority}  ',
        '{} | {}'.format(
            link('API', API_URL.format(pba.category, id_)), link('Portal', PORTAL_URL.format(id_))
        ),
    ]
    md_maker.add_section('Summary', general_info)


def _unsupported_pba(pba, *args, **kwargs) -> str:  # noqa: ARG001
    raise NotImplementedError(f'No markdown function for playbook alert category: {pba.category}')


def _markdown_playbook_alert(
    playbook_alert,
    html_tags: bool = True,
    character_limit: int = None,
    defang_iocs: bool = False,
    iocs_to_defang: list = None,
    extra_context: list = None,
) -> str:
    md_maker = MarkdownMaker(
        addendum=TRUNCATE_COMMENT.format(
            type_='alert', url=PORTAL_URL.format(playbook_alert.playbook_alert_id)
        ),
        character_limit=character_limit,
        defang_iocs=defang_iocs,
        iocs_to_defang=iocs_to_defang or [],
    )
    _generic_pba_summary(playbook_alert, md_maker)

    if markdown := MARKDOWN_BY_PBA_TYPE.get(playbook_alert.category, _unsupported_pba)(
        playbook_alert, md_maker, html_tags, extra_context
    ):
        return markdown

    return md_maker.format_output()
