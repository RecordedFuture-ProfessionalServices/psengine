from psengine.entity_lists import EntityListMgr

domain = "example2.com"

mgr = EntityListMgr()
domain_watch_list = mgr.search(
    "Domain Watch List", "domain"
)

if domain_watch_list:
    domain_watch_list = domain_watch_list[0]
    add_op = domain_watch_list.add(
        (domain, "InternetDomainName")
    )

    if add_op.result == "added":
        for entity in domain_watch_list.entities():
            print(entity)

    print(domain_watch_list.status())
