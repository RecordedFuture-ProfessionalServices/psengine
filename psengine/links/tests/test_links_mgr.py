import os
import pytest
from psengine.links.links_mgr import LinksMgr
from psengine.links.response import MetadataSection

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
        # Print the first parsed object to the console so the user can inspect it.
        print("\n" + "="*40)
        print("LIVE API DATA PARSED BY PYDANTIC:")
        print(sections[0].model_dump_json(indent=2))
        print("="*40 + "\n")
        
        # 2. Extract the IDs to verify against known Recorded Future data
        section_ids = {s.id_ for s in sections}
        
        # 'iU_ZsE' is the known ID for "Actors, Tools & TTPs"
        assert "iU_ZsE" in section_ids, "Expected standard RF Section ID not found in live response."

    def test_valid_sections_live_caching(self, links_mgr):
        """Verify that lazy-loading works seamlessly with the live API."""
        # 1. Initially, cache should be empty
        assert links_mgr._cache_sections is None
        
        # 2. First access triggers the live fetch
        sections_set = links_mgr.valid_sections
        assert len(sections_set) > 0
        assert isinstance(sections_set, set)
        
        # 'iU_ZsG' is the known ID for "Indicators & Detection Rules"
        assert "iU_ZsG" in sections_set
        
        # 3. Cache must be populated after the property is accessed
        assert links_mgr._cache_sections is not None
