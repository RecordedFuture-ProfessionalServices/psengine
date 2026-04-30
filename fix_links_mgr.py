import re

with open("psengine/links/links_mgr.py", "r") as f:
    content = f.read()

content = content.replace('"""Domain validation for search filters against live caches"""', '"""Domain validation for search filters against live caches."""')
content = content.replace('assert self._cache_sections is not None', 'if self._cache_sections is None:\n            raise RuntimeError("Sections cache failed to populate.")')
content = content.replace('"""Lazy load and return a set of valid events for validation"""', '"""Lazy load and return a set of valid events for validation."""')
content = content.replace('assert self._cache_events is not None', 'if self._cache_events is None:\n            raise RuntimeError("Events cache failed to populate.")')

content = content.replace('''    @property
    @debug_call
    def valid_entity_types(self) -> set[str]:
        if self._cache_entity_types is None:''', '''    @property
    @debug_call
    def valid_entity_types(self) -> set[str]:
        """Lazy load and return a set of valid entity types for validation."""
        if self._cache_entity_types is None:''')

content = content.replace('assert self._cache_entity_types is not None', 'if self._cache_entity_types is None:\n            raise RuntimeError("Entity types cache failed to populate.")')
content = content.replace('"""List all supported entity types for Link Searches"""', '"""List all supported entity types for Link Searches."""')

with open("psengine/links/links_mgr.py", "w") as f:
    f.write(content)
