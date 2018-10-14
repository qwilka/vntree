import json
#import logging

from vntree import Node

#logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
#ch = logging.StreamHandler()
#logger.addHandler(ch)

rootnode   = Node('ROOT')
Node("1st child", parent=rootnode)
child2 = Node("2nd child", rootnode)
Node("grand-child1", child2)
Node("grand-child2", child2)
child3 = Node("3rd child", rootnode)
Node("another child", rootnode)
grandchild3 = Node(parent=child3, name="grand-child3")
ggrandchild = Node("great-grandchild", grandchild3)
Node("great-great-grandchild", ggrandchild)
Node(None, grandchild3, {"name":"name-in-data"})

#print(rootnode.to_texttree(func=lambda n: " {}, coord={}".format(n.name, n.coord)))
print(rootnode.to_texttree())
#print(json.dumps(rootnode.to_treedict()))
# for ii, node in enumerate(rootnode):
#     print("{} top-down «{}»".format(ii, node.name))
# for ii, node in enumerate(reversed(rootnode)):
#     print("{} bottom-up «{}»".format(ii, node.name))
