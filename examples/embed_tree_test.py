from vntree import EmbedNode as Node
from vntree.utilities import turn_on_logging
turn_on_logging()

rootnode   = Node('root EmbedNode')
Node("first child", parent=rootnode)
child2 = Node("2nd child", rootnode)
Node("grand-child1 (leaf node)", child2)
Node("grand-child2 (leaf node)", child2)
child3 = Node("3rd child", rootnode)
Node("another child (leaf node)", rootnode)
grandchild3 = Node(parent=child3, name="grand-child3")
ggrandchild = Node("great-grandchild", grandchild3)
Node("great-great-grandchild (leaf node)", ggrandchild)
Node("great-grandchild2 (leaf node)", grandchild3)



world = Node('The World', data={"population":7762609412}) 
europe = Node('Europe', world)
Node('Belgium', europe, {"capital":"Brussels","population":11515793})
europe.add_child( Node('Greece', data={"capital":"Athens","population":10768477}) )
scandinavia = Node('Scandinavia', europe)
europe.add_child( Node('Spain', data={"capital":"Madrid","population":46733038}) )
denmark = Node('Denmark', scandinavia, {"capital":"Copenhagen","population":5822763})
scandinavia.add_child( Node('Sweden', data={"capital":"Stockholm","population":10302984}) )
Node('Norway', scandinavia, {"capital":"Oslo","population":5421241})
Node('Faroe Islands', denmark)
denmark.add_child( Node("Greenland") )
samerica = Node('South America', world)
Node('Chile', samerica, {"capital":"Santiago","population":17574003})

rootnode.embed_tree(world)

print()
print(rootnode.to_texttree())
