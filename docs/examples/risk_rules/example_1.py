from psengine.risk_rules import (
    RiskRuleEntityType,
    RiskRuleMgr,
)

mgr = RiskRuleMgr()
rules = mgr.fetch(RiskRuleEntityType.DOMAIN)

malicious = [r for r in rules if r.criticality >= 3]

for rule in sorted(malicious, reverse=True):
    print(rule)
    for category in rule.categories:
        print(f'  - {category.framework}: {category.name}')
