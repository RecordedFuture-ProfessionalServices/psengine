from psengine.entity_match import EntityMatchMgr

ID = 'b89Juu'
mgr = EntityMatchMgr()

entity = mgr.lookup(ID)
if entity:
    print(entity.attributes.name)
