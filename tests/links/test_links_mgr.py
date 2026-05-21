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
from requests import Response
from requests.exceptions import HTTPError

from psengine.links.errors import LinksMetadataError, LinksSearchError
from psengine.links.models import (
    CriticalityAttribute,
    GenericAttribute,
    LinksFilterObjects,
    MitreNameAttribute,
    RiskAttribute,
    ThreatActorAttribute,
)


def test_list_sections(links_mgr, mocker, make_response):
    mock_data = {
        'data': [
            {'id': 's1', 'name': 'Section 1', 'description': 'Desc 1'},
            {'id': 's2', 'name': 'Section 2', 'description': 'Desc 2'},
        ]
    }
    mocker.patch.object(links_mgr.rf_client, 'request', return_value=make_response(mock_data))

    sections = links_mgr.list_sections()
    assert len(sections) == 2
    assert sections[0].id_ == 's1'
    assert sections[1].name == 'Section 2'


def test_list_events(links_mgr, mocker, make_response):
    mock_data = {
        'data': [
            {'id': 'e1', 'name': 'Event 1', 'description': 'Desc 1'},
            {'id': 'e2', 'name': 'Event 2', 'description': 'Desc 2'},
        ]
    }
    mocker.patch.object(links_mgr.rf_client, 'request', return_value=make_response(mock_data))

    events = links_mgr.list_events()
    assert len(events) == 2
    assert events[0].id_ == 'e1'
    assert events[1].name == 'Event 2'


def test_list_entity_types(links_mgr, mocker, make_response):
    mock_data = {
        'data': [
            {'id': 'Type1', 'name': 'Type 1'},
            {'id': 'Type2', 'name': 'Type 2'},
        ]
    }
    mocker.patch.object(links_mgr.rf_client, 'request', return_value=make_response(mock_data))

    entity_types = links_mgr.list_entity_types()
    assert len(entity_types) == 2
    assert entity_types[0].id_ == 'Type1'
    assert entity_types[1].name == 'Type 2'


def test_search_basic(links_mgr, mocker, make_response):
    mock_data = {
        'data': [
            {
                'entity': {'id': 'ent1', 'name': 'Entity 1', 'type': 'Type1'},
                'links': [
                    {
                        'id': 'link1',
                        'name': 'Link 1',
                        'type': 'Type2',
                        'source': 'technical',
                        'section': 's1',
                        'attributes': [{'id': 'risk_score', 'value': 50}],
                    }
                ],
            }
        ]
    }
    mocker.patch.object(links_mgr.rf_client, 'request', return_value=make_response(mock_data))

    results = links_mgr.search(entities=['ent1'])
    assert len(results.data) == 1
    assert results.data[0].entity.id_ == 'ent1'
    assert len(results.data[0].links) == 1
    assert results.data[0].links[0].id_ == 'link1'


def test_filter_objects_invalid_source():
    with pytest.raises(ValidationError, match='sources'):
        LinksFilterObjects(sources=['invalid_source'])


def test_metadata_error(links_mgr, mocker):
    mock_resp = mocker.Mock(spec=Response)
    mock_resp.status_code = 500
    mock_resp.text = 'Internal Server Error'
    mocker.patch.object(
        links_mgr.rf_client,
        'request',
        side_effect=HTTPError('500 Server Error', response=mock_resp),
    )

    with pytest.raises(LinksMetadataError, match='500'):
        links_mgr.list_sections()


def test_search_error(links_mgr, mocker):
    mock_resp = mocker.Mock(spec=Response)
    mock_resp.status_code = 400
    mock_resp.text = 'Bad Request'
    mocker.patch.object(
        links_mgr.rf_client,
        'request',
        side_effect=HTTPError('400 Client Error', response=mock_resp),
    )

    with pytest.raises(LinksSearchError, match='400'):
        links_mgr.search(entities=['ent1'])


def test_search_complex_attributes(links_mgr, mocker, make_response):
    mock_data = {
        'data': [
            {
                'entity': {'id': 'ent1', 'name': 'Entity 1', 'type': 'Type1'},
                'links': [
                    {
                        'id': 'link1',
                        'name': 'Link 1',
                        'type': 'Type2',
                        'attributes': [
                            {'id': 'risk_score', 'value': 75.0},
                            {'id': 'risk_level', 'value': 'High'},
                            {'id': 'criticality', 'value': 'Critical'},
                            {'id': 'display_name', 'value': 'T1234'},
                            {'id': 'threat_actor', 'value': True},
                            {'id': 'unknown_attr', 'value': 'some value'},
                        ],
                    }
                ],
            }
        ]
    }
    mocker.patch.object(links_mgr.rf_client, 'request', return_value=make_response(mock_data))

    results = links_mgr.search(entities=['ent1'])
    attrs = results.data[0].links[0].attributes
    assert len(attrs) == 6

    assert isinstance(attrs[0], RiskAttribute)
    assert attrs[0].id_ == 'risk_score'
    assert attrs[0].value == 75.0

    assert isinstance(attrs[1], RiskAttribute)
    assert attrs[1].id_ == 'risk_level'
    assert attrs[1].value == 'High'

    assert isinstance(attrs[2], CriticalityAttribute)
    assert attrs[2].value == 'Critical'

    assert isinstance(attrs[3], MitreNameAttribute)
    assert attrs[3].value == 'T1234'

    assert isinstance(attrs[4], ThreatActorAttribute)
    assert attrs[4].value is True

    assert isinstance(attrs[5], GenericAttribute)
    assert attrs[5].id_ == 'unknown_attr'
    assert attrs[5].value == 'some value'


def test_search_with_limits(links_mgr, mocker, make_response):
    mocker.patch.object(links_mgr.rf_client, 'request', return_value=make_response({'data': []}))

    links_mgr.search(entities=['ent1'], search_scope='small', per_entity_type=10)

    _, kwargs = links_mgr.rf_client.request.call_args
    assert kwargs['data']['limits']['search_scope'] == 'small'
    assert kwargs['data']['limits']['per_entity_type'] == 10
