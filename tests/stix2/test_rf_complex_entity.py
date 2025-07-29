import pytest
import stix2

from psengine.analyst_notes import AnalystNoteMgr
from psengine.stix2 import (
    DetectionRuleEntity,
    Grouping,
    IndicatorEntity,
    NoteEntity,
    Relationship,
    STIX2TransformError,
    ThreatActor,
)
from tests.stix2.conftest import MOCK_DIR


class Test_ComplexEntity:
    @pytest.mark.parametrize(
        ('name', 'type_', 'expected_type'),
        [
            ('8.8.8.8', 'IpAddress', 'IpAddress'),
            ('2001:db8:3333:4444:5555:6666:7777:8888', 'IpAddress', 'IpAddress'),
            ('google.com', 'InternetDomainName', 'InternetDomainName'),
            ('https://www.google.com/endpoint', 'URL', 'URL'),
            (
                '4b61697d61a8835a503f2ea6c202b338bde721644dc3ec3e41131d910c657545',
                'FileHash',
                'FileHash',
            ),
            ('6f122aa219d59dbeaacbbfa172c2da6f487d4f8c', 'FileHash', 'FileHash'),
            ('aad3b435b51404eeaad3b435b51404ee', 'FileHash', 'FileHash'),
            ('8.8.8.8', 'ip', 'IpAddress'),
            ('2001:db8:3333:4444:5555:6666:7777:8888', 'ip', 'IpAddress'),
            ('google.com', 'domain', 'InternetDomainName'),
            ('https://www.google.com/endpoint', 'url', 'URL'),
            (
                '4b61697d61a8835a503f2ea6c202b338bde721644dc3ec3e41131d910c657545',
                'hash',
                'FileHash',
            ),
        ],
    )
    def test_indicator_class(self, name, type_, expected_type):
        indicator = IndicatorEntity(name=name, type_=type_, create_indicator=True, create_obs=True)
        assert isinstance(indicator, IndicatorEntity)
        assert indicator.indicator
        assert indicator.observable
        assert indicator.relationship
        assert indicator.type == expected_type

        indicator = IndicatorEntity(name=name, type_=type_, create_indicator=True, create_obs=False)
        assert isinstance(indicator, IndicatorEntity)
        assert indicator.indicator
        assert not indicator.observable
        assert not indicator.relationship
        assert indicator.type == expected_type

        indicator = IndicatorEntity(name=name, type_=type_, create_indicator=False, create_obs=True)
        assert isinstance(indicator, IndicatorEntity)
        assert not indicator.indicator
        assert indicator.observable
        assert not indicator.relationship
        assert indicator.type == expected_type

    @pytest.mark.parametrize(
        ('name', 'type_'),
        [
            ('8.8.8.8', 'ips'),
            ('2001:db8:3333:4444:5555:6666:7777:8888', 'ips'),
            ('google.com', 'domains'),
            ('https://www.google.com/endpoint', 'urls'),
            ('4b61697d61a8835a503f2ea6c202b338bde721644dc3ec3e41131d910c657545', 'shash'),
        ],
    )
    def test_indicator_class_raises_STIX2TransformError_invalid_entity_type(self, name, type_):
        with pytest.raises(STIX2TransformError):
            IndicatorEntity(name=name, type_=type_, create_indicator=True, create_obs=True)

    @pytest.mark.parametrize(
        ('name', 'type_'),
        [
            ('8.8.8.8', 'IpAddress'),
            ('2001:db8:3333:4444:5555:6666:7777:8888', 'IPAddress'),
            ('google.com', 'InternetDomainName'),
            ('https://www.google.com/endpoint', 'URL'),
            ('4b61697d61a8835a503f2ea6c202b338bde721644dc3ec3e41131d910c657545', 'FileHash'),
            ('6f122aa219d59dbeaacbbfa172c2da6f487d4f8c', 'FileHash'),
            ('aad3b435b51404eeaad3b435b51404ee', 'FileHash'),
        ],
    )
    def test_indicator_raises_STIX2TransformError_bad_param(self, name, type_):
        with pytest.raises(STIX2TransformError):
            IndicatorEntity(name=name, type_=type_, create_indicator=False, create_obs=False)

    def test_indicator_raises_STIX2TransformError_wrong_hash_alg(self):
        with pytest.raises(STIX2TransformError):
            IndicatorEntity(
                name='123456_bad-hash',
                type_='FileHash',
                create_indicator=True,
                create_obs=False,
            )

    @pytest.mark.parametrize('domain', ['google.com', 'recordedfuture.com', 'bananas.co.uk'])
    def test_note_class(self, domain):
        domain_name = stix2.v21.DomainName(value=domain)
        note = NoteEntity(name='note_title', content='content', object_refs=[domain_name.id])

        assert isinstance(note, NoteEntity)
        assert note.name
        assert note.content
        assert note.object_refs
        assert len(note.object_refs) == 1
        assert note.object_refs[0] == domain_name.id
        assert isinstance(note.stix_obj.serialize(), str)

    @pytest.mark.parametrize('domain', ['google.com', 'recordedfuture.com', 'bananas.co.uk'])
    def test_grouping_class(self, domain):
        domain_name = stix2.v21.DomainName(value=domain)
        grouping = Grouping(
            name='Unique Name',
            description='unique description',
            is_malware=True,
            object_refs=[domain_name.id],
        )

        assert isinstance(grouping, Grouping)
        assert grouping.name
        assert grouping.description
        assert grouping.context
        assert grouping.context == 'malware-analysis'
        assert grouping.object_refs
        assert len(grouping.object_refs) == 1
        assert grouping.object_refs[0] == domain_name.id
        assert isinstance(grouping.stix_obj.serialize(), str)

    # oJeqDP - existing note with yara attachment
    # cynQie - existing note with snort attachment
    @pytest.mark.parametrize(
        'note_id',
        ['oJeqDP', 'cynQie'],
    )
    def test_detectionrule_class(
        self,
        an_mgr: AnalystNoteMgr,
        note_id: str,
        mocker,
        make_binary_response,
        request,
        mock_request,
    ):
        node_id = request.node.callspec.id
        file = MOCK_DIR / f'test_detectionrule_class[{node_id}]_0.json'
        mock = make_binary_response(b'abcd', {'Content-Disposition': 'filename=abc.ad'})
        mocks = [mock_request(file), mock]

        mocker.patch.object(an_mgr.rf_client, 'request', side_effect=mocks)

        note = an_mgr.lookup(note_id)
        attachment, _ = an_mgr.fetch_attachment(note.id_)
        rule = DetectionRuleEntity(
            name=note.attributes.title,
            type_=note.detection_rule_type,
            content=str(attachment, 'UTF-8'),
        )

        assert isinstance(rule, DetectionRuleEntity)
        assert rule.name == note.attributes.title

    def test_detectionrule_class_raises_STIX2TransformError_invalid_type(self):
        with pytest.raises(STIX2TransformError):
            DetectionRuleEntity(name='rule', type_='invalid_type', content='content')

    def test_relationship_class(self):
        indicator = IndicatorEntity(
            name='8.8.8.8',
            type_='IpAddress',
            create_indicator=True,
            create_obs=True,
        )
        ta = ThreatActor('APT41')
        relationship = Relationship(
            source=indicator.indicator.id,
            target=ta.stix_obj.id,
            type_='related-to',
            author=indicator.author,
        )

        assert isinstance(relationship, Relationship)
        assert isinstance(relationship.stix_obj, stix2.Relationship)
        assert relationship.stix_obj.id == 'relationship--7797776a-fbd5-54f5-8dd6-d4a4e5f451db'
        assert relationship.stix_obj.source_ref == indicator.indicator.id
        assert relationship.stix_obj.target_ref == ta.stix_obj.id
        assert relationship.stix_obj.relationship_type == 'related-to'
        assert relationship.stix_obj.created_by_ref == indicator.author.id
