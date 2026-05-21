##################################### TERMS OF USE ###########################################
# The following code is provided for demonstration purpose only, and should not be used      #
# without independent verification. Recorded Future makes no representations or warranties,  #
# express, implied, statutory, or otherwise, regarding any aspect of this code or of the     #
# information it may retrieve, and provides it both strictly “as-is” and without assuming    #
# responsibility for any information it may retrieve. Recorded Future shall not be liable    #
# for, and you assume all risk of using, the foregoing. By using this code, Customer         #
# represents that it is solely responsible for having all necessary licenses, permissions,   #
# rights, and/or consents to connect to third party APIs, and that it is solely responsible  #
# for having all necessary licenses, permissions, rights, and/or consents to any data        #
# accessed from any third party API.                                                         #
##############################################################################################

import pytest
from pydantic import ValidationError

from psengine.endpoints import EP_LINKS_SEARCH
from psengine.links.models import (
    FilterTechnical,
    LinksFilterObjects,
    LinksLimitsObjects,
    LinkSource,
    SearchScope,
)


def test_link_source_enum_values():
    assert [member.value for member in LinkSource] == ['technical', 'insikt']


def test_search_scope_enum_values():
    assert [member.value for member in SearchScope] == ['small', 'medium', 'large']


def test_filter_technical_timeframe_invalid_format():
    with pytest.raises(ValidationError, match='Invalid relative time'):
        FilterTechnical(timeframe='not-a-time')


def test_filter_technical_converts_string_fields_to_lists():
    model = FilterTechnical(
        timeframe='-30d',
        events='type:MalwareAnalysis',
        connected_entities='id:Ent1',
    )

    assert model.timeframe == '-30d'
    assert model.events == ['type:MalwareAnalysis']
    assert model.connected_entities == ['id:Ent1']


def test_filter_technical_removes_none_values_in_list_fields():
    model = FilterTechnical(
        events=['type:MalwareAnalysis', None, 'type:TTPAnalysis'],
        connected_entities=['id:Ent1', None, 'id:Ent2'],
    )

    assert model.events == ['type:MalwareAnalysis', 'type:TTPAnalysis']
    assert model.connected_entities == ['id:Ent1', 'id:Ent2']


def test_filter_technical_json_excludes_unset_fields():
    model = FilterTechnical(timeframe='-7d')
    assert model.json() == {'timeframe': '-7d'}


def test_links_filter_objects_normalizes_scalar_fields():
    model = LinksFilterObjects(
        sections='section:actors',
        entity_types='type:IpAddress',
        sources=['technical', 'insikt'],
        technical=FilterTechnical(timeframe='-30d'),
    )

    assert model.json() == {
        'sections': ['section:actors'],
        'entity_types': ['type:IpAddress'],
        'sources': ['technical', 'insikt'],
        'technical': {'timeframe': '-30d'},
    }


def test_links_filter_objects_accepts_link_source_enums():
    model = LinksFilterObjects(sources=[LinkSource.technical, LinkSource.insikt])
    assert model.json() == {'sources': ['technical', 'insikt']}


def test_links_filter_objects_invalid_source():
    with pytest.raises(ValidationError, match='sources'):
        LinksFilterObjects(sources=['invalid_source'])


def test_links_limits_objects_serializes_search_scope_enum():
    model = LinksLimitsObjects(search_scope=SearchScope.small, per_entity_type=25)
    assert model.json() == {'search_scope': 'small', 'per_entity_type': 25}


def test_links_limits_objects_invalid_search_scope():
    with pytest.raises(ValidationError, match='search_scope'):
        LinksLimitsObjects(search_scope='huge')


def test_links_mgr_search_builds_minimal_payload_with_entity_str(links_mgr, mocker, make_response):
    mocker.patch.object(links_mgr.rf_client, 'request', return_value=make_response({'data': []}))

    links_mgr.search(entities='ent1')

    _, kwargs = links_mgr.rf_client.request.call_args
    assert kwargs['method'] == 'POST'
    assert kwargs['url'] == EP_LINKS_SEARCH
    assert kwargs['data'] == {
        'entities': ['ent1'],
        'filters': {'technical': {}},
        'limits': {},
    }


