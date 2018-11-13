import logging

from vntree import Node, TreeAttr, NodeAttr

logger = logging.getLogger(__name__)

class Tode(Node):
    nattr = NodeAttr()
    tattr = TreeAttr()
    def __init__(self, name=None, parent=None, data=None):
        super().__init__(name, parent, data)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    logger.addHandler(ch)

    SIMPLE_TREE = True

    if SIMPLE_TREE:

        rootnode   = Tode('ROOT (level 0, the "top" of the tree)',
                        data={
                            "nattr": "this is a NodeAttr!",
                            "tattr": "this is a TreeAttr?!",
                        })
        Tode("1st child (level 1, leaf node)", parent=rootnode)
        child2 = Tode("2nd child (level 1)", rootnode)
        Tode("grand-child1 (level 2, leaf node)", child2)
        Tode("grand-child2 (level 2, leaf node)", child2)
        child3 = Tode("3rd child (level 1)", rootnode)
        Tode("another child (level 1, leaf node)", rootnode)
        grandchild3 = Tode(parent=child3, name="grand-child3 (level 2")
        ggrandchild = Tode("great-grandchild (level 3)", grandchild3)
        Tode("great-great-grandchild (level4, leaf node)", ggrandchild)
        Tode("great-grandchild2 (level 3, leaf node)", grandchild3)

        print(rootnode.to_texttree())