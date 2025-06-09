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

import itertools
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from markdown_strings import bold, unordered_list

from ...analyst_notes import AnalystNote
from ...analyst_notes.markdown import _cleanup_insikt_note_text
from ...constants import TIMESTAMP_STR
from ...enrich import EnrichedIP, EnrichmentData, SOAREnrichOut
from ...markdown import MarkdownMaker
from ...markdown.markdown import divider, header, html_collapsible
from ..models.pba_third_party_risk import TPRAssessment

if TYPE_CHECKING:
    from ...playbook_alerts import PBA_ThirdPartyRisk


ASSESSMENT_CATEGORY_MAP = {
    'ip_rule': 'Malicious Network',
    'hosts_communication': 'Malicious Network',
    'reference': 'Security Incidents',
    'cyber_trend': 'Cyber Trend',
    'insikt_note': 'Security Incidents',
}


@dataclass
class MDEnrichedIps:
    """Dataclass for normalizing SOAR and Lookup info."""

    ip: str
    score: int
    evidence_string: list[str]


def _add_assessment_headers(
    assessment: TPRAssessment, title: str, add_evidence: bool = True
) -> str:
    """Add main headers for the assessment.

    Headers are:
        - Title
        - Added
        - Summary
        - Evidence
    """
    title = f'{header(title, 4)}'
    added = (
        f'{bold("Added:")} {assessment.added.strftime(TIMESTAMP_STR)}  ' if assessment.added else ''
    )

    summary = (
        f'{bold("Summary:")} {assessment.evidence.summary}' if assessment.evidence.summary else ''
    )
    evidence = header('Evidence', 5) if add_evidence else ''

    return f'\n{title}\n{added}\n{summary}\n{evidence}\n'


def _format_ip_rule_type(
    assessment: TPRAssessment,
    *,
    pba: 'PBA_ThirdPartyRisk',
    html_tags: bool,
    extra_context: Union[list[MDEnrichedIps], list[AnalystNote]],
    **kwargs,  # noqa: ARG001
) -> str:
    """Format assessment with ip_rule type. Enrich IPs with risk score."""
    ip_info, ip_list = [], []
    tpr_risk_rules, ips_from_summary = pba.ips_from_ip_rule(assessment)
    if not ips_from_summary:
        return ''

    intro = _add_assessment_headers(assessment, tpr_risk_rules)
    extra = [c for c in extra_context if isinstance(c, MDEnrichedIps)]

    for ip_risk_rule, ips in ips_from_summary.items():
        for ip in ips:
            enriched_ip = next((x for x in extra if ip in x.ip), None)
            if enriched_ip:
                ip_list.append(f'\n- {ip} ({enriched_ip.score})')
            else:
                ip_list.append(f'\n- {ip}')

        formatted_risk_rule_with_ip_list = ''
        if html_tags:
            formatted_risk_rule_with_ip_list = html_collapsible(
                f'{ip_risk_rule}', '\n\n' + ''.join(ip_list) + '\n\n'
            )
        else:
            formatted_risk_rule_with_ip_list = f'\n\n{bold(ip_risk_rule)}\n{"".join(ip_list)}'
        ip_info.append(formatted_risk_rule_with_ip_list)

    return f'{intro}{"".join(ip_info)}\n'


def _format_hosts_communication_type(
    assessment: TPRAssessment,
    *,
    pba: 'PBA_ThirdPartyRisk',
    extra_context: Union[list[AnalystNote], list[MDEnrichedIps]],
    html_tags: bool,
    **kwargs,  # noqa: ARG001
) -> str:
    descr = []
    extra = [c for c in extra_context if isinstance(c, MDEnrichedIps)]

    malware_ips_to_enrich = pba.ip_address_by_assessment.get('hosts_communication')

    if not malware_ips_to_enrich:
        return ''

    for row in assessment.evidence.data or []:
        client_ip = row.client_ip_address

        malw_family = row.malware_family
        ip_in_assessment = row.malware_ip_address

        enriched_ip = next((ip for ip in extra if ip.ip == ip_in_assessment), None)

        recent_tmstp = row.recent_timestamp or ''
        if recent_tmstp:
            recent_tmstp = (
                f'{bold("Recent Timestamp")}: {recent_tmstp.strftime("%Y-%m-%d %H:%M:%S")}  '
            )

        if enriched_ip:
            malw_ip_descr = [
                f'{bold("Malware IP Address:")} {ip_in_assessment} ({enriched_ip.score})  ',
                f'{bold("Malware Family:")} {malw_family}  ',
                f'{bold("Malware IP Risk Description:")}\n{enriched_ip.evidence_string}\n\n'
                if enriched_ip.evidence_string
                else '',
            ]
        else:
            malw_ip_descr = [
                f'{bold("Malware IP Address:")} {ip_in_assessment}  ',
                f'{bold("Malware Family:")} {malw_family}  ',
            ]

        malw_ip_descr = '\n'.join(malw_ip_descr)

        if html_tags:
            descr.append(
                html_collapsible(
                    f'<h5>Observed Network Traffic - Client IP: {client_ip}',
                    f'</h5>\n\n{recent_tmstp}\n{malw_ip_descr}',
                )
                + '\n\n'
            )
        else:
            subtitle = header(f'Observed Network Traffic - Client IP: {client_ip}', 5)
            descr.append(f'{subtitle}\n{recent_tmstp}\n{malw_ip_descr}\n\n')

    return ''.join(descr)