@pytest.mark.parametrize(
    ('search_kwargs', 'expected_filter_key', 'expected_value'),
    [
        ({'sections': 'section:actors'}, ('sections',), ['section:actors']),
        ({'entity_types': 'type:IpAddress'}, ('entity_types',), ['type:IpAddress']),
        ({'events': 'type:MalwareAnalysis'}, ('technical', 'events'), ['type:MalwareAnalysis']),
        ({'connected_entities': 'id:Ent1'}, ('technical', 'connected_entities'), ['id:Ent1']),
    ],
)
def test_links_mgr_search_converts_str_filter_fields_to_lists(
    links_mgr, mocker, make_response, search_kwargs, expected_filter_key, expected_value
):
    mocker.patch.object(links_mgr.rf_client, 'request', return_value=make_response({'data': []}))

    links_mgr.search(entities='ent1', **search_kwargs)

    _, kwargs = links_mgr.rf_client.request.call_args
    filters = kwargs['data']['filters']
    target = filters
    for key in expected_filter_key:
        target = target[key]
    assert target == expected_value


@pytest.mark.parametrize(
    ('search_kwargs', 'expected_filter_key', 'expected_value'),
    [
        (
            {'sections': ['section:actors', 'section:tools']},
            ('sections',),
            ['section:actors', 'section:tools'],
        ),
        (
            {'entity_types': ['type:IpAddress', 'type:DomainName']},
            ('entity_types',),
            ['type:IpAddress', 'type:DomainName'],
        ),
        (
            {'events': ['type:MalwareAnalysis', 'type:TTPAnalysis']},
            ('technical', 'events'),
            ['type:MalwareAnalysis', 'type:TTPAnalysis'],
        ),
        (
            {'connected_entities': ['id:Ent1', 'id:Ent2']},
            ('technical', 'connected_entities'),
            ['id:Ent1', 'id:Ent2'],
        ),
    ],
)
def test_links_mgr_search_preserves_list_filter_fields(
    links_mgr, mocker, make_response, search_kwargs, expected_filter_key, expected_value
):
    mocker.patch.object(links_mgr.rf_client, 'request', return_value=make_response({'data': []}))

    links_mgr.search(entities='ent1', **search_kwargs)

    _, kwargs = links_mgr.rf_client.request.call_args
    filters = kwargs['data']['filters']
    target = filters
    for key in expected_filter_key:
        target = target[key]
    assert target == expected_value


def test_links_mgr_search_builds_full_payload_from_model_inputs(links_mgr, mocker, make_response):
    mocker.patch.object(links_mgr.rf_client, 'request', return_value=make_response({'data': []}))

    links_mgr.search(
        entities=['ent1', 'ent2'],
        sections='section:actors',
        entity_types='type:IpAddress',
        sources=[LinkSource.technical, LinkSource.insikt],
        timeframe='-30d',
        events='type:MalwareAnalysis',
        connected_entities=['id:EntA', 'id:EntB'],
        search_scope=SearchScope.large,
        per_entity_type=10,
    )

    _, kwargs = links_mgr.rf_client.request.call_args
    assert kwargs['data'] == {
        'entities': ['ent1', 'ent2'],
        'filters': {
            'sections': ['section:actors'],
            'entity_types': ['type:IpAddress'],
            'sources': ['technical', 'insikt'],
            'technical': {
                'timeframe': '-30d',
                'events': ['type:MalwareAnalysis'],
                'connected_entities': ['id:EntA', 'id:EntB'],
            },
        },
        'limits': {'search_scope': 'large', 'per_entity_type': 10},
    }


def test_links_mgr_search_invalid_timeframe_raises_before_request(links_mgr, mocker):
    request_mock = mocker.patch.object(links_mgr.rf_client, 'request')

    with pytest.raises(ValidationError, match='Invalid relative time'):
        links_mgr.search(entities=['ent1'], timeframe='invalid-time')

    request_mock.assert_not_called()
