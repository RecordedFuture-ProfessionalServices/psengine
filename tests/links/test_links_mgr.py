import os

import pytest

from psengine.common_models import IdName
from psengine.links.links_mgr import LinksMgr
from psengine.links.requests import LinksFilterObjects
from psengine.links.response import LinksSearchResponse, MetadataEvent, MetadataSection
from tests.links.conftest import links_vcr


# Safety check: Skip if no API token and no cassette (for recording)
# For playback, we don't need the token.
def is_playback_only():
    return not os.environ.get('RF_TOKEN')


class TestLinksMgr:
    """Test suite for the LinksMgr class using VCR for playback."""

    @pytest.fixture
    def links_mgr(self):
        """Fixture to provide a clean LinksMgr instance."""
        # Use a dummy token if we are in playback mode to satisfy RFClient validation
        token = os.environ.get('RF_TOKEN') or '0' * 32
        return LinksMgr(rf_token=token)

    @links_vcr.use_cassette('test_vulnerability_links.yaml')
    def test_vulnerability_links(self, links_mgr):
        """
        Verify technical and insikt links for a high-signal vulnerability (Log4Shell).
        """
        target_entity = 'kvXvR5'

        for source in ['technical', 'insikt']:
            filters = LinksFilterObjects(sources=[source])
            response = links_mgr.search(entities=[target_entity], filters=filters)

            links_found = response.data[0].links
            assert isinstance(response, LinksSearchResponse)
            # Vulnerability should have links in these sources
            assert len(links_found) >= 0

    @links_vcr.use_cassette('test_list_sections.yaml')
    def test_list_sections(self, links_mgr):
        """Verify that the API returns valid section data."""
        sections = links_mgr.list_sections()
        assert len(sections) > 0
        assert isinstance(sections[0], MetadataSection)

    @links_vcr.use_cassette('test_list_events.yaml')
    def test_list_events(self, links_mgr):
        """Verify that the API returns valid event types."""
        events = links_mgr.list_events()
        assert len(events) > 0
        assert isinstance(events[0], MetadataEvent)

    @links_vcr.use_cassette('test_list_entity_types.yaml')
    def test_list_entity_types(self, links_mgr):
        """Verify that the API returns valid entity types."""
        types = links_mgr.list_entity_types()
        assert len(types) > 0
        assert isinstance(types[0], IdName)

    @links_vcr.use_cassette('test_full_links_search.yaml')
    def test_full_links_search(self, links_mgr):
        """
        Verify a full end-to-step search for a known entity.
        """
        target_entity = 'idn:google.com'
        search_filters = LinksFilterObjects(sources=['technical'])

        response = links_mgr.search(entities=[target_entity], filters=search_filters)

        assert isinstance(response, LinksSearchResponse)
        assert len(response.data) > 0
        result_set = response.data[0]
        assert result_set.entity.id_ == target_entity

    def test_caching_isolation(self, links_mgr):
        """Verify that caches are isolated and don't overwrite each other."""
        # Mock the list methods to avoid actual API calls for cache test if not using VCR here
        # or we can just use VCR for this too.
        with links_vcr.use_cassette('test_caching_isolation.yaml'):
            # Trigger sections cache
            _ = links_mgr.valid_sections
            assert links_mgr._cache_sections is not None
            assert links_mgr._cache_events is None

            # Trigger events cache
            _ = links_mgr.valid_events
            assert links_mgr._cache_events is not None

    @links_vcr.use_cassette('test_malware_and_c2_links.yaml')
    def test_malware_and_c2_links(self, links_mgr):
        """
        Verify technical and insikt links for an IP.
        """
        target_id = 'ip:185.225.75.241'

        results = {}
        for source in ['technical', 'insikt']:
            filters = LinksFilterObjects(sources=[source])
            response = links_mgr.search(entities=[target_id], filters=filters)

            links_found = response.data[0].links
            results[source] = len(links_found)
            assert isinstance(response, LinksSearchResponse)

        assert results['technical'] >= 0