def _format_reference_type(
    assessment: TPRAssessment,
    **kwargs,  # noqa: ARG001
) -> str:
    add_evidence = True
    if len(assessment.evidence.data) == 0:
        add_evidence = False

    intro = _add_assessment_headers(assessment, assessment.risk_rule, add_evidence)
    contents = []
    for data in assessment.evidence.data or []:
        title = f'{bold("Title:")} {data.title}  '
        document_url = f'{bold("URL:")} {data.document_url}  ' if data.document_url else ''
        source = f'{bold("Source:")} {data.source}  '
        fragment = f'{bold("Fragment:")} {data.fragment}  '
        published = (
            f'{bold("Published:")} {data.published.strftime(TIMESTAMP_STR)}  '
            if data.published
            else ''
        )

        contents.append(f'{title}\n{published}\n{source}\n{document_url}\n{fragment}\n{divider()}')

    return f'{intro}{"".join(contents)}'


def _format_cyber_trend_type(assessment: TPRAssessment, **kwargs) -> str:  # noqa: ARG001
    return _add_assessment_headers(assessment, f'{assessment.risk_rule}', add_evidence=False)


def _format_insikt_note_type(
    assessment: TPRAssessment,
    *,
    extra_context: list[AnalystNote],
    **kwargs,  # noqa: ARG001
) -> str:
    result = []
    extra = [c for c in extra_context if isinstance(c, AnalystNote)]

    for insikt_note in assessment.evidence.data or []:
        topic = (
            insikt_note.topic
            if isinstance(insikt_note.topic, str)
            else ', '.join(insikt_note.topic)
        )
        note_title = f'{bold("Title:")} {insikt_note.title}  '
        published_date = f'{bold("Published:")} {insikt_note.published.strftime(TIMESTAMP_STR)}  '
        topic = f'{bold("Topic:")} {topic}  '
        note_text = insikt_note.fragment
        validation_urls = ''

        for entity in extra:
            if entity.id_ == insikt_note.id_:
                validation_urls = '\n- '.join(url.name for url in entity.attributes.validation_urls)
                if validation_urls:
                    validation_urls = f'\n- {validation_urls}\n'
                    validation_urls = f'{bold("Validation URLs:")} {validation_urls}'
                note_text = entity.attributes.text

        note_text = f'{bold("Text:")} {_cleanup_insikt_note_text(note_text)}\n'
        note_md = [note_title, published_date, topic, validation_urls, note_text, divider()]
        result.extend(note_md)
    return '\n'.join(result)


def _add_assessments(
    pba: 'PBA_ThirdPartyRisk',
    md_maker: MarkdownMaker,
    html_tags: bool,
    extra_context: Union[list[AnalystNote], list[MDEnrichedIps]],
) -> None:
    results = []
    err = '\nAssessments unavailable. Consult the Recorded Future Portal.\n\n'
    assessment_funcs = {
        'ip_rule': _format_ip_rule_type,
        'hosts_communication': _format_hosts_communication_type,
        'reference': _format_reference_type,
        'cyber_trend': _format_cyber_trend_type,
        'insikt_note': _format_insikt_note_type,
    }
    if pba.panel_evidence_summary.assessments:
        assessments_body = []
        assessments = itertools.groupby(
            sorted(pba.panel_evidence_summary.assessments, key=lambda x: x.evidence.type_),
            key=lambda x: x.evidence.type_,
        )

        for asses_type, assess_data in assessments:
            asses_category = ASSESSMENT_CATEGORY_MAP.get(asses_type)
            category_title = f'{header(asses_category or "", 4)}\n'
            if asses_category and category_title not in assessments_body:
                assessments_body.append(category_title)

            for assessment in assess_data:
                func = assessment_funcs.get(assessment.evidence.type_, lambda *args, **kwargs: None)  # noqa: ARG005
                formatted_assessment = func(
                    assessment, pba=pba, html_tags=html_tags, extra_context=extra_context
                )
                if formatted_assessment:
                    assessments_body.append(formatted_assessment)

        if assessments_body:
            results.append(f'{"".join(assessments_body)}')
        else:
            results.append(err)
    else:
        results.append(err)

    md_maker.add_section('Assessments', results)


def _third_party_risk_markdown(
    pba: 'PBA_ThirdPartyRisk',
    md_maker: MarkdownMaker,
    html_tags: bool,
    extra_context: Union[list[EnrichmentData], list[AnalystNote], list[SOAREnrichOut]],
) -> str:  # noqa: ARG001
    if extra_context is None:
        extra_context = []

    notes = [note for note in extra_context if isinstance(note, AnalystNote)]
    lookup_ips = [
        MDEnrichedIps(
            ip.content.entity.name,
            ip.content.risk.score or 0,
            unordered_list(d.evidence_string for d in ip.content.risk.evidence_details),
        )
        for ip in extra_context
        if isinstance(ip, EnrichmentData) and ip.is_enriched and isinstance(ip.content, EnrichedIP)
    ]
    soar_ips = [
        MDEnrichedIps(
            ip.content.entity.name,
            ip.content.risk.score or 0,
            unordered_list(d.description for d in ip.content.risk.rule.evidence),
        )
        for ip in extra_context
        if isinstance(ip, SOAREnrichOut) and ip.is_enriched
    ]

    extra_context = notes + lookup_ips + soar_ips
    if targets := pba.panel_status.entity_name:
        md_maker.add_section('Target', targets)

    _add_assessments(pba, md_maker, html_tags, extra_context)
    return md_maker.format_output()
