## Introduction

The `RiskRuleMgr` class of the `risk_rules` module allows you to fetch the catalogue of risk rules Recorded Future evaluates for a given IOC type.

A risk rule is a named scoring rule that contributes to the overall risk score of an entity (an IP, domain, hash, URL, or vulnerability). Each rule ships with a criticality (1 = Unusual, 2 = Suspicious, 3 = Malicious/High), a description, an optional list of framework categories (e.g. MITRE ATT&CK), and a count of entities currently matching the rule.

The supported IOC types are `ip`, `domain`, `hash`, `vulnerability`, and `url`. Pass one of these values (either the string or the `RiskRuleEntityType` enum) to `fetch_risk_rule`. Any other value raises a `ValidationError`.

See the [**API Reference**](../api/risk_rules/risk_rule_mgr.md) for internal details of the module.


## Examples

{! modules/_includes/examples_warning.md !}

#### 2: Fetch rules for a type and filter by criticality

In this example we are fetching the domain's risk rules and filtering them based on criticality.
The `RiskRule` model implements ordering by criticality (highest first), which makes it easy to focus on the most severe rules.

```python
--8<-- "docs/examples/risk_rules/example_1.py"
```

The output will be:

```
Risk Rule: recentValidatedCnc, Criticality: 4 (Very Malicious), Count: 223
  - MITRE: TA0011
Risk Rule: recentCncSite, Criticality: 4 (Very Malicious), Count: 865
Risk Rule: recentWeaponizedDomain, Criticality: 3 (Malicious), Count: 150770
  - MITRE: T1566.002
  - MITRE: TA0011
Risk Rule: recentUkraineLure, Criticality: 3 (Malicious), Count: 27
Risk Rule: recentScamMerchant, Criticality: 3 (Malicious), Count: 0
Risk Rule: recentPhishingSiteDetected, Criticality: 3 (Malicious), Count: 1281105
  - MITRE: T1566.002
```
