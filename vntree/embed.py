import itertools


from .node import Node, NodeAttr, TreeAttr


class EmbedNode(Node):

    def __init__(self, name=None, parent=None, data=None, 
                treedict=None, fpath=None, nodeid=None):
        super().__init__(name, parent, data, treedict, fpath, nodeid)
        #self.childs.insert(0, Node("EMBED"))
        self.childs.insert(0, None)
        self._activated = False
        #self.childs[0].parent = self


    def __iter__(self): 
        yield self  
        if not self._activated or self.childs[0] is None:
            _i = 1
        else:
            _i = 0
        for node in itertools.chain(*map(iter, self.childs[_i:])):
            yield node


    def __reversed__(self):  
        if not self._activated or self.childs[0] is None:
            _i = 1
        else:
            _i = 0
        for node in itertools.chain(*map(reversed, reversed(self.childs[_i:]))):
            yield node
        yield self 


    def embed_tree(self, newtree):
        if self.childs[0] is None:
            self.childs.pop(0)
            self.add_child(self.__class__("EMBED"), idx=0) 
        self.childs[0].add_child(newtree)


    def activate(self, recursive=False):
        if recursive:
            for _n in self:
                if isinstance(_n, EmbedNode):
                    _n.activate()
        else:
            self._activated = True


    def deactivate(self, recursive=False):
        if recursive:
            for _n in self:
                if isinstance(_n, EmbedNode):
                    _n.deactivate()
        else:
            self._activated = False

