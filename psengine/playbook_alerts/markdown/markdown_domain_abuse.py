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

from markdown_strings import bold

from ...constants import TIMESTAMP_STR
from ...helpers import FormattingHelpers
from ...markdown import MarkdownMaker
from ...markdown.markdown import divider, table_from_rows
from ..models.pba_domain_abuse import ValueServer


def _add_screenshots(pba, md_maker: MarkdownMaker):
    screenshots = [f'{bold("Screenshot Count:")} {len(pba.panel_evidence_summary.screenshots)}']
    for screenshot in pba.panel_evidence_summary.screenshots:
        screenshots.append(f'{bold("Created:")} {screenshot.created.strftime(TIMESTAMP_STR)}')

        image = base64.b64encode(pba.images[screenshot.image_id]['image_bytes']).decode('utf-8')

        for mentions in pba.panel_evidence_summary.screenshot_mentions:
            if mentions.screenshot == screenshot.image_id and mentions.url:
                url = FormattingHelpers.cleanup_rf_id(mentions.url)
                md_maker.iocs_to_defang.append(url)
                screenshots.append(f'{bold("Screenshot URL:")} {"".join(url)}')

        screenshots.append(f'![img](data:image/png;base64,{image})')
        screenshots.append(divider())

    md_maker.add_section('Screenshots', screenshots)


def _add_whois(pba, md_maker: MarkdownMaker):
    whois_body = [
        body for body in pba.panel_evidence_whois.body if isinstance(body.value, ValueServer)
    ]

    whois_data = []
    for whois in whois_body:
        entity = FormattingHelpers.cleanup_rf_id(whois.entity)
        md_maker.iocs_to_defang.append(entity)
        whois_entity = f"{bold('Entity:')} {entity}"

        if (v := whois.value) and v.name_servers:
            created_dt, updated_dt, expires_dt = '', '', ''
            name_servers = [FormattingHelpers.cleanup_rf_id(s) for s in v.name_servers]
            servers = f"{bold('Name servers:')} {', '.join(name_servers)}"
            md_maker.iocs_to_defang.extend(name_servers)

            if v.created_date:
                created_dt = f'{bold("Creation Date:")} {v.created_date.strftime(TIMESTAMP_STR)}'

            if v.updated_date:
                updated_dt = f'{bold("Update Date:")} {v.updated_date.strftime(TIMESTAMP_STR)}'

            if v.expires_date:
                expires_dt = f'{bold("Expiration Date:")} {v.expires_date.strftime(TIMESTAMP_STR)}'

            registrar = f'{bold("Registrar:")} {v.registrar_name}' if v.registrar_name else ''

            whois_data.extend(
                [whois_entity, servers, created_dt, updated_dt, expires_dt, registrar]
            )

    if whois_data:
        md_maker.add_section('WHOIS Details', whois_data)


def _add_dns_records(pba, md_maker: MarkdownMaker):
    records = [
        [
            FormattingHelpers.cleanup_rf_id(record.entity),
            record.risk_score,
            record.criticality,
            record.record_type,
            ', '.join(c.context for c in record.context_list if c),
        ]
        for record in pba.panel_evidence_summary.resolved_record_list
    ]
    md_maker.iocs_to_defang.extend(list(zip(*records))[0])

    records.sort(key=lambda x: x[1], reverse=True)
    records.insert(0, ['Entity', 'Risk Score', 'Criticality', 'Record Type', 'Context'])
    evidence_summary = [
        f'{bold("Reason:")} {pba.panel_evidence_summary.explanation}\n',
        f'{table_from_rows(records)}',
    ]

    md_maker.add_section('DNS Records', evidence_summary)


def _domain_abuse_markdown(pba, md_maker: MarkdownMaker, *args) -> str:  # noqa: ARG001
    if targets := pba.panel_status.targets:
        targets = [FormattingHelpers.cleanup_rf_id(t) for t in targets]
        md_maker.iocs_to_defang.extend(targets)
        md_maker.add_section('Targets', targets)

    if pba.panel_evidence_summary.resolved_record_list:
        _add_dns_records(pba, md_maker)

    if pba.panel_evidence_whois:
        _add_whois(pba, md_maker)

    if pba.images and not md_maker.character_limit:
        _add_screenshots(pba, md_maker)

    return md_maker.format_output()
