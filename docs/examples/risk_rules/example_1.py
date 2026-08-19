from psengine.risk_rules import (
    RiskRuleEntityType,
    RiskRuleMgr,
)

mgr = RiskRuleMgr()
rules = mgr.fetch(RiskRuleEntityType.IP)

for rule in rules:
    print(rule)
