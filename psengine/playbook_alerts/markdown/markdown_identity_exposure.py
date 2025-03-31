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

from markdown_strings import bold, unordered_list

from ...constants import TIMESTAMP_STR
from ...markdown import MarkdownMaker
from ...markdown.markdown import divider

DOMAIN_CONFIG_URL = 'https://app.recordedfuture.com/portal/identity/domain-configuration'
PORTAL_URL = 'https://app.recordedfuture.com/portal/playbook-alerts/{}'


def _get_compromised_host(pba) -> str:
    host_data = []
    summ = pba.panel_evidence_summary

    if not (
        summ.compromised_host
        and summ.compromised_host.os_username
        and summ.compromised_host.computer_name
    ):
        return ''

    comprom = summ.compromised_host
    os = _format_field('Operating System', comprom.os)
    username = _format_field('OS Username', comprom.os_username)
    file_path = _format_field('File Path', comprom.malware_file)
    timezone = _format_field('Time Zone', comprom.timezone)
    uac = _format_field('User Account Control Setting', comprom.uac)
    av = _format_field('Antivirus', comprom.antivirus)
    machine = _format_field('Machine Name', comprom.computer_name)

    host_data = [x for x in [os, username, file_path, timezone, machine, uac, av] if x]

    return f"\n{bold('Compromised Host:')}\n\n{unordered_list(host_data, esc=False)}"


def _get_technology(pba) -> str:
    items = []
    for tech in pba.panel_evidence_summary.technologies:
        label = 'Category:' if tech.category else 'Technology:'
        items.append(f'{bold(label)} {tech.name}')

    if not items:
        return ''

    return f"\n{bold('Technology:')}\n\n{unordered_list(items, esc=False)}"


def _add_exposure(pba, md_maker: MarkdownMaker):
    summ = pba.panel_evidence_summary
    result = []

    result.append(_format_field('Identity', pba.panel_status.entity_name))
    result.append(_format_password(summ.exposed_secret.details))
    result.append(_format_assessments(summ.assessments))
    if summ.compromised_host.exfiltration_date:
        result.append(
            _format_field(
                'Exfiltration Date', summ.compromised_host.exfiltration_date.strftime(TIMESTAMP_STR)
            )
        )

    result.append(_format_field('Authorization URL', summ.authorization_url))
    result.append(_format_field('IP Address', summ.infrastructure.ip))
    result.append(_format_field('Properties', summ.exposed_secret.details.properties))

    result.append(_format_hashes(summ.exposed_secret.hashes))
    result.append(_format_source(summ.dump))
    result.append(_get_compromised_host(pba))

    result.append('\n' + _format_field('Malware Family', summ.malware_family.name))

    result.append(_get_technology(pba))
    result.append(divider())

    md_maker.add_section('Exposure', result)


def _format_field(label, value) -> str:
    """Generic helper for fields that can be single strings or lists.
    Returns an empty string if there's no value.
    """
    if not value:
        return ''
    if isinstance(value, list):
        value = ', '.join(value)
    return f'{bold(label + ":")} {value}'


def _format_password(secret_details):
    password = ''
    if secret_details.clear_text_hint:
        # Hides all but the password hint
        password = (
            f"{bold('Password:')} {secret_details.clear_text_hint:•<8} [ⓘ] ({DOMAIN_CONFIG_URL})"
        )
    if secret_details.clear_text_value:
        # If support has enabled clear text, it takes precedence
        password = f"{bold('Password:')} {secret_details.clear_text_value}"
    return password


def _format_assessments(assessments) -> str:
    if assessments:
        names = ', '.join(ass.name for ass in assessments)
        return f"{bold('Assessment:')} {names}"
    return ''


def _format_hashes(hashes) -> str:
    hash_values = [f'{bold(h.algorithm)} {h.hash_}' for h in hashes if h.hash_]
    if hash_values:
        formatted_hashes = '\n\n' + unordered_list(hash_values, esc=False)
        return f"\n{bold('Hashes:')} {formatted_hashes}\n"
    return ''


def _format_source(dump) -> str:
    source_data = []
    if dump.name:
        source_data.append(f"{bold('Name:')} {dump.name}")
    if dump.description:
        source_data.append(f"{bold('Description:')} {dump.description}")
    if source_data:
        return f"\n{bold('Source:')}\n\n{unordered_list(source_data, esc=False)}"
    return ''


def _add_actions_to_consider(pba, md_maker: MarkdownMaker):
    actions = []
    actions.append(f'-  [Check Incident Report] ({PORTAL_URL.format(pba.playbook_alert_id)})')
    actions.append('-  Enforce Password Reset')
    actions.append('-  Initiate MFA Challenge')
    actions.append('-  Request Compromised Host Incident Response')
    actions.append('-  Review Malware Hunting Packages')

    md_maker.add_section('Actions to Consider', actions)


def _identity_exposure_markdown(pba, md_maker: MarkdownMaker, *args) -> str:  # noqa: ARG001
    if pba.panel_evidence_summary:
        _add_exposure(pba, md_maker)

    _add_actions_to_consider(pba, md_maker)

    return md_maker.format_output()
