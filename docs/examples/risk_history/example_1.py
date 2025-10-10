from psengine.risk_history import RiskHistoryMgr

# TODO: add graph
mgr = RiskHistoryMgr()
data = mgr.search(
    entities=['gVd1R', 'EJXkx'], from_='-20d', to='-1d'
)

print(data)
