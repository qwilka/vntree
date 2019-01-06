import json

from vntree import Node

example1 = False
example2 = False
treedict_example = False
JSON_example = False
YAML_example = True

if example1:
    rootnode = Node("root-node")    # the root node has no parent
    print(f"The name of the root node is «{rootnode.name}»")
    Node("The first child", rootnode)
    c1 = rootnode.childs[0]
    gc1 = Node("first grand-child", c1)
    print(rootnode.to_texttree())

if example2:
    rootnode = Node("The Root Node")    # the root node has no parent
    Node("first child", rootnode)       # create a child node
    c2 = Node("child 2", rootnode)      # create another child node
    Node("child3", rootnode)            # create 3rd child node
    g1 = Node("grandchild1", c2)        # child of node «child 2»
    Node(parent=c2)       # another grandchild node, name not specified
    c1 = rootnode.get_node_by_nodepath("/rootnode/first child")
    c1.add_child(Node())  # grafting an external node into the tree
    print(rootnode.to_texttree())

if treedict_example:
    # create a tree from a treedict
    tdict = {
        "name": "ROOT",
        "data": {
            "meta1": 1234,
        },
        "childs": [
            {
                "name": "child1",
                "childs": [{"name":"gc1"}, {"name":"gc2"}],
            },
            {
                "name": "child2",
                "data": {"test1": "this is test data"},
                "childs": [{"name":"another gc", "childs":[{"name":"ggc1"}]} ],
            },
        ]
    }
    rootnode = Node(treedict=tdict)
    print(rootnode.to_texttree())

if JSON_example:
    # tree from JSON (for convenience, start by creating a tree from treedict)
    tdict = {
        "name": "ROOT",
        "data": {
            "meta1": 1234,
        },
        "childs": [
            {
                "name": "child1",
                "childs": [{"name":"gc1"}, {"name":"gc2"}],
            },
            {
                "name": "child2",
                "data": {"test1": "this is test data"},
                "childs": [{"name":"another gc", "childs":[{"name":"ggc1"}]} ],
            },
        ]
    }
    origtree = Node(treedict=tdict)
    jsonstring = json.dumps(origtree.to_treedict())
    print(jsonstring)
    td_fromjson = json.loads(jsonstring)
    newtree = Node(treedict=td_fromjson)
    print(newtree.to_texttree())
    tcomp = newtree.tree_compare(origtree)
    print("origtree is newtree: ", origtree is newtree)
    print("Similarity between origtree and newtree: ", tcomp)
    # add another child to newtree
    newtree.add_child(Node("A NEW CHILD"))
    print(newtree.to_texttree())
    tcomp = newtree.tree_compare(origtree)
    print("Similarity between origtree and newtree: ", tcomp)

if YAML_example:
    # tree from YAML
    yamltree = """
- !Node &root
  name: "root node"
  parent: null
  data:
    testval1: 111
    testval2: 222
- !Node &n0
  name: "child 1"
  parent: *root
- !Node &n1
  parent: *root
  data:
    name: "second child"
    astring: "testing..."
- !Node &n2
  parent: *root
  data:
    name: "third child"
    astring: "testing..."
- !Node 
  parent: *n1
  data:
    name: "grand child"
    test: 1234
"""
    #Node.setup_yaml()
    ytree = Node.yaml2tree(yamltree)
    print(ytree.to_texttree())

