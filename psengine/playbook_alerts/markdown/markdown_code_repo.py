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

from collections import defaultdict

from markdown_strings import blockquote, bold

from ...constants import TIMESTAMP_STR
from ...markdown import MarkdownMaker, clean_text, divider, html_textarea


def _add_repository(pba, md_maker: MarkdownMaker):
    repos = [
        f'{bold("Owner:" )} {pba.panel_evidence_summary.repository.owner.name}',
        f'{bold("URL:" )} {pba.panel_evidence_summary.repository.name}',
    ]

    md_maker.add_section('Repository', repos)


def _add_assessment(pba, md_maker: MarkdownMaker, html_tags: bool):
    assessments = []

    for assess in pba.panel_evidence_summary.evidence:
        details = defaultdict(list)
        for a in assess.assessments:
            details[a.title].append(clean_text(a.value))

        details_list = []
        for k, v in details.items():
            details_list.append(f'{bold(k + ":")} {", ".join(v)}')

        targets = ''
        if targets := ', '.join(t.name for t in assess.targets):
            targets = f'{bold("Assessment targets:")} {targets}'

        commit = f'{bold("Commit:")} {assess.url}'
        published = f'{bold("Published:")} {assess.published.strftime(TIMESTAMP_STR)}'
        content = blockquote(
            html_textarea(clean_text(assess.content)) if html_tags else clean_text(assess.content)
        )
        content = f'{bold("Content:")}\n\n{content}'

        assessments.extend([published, targets, *details_list, commit, content, divider()])
    md_maker.add_section('Assessments', assessments)


def _code_repo_markdown(pba, md_maker: MarkdownMaker, html_tags: bool) -> str:
    if targets := pba.panel_status.targets:
        md_maker.add_section('Targets', [t.name for t in targets])

    _add_repository(pba, md_maker)
    _add_assessment(pba, md_maker, html_tags)
    return md_maker.format_output()
