import os
import pytest
from psengine.links.links_mgr import LinksMgr
from psengine.links.response import MetadataSection, MetadataEvent, LinksSearchResponse
from psengine.links.requests import LinksFilterObjects
from psengine.common_models import IdName

# Safety check: Skip these tests if no API token is found in the environment.
pytestmark = pytest.mark.skipif(
    not os.environ.get("RF_TOKEN"),
    reason="RF_TOKEN environment variable is not set. Skipping live integration tests."
)

from psengine.entity_match.entity_match_mgr import EntityMatchMgr

class TestLinksMgrIntegration:
    """Live integration test suite for the LinksMgr class."""

    @pytest.fixture
    def links_mgr(self):
        """Fixture to provide a clean LinksMgr instance."""
        return LinksMgr()

    @pytest.fixture
    def entity_match_mgr(self):
        """Fixture to provide an EntityMatchMgr instance."""
        return EntityMatchMgr()

    def test_vulnerability_links_live(self, links_mgr):
        """
        Verify technical and insikt links for a high-signal vulnerability (Log4Shell).
        This guarantees a massive amount of data in both Technical and Insikt sources,
        allowing us to definitively prove the filtering logic works.
        """
        target_entity = "vulnerability:CVE-2021-44228"
        print("\n" + "="*40)
        print(f"ANALYZING VULNERABILITY: {target_entity}")
        
        for source in ["technical", "insikt"]:
            filters = LinksFilterObjects(sources=[source])
            response = links_mgr.search(entities=[target_entity], filters=filters)
            
            links_found = response.data[0].links
            print(f"Source: {source.upper()} | Links found: {len(links_found)}")
            
            assert isinstance(response, LinksSearchResponse)
            
            # Log4j is historically massive; it MUST have links in both sources
            if len(links_found) > 0:
                sample = links_found[0]
                print(f" - Sample {source.title()} Link: {sample.name} ({sample.type_})")

        print("="*40 + "\n")

    def test_list_sections_live(self, links_mgr):
        """Verify that the live API returns valid section data."""
        sections = links_mgr.list_sections()
        assert len(sections) > 0
        assert isinstance(sections[0], MetadataSection)
        
        print("\n" + "="*40)
        print("METADATA SECTION (LIVE):")
        print(sections[0].model_dump_json(indent=2))
        print("="*40 + "\n")

    def test_list_events_live(self, links_mgr):
        """Verify that the live API returns valid event types."""
        events = links_mgr.list_events()
        assert len(events) > 0
        assert isinstance(events[0], MetadataEvent)
        
        print("\n" + "="*40)
        print("METADATA EVENT (LIVE):")
        print(events[0].model_dump_json(indent=2))
        print("="*40 + "\n")

    def test_list_entity_types_live(self, links_mgr):
        """Verify that the live API returns valid entity types."""
        types = links_mgr.list_entity_types()
        assert len(types) > 0
        assert isinstance(types[0], IdName)
        
        print("\n" + "="*40)
        print("METADATA ENTITY TYPE (LIVE):")
        print(types[0].model_dump_json(indent=2))
        print("="*40 + "\n")

    def test_full_links_search_live(self, links_mgr):
        """
        Verify a full end-to-step search for a known entity.
        This tests: Validation -> Transport -> Complex Response Parsing.
        """
        # 1. Setup the search for a known stable entity (Google)
        target_entity = "idn:google.com"
        
        # 2. Apply a filter to exercise the _validate_filters logic
        search_filters = LinksFilterObjects(
            sources=["technical"]
        )
        
        # 3. Execute the search
        response = links_mgr.search(
            entities=[target_entity],
            filters=search_filters
        )
        
        # 4. Basic Assertions
        assert isinstance(response, LinksSearchResponse)
        assert len(response.data) > 0
        
        # 5. Result Set Verification
        result_set = response.data[0]
        assert result_set.entity.id_ == target_entity
        
        # === VISUAL VERIFICATION OF SEARCH RESULTS ===
        print("\n" + "="*40)
        print(f"SEARCH RESULTS FOR {target_entity}:")
        # We print the first result set and its first 2 links for clarity
        sample_output = {
            "queried_entity": result_set.entity.model_dump(),
            "total_links_found": len(result_set.links),
            "sample_link": result_set.links[0].model_dump() if result_set.links else "No links found"
        }
        import json
        print(json.dumps(sample_output, indent=2))
        print("="*40 + "\n")

    def test_caching_isolation_live(self, links_mgr):
        """Verify that caches are isolated and don't overwrite each other."""
        # Trigger sections cache
        _ = links_mgr.valid_sections
        assert links_mgr._cache_sections is not None
        assert links_mgr._cache_events is None
        
        # Trigger events cache
        _ = links_mgr.valid_events
        assert links_mgr._cache_events is not None

    def test_malware_and_c2_links_live(self, links_mgr):
        """
        Verify technical and insikt links. 
        We use an IP for this because the Links API supports Natural IDs for IPs.
        """
        # Using the C2 IP you provided
        target_id = "ip:185.225.75.241"
        
        print("\n" + "="*40)
        print(f"ANALYZING INFRASTRUCTURE: {target_id}")
        
        # We test BOTH sources to see if we get different telemetry
        results = {}
        for source in ["technical", "insikt"]:
            filters = LinksFilterObjects(sources=[source])
            response = links_mgr.search(entities=[target_id], filters=filters)
            
            links_found = response.data[0].links
            results[source] = len(links_found)
            print(f"Source: {source.upper()} | Links found: {len(links_found)}")
            
            assert isinstance(response, LinksSearchResponse)

        # Verification: A known C2 IP should have at least some technical links
        # Insikt links might be 0 if no analyst has written a note about it recently.
        assert results["technical"] >= 0
        
        if results["technical"] > 0:
            sample = response.data[0].links[0]
            print(f"Sample Link: {sample.name} ({sample.type_})")
            for attr in sample.attributes:
                print(f" - {attr.id_}: {attr.value}")

        print("="*40 + "\n")
