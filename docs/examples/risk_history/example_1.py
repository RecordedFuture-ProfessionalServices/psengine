from psengine.constants import TIMESTAMP_STR
from psengine.risk_history import RiskHistoryMgr
from rich.console import Console
from rich.table import Table

mgr = RiskHistoryMgr()

data = mgr.search(entities=['gVd1R', 'EJXkx'], from_='-20d', to='-1d')

console = Console()
table = Table(title='Score Summary')

table.add_column('Entity', justify='right')
table.add_column('Score', justify='right')
table.add_column('Added', justify='right')
table.add_column('Removed', justify='right')


table_data = []
for entity in data:
    for score in entity.scores:
        removed = score.removed.strftime(TIMESTAMP_STR) if score.removed else 'Not removed'
        table.add_row(
            entity.entity.name,
            str(score.score),
            score.added.strftime(TIMESTAMP_STR),
            removed,
        )


console.print(table)
