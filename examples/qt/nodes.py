"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See «vntree» LICENSE file for details https://github.com/qwilka/vntree/blob/master/LICENSE
"""
import itertools
import json
import logging
import os
import types
logger = logging.getLogger(__name__)
try:
    from scandir import scandir, walk
except ImportError:
    from os import scandir, walk



class Node:
    """Base (super) class for the tree data structure.
    
    Node is designed to work as part of the Qt model-view framework, it acts
    as the interface between the (real) data and the 'model' part of Qt 
    model-view. Although Node is designed to be consistent with 
    the Qt model-view framework, and is embedded within the 'model', it is 
    an independent data structure and can be also used apart from Qt.  
    Note that Node is not the actual (real) data, it is a parallel data 
    structure for interfacing with Qt model-view.  Contrary to claims made 
    in the official Qt documentation, it involves duplicating the original/real
    data, and it is necessary for the programmer to ensure that Node remains 
    consistent with the real data.  

    Notes
    =====
    http://doc.qt.io/qt-5/modelview.html
    http://www.yasinuludag.com/blog/?p=98  PyQt model-view video tutorials
    """

    def __init__(self, name="nameless node", parent=None, data=None):
        self._name = name  # self.name here causes sub-class crash
        self._childs = []
        if parent is not None:
            parent.insert_child(self)
        self.parent = parent
        self._data = []
        if data and isinstance(data, (list, tuple) ):
            self._data.extend(data)
        else:                     
            self._data.append(data)

    def __iter__(self):
        # http://stackoverflow.com/questions/6914803/python-iterator-through-tree-with-list-of-children
        yield self  # yielding from here preserves order
        for node in itertools.chain(*map(iter, self._childs)):
            yield node

    def get_child(self, idx):
        if idx<0 or idx>=len(self._childs):
            return False
        return self._childs[idx]

    def count_child(self):
        return len(self._childs)

    def child_idx(self):
        if self.parent != None:
            return self.parent._childs.index(self)
        return 0

    def column_count(self):
        return len(self._data) + 1  # name and data

    def get_data(self, idx=None):
        if isinstance(idx, int) and idx>=0 and idx<len(self._data):
            return self._data[idx]
        else:
            return self._data

    def insert_child(self, newchild, idx=None):
        if idx and (idx<0 or idx>len(self._childs)): # Note: idx==len(self._childs) is equivalent to append
            return False
        if idx:
            self._childs.insert(idx, newchild)
        else:
            self._childs.append(newchild)
        newchild.parent = self
        return True

    def insert_column(self):
        raise NotImplementedError("insert_column/insertColumns")

    def get_parent(self): 
        return self.parent

    def remove_child(self):
        raise NotImplementedError("remove_child/removeChildren")

    def remove_column(self):
        raise NotImplementedError("remove_column/removeColumns")

    def set_data(self, idx, value):
        if idx < 0 or idx >= len(self._data):
            return False
        self._data[idx] = value
        return True

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, newname):
        self._name = newname
        return True

    def pop_child(self, idx=None):
        if idx and (idx<0 or idx>=len(self._childs)):
            return False
        if idx:
            oldchild = self._childs.pop(idx)
        else:
            oldchild = self._childs.pop()
        oldchild.parent = None
        return oldchild

    def to_texttree(self, printdata=False, tabLevel=-1):
        nodetext = ""
        tabLevel += 1        
        for i in range(tabLevel):
            nodetext += "." + " "*3  
        nodetext += "|---" + self._name 
        # option printdata: complications due to Python weirdness;
        # slicing, orig[:idx] cannot get the last item in orig;
        # bool is int, http://stackoverflow.com/questions/8169001/why-is-bool-a-subclass-of-int
        if printdata and isinstance(printdata, bool):
            nodetext += " : " + str(self.get_data()) + "\n"
        elif printdata and isinstance(printdata, int):
            nodetext += " : " + str(self.get_data())[:printdata] + "\n"
        else:
            nodetext += "\n"
        for child in self._childs:
            nodetext += child.to_texttree(printdata, tabLevel)         
        return nodetext

    def patch(self, func):
        """Patch a function onto a single Node instance. 
        To patch all nodes in a tree, need to patch the class itself, e.g.:
            rootNode.__class__.func = func """
        f = types.MethodType(func, self)
        setattr(self, func.__name__, f)


class VnNode(Node):
    """Node class for tree data structure for the Visinum program.  
    
    VnNode implements a tree data structure based on a Python dictionary, 
    with child nodes in a list with the key '_childs'. 
    
    Examples
    ========
    >>> vndict = {"name":"root VnNode", "attribute1":123,
    ...  "_childs":[
    ...     {"name":"child1"},
    ...     {"name":"child2",
    ...           "_childs":[
    ...           {"name":"grandchild1"}]  },
    ...     {"name":"child3", "attribute11":321}, 
    ...     {}, 
    ...     {"name":"child5", 
    ...           "_childs":[
    ...           {"name":"grandchild2"}, 
    ...           {"name":"grandchild3"}]  } 
    ...     ]  }
    >>> print(test_make_VnNode_tree_from_dictionary(vndict).to_texttree())
    |---root VnNode
    .   |---child1
    .   |---child2
    .   .   |---grandchild1
    .   |---child3
    .   |---nameless vnnode
    .   |---child5
    .   .   |---grandchild2
    .   .   |---grandchild3
    <BLANKLINE>"""

    def __init__(self, name="nameless vnnode", parent=None, metadata=None,
                 numcols=1):
        super().__init__(name, parent, None)
        self._data = {}
        self.name = name   # self._data must exist before self.name is set
        if metadata and isinstance(metadata, dict):
            self.set_data(metadata)
        #self.set_data(visinum_type=self.__class__.__name__) # causes test failure
        self._numcols = numcols

    def column_count(self):
        return self._numcols

    def get_data(self, idx=None):
        if idx in self._data:
            return self._data[idx]
        else:
            return {k:v for k, v in self._data.items() if k != "_childs"}

    def set_data(self, dict_=None, **kwargs):
        if dict_ and isinstance(dict_, dict):
            self._data.update(dict_)
            success = True
        else:
            success = False
        for k, v in kwargs.items():
            if k=="_childs":
                continue
            self._data[k] = v
            success = True
        if "name" in self._data:
            self._name = self._data["name"] # directly set self._name to avoid circular reference in name setter
            #del self._data["name"]
        return success

    def to_vndict(self): 
        dict_ = {"name":self._name}
        dict_.update(self._data)
        if self._childs:
            dict_["_childs"] = []
            for child in self._childs:
                dd = child.to_vndict()
                dict_["_childs"].append(dd)
        return dict_ 

    def to_JSON(self, filepath): 
        with open(filepath, 'w') as jfile:
            json.dump(self.to_vndict(), jfile)

    def find_childname(self, childname):
        for child in self._childs:
            if childname==child._name:
                return child
        return False

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, newname):
        self._name = newname
        self.set_data(name = newname)
        return True



def tree_from_dict(dict_, root_node=None, parent=None):
    """converts a dictionary to a Node tree"""
    if not parent:
        root_node = Node('Root (tree_from_dict)') # QTreeView does not display the tree root, "invisibleRoot"
        parent = root_node
    for name, value in dict_.items():
        node = Node(name, parent, value)
        if isinstance(value, dict):
            node = tree_from_dict(value, root_node, node)
    return root_node


def vntree_from_vndict(dict_, root_node=None, parent=None):
    """converts a dictionary (or list) to VnNode tree objects """
    if isinstance(dict_, list): # rootless tree if the top level is a list of dictionaries
        raise NotImplementedError("tree_from_vndict cannot handle lists")
    metadata = {k:v for k, v in dict_.items() if k != "_childs"}
    #nodename = dict_["name"] if "name" in dict_ else (
    #          "nameless node" if root_node else "nameless root"  )
    node = VnNode(parent=parent, metadata=metadata)
    if not root_node:
        root_node = node
    if "_childs" in dict_:
        for child in dict_["_childs"]:
            vntree_from_vndict(child, root_node, node)
    return root_node


def vntree_from_JSON(filepath):
    with open(filepath, 'r') as jfile:
        dict_ = json.load(jfile)
    return vntree_from_vndict(dict_)


def traverse_vndict_yield_metadata(vndict):
    metadata = {k:v for k, v in vndict.items() if k != "_childs"}
    yield metadata # yielding from here preserves order
    if "_childs" in vndict:
        #http://stackoverflow.com/questions/8407760/python-how-to-make-a-recursive-generator-function
        for child in vndict["_childs"]:
            yield from traverse_vndict_yield_metadata(child)
            #for data_ in traverse_tree_yield_metadata(child): # Python2
            #    yield data_
    #yield metadata


def node_from_pathlist(rootnode, pathparts):
    if not pathparts or pathparts==".":
        return rootnode
    parent = rootnode
    #foundchild = False
    for child in pathparts:
        foundchild = parent.find_childname(child)
        #print(child, " found in foundchild: ", foundchild)
        if foundchild:
            parent = foundchild
        else:
            return False
    return foundchild


if __name__ == '__main__':   # tests
    import doctest
    doctest.testmod(verbose=True, optionflags=doctest.ELLIPSIS)

    def test_setup_basic_Node_tree():
        rootnode   = Node("root (level0)")
        node1 = Node("node1 (level1)", rootnode)
        Node("node2 (level2)", node1)
        Node("node8 (level2)", node1)
        node3 = Node("node3 (level1)", rootnode)
        Node("node7 (level1)", rootnode)
        Node(parent=rootnode)
        node4 = Node(parent=node3, name="node4 (level2)")
        node5 = Node("node5 (level3)", node4)
        Node("node6 (level4)", node5)
        return rootnode

    def test_make_Node_tree_from_dictionary(dict_=None):
        if not dict_:
            dict_ = {"name":"TopLevel-notroot", "number":123,
        "_childs":[
        {"name":"child10"},
        {"name":"child20"},
        {"name":"child1", "anumber":321}, 
        {"name":"child2"}, 
        {"name":"child3", 
        "_childs":[
        {"name":"child4"}, 
        {"name":"child5"}]} 
        ],
        "child1" : {"name":"childone"},   
        "child2" : {"name":"childtwo", "again":{"name":"thegrandchildren"}}
        }
        rootnode = tree_from_dict(dict_)
        return rootnode

    def test_make_VnNode_tree_from_dictionary(dict_=None):
        if not dict_:
            dict_ = {"name":"root VnNode", "attribute1":123,
            "_childs":[
            {"name":"child1"},
            {"name":"child2",
              "_childs":[
              {"name":"grandchild1"}]  },
            {"name":"child3", "attribute11":321}, 
            {}, 
            {"name":"child5", 
              "_childs":[
              {"name":"grandchild2"}, 
              {"name":"grandchild3"}]  } 
            ]}
        rootnode = vntree_from_vndict(dict_)
        return rootnode


    def print_VnNode_tree_metadata(dict_=None):
        if not dict_:
            dict_ = {"name":"TopLevel-notroot", "number":123,
            "_childs":[
            {"noname":"child10"},
            {"aname":"child20"},
            {"name":"child1", "anumber":321}, 
            {}, 
            {"name":"child3", 
            "_childs":[
            {"name":"child4"}, 
            {"name":"child5"}]} 
            ]}
        output = ""
        gener = traverse_vndict_yield_metadata(dict_)
        for mdata in gener:
            output += str(mdata) + "\n"
        return output


    # Each line below is a test, un-comment line to run test as required
    #print( test_setup_basic_Node_tree().to_texttree() )
    #for node in list(test_setup_basic_Node_tree()): print(node.name)
    #print( test_make_Node_tree_from_dictionary().to_texttree(printdata=30) )
    #print(test_make_VnNode_tree_from_dictionary().to_texttree(printdata=True))  #printdata=True
    #print(json.dumps( test_make_VnNode_tree_from_dictionary().to_vndict(), sort_keys=False, indent=2 ))
    #print(print_VnNode_tree_metadata())

