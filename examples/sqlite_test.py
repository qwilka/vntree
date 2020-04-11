import argparse
import json
import logging

from vntree.sqlite import SqliteNode as Node



description = """Tesing SqliteNode."""

aparser = argparse.ArgumentParser(description=description)
aparser.add_argument("case", help="select example case", 
    nargs='?', default="open",
    choices=["basic1", "basic2", "world", "treedict", "JSON", "YAML",
    "top-down", "bottom-up", "open"])
aparser.add_argument("--logging", help="select logging level", 
    default="ERROR",
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
aparser.add_argument("-f", "--fpath", dest="fpath", 
    default=None, help="«-f filepath» open specifed vn4 file.")
args = aparser.parse_args()
# if hasattr(args, "fpath") and args.fpath is None:
#     raise ValueError("open -f «filepath» must specify a valid file path") 

logger = logging.getLogger()
try:
    logging_lvl = getattr(logging, args.logging)
except AttributeError:
    logging_lvl = logging.ERROR
logger.setLevel(logging_lvl)
lh = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s|%(name)s|%(message)s')
lh.setFormatter(formatter)
logger.addHandler(lh)


print(f"vntree usage example with sqlite «{args.case}»:")

if args.case == "basic1":
    rootnode = Node("root-node")    # the root node has no parent
    print(f"The name of the root node is «{rootnode.name}»")
    Node("The first child", rootnode, data={"test1": "this is test data"})
    Node("anon child", rootnode)
    Node("2nd child", rootnode)
    Node("anon child", rootnode)
    Node("3rd child", rootnode)
    c1 = rootnode.childs[0]
    gc1 = Node("first grand-child", c1)
    Node("2nd grand-child", c1)
    gc3 = Node("3rd grand-child", c1)
    Node("1st great grand-child", gc3)
    Node("great grand-child", gc3)
    Node("great grand-child", gc3)
    print(rootnode.to_texttree())
    rootnode.savefile("basictest.vn4")


elif args.case == "basic2":
    rootnode = Node("The Root Node")    # the root node has no parent
    Node("first child", rootnode)       # create a child node
    c2 = Node("child 2", rootnode)      # create another child node
    Node("child3", rootnode)            # create 3rd child node
    g1 = Node("grandchild1", c2)        # child of node «child 2»
    Node(parent=c2)       # another grandchild node, name not specified
    c1 = rootnode.get_node_by_path("/rootnode/first child")
    c1.add_child(Node())  # grafting an external node into the tree
    print(rootnode.to_texttree())


elif args.case == "world":
    rootnode = Node('The World', data={"population":7762609412}) 
    europe = Node('Europe', rootnode)
    Node('Belgium', europe, {"capital":"Brussels","population":11515793})
    europe.add_child( Node('Greece', data={"capital":"Athens","population":10768477}) )
    scandinavia = Node('Scandinavia', europe)
    europe.add_child( Node('Spain', data={"capital":"Madrid","population":46733038}) )
    denmark = Node('Denmark', scandinavia, {"capital":"Copenhagen","population":5822763})
    scandinavia.add_child( Node('Sweden', data={"capital":"Stockholm","population":10302984}) )
    Node('Norway', scandinavia, {"capital":"Oslo","population":5421241})
    Node('Faroe Islands', denmark)
    denmark.add_child( Node("Greenland") )
    samerica = Node('South America', rootnode)
    Node('Chile', samerica, {"capital":"Santiago","population":17574003})
    print(rootnode.to_texttree())
    rootnode.savefile("theworld.vn4")

elif args.case == "treedict":
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

elif args.case == "JSON":
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

elif args.case == "YAML":
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

elif args.case == "top-down":
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
    print(f"using example tree:\n{rootnode.to_texttree()}")
    print("print tree nodes in «top-down» order:")
    for ii, n in enumerate(rootnode):
        print(f"node{ii} name=«{n.name}» coord={n._coord} level={n._level}")

elif args.case == "bottom-up":
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
    print(f"using example tree:\n{rootnode.to_texttree()}")
    print("print tree nodes in «bottom-up» order:")
    for ii, n in enumerate(reversed(rootnode)):
        print(f"node{ii} name=«{n.name}» coord={n._coord} level={n._level}")


elif args.case == "open":
    print(f"args={args}")
    if hasattr(args, "fpath") and args.fpath is None:
        raise ValueError("-f «filepath» must specify a valid file path") 
    rootnode = Node.openfile(args.fpath) 
    #rootnode.show()

