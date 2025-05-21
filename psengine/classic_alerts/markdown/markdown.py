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

import re
from itertools import chain

from markdown_strings import blockquote, bold, esc_format, link

from ...constants import TIMESTAMP_STR, TRUNCATE_COMMENT
from ...markdown import (
    MarkdownMaker,
    clean_text,
    escape_pipe_characters,
    html_textarea,
    table_from_rows,
)
from ..constants import MARKDOWN_ENTITY_TYPES_TO_DEFANG
from ..errors import AlertMarkdownError

TRIGGERED_BY_HTML = (
    '<details>\n<summary>Triggered By (Click to expand)\n</summary>\n- {}\n</details>\n'
)


def _clean_title(alert_title: str) -> str:
    """Utility function to remove the new references count from the legacy alert title.

    INPUT:  "Leaked Credentials Monitoring - 1 reference"
    OUTPUT: "Leaked Credentials Monitoring"
    """
    alert_title = alert_title.strip()
    expression = re.compile(r'(\-\s\d+(\+?)\sreference(s?))')

    return re.sub(expression, '', alert_title).strip()


def _owner_org_markdown(classic_alert) -> list[str]:
    results = []
    details = classic_alert.owner_organisation_details

    if not details:
        return []

    if details.enterprise_name:
        results.append(f"{bold('Enterprise:')} {details.enterprise_name}  ")
    if details.owner_name:
        results.append(f"{bold('Owner:')} {details.owner_name}  ")

    orgs = [[org.organisation_id, org.organisation_name] for org in details.organisations]
    orgs.insert(0, ['Organisation ID', 'Organisation Name'])
    results.append(table_from_rows(orgs))

    return results


