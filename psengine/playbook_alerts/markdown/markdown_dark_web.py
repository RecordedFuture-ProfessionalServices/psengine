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

from typing import TYPE_CHECKING

from ...constants import TIMESTAMP_STR
from ...markdown import MarkdownMaker
from ...markdown.markdown_strings import bold

if TYPE_CHECKING:
    from ...playbook_alerts.playbook_alerts import PBA_DarkWebBrand


def _add_panel_triage(pba: 'PBA_DarkWebBrand', md_maker: MarkdownMaker):
    triage_details = []
    if pba.panel_analysis_report:
        triage_details.append(f'{bold("Assessment")}: {pba.panel_triage.assessment.name}')
        triage_details.append(f'{bold("Criticality")}: {pba.panel_triage.assessment.criticality}')
        triage_details.append(f'{bold("Rational")}: {pba.panel_triage.rationale}')

    if triage_details:
        md_maker.add_section('AI Triage', triage_details)


def _add_matched_assets(pba: 'PBA_DarkWebBrand', md_maker: MarkdownMaker):
    matched_assets = []
    if pba.panel_evidence_summary.matched_assets:
        matched_assets.extend(
            f'{bold("Matched Asset")}: {matched_asset.name}'
            for matched_asset in pba.panel_evidence_summary.matched_assets
        )

    if matched_assets:
        md_maker.add_section('Matched Asset(s)', matched_assets)


def _add_post_details_ransomware(pba: 'PBA_DarkWebBrand', md_maker: MarkdownMaker):
    post_details = []
    details = pba.panel_evidence_summary.details

    if details.source:
        post_details.append(f'{bold("Source")}: {details.source.name}')

    if details.post_details:
        post_details.append(f'{bold("Post Details")}: {details.post_details}')

    if details.post_date:
        post_details.append(f'{bold("Date")}: {details.post_date.strftime(TIMESTAMP_STR)}')

    if post_details:
        md_maker.add_section('Incident Details', post_details)


def _add_post_details_telegram(pba: 'PBA_DarkWebBrand', md_maker: MarkdownMaker):
    post_details = []
    details = pba.panel_evidence_summary.details
    if details.source:
        post_details.append(f'{bold("Source")}: {details.source.name}')

    if details.telegram_channel_title:
        post_details.append(f'{bold("Channel Title")}: {details.telegram_channel_title}')

    if details.post:
        post_details.append(f'{bold("Post")}: {pba.panel_evidence_summary.details.post}')

    if pba.panel_evidence_summary.details.publish_date:
        post_details.append(f'{bold("Date")}: {details.publish_date.strftime(TIMESTAMP_STR)}')

    if post_details:
        md_maker.add_section('Incident Details', post_details)


def _add_post_details_forum_mention(pba: 'PBA_DarkWebBrand', md_maker: MarkdownMaker):
    post_details = []
    details = pba.panel_evidence_summary.details
    if details.post_title:
        post_details.append(f'{bold("Title")}: {details.post_title}')

    if details.post:
        post_details.append(f'{bold("Content")}: {details.post}')

    if details.post_date:
        post_details.append(f'{bold("Date")}: {details.post_date.strftime(TIMESTAMP_STR)}')

    if post_details:
        md_maker.add_section('Post Details', post_details)


def _add_post_details_market_mention(pba: 'PBA_DarkWebBrand', md_maker: MarkdownMaker):
    post_details = []
    details = pba.panel_evidence_summary.details
    if details.source:
        post_details.append(f'{bold("Source")}: {details.source.name}')

    if details.listing_title:
        post_details.append(f'{bold("Listing Title")}: {details.listing_title}')

    if details.listing_content:
        post_details.append(f'{bold("Listing Content")}: {details.listing_content}')

    if details.post_date:
        post_details.append(f'{bold("Date")}: {details.post_date.strftime(TIMESTAMP_STR)}')

    if post_details:
        md_maker.add_section('Post Details', post_details)


def _dark_web_markdown(
    pba: 'PBA_DarkWebBrand',
    md_maker: MarkdownMaker,
    *args,  # noqa: ARG001
):
    _add_panel_triage(pba, md_maker)
    _add_matched_assets(pba, md_maker)

    if pba.panel_evidence_summary.details.type == 'ransomware_extortion_site':
        _add_post_details_ransomware(pba, md_maker)

    elif pba.panel_evidence_summary.details.type == 'telegram_mention':
        _add_post_details_telegram(pba, md_maker)

    elif pba.panel_evidence_summary.details.type == 'dark_web_forum_mention':
        _add_post_details_forum_mention(pba, md_maker)

    elif pba.panel_evidence_summary.details.type == 'dark_web_market_mention':
        _add_post_details_market_mention(pba, md_maker)

    return md_maker.format_output()
