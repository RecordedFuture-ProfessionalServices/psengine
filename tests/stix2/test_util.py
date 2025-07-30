import pytest
from stix2 import Identity

from psengine.stix2.util import create_rf_author, generate_uuid


class Test_Util:
    @pytest.mark.parametrize(
        ('name', 'content', 'type_'),
        [
            ('APT41_rules.txt', 'xyz content', 'yara'),
            ('8.8.8.8', '', 'IpAddress'),
            ('note about x', 'content', ''),
        ],
    )
    def test_generate_uuid(self, name, content, type_):
        uuid = 'indicator--' + generate_uuid(name=name, content=content, type=type_)
        assert len(uuid.split('--')) == 2

    def test_generate_uuid_is_consistent(self):
        uuid1 = generate_uuid(name='8.8.8.8', type='IpAddress')
        uuid2 = generate_uuid(name='8.8.8.8', type='IpAddress')
        assert uuid1 == uuid2

    def test_create_rf_author(self):
        rf_author = create_rf_author()

        assert isinstance(rf_author, Identity)
        assert rf_author.id == 'identity--509cdfd1-b97f-5329-9e27-a841f8b2dbce'
        assert rf_author.name == 'Recorded Future'
        assert rf_author.identity_class == 'organization'
        assert rf_author.revoked is False
