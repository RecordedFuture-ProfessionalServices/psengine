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
from ...markdown import MarkdownMaker
from ...markdown.markdown import divider, table_from_rows
from ...markdown.markdown_strings import bold

if TYPE_CHECKING:
    from ...playbook_alerts.playbook_alerts import PBA_CompromisedBankChecks


def _add_images(pba: 'PBA_CompromisedBankChecks', md_maker: MarkdownMaker):
    images = []
    for image in pba.images:
        if pba.panel_evidence_summary.collected_date:
            formatted_timestamp = pba.panel_evidence_summary.collected_date.strftime(TIMESTAMP_STR)
            images.append(f'{bold("Created:")} {formatted_timestamp}  ')

        b64_image = base64.b64encode(pba.images[image]['image_bytes']).decode('utf-8')
        images.append(f'![img](data:image/png;base64,{b64_image})')
        images.append(divider())

    md_maker.add_section('Images', images)


def _add_check_attributes(pba: 'PBA_CompromisedBankChecks', md_maker: MarkdownMaker):
    attributes = []
    if pba.panel_evidence_summary.check_date:
        formatted_timestamp = pba.panel_evidence_summary.check_date.strftime(TIMESTAMP_STR)
        attributes.append(f'{bold("Check Date:")}  {formatted_timestamp}  ')

    if pba.panel_evidence_summary.expired:
        attributes.append(f'{bold("Expired:")}  {pba.panel_evidence_summary.expired}  ')

    if pba.panel_evidence_summary.amount:
        attributes.append(f'{bold("Amount:")}  {pba.panel_evidence_summary.amount}  ')

    if pba.panel_evidence_summary.check_number:
        attributes.append(f'{bold("Check Number:")}  {pba.panel_evidence_summary.check_number}  ')

    if len(attributes):
        md_maker.add_section('Check Attributes', attributes)


def _add_bank_identifiers(pba: 'PBA_CompromisedBankChecks', md_maker: MarkdownMaker):
    bank_identifiers = []
    if pba.panel_evidence_summary.fraction_number:
        bank_identifiers.append(
            f'{bold("Fraction Number:")} {pba.panel_evidence_summary.fraction_number}  '
        )

    if pba.panel_evidence_summary.bank:
        bank_identifiers.append(f'{bold("Bank:")} {pba.panel_evidence_summary.bank}  ')

    if pba.panel_evidence_summary.bank_routing_number:
        bank_identifiers.append(
            f'{bold("Bank Routing Number:")} {pba.panel_evidence_summary.bank_routing_number}  '
        )

    if bank_identifiers:
        md_maker.add_section('Bank Identifiers', bank_identifiers)


def _add_seen_details(pba: 'PBA_CompromisedBankChecks', md_maker: MarkdownMaker):
    seen_details = []
    if pba.panel_evidence_summary.previously_seen:
        seen_details.append(
            f'{bold("Seen:")} Previously Seen {len(pba.panel_evidence_summary.seen_ids)} Time(s)  '
        )
        if pba.panel_evidence_summary.seen_dates:
            sorted_seen_times = sorted(pba.panel_evidence_summary.seen_dates)
            seen_details.append(
                f'{bold("First Seen:")} {sorted_seen_times[0].strftime(TIMESTAMP_STR)}  '
            )
            seen_details.append(
                f'{bold("Last Seen:")} {sorted_seen_times[-1].strftime(TIMESTAMP_STR)}  '
            )

    else:
        seen_details.append(f'{bold("Seen:")} First Appearance  ')

    if seen_details:
        md_maker.add_section('Seen', seen_details)


def _add_collection_dates(pba: 'PBA_CompromisedBankChecks', md_maker: MarkdownMaker):
    collection_dates = []
    if pba.panel_evidence_summary.posted_date:
        collection_dates.append(
            f'{bold("Posted Date:")} {pba.panel_evidence_summary.collected_date}  '
        )

    if pba.panel_evidence_summary.posted_date:
        collection_dates.append(
            f'{bold("Collected Date:")} {pba.panel_evidence_summary.posted_date}  '
        )

    if len(collection_dates):
        md_maker.add_section('Collection Dates', collection_dates)


def _add_payment_details(pba: 'PBA_CompromisedBankChecks', md_maker: MarkdownMaker):
    details = [
        ['', 'Identity 1', 'Identity 2'],
        [
            'Identity',
            pba.panel_evidence_summary.identity_1 or '-',
            pba.panel_evidence_summary.identity_2 or '-',
        ],
        [
            'Address',
            pba.panel_evidence_summary.address_1 or '-',
            pba.panel_evidence_summary.address_2 or '-',
        ],
        [
            'City',
            pba.panel_evidence_summary.city_1 or '-',
            pba.panel_evidence_summary.city_2 or '-',
        ],
        [
            'State',
            pba.panel_evidence_summary.state_1 or '-',
            pba.panel_evidence_summary.state_2 or '-',
        ],
        [
            'Zip',
            pba.panel_evidence_summary.zip_1 or '-',
            pba.panel_evidence_summary.zip_2 or '-',
        ],
    ]

    md_maker.add_section('Payer & Payee Identifiers', table_from_rows(details))


def _add_source_information(pba: 'PBA_CompromisedBankChecks', md_maker: MarkdownMaker):
    sources = []
    if pba.panel_evidence_summary.source_id:
        sources.append(f'{bold("Source ID:")} {pba.panel_evidence_summary.source_id}  ')

    if pba.panel_evidence_summary.source_type:
        sources.append(f'{bold("Source Type:")} {pba.panel_evidence_summary.source_type}  ')

    if pba.panel_evidence_summary.post_url:
        md_maker.iocs_to_defang.append(pba.panel_evidence_summary.post_url)
        sources.append(f'{bold("Post URL:")} {pba.panel_evidence_summary.post_url}  ')

    if pba.panel_evidence_summary.actor:
        sources.append(f'{bold("Actor:")} {pba.panel_evidence_summary.actor}  ')

    if pba.panel_evidence_summary.actor_url:
        md_maker.iocs_to_defang.append(pba.panel_evidence_summary.actor_url)
        sources.append(f'{bold("Actor URL:")} {pba.panel_evidence_summary.actor_url}  ')

    if sources:
        md_maker.add_section('Source Information', sources)


def _compromised_bank_check_markdown(
    pba: 'PBA_CompromisedBankChecks',
    md_maker: MarkdownMaker,
    *args,  # noqa: ARG001
) -> str:
    if pba.images and not md_maker.character_limit:
        _add_images(pba, md_maker)

    _add_check_attributes(pba, md_maker)
    _add_bank_identifiers(pba, md_maker)
    _add_payment_details(pba, md_maker)
    _add_seen_details(pba, md_maker)
    _add_collection_dates(pba, md_maker)
    _add_source_information(pba, md_maker)

    return md_maker.format_output()
