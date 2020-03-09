"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
https://github.com/qwilka/PyCon_Limerick_2020/blob/master/examples/LICENSE
"""
import itertools
import os
import sys

description = """A simple tree data structure based on a Node class."""


class Node:
    """Node class for simple tree data structure.  

    Refs:
    https://en.wikipedia.org/wiki/Tree_(data_structure)
    https://github.com/qwilka/vntree
    """
    def __init__(self, name, parent=None):
        self.name = name
        self.children = []
        if parent and isinstance(parent, Node):
            parent.add_child(self)
        elif parent is None:
            self.parent = None
            self._show_traversal = False  # print messages in __iter__ and __reversed__ methods
        else:
            raise TypeError("Node instance «{}» argument «parent» type not valid: {}".format(name, type(parent)))
        

    def __str__(self):
        return "{} «{}» level={} coord={}".format(self.__class__.__name__, self.name, self._level, self._coord)

    """
    https://docs.python.org/3/library/itertools.html
    https://realpython.com/python-itertools/
    https://pymotw.com/3/itertools/index.html
    https://realpython.com/introduction-to-python-generators/
    """
    def __iter__(self): 
        if self._root._show_traversal: print(f":self: «{self.name}»")
        yield self  
        for ii, node in enumerate(itertools.chain(*map(iter, self.children))):
            if self._root._show_traversal: print(f":{ii}: «{node.name}» «{self.name}»")
            yield node 


    def __reversed__(self):  
        for ii, node in enumerate(itertools.chain(*map(reversed, reversed(self.children)))):
            if self._root._show_traversal: print(f":{ii}: «{node.name}» «{self.name}»")
            yield node
        if self._root._show_traversal: print(f":self: «{self.name}»")
        yield self 


    def add_child(self, newnode):
        self.children.append(newnode)
        newnode.parent = self
        return newnode    


    def get_ancestors(self):
        ancestors=[]
        _curnode = self
        while _curnode.parent:
            _curnode = _curnode.parent
            ancestors.append(_curnode)
        return ancestors


    @property
    def _root(self):
        _n = self
        while _n.parent:
            _n = _n.parent
        return _n


    @property
    def _coord(self):
        _coord = []
        _node = self
        while _node.parent:
            _idx = _node.parent.children.index(_node)
            _coord.insert(0, _idx)
            _node = _node.parent
        return tuple(_coord)

    @property
    def _level(self):
        return len(self.get_ancestors())

    def to_texttree(self):
        treetext = ""
        root_level = len(self.get_ancestors())
        for node in self: 
            level = len(node.get_ancestors()) - root_level
            treetext += ("." + " "*3)*level + "|---{}\n".format(node.name)
        return treetext



if __name__ == '__main__':
    import argparse

    aparser = argparse.ArgumentParser(description=description)
    aparser.add_argument("case", help="Specify an example case to run.", 
        nargs='?', default="basic",
        choices=["basic", "traverse", "topdown", "bottomup"])
    args = aparser.parse_args()

    rootnode = Node('The World')
    europe = Node('Europe', rootnode)
    Node('Belgium', europe)
    europe.add_child( Node('Greece') )
    scandinavia = Node('Scandinavia', europe)
    europe.add_child( Node('Spain') )
    denmark = Node('Denmark', scandinavia)
    scandinavia.add_child( Node('Sweden') )
    Node('Norway', scandinavia)
    Node('Faroe Islands', denmark)
    denmark.add_child( Node("Greenland") )
    samerica = Node('South America', rootnode)
    Node('Chile', samerica)

    print("\n", rootnode.to_texttree())

    if args.case == "basic":
        # $ python simple_tree.py basic 
        pass
    
    if args.case == "traverse":
        # $ python simple_tree.py traverse 
        rootnode._show_traversal = False
        print("\nTree traverse top-down:")
        for node in rootnode:
            print(node)    
        print("\nTree traverse bottom-up:")
        for node in reversed(rootnode):
            print(node)

    if args.case == "topdown":
        # $ python simple_tree.py topdown 
        # switch-on tracing messages in __iter__ method:
        rootnode._show_traversal = True
        print("\nTree iterate top-down:")
        for node in rootnode:
            print(node)

    if args.case == "bottomup":
        # $ python simple_tree.py bottomup 
        # switch-on tracing messages in __reversed__ method:
        rootnode._show_traversal = True
        print("\nTree iterate bottom-up:")
        for node in reversed(rootnode):
            print(node)

