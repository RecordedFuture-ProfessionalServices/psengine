import pytest

from psengine.stix2 import BaseStixEntity


class Test_RFBaseStixEntity:
    @pytest.mark.parametrize('name', ['google.com', '8.8.8.8', 'recfut.com/blah'])
    def test_init(self, name):
        entity = BaseStixEntity(name=name)
        assert isinstance(entity, BaseStixEntity)
        assert str(entity) == f'Base STIX Entity: {name}, Author Name: Recorded Future'

        same_entity = BaseStixEntity(name=name)
        assert entity == same_entity
        assert hash(entity) == hash(same_entity)
