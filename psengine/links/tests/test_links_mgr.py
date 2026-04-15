import os
import pytest
from psengine.links.links_mgr import LinksMgr
from psengine.links.response import MetadataSection, MetadataEvent
from psengine.common_models import IdName

# Safety check: Skip these tests if no API token is found in the environment.
pytestmark = pytest.mark.skipif(
    not os.environ.get("RF_TOKEN"),
    reason="RF_TOKEN environment variable is not set. Skipping live integration tests."
)

class TestLinksMgrIntegration:
    """Live integration test suite for the LinksMgr class."""

    @pytest.fixture
    def links_mgr(self):
        """Fixture to provide a clean LinksMgr instance."""
        # By providing no arguments, it relies on the RF_TOKEN env var.
        return LinksMgr()

    def test_list_sections_live(self, links_mgr):
        """Verify that the live API returns valid section data."""
        sections = links_mgr.list_sections()
        
        # 1. We expect Recorded Future to return at least 1 section
        assert len(sections) > 0
        assert isinstance(sections[0], MetadataSection)
        
        # === VISUAL VERIFICATION ===
        print("\n" + "="*40)
        print("METADATA SECTION (LIVE):")
        print(sections[0].model_dump_json(indent=2))
        print("="*40 + "\n")
        
        # 2. Extract the IDs to verify against known Recorded Future data
        section_ids = {s.id_ for s in sections}
        assert "iU_ZsE" in section_ids, "Expected RF Section ID 'iU_ZsE' not found."

    def test_valid_sections_live_caching(self, links_mgr):
        """Verify that lazy-loading works for sections."""
        assert links_mgr._cache_sections is None
        _ = links_mgr.valid_sections
        assert links_mgr._cache_sections is not None

    def test_list_events_live(self, links_mgr):
        """Verify that the live API returns valid event types."""
        events = links_mgr.list_events()
        
        assert len(events) > 0
        assert isinstance(events[0], MetadataEvent)
        
        # === VISUAL VERIFICATION ===
        print("\n" + "="*40)
        print("METADATA EVENT (LIVE):")
        print(events[0].model_dump_json(indent=2))
        print("="*40 + "\n")
        
        event_ids = {e.id_ for e in events}
        # Recorded Future prefixes event IDs with 'type:'
        assert "type:InfrastructureAnalysis" in event_ids

    def test_valid_events_live_caching(self, links_mgr):
        """Verify that lazy-loading works for events."""
        assert links_mgr._cache_events is None
        _ = links_mgr.valid_events
        assert links_mgr._cache_events is not None

    def test_list_entity_types_live(self, links_mgr):
        """Verify that the live API returns valid entity types."""
        types = links_mgr.list_entity_types()
        
        assert len(types) > 0
        assert isinstance(types[0], IdName)
        
        # === VISUAL VERIFICATION ===
        print("\n" + "="*40)
        print("METADATA ENTITY TYPE (LIVE):")
        print(types[0].model_dump_json(indent=2))
        print("="*40 + "\n")
        
        type_ids = {t.id_ for t in types}
        # Recorded Future prefixes entity type IDs with 'type:'
        assert "type:IpAddress" in type_ids or "type:Company" in type_ids

    def test_valid_entity_types_live_caching(self, links_mgr):
        """Verify that lazy-loading works for entity types."""
        assert links_mgr._cache_entity_types is None
        _ = links_mgr.valid_entity_types
        assert links_mgr._cache_entity_types is not None
