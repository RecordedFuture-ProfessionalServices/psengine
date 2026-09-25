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
    from ...playbook_alerts.playbook_alerts import PBA_SocialMediaImpersonation


def _add_matched_assets_assessment(pba: 'PBA_SocialMediaImpersonation', md_maker: MarkdownMaker):
    matched_assets_assessment = []
    if pba.panel_evidence_summary.matched_assets:
        matched_assets_assessment.extend(
            f'{bold("Matched Asset")}: {matched_asset.name}\n'
            for matched_asset in pba.panel_evidence_summary.matched_assets
        )

    if pba.panel_evidence_summary.assessments:
        assessments = [assessment.name for assessment in pba.panel_evidence_summary.assessments]
        matched_assets_assessment.append(f'{bold("Assessments")}: {", ".join(assessments)}')

    if matched_assets_assessment:
        md_maker.add_section('Summary', matched_assets_assessment)


def _add_post_details(pba: 'PBA_SocialMediaImpersonation', md_maker: MarkdownMaker):
    post_details = []
    if pba.panel_evidence_summary.user_name:
        post_details.append(f'{bold("Username")}: {pba.panel_evidence_summary.user_name}')

    if pba.panel_evidence_summary.user_handel:
        post_details.append(f'{bold("Username")}: {pba.panel_evidence_summary.user_handel}')

    if pba.panel_evidence_summary.description:
        post_details.append(
            f'{bold("Bio/About/Description")}: {pba.panel_evidence_summary.description}'
        )

    if pba.panel_evidence_summary.created_date:
        post_details.append(
            f'{bold("Page Creation Date")}: '
            f'{pba.panel_evidence_summary.created_date.strftime(TIMESTAMP_STR)}'
        )

    if pba.panel_evidence_summary.number_of_followers:
        post_details.append(
            f'{bold("Follower Count")}: {pba.panel_evidence_summary.number_of_followers}'
        )

    if pba.panel_evidence_summary.number_of_posts:
        post_details.append(f'{bold("Posts")}: {pba.panel_evidence_summary.number_of_posts}')

    if pba.panel_evidence_summary.private_profile:
        post_details.append(
            f'{bold("Private Account")}: {pba.panel_evidence_summary.private_profile}'
        )

    if pba.panel_evidence_summary.profile_url_id:
        post_details.append(
            f'{bold("Account URL")}: '
            f'{pba.panel_evidence_summary.profile_url_id.replace("url:", "")}'
        )

    if post_details:
        md_maker.add_section('Post Details', post_details)


def _social_media_impersonation_markdown(
    pba: 'PBA_SocialMediaImpersonation',
    md_maker: MarkdownMaker,
    *args,  # noqa: ARG001
):
    _add_matched_assets_assessment(pba, md_maker)
    _add_post_details(pba, md_maker)

    return md_maker.format_output()
