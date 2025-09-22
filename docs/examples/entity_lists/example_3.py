from psengine.entity_lists import EntityListMgr

domains = ['idn:example2.com', 'idn:reddit.com']

mgr = EntityListMgr()
domain_watch_list = mgr.search(
    'Domain Watch List', 'domain'
)

if domain_watch_list:
    domain_watch_list = domain_watch_list[0]
    remove_op = domain_watch_list.bulk_remove(
        [
            (domain, 'InternetDomainName')
            for domain in domains
        ]
    )

    print(remove_op)
