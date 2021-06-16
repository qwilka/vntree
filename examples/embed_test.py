#import argparse

from vntree import EmbedNode, Node

description = """A simple tree data structure based on vntree.Node class."""

# aparser = argparse.ArgumentParser(description=description)
# aparser.add_argument("case", help="Specify an example case to run.", 
#     nargs='?', default="basic",
#     choices=["basic", "world"])
# args = aparser.parse_args()




#if args.case == "basic":
rootnode   =EmbedNode('ROOT')
EmbedNode("1st child", parent=rootnode)
child2 = EmbedNode("2nd child", rootnode)
EmbedNode("grand-child1", child2)
# EmbedNode("grand-child2", child2)
# child3 = EmbedNode("3rd child", rootnode)
# EmbedNode("another child", rootnode)
# grandchild3 = EmbedNode(parent=child3, name="grand-child3")
# ggrandchild = EmbedNode("great-grandchild", grandchild3)
# EmbedNode("great-great-grandchild", ggrandchild)
# EmbedNode(None, grandchild3, {"name":"name-in-data"})

newtree = Node("EMBED: new-tree")
Node("EMBED: 1st child", parent=newtree)
rootnode.embed_tree(newtree)

newtree2 = Node("EMBED2: new-tree")
Node("EMBED2: 1st child", parent=newtree2)
child2.embed_tree(newtree2)
