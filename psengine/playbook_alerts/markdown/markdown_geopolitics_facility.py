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
from datetime import datetime
from typing import TYPE_CHECKING

from markdown_strings import bold, link

from ...markdown import MarkdownMaker, divider

if TYPE_CHECKING:
    from ...playbook_alerts.playbook_alerts import PBA_GeopoliticsFacility

IMG_PORTAL_URL = 'https://app.recordedfuture.com/portal/intelligence-card/{}/overview'


def _format_timestamp(time: datetime):
    return time.strftime('%b %d, %Y, %H:%M %Z') if time else ''


def _add_event_summary(pba: 'PBA_GeopoliticsFacility', md_maker: MarkdownMaker) -> None:
    panel = pba.panel_overview
    loc = panel.location_distance
    result = [
        f'{bold("What:")} {panel.event_type}  ' if panel.event_type else '',
        f'{bold("When:")} {_format_timestamp(panel.event_time)}  ' if panel.event_time else '',
        f'{bold("Source:")} {panel.source}  ' if panel.source else '',
    ]

    if loc.number or loc.unit or loc.facility_name:
        where = '{} {} {} from {}  '.format(
            bold('Where:'), loc.number or '', loc.unit or '', loc.facility_name or ''
        )
        result.insert(2, where)

    result = [r for r in result if r]
    if result:
        md_maker.add_section('Overview', result)


def _add_images(pba: 'PBA_GeopoliticsFacility', md_maker: MarkdownMaker) -> None:
    if not pba.images:
        return
    images = []
    for i, img_id in enumerate(pba.image_ids, 1):
        img = base64.b64encode(pba.images[img_id]['image_bytes']).decode('utf-8')
        images.extend(
            [
                bold(f'Image {i}')
                + f' - {link("See image in Portal", IMG_PORTAL_URL.format(img_id))}',
                f'![img](data:image/png;base64,{img})\n\n',
                divider(),
            ]
        )

    if images:
        md_maker.add_section('Images', images)


def _add_events(pba: 'PBA_GeopoliticsFacility', md_maker: MarkdownMaker) -> None:
    result = []
    for event in pba.panel_events_summary.events:
        section = [
            f'{bold("When:")} {_format_timestamp(event.time)}  ',
            f'{bold("Source:")} {event.source} - {event.url} ',
            f'{event.translated_text}  ',
        ]
        title = ', '.join(assessment.name for assessment in event.assessments)
        result.append(bold(title))
        result.append('\n'.join(section))
        result.append(divider())

    if len(result) == 0:
        md_maker.add_section('Events', ['No events found'])

    md_maker.add_section('Events', result)


def _geopolitics_facility_markdown(pba: 'PBA_GeopoliticsFacility', md_maker: MarkdownMaker, *args):  # noqa: ARG001
    _add_event_summary(pba, md_maker)

    if targets := pba.panel_status.entity_name:
        md_maker.add_section('Target', targets)

    if pba.panel_overview.ai_insights:
        md_maker.add_section('AI Insights', f'{pba.panel_overview.ai_insights}  ')

    if pba.panel_events_summary.events:
        _add_events(pba, md_maker)

        if not md_maker.character_limit:
            _add_images(pba, md_maker)

    return md_maker.format_output()
