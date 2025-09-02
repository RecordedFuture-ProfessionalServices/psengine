from psengine.enrich import LookupMgr

URLS = [
    "http://www.example.com/1",
    "http://www.example.com/2",
]
mgr = LookupMgr()

urls = mgr.lookup_bulk(
    URLS, "url", fields=["links"], max_workers=2
)
for url in urls:
    if url.is_enriched:
        print(url)
