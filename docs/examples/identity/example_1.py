from psengine.identity import IdentityMgr
from rich.console import Console
from rich.table import Table

console = Console()
table = Table(title='Discovered Credentials')

table.add_column('Subject')
table.add_column('Password Properties')
table.add_column('Is Password Clear', justify='center')

mgr = IdentityMgr()
credentials = mgr.search_credentials(
    'norsegods.online', 'Email'
)

if len(credentials):
    detailed_identities = mgr.lookup_credentials(
        subjects_login=credentials
    )

    for identity in detailed_identities:
        for cred in identity.credentials:
            properties = ', '.join(
                cred.exposed_secret.details.properties
            )
            is_clear = (
                'Yes'
                if cred.exposed_secret.effectively_clear
                else 'No'
            )

            table.add_row(
                cred.subject, properties, is_clear
            )

console.print(table)
