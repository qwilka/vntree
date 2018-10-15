
import itertools
import logging

logger = logging.getLogger(__name__)


class Node:
    """Node class for tree data structure.  
    """
    def __init__(self, name, parent=None):
        self.name = name
        self.childs = []
        if parent and isinstance(parent, Node):
            parent.add_child(self)
        elif parent is None:
            self.parent = parent
        else:
            raise TypeError("Node instance «{}» argument «parent» type not valid: {}".format(name, type(parent)))

    def __str__(self):
        _level = len(self.get_ancestors())
        return "{} level={} «{}»".format(self.__class__.__name__, _level, self.name)

    def __iter__(self): 
        logger.debug("__iter__ self yield «%s»" % (self.name,))
        yield self  
        if logger.getEffectiveLevel() == logging.DEBUG: 
            print(*map(iter, self.childs))
        for node in itertools.chain(*map(iter, self.childs)):
            #if VIEW_ITER_TREE: print("node yield «{}»".format(node.name))
            logger.debug("__iter__ node yield «%s»" % (node.name,))
            yield node

    def __reversed__(self):  
        for node in itertools.chain(*map(reversed, self.childs)):
            #if VIEW_ITER_TREE: print("node yield «{}»".format(node.name))
            logger.debug("__reversed__ node yield «%s»" % (node.name,))
            yield node
        #if VIEW_ITER_TREE: print("self yield «{}»".format(self.name))
        logger.debug("__reversed__ self yield «%s»" % (self.name,))
        yield self 

    def add_child(self, newnode):
        self.childs.append(newnode)
        newnode.parent = self
        return True    

    def get_ancestors(self):
        ancestors=[]
        _curnode = self
        while _curnode.parent:
            _curnode = _curnode.parent
            ancestors.append(_curnode)
        return ancestors

    def to_texttree(self):
        treetext = ""
        root_level = len(self.get_ancestors())
        for node in self: 
            level = len(node.get_ancestors()) - root_level
            treetext += ("." + " "*3)*level + "|---{}\n".format(node.name)
        return treetext


if __name__ == "__main__":
    logger.setLevel(logging.INFO)  # logging.DEBUG logging.INFO
    ch = logging.StreamHandler()
    logger.addHandler(ch)

    SIMPLE_TREE = True

    if SIMPLE_TREE:

        rootnode   = Node('ROOT ("top" of the tree)')
        Node("1st child (leaf node)", parent=rootnode)
        child2 = Node("2nd child", rootnode)
        Node("grand-child1 (leaf node)", child2)
        Node("grand-child2 (leaf node)", child2)
        child3 = Node("3rd child", rootnode)
        Node("another child (leaf node)", rootnode)
        grandchild3 = Node(parent=child3, name="grand-child3")
        ggrandchild = Node("great-grandchild", grandchild3)
        Node("great-great-grandchild (leaf node)", ggrandchild)
        Node("great-grandchild2 (leaf node)", grandchild3)

        if logger.getEffectiveLevel() == logging.DEBUG:
            # for ii, node in enumerate(rootnode):
            #     logger.debug("%s for-loop top-down iteration" % (ii,))
            for ii, node in enumerate(reversed(rootnode)):
                logger.debug("%s for-loop bottom-up iteration" % (ii,))
        else:
            print("\n", rootnode.to_texttree())
            print("\nTree iterate top-down:")
            for node in rootnode:
                print(node)
            print("\nTree iterate bottom-up:")
            for node in reversed(rootnode):
                print(node)

