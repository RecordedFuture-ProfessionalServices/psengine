import pytest

from psengine.stix2 import BaseStixEntity, STIX2TransformError, convert_entity


class Test_ConvertEntity:
    @pytest.mark.parametrize(
        ('entity', 'type_', 'description'),
        [
            ('TA0001', 'MitreAttackIdentifier', None),
            ('Google', 'Company', None),
            ('TrojanRAT', 'Malware', None),
            ('CVE-2023-1234', 'CyberVulnerability', None),
            (
                'CVE-2017-8570',
                'CyberVulnerability',
                'A description of the vunlerability noting its very bad',
            ),
        ],
    )
    def test_convert_entity(self, entity, type_, description):
        if description:
            converted_entity = convert_entity(entity, type_, description)
        else:
            converted_entity = convert_entity(entity, type_)
        assert isinstance(converted_entity, BaseStixEntity)

    def test_convert_entity_raises_STIX2TransformError(self):
        with pytest.raises(STIX2TransformError):
            convert_entity('invalid', 'invalid', invalid_kwarg='apples')
