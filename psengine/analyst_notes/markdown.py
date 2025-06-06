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
from collections import defaultdict
from itertools import chain
from typing import TYPE_CHECKING

from markdown_strings import bold, unordered_list

from ..constants import TIMESTAMP_STR
from ..endpoints import EP_ANALYST_NOTE_LOOKUP
from ..markdown.markdown import MarkdownMaker, divider, html_collapsible

if TYPE_CHECKING:
    from ..analyst_notes import AnalystNote

EXTRACTED_KEYS = {
    'AttackVector': 'Attack Vector',
    'Malware': 'Malware',
    'MalwareCategory': 'Malware Category',
    'WinRegKey': 'Windows Registry Key',
    'Hash': 'Hash',
}


def _cleanup_insikt_note_text(note_text: str) -> str:
    """Clean up insikt note text to avoid markdown rendering issues."""
    translation = {
        r'\•': '+ ',
        r'--+': '',
        r'>>+': '',
        r'<<+': '',
        r'\*\*': '••',
        r'#': '\\#',
        r'_': '\\_',
    }
    for k, v in translation.items():
        note_text = re.sub(k, v, note_text)

    return note_text


def _entity_by_type_list(entities: list, entity_type: str) -> list:
    """Extract all the related entities by type."""
    return sorted({entity.name for entity in entities if entity.type_ == entity_type})


def _vuln_list(entities: list) -> list:
    """Extract all the vulnerabilities and add the description if present."""
    vulns = [entity for entity in entities if entity.type_ == 'CyberVulnerability']

    texts = []
    for vuln in sorted(vulns, key=lambda x: x.name):
        text = bold(vuln.name)
        if vuln.description:
            descr = vuln.description.replace('\n', ' ')
            text = f'{text}: {descr}'
        texts.append(text)

    return texts


def _add_extra_entities(note: 'AnalystNote', html_tags: bool, md_maker: MarkdownMaker):
    """Add the Entities Extracted block for EXTRACTED_KEYS types."""
    data = defaultdict(list)
    entities = list(chain(note.attributes.note_entities, note.attributes.context_entities))

    for entity_type, clean_entity_type in EXTRACTED_KEYS.items():
        if extracted := _entity_by_type_list(entities, entity_type):
            data[clean_entity_type].extend(extracted)

    if vulns := _vuln_list(entities):
        data['Vulnerability'].extend(vulns)

    data = dict(sorted(data.items()))
    if data:
        if html_tags:
            md_maker.add_section(
                'Entities',
                [
                    html_collapsible(f'<b>{k}</b>', '\n\n' + unordered_list(v, esc=False)) + '\n'
                    if len(v) > 5
                    else f'{bold(k)}\n{unordered_list(v, esc=False)}\n\n'
                    for k, v in data.items()
                ],
            )
        else:
            md_maker.add_section(
                'Entities',
                [
                    '\n'.join([bold(f'{k}:'), unordered_list(v, esc=False) + '\n'])
                    for k, v in data.items()
                ],
            )


def _add_diamond_model(
    note: 'AnalystNote',
    html_tags: bool,
    defang_malicious_infrastructure: bool,
    md_maker: MarkdownMaker,
):
    """Add all the Diamond Models if present.

    Since a note can have more than one Diamond model for different targets/methods all will be
    displayed.
    The collapsible is only applied to the title (ie. Diamond Model 1) and each section that has
    more than 5 entries.

    """
    html_title = '<h4>Cyber Attack'
    diamond_models, data = [], []
    for diamond_model in note.attributes.diamond_model:
        model = {
            'Malicious Infrastructure': [e.name for e in diamond_model.malicious_infrastructure],
            'Capabilities': [e.name for e in diamond_model.capabilities],
            'Adversary': [e.name for e in diamond_model.adversary],
            'Target': [f'{e.name} ({e.type_})' for e in diamond_model.target],
        }
        if defang_malicious_infrastructure:
            iocs = [ioc.replace('.', '[.]') for ioc in model['Malicious Infrastructure']]
            model['Malicious Infrastructure'] = iocs

        diamond_models.append({k: v for k, v in model.items() if v})

    if html_tags:
        data = [
            html_collapsible(
                f'{html_title} {i}{": " + model["Adversary"][0] if model.get("Adversary") else ""}',
                '\n\n'
                + ''.join(
                    html_collapsible(f'<b>{section}</b>', f'\n\n{unordered_list(sorted(entities))}')
                    + '\n'
                    if len(entities) > 5
                    else f'\n{bold(section)}\n\n{unordered_list(sorted(entities))}\n\n'
                    for section, entities in model.items()
                )
                + f'\n{divider()}',
            )
            + '\n'
            for i, model in enumerate(diamond_models, 1)
        ]

    else:
        data = [
            '\n'
            + bold(
                f'Cyber Attack {i}{": " + model["Adversary"][0] if model.get("Adversary") else ""}'
            )
            + '\n'
            + '\n\n'.join(
                [
                    '\n' + section + ':\n' + unordered_list(sorted(entities))
                    for section, entities in model.items()
                ]
            )
            + f'\n{divider()}\n'
            for i, model in enumerate(diamond_models, 1)
        ]

    if data:
        md_maker.add_section('Diamond Models', data)


def _markdown(
    note: 'AnalystNote',
    extract_entities: bool,
    diamond_model: bool,
    html_tags: bool,
    defang_malicious_infrastructure: bool,
    character_limit: int,
) -> str:
    """Main markdown function."""
    md_maker = MarkdownMaker()
    topic = (
        note.attributes.topic
        if isinstance(note.attributes.topic, list)
        else [note.attributes.topic]
    )
    topic_str = f'{bold("Topic:")} {{}}' if len(topic) == 1 else f'{bold("Topics:")} {{}}'
    intro = [
        f'{bold("ID:")} {note.id_}  ',
        f'{bold("Published:")} {note.attributes.published.strftime(TIMESTAMP_STR)}  ',
        f'{bold("Source:")} {note.source.name}  ',
        topic_str.format(', '.join(t.name for t in topic) + '  '),
    ]
    if validation_urls := '\n- '.join(url.name for url in note.attributes.validation_urls):
        validation_urls = f'\n- {validation_urls}\n'
        intro.append(f'{bold("Validation URLs:")} {validation_urls}')

    intro.append(f'[API]({EP_ANALYST_NOTE_LOOKUP.format(note.id_)}) | [Portal]({note.portal_url})')

    md_maker.add_title(note.attributes.title)
    md_maker.add_section('Summary', intro)

    if extract_entities:
        _add_extra_entities(note, html_tags, md_maker)

    if diamond_model:
        _add_diamond_model(note, html_tags, defang_malicious_infrastructure, md_maker)

    md_maker.add_section('Note', _cleanup_insikt_note_text(note.attributes.text))

    output = md_maker.format_output()
    return output if not character_limit else output[:character_limit]
