import logging

from vntree.mongo import MongoNode, vn_uri_to_id

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
lh = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s|%(name)s|%(message)s')
lh.setFormatter(formatter)
logger.addHandler(lh)

host="localhost"
port=3005
db="testing"
collection="newcoll"
root_vn_uri = "this is the rootnode"
db_uri = {
    "host": host,
    "port": port,
    "db": db,
    "collection": collection           
}
db_uri["_id"] = vn_uri_to_id(root_vn_uri )

CREATE_TREE = False
READ_TREE = True

if CREATE_TREE:
    oldtree = MongoNode.node_from_db(**db_uri, load=False)
    if oldtree:
        oldtree.db_delete(True) 

    rootnode = MongoNode("testroot", host=host, port=port, 
        db=db, collection=collection, vn_uri=root_vn_uri )

    ch1 = rootnode.add_child(MongoNode("first child", vn_uri="this is a test"))
    ch2 = rootnode.add_child(MongoNode("second child"))
    gc1 = ch1.add_child(MongoNode("first grandchild"))

    print(rootnode.to_texttree())
    # rootnode.db_insert(True)    


if READ_TREE:
    rootnode = MongoNode.node_from_db(**db_uri, load=False)
    ch1 = rootnode.childs[0]
    ch2 = rootnode.childs[1]
    gc1 = rootnode.childs[0].childs[0]
    print(rootnode.to_texttree())