def _process_hit_fragment(
    hit, include_triggered_by: bool, html_tags: bool, classic_alert
) -> tuple[str, str]:
    content = []
    authors = ', '.join(author.name for author in hit.document.authors)

    title_line = f' From {hit.document.source.name}'
    if authors:
        content.append(f"{bold('Author(s):')} {authors}\n")

    if hit.document.title and hit.fragment:
        first_half_title = hit.document.title[: (len(hit.document.title) // 2)]
        if not hit.fragment.lower().startswith(first_half_title.lower()):
            content.append(f"{bold('Title:')} {clean_text(hit.document.title)}\n")
    elif hit.document.title and not hit.fragment:
        content.append(f"{bold('Title:')} {clean_text(hit.document.title)}\n")

    if hit.document.url:
        content.append(f"{bold('URL:')} {hit.document.url}\n")

    if hit.fragment:
        fragment = (
            html_textarea(clean_text(hit.fragment)) if html_tags else clean_text(hit.fragment)
        )
        content.append(f'{blockquote(fragment)}\n')
    else:
        content.append(
            f"_Reference text is missing, check the Recorded Future {link('Portal', str(classic_alert.url.portal))} for more information._\n"  # noqa: E501
        )

    if include_triggered_by:
        triggered_by = classic_alert.triggered_by_from_hit(hit)
        if triggered_by:
            triggered_by = '\n+ '.join(triggered_by).replace('->', '→')
            if html_tags:
                triggered_by = TRIGGERED_BY_HTML.format(triggered_by)
                content.append(triggered_by)
            else:
                content.append(f"{bold('Triggered By:')}\n+ {triggered_by}\n")

    return title_line, content


def _process_entities(entities, hit) -> list[list[str]]:
    if entities is None:
        if not any(entity.description for entity in hit.entities):
            entities = [[entity.name, entity.type_] for entity in hit.entities]
            entity_headers = ['Entity', 'Type']
        else:
            entities = [
                [entity.name, entity.type_, entity.description or ''] for entity in hit.entities
            ]
            entity_headers = ['Entity', 'Type', 'Description']
        entities.insert(0, entity_headers)
    else:
        for entity in hit.entities:
            entities.append([entity.name, entity.type_, entity.description or ''])

    return entities


def _hits_markdown(
    classic_alert,
    hits,
    include_fragment_entities: bool = True,
    include_triggered_by: bool = True,
    html_tags: bool = False,
) -> list:
    sections = []
    for idx, hit in enumerate(hits):
        section = {
            'title': f'{idx + 1}.',
            'content': [],
        }

        title_line, fragment_content = _process_hit_fragment(
            hit, include_triggered_by, html_tags, classic_alert
        )
        section['title'] += title_line
        section['content'].extend(fragment_content)

        entities = None
        if hit.primary_entity and include_fragment_entities:
            description = 'This is the primary entity for this reference'
            if hit.primary_entity.description:
                description += f'.\n{hit.primary_entity.description}'
            entities = [[hit.primary_entity.name, hit.primary_entity.type_, description]]
            entity_headers = ['Entity', 'Type', 'Description']
            entities.insert(0, entity_headers)

        if hit.entities and include_fragment_entities:
            entities = _process_entities(entities, hit)

        if entities:
            section['content'].append(table_from_rows(entities))

        if idx < len(hits) - 1:
            section['content'].append('\n---\n')

        sections.append(section)

    return sections


def _enriched_entities_markdown(classic_alert) -> list:
    results = []
    for entity in classic_alert.enriched_entities:
        if not entity.evidence:
            continue

        criticality = entity.criticality
        contents = [
            f"{bold('Risk Score:')} {criticality.score}",
            f"{bold('Criticality:')} {criticality.name}",
            f"{bold('Triggered:')} {criticality.triggered.strftime(TIMESTAMP_STR)}",
            f"{bold('Last Triggered:')} {criticality.last_triggered.strftime(TIMESTAMP_STR)}  \n\n",
        ]

        evidences = []
        for evidence in sorted(entity.evidence, key=lambda x: x.criticality, reverse=True):
            evidence_result = [
                evidence.criticality,
                evidence.rule,
                escape_pipe_characters(evidence.evidence_string),
                evidence.timestamp.strftime(TIMESTAMP_STR),
            ]
            evidences.append(evidence_result)
        evidences.insert(0, ['Rule Criticality', 'Rule', 'Evidence', 'Timestamp'])
        contents.append(table_from_rows(evidences))
        results.append((entity.entity.name, contents))

    return results


def _target_entities_markdown(classic_alert, html_tags: bool = False) -> list:
    results = []
    for entity in classic_alert.enriched_entities:
        result = {'title': f'Target {entity.entity.name}'}
        result['content'] = _hits_markdown(
            classic_alert,
            hits=entity.references,
            include_fragment_entities=False,
            html_tags=html_tags,
        )
        if len(result['content']):
            results.append(result)

    return results


def _create_summary_section(ca) -> None:
    summary_content = [
        f"{bold('ID:')} {ca.id_}  ",
        f"{bold('Triggered:')} {ca.log.triggered.strftime(TIMESTAMP_STR)}  ",
        f"{bold('Alerting Rule:')} {ca.rule.name}  ",
        f"{link('API', str(ca.url.api))} | {link('Portal', str(ca.url.portal))}",
    ]
    return summary_content


def _get_entities_to_defang(classic_alert) -> set:
    """Return a set of IOC entities to defang from the classic_alert hits."""
    if not classic_alert.hits:
        return set()

    raw_entities = {
        entity.name
        for entity in chain.from_iterable(h.entities for h in classic_alert.hits)
        if entity.type_ in MARKDOWN_ENTITY_TYPES_TO_DEFANG
    }
    defanged_entities = raw_entities.union({esc_format(ent, esc=True) for ent in raw_entities})
    return defanged_entities


def _add_summary_section(md_maker: MarkdownMaker, classic_alert) -> None:
    """Adds the 'Summary' section to the markdown builder."""
    md_maker.add_title(_clean_title(classic_alert.title))
    md_maker.add_section('Summary', _create_summary_section(classic_alert))


def _add_owner_org_section(md_maker: MarkdownMaker, classic_alert, owner_org: bool) -> None:
    """Adds 'Owner Organisation Details' section if owner_org is True and details are present."""
    if owner_org and classic_alert.owner_organisation_details:
        md_maker.add_section('Owner Organisation Details', _owner_org_markdown(classic_alert))


def _add_ai_insights_section(md_maker: MarkdownMaker, classic_alert, ai_insights: bool) -> None:
    """Adds the 'AI Insights' sections if ai_insights is True and data is present."""
    if ai_insights and classic_alert.ai_insights:
        if classic_alert.ai_insights.text:
            md_maker.add_section('AI Insights', [classic_alert.ai_insights.text])
        if classic_alert.ai_insights.comment:
            md_maker.add_section(
                'AI Insights', [f"{bold('Comment:')} {classic_alert.ai_insights.comment}"]
            )


def _add_enriched_entities_sections(
    md_maker: MarkdownMaker, classic_alert, html_tags: bool
) -> None:
    """Adds sections related to enriched entities (evidence and references)."""
    if any(x.evidence for x in classic_alert.enriched_entities):
        for entity, contents in _enriched_entities_markdown(classic_alert):
            md_maker.add_section(entity, contents)

    if any(x.references for x in classic_alert.enriched_entities):
        md_maker.add_section(
            'Target Entities',
            _target_entities_markdown(classic_alert, html_tags),
        )


def _add_hits_section_if_no_enriched_entities(
    md_maker: MarkdownMaker,
    classic_alert,
    fragment_entities: bool,
    triggered_by: bool,
    html_tags: bool,
) -> None:
    """If there are no enriched entities, add a 'References' section from alert hits."""
    if classic_alert.hits:
        md_maker.add_section(
            'References',
            _hits_markdown(
                classic_alert,
                hits=classic_alert.hits,
                include_fragment_entities=fragment_entities,
                include_triggered_by=triggered_by,
                html_tags=html_tags,
            ),
        )


def _markdown_alert(
    classic_alert,
    owner_org: bool = False,
    ai_insights: bool = True,
    fragment_entities: bool = True,
    triggered_by: bool = True,
    html_tags: bool = False,
    character_limit: int = None,
    defang_iocs: bool = False,
) -> str:
    """Returns a markdown string representation of the ``ClassicAlert`` instance.

    This function works on ``ClassicAlert`` instances returned by ``ClassicAlertMgr.fetch()``,
    if you are passing the result of ``ClassicAlertMgr.search()`` make sure the ``search`` method
    has been called with all the fields. Keep in mind that this will make the ``search`` slower.

    Args:
        classic_alert (ClassicAlert): ClassicAlert instance to create markdown from.
        owner_org (bool, optional): Include owner org details. Defaults to False.
        ai_insights (bool, optional): Include AI insights. Defaults to True.
        fragment_entities (bool, optional): Include fragment entities. Defaults to True.
        triggered_by (bool, optional): Include triggered by. Defaults to True.
        html_tags (bool, optional): Include HTML tags in the markdown. Defaults to False.
        character_limit (int, optional): Character limit for the markdown. Defaults to None.
        defang_iocs (bool, optional): Defang IOCs in hits. Defaults to False.

    Raises:
        AlertMarkdownError: If fields are not available.

    Returns:
        str: Markdown representation of the alert.
    """
    try:
        entities_to_defang = _get_entities_to_defang(classic_alert)

        md_maker = MarkdownMaker(
            TRUNCATE_COMMENT.format(type_='alert', url=str(classic_alert.url.portal)),
            character_limit=character_limit,
            defang_iocs=defang_iocs,
            iocs_to_defang=entities_to_defang,
        )

        _add_summary_section(md_maker, classic_alert)
        _add_owner_org_section(md_maker, classic_alert, owner_org)
        _add_ai_insights_section(md_maker, classic_alert, ai_insights)

        if classic_alert.enriched_entities:
            _add_enriched_entities_sections(md_maker, classic_alert, html_tags)
        else:
            _add_hits_section_if_no_enriched_entities(
                md_maker, classic_alert, fragment_entities, triggered_by, html_tags
            )

        return md_maker.format_output()

    except AttributeError as ae:
        message = (
            f'Unable to create markdown for {classic_alert.id_}. '
            f'Request all CA fields if you are working with search results. Error: {ae}'
        )
        raise AlertMarkdownError(message=message) from ae
