from psengine.entity_lists import EntityListMgr

domain = "example2.com"

mgr = EntityListMgr()
watch_lists = mgr.search("Domain Watch List", "domain")

domain_watch_list = None
for watch_list in watch_lists:
    if (
        watch_list.owner_name
        == "Professional Services Development"
    ):
        domain_watch_list = watch_list

if domain_watch_list:
    add_op = domain_watch_list.add(
        (domain, "InternetDomainName")
    )

    if add_op.result == "added":
        for entity in domain_watch_list.entities():
            print(entity)

    print(domain_watch_list.status())
