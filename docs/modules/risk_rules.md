## Introduction

The `RiskRuleMgr` class of the `risk_rules` module allows you to fetch the catalogue of risk rules Recorded Future evaluates for a given IOC type.

A risk rule is a named scoring rule that contributes to the overall risk score of an entity (an IP, domain, hash, URL, or vulnerability). Each rule ships with a criticality (1 = Unusual, 2 = Suspicious, 3 = Malicious/High), a description, an optional list of framework categories (e.g. MITRE ATT&CK), and a count of entities currently matching the rule.

See the [**API Reference**](../api/risk_rules/risk_rule_mgr.md) for internal details of the module.

## Notes

- The supported IOC types are `ip`, `domain`, `hash`, `vulnerability`, and `url`. Pass one of these values (either the string or the `RiskRuleEntityType` enum) to `fetch_risk_rule`. Any other value raises a `ValidationError`.
- The endpoint returns the full catalogue for the given type in a single response — there is no pagination.
- `RiskRule` instances support hashing, equality, and total ordering. Two rules are equal when they share the same `name` and `criticality`. Sorting a list of rules puts higher-criticality rules last; use `sorted(rules, reverse=True)` to iterate most-critical-first.

## Examples

{! modules/_includes/examples_warning.md !}

#### 1: Fetch and print all IP risk rules

```python
--8<-- "docs/examples/risk_rules/example_1.py"
```

#### 2: Fetch rules for a type and filter by criticality

The `RiskRule` model implements ordering by criticality (highest first), which makes it easy to focus on the most severe rules.

```python
--8<-- "docs/examples/risk_rules/example_2.py"
```
