import json

import pytest

from psengine.risk_rules import RiskRule
from tests.risk_rules.constants import MOCK_DIR

ENTITY_TYPES = ['ip', 'domain', 'hash', 'vulnerability', 'url']


class Test_RiskRuleModel:
    @pytest.mark.parametrize('entity_type', ENTITY_TYPES)
    def test_risk_rule_model_validate(self, entity_type: str):
        payload = json.loads((MOCK_DIR / f'riskrules_{entity_type}.json').read_text())
        results = payload['data']['results']
        rules = [RiskRule.model_validate(r) for r in results]
        assert len(rules) == len(results)
        for rule in rules:
            assert isinstance(rule.name, str)
            assert isinstance(rule.description, str)
            assert isinstance(rule.criticality, int)
            assert isinstance(rule.criticality_label, str)
            assert isinstance(rule.count, int)

    def test_hash_dedupes_equal_rules(self):
        a = RiskRule.model_validate(
            {
                'name': 'dupe',
                'description': 'first',
                'criticality': 2,
                'criticalityLabel': 'Suspicious',
                'count': 10,
                'categories': [],
                'relatedEntities': [],
            }
        )
        b = RiskRule.model_validate(
            {
                'name': 'dupe',
                'description': 'second',
                'criticality': 2,
                'criticalityLabel': 'Suspicious',
                'count': 999,
                'categories': [],
                'relatedEntities': [],
            }
        )
        assert a == b
        assert hash(a) == hash(b)
        assert len({a, b}) == 1

    def test_ordering_highest_criticality_first(self):
        low = RiskRule.model_validate(
            {
                'name': 'alpha',
                'description': '',
                'criticality': 1,
                'criticalityLabel': 'Unusual',
                'count': 1,
            }
        )
        medium = RiskRule.model_validate(
            {
                'name': 'beta',
                'description': '',
                'criticality': 2,
                'criticalityLabel': 'Suspicious',
                'count': 1,
            }
        )
        high_a = RiskRule.model_validate(
            {
                'name': 'alpha',
                'description': '',
                'criticality': 3,
                'criticalityLabel': 'Malicious',
                'count': 1,
            }
        )
        high_b = RiskRule.model_validate(
            {
                'name': 'beta',
                'description': '',
                'criticality': 3,
                'criticalityLabel': 'Malicious',
                'count': 1,
            }
        )
        ordered_desc = sorted([low, medium, high_a, high_b], reverse=True)
        assert ordered_desc == [high_b, high_a, medium, low]
        assert low < medium < high_a < high_b

    def test_str_representation(self):
        rule = RiskRule.model_validate(
            {
                'name': 'bogusBgp',
                'description': 'Inside Possible Bogus BGP Route',
                'criticality': 1,
                'criticalityLabel': 'Unusual',
                'count': 24590,
            }
        )
        assert str(rule) == 'Risk Rule: bogusBgp, Criticality: 1 (Unusual), Count: 24590'

    def test_categories_parsed(self):
        payload = json.loads((MOCK_DIR / 'riskrules_ip.json').read_text())
        rules = [RiskRule.model_validate(r) for r in payload['data']['results']]
        with_categories = [r for r in rules if r.categories]
        assert with_categories, 'expected at least one rule with categories in the mock'
        cat = with_categories[0].categories[0]
        assert cat.name
        assert cat.framework
