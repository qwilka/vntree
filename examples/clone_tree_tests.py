import argparse
import json
#import logging

from vntree import Node

#logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)
#ch = logging.StreamHandler()
#logger.addHandler(ch)

description = """Examples of cloning/copying trees."""


aparser = argparse.ArgumentParser(description=description)
aparser.add_argument("case", help="Specify an example case to run.", 
    nargs='?', default="basic",
    choices=["basic", "world"])
args = aparser.parse_args()




if args.case == "basic":
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
    Node(None, grandchild3, {"_vntree":{"name":"name-in-data"}})


if args.case == "world":
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


print("\nOriginal tree «rootnode»")
rootnode.show()


# copy tree via JSON
print("\nCreate «newtree» using Node.from_JSON \n")
Jstr = rootnode.to_JSON()
newtree = Node.from_JSON(Jstr)
newtree.show()
print(f"\nrootnode._id = {rootnode._id}\nnewtree._id  = {newtree._id}")

# clone tree using «clone» method
print("\nCreate «newtree» using the «self.clone» method \n")
del newtree
newtree = rootnode.clone()
newtree.show()
print(f"\nrootnode._id = {rootnode._id}\nnewtree._id  = {newtree._id}")

# clone tree using «clone» method and change _ids
print("\nCreate «newtree» with new _ids using «self.clone(change_id=True)»\n")
del newtree
newtree = rootnode.clone(change_id=True)
newtree.show()
print(f"\nrootnode._id = {rootnode._id}\nnewtree._id  = {newtree._id}")

for n in newtree:
    n.name = "NEW: " + n.name

rootnode.add_child(newtree, check_id=True)
rootnode.show()
