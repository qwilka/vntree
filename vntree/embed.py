import itertools
import logging


from .node import Node, NodeAttr, TreeAttr

logger = logging.getLogger(__name__)


class EmbedNode(Node):

    def __init__(self, name=None, parent=None, data=None, 
                treedict=None, fpath=None, nodeid=None):
        super().__init__(name, parent, data, treedict, fpath, nodeid)
        #self.childs.insert(0, Node("EMBED"))
        self._active = False
        if treedict is None:
            self.childs.insert(0, None)
        #self.add_child(self.__class__("EMBED"), idx=0)
        #self._activated = False
        #self._state = "NORMAL" # "NORMAL" | "EMBED" | "ALL"
        #self.childs[0].parent = self


    def __iter__(self): 
        yield self  
        if self._active and self.childs[0] is not None:
            _i = 0
        else:
            _i = 1
        for ii, node in enumerate(itertools.chain(*map(iter, self.childs[_i:]))):
            yield node


    def __reversed__(self):  
        if self._active and self.childs[0] is not None:
            _i = 0
        else:
            _i = 1
        for node in itertools.chain(*map(reversed, reversed(self.childs[1:]))):
            yield node
        yield self 


    def embed_tree(self, newtree):
        # _tmp = self._active
        # self._active = True
        if self.childs[0] is None:
            self.childs.pop(0)
            self.add_child(self.__class__("EMBEDDED"), idx=0, check_id=True)
            #self.add_child(newtree, idx=0, check_id=True)  
        self.childs[0].add_child(newtree, check_id=True)
        # else:
        #     logger.error("%s.embed_tree: node «%s» already has embedded tree, cannot embed node «%s»." % (self.__class__.__name__, self.name, newtree.name))
        #self._active = _tmp


    def activate(self, recursive=False):
        if recursive:
            for _n in self:
                if isinstance(_n, EmbedNode):
                    _n.activate()
        else:
            self._active = True


    def deactivate(self, recursive=False):
        if recursive:
            for _n in self:
                if isinstance(_n, EmbedNode):
                    _n.deactivate()
        else:
            self._active = False


    def get_node_by_id(self, _id):
        _tmp = self._active
        self._active = True
        for _n in self:
            if _n._id == _id:
                self._active = _tmp
                return _n
        self._active = _tmp


# if __name__ == "__main__":
#     logger.setLevel(logging.DEBUG)
#     ch = logging.StreamHandler()
#     logger.addHandler(ch)

#     rootnode   = EmbedNode('root EmbedNode')
#     Node("EMBEDDED first child", parent=rootnode)
#     child2 = Node("2nd child", rootnode)
#     Node("grand-child1 (leaf node)", child2)
#     Node("grand-child2 (leaf node)", child2)
#     child3 = Node("3rd child", rootnode)
#     Node("another child (leaf node)", rootnode)
#     grandchild3 = Node(parent=child3, name="grand-child3")
#     ggrandchild = Node("great-grandchild", grandchild3)
#     Node("great-great-grandchild (leaf node)", ggrandchild)
#     Node("great-grandchild2 (leaf node)", grandchild3)
#     print()
#     print(rootnode.to_texttree())
