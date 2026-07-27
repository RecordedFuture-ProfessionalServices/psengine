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

import base64
from typing import TYPE_CHECKING

from ...constants import TIMESTAMP_STR
from ...helpers import FormattingHelpers
from ...markdown import MarkdownMaker
from ...markdown.markdown import divider, table_from_rows
from ...markdown.markdown_strings import bold
from ..models.pba_malicious_sites import ValueServer

if TYPE_CHECKING:
    from ...playbook_alerts.playbook_alerts import PBA_MaliciousSites


def _add_dns_records(pba: 'PBA_MaliciousSites', md_maker: MarkdownMaker):
    records = [
        [
            FormattingHelpers.cleanup_rf_id(record.entity),
            record.risk_score,
            record.criticality,
            record.record_type,
            ', '.join(a.name for a in record.assessments if a and a.name),
        ]
        for record in pba.panel_evidence_summary.resolved_record_list
    ]
    md_maker.iocs_to_defang.extend(list(zip(*records, strict=False))[0])

    records.sort(key=lambda x: x[1] or 0, reverse=True)
    records.insert(0, ['Entity', 'Risk Score', 'Criticality', 'Record Type', 'Assessments'])
    evidence_summary = [
        f'{bold("Reason:")} {pba.panel_evidence_summary.explanation}\n',
        f'{table_from_rows(records)}',
    ]

    md_maker.add_section('DNS Records', evidence_summary)


def _add_whois(pba: 'PBA_MaliciousSites', md_maker: MarkdownMaker):
    whois_body = [
        body for body in pba.panel_evidence_whois.body if isinstance(body.value, ValueServer)
    ]

    whois_data = []
    for whois in whois_body:
        entity = FormattingHelpers.cleanup_rf_id(whois.entity)
        md_maker.iocs_to_defang.append(entity)
        whois_entity = f'{bold("Entity:")} {entity}  '

        if (v := whois.value) and v.name_servers:
            created_dt, updated_dt, expires_dt = '', '', ''
            name_servers = [FormattingHelpers.cleanup_rf_id(s) for s in v.name_servers]
            servers = f'{bold("Name servers:")} {", ".join(name_servers)}  '
            md_maker.iocs_to_defang.extend(name_servers)

            if v.created_date:
                created_dt = f'{bold("Creation Date:")} {v.created_date.strftime(TIMESTAMP_STR)}  '

            if v.updated_date:
                updated_dt = f'{bold("Update Date:")} {v.updated_date.strftime(TIMESTAMP_STR)}  '

            if v.expires_date:
                expires_dt = (
                    f'{bold("Expiration Date:")} {v.expires_date.strftime(TIMESTAMP_STR)}  '
                )

            registrar = f'{bold("Registrar:")} {v.registrar_name}  ' if v.registrar_name else ''

            whois_data.extend(
                [
                    whois_entity,
                    servers,
                    created_dt,
                    updated_dt,
                    expires_dt,
                    registrar,
                ]
            )

    if whois_data:
        md_maker.add_section('WHOIS Details', whois_data)


def _add_screenshots(pba: 'PBA_MaliciousSites', md_maker: MarkdownMaker):
    all_screenshots = [
        screenshot
        for attacker in pba.panel_evidence_summary.attackers
        for screenshot in attacker.screenshots
    ]
    all_mentions = [
        mention
        for attacker in pba.panel_evidence_summary.attackers
        for mention in attacker.screenshot_mentions
    ]

    screenshots = [f'{bold("Screenshot Count:")} {len(all_screenshots)}  ']
    for screenshot in all_screenshots:
        if screenshot.image_id not in pba.images:
            continue

        if screenshot.created:
            screenshots.append(f'{bold("Created:")} {screenshot.created.strftime(TIMESTAMP_STR)}  ')

        image = base64.b64encode(pba.images[screenshot.image_id]['image_bytes']).decode('utf-8')

        for mention in all_mentions:
            if mention.screenshot == screenshot.image_id and mention.url:
                url = FormattingHelpers.cleanup_rf_id(mention.url)
                md_maker.iocs_to_defang.append(url)
                screenshots.append(f'{bold("Screenshot URL:")} {"".join(url)}')

        screenshots.append(f'![img](data:image/png;base64,{image})')
        screenshots.append(divider())

    md_maker.add_section('Screenshots', screenshots)


def _malicious_sites_markdown(
    pba: 'PBA_MaliciousSites',
    md_maker: MarkdownMaker,
    *args,  # noqa: ARG001
) -> str:
    if targets := pba.panel_status.targets:
        targets = [FormattingHelpers.cleanup_rf_id(t) for t in targets]
        md_maker.iocs_to_defang.extend(targets)
        md_maker.add_section('Targets', targets)

    if attackers := pba.panel_status.attackers:
        attackers = [FormattingHelpers.cleanup_rf_id(a) for a in attackers]
        md_maker.iocs_to_defang.extend(attackers)
        md_maker.add_section('Attackers', attackers)

    if pba.panel_evidence_summary.resolved_record_list:
        _add_dns_records(pba, md_maker)

    if pba.panel_evidence_whois:
        _add_whois(pba, md_maker)

    if pba.images and not md_maker.character_limit:
        _add_screenshots(pba, md_maker)

    return md_maker.format_output()
