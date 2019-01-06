"""
Copyright © 2018-2019 Stephen McEntee
Licensed under the MIT license. 
See «vn-tree» LICENSE file for details https://github.com/qwilka/vn-tree/blob/master/LICENSE
"""
import collections
import copy
from difflib import SequenceMatcher
import json
import itertools
import logging
import os
import pathlib 

import yaml

logger = logging.getLogger(__name__)


class NodeAttr:
    """Descriptor class for node attributes. 
    
    NodeAttr attributes are stored in the node instance `data` dictionary. 
    This facilitates serialization and persistance of the tree.

    :param ns: namespace for storing attribute in a nested dictionary in `data`.
                `ns=None` for top-level attributes.
    :type ns: str or None
    """
    def __init__(self, ns=None):
        self.ns = ns    
    def __get__(self, instance, owner):
        if self.ns in instance.data and isinstance(instance.data[self.ns], dict):
            _value = instance.data[self.ns].get(self.name, None)
        else:
            #logger.error("%s.__get__ «%s»; ns «%s» not in %s" % (self.__class__.__name__, self.name, self.ns, instance))
            _value = instance.data.get(self.name, None)
        return _value
    def __set__(self, instance, value):
        if self.ns:
            instance.data[self.ns][self.name] = value
        else:
            instance.data[self.name] = value
    def __delete__(self, instance):
        if self.ns and self.name in instance.data[self.ns]:
            del instance.data[self.ns][self.name]
        elif self.name in instance.data:
            del instance.data[self.name]
    def __set_name__(self, owner, name):
        self.name = name


class TreeAttr(NodeAttr):
    """Descriptor class for tree attributes.  `TreeAttr` attribute 
    values are stored in the root node `data` dictionary. 
    
    Storing an attribute in the root node of the tree ensures that the
    attribute can be found by all nodes in the tree. 
    `TreeAttr` is a subclass of `NodeAttr`.

    :param ns: namespace for attribute. `ns=None` for top-level attributes.
    :type ns: str or None
    """
    def __init__(self, ns=None):
        super().__init__(ns)
    def __get__(self, instance, owner):
        _value = super().__get__(instance, owner)
        if _value is None and instance.parent:
            _value = getattr(instance.parent, self.name)
        return _value
    def __set__(self, instance, value):
        if instance is not instance._root: #if instance is not instance.get_rootnode():
            logger.warning("%s.__set__: non-root node «%s» set value «%s»=«%s»" % (self.__class__.__name__, instance.name, self.name, value))
        super().__set__(instance, value)



class Node:
    """Class for creating vntree nodes.

    :param name: node name
    :type name: str or None
    :param parent: The parent node of this node.
    :type parent: Node or None
    :param data: Dictionary containing node data.
    :type data: dict or None
    :param treedict: Dictionary specifying a complete tree.
    :type treedict: dict or None
    """
    YAML_setup = False
    name = NodeAttr()


    def __init__(self, name=None, parent=None, data=None, treedict=None):
        if data and isinstance(data, dict):
            self.data = collections.defaultdict(dict, copy.deepcopy(data)) # copy.deepcopy(data)
        else:
            self.data = {}
        if name:
            self.name = str(name)
        elif not getattr(self, "name", None) and name is None:
            self.name = ""
        self.childs = []
        if parent and issubclass(parent.__class__, Node):
            parent.add_child(self)
        elif parent is None:
            self.parent = None
        else:
            raise TypeError("{}.__init__: instance «{}» argument «parent» type not valid: {}".format(self.__class__.__name__, name, type(parent)))
        if callable(name):
            self.name = str(name(self))
        if treedict and isinstance(treedict, dict):
            self.from_treedict(treedict)


    def __str__(self):
        return "{} coord={} «{}»".format(self.__class__.__name__, self.coord, self.name)


    def __iter__(self): 
        yield self  
        for node in itertools.chain(*map(iter, self.childs)):
            yield node


    def __reversed__(self):  
        for node in itertools.chain(*map(reversed, self.childs)):
            yield node
        yield self 


    def add_child(self, node):
        """Add a child node to the current node instance.

        :param node: the child node instance.
        :type node: Node
        :returns: True if successful.   
        """
        if not issubclass(node.__class__, Node):
            raise TypeError("{}.add_child: arg «node»=«{}», type {} not valid.".format(self.__class__.__name__, node, type(node)))
        self.childs.append(node)
        node.parent = self
        return True    

    def remove_child(self, idx=None, *, name=None, node=None):
        """Remove a child node from the current node instance.

        :param idx: Index of child node to be removed.
        :type idx: int 
        :param name: The first child node found with «name» will be removed. 
        :type name: str
        :param node: Child node to be removed.
        :type node: Node 
        :returns: The node that has been removed, or False if not successful.
        :rtype: Node or False 
        """
        if (idx and isinstance(idx, int) and 
            -len(self.childs) <= idx < len(self.childs) ):
                return self.childs.pop(idx)
        if name and isinstance(name, str):
            found_node = None
            for _n in self.childs:
                if _n.name == name:
                    found_node = _n
                    break
            if found_node:
                self.childs.remove(found_node)
                return found_node
        if node and node in self.childs:
            self.childs.remove(node)
            return node
        return False

    @property
    def nodepath(self):
        """Attribute indicating the absolute nodepath for this node. 
        
        Note that the absolute nodepath starts with a forward slash 
        followed by the root node's name: e.g: 
        `/root.name/child.name/grandchild.name`
        Warning: it should be noted that use of nodepath assumes  
        that sibling nodes have unique names. If unique nodepaths
        cannot be assured, use node attribute «coord» instead.

        :returns: The absolute nodepath for this node.
        :rtype: str 
        """
        _path = pathlib.PurePosixPath(self.name)
        _node = self
        while _node.parent:
            _path = _node.parent.name / _path
            _node = _node.parent
        _path = pathlib.posixpath.sep / _path
        return _path.as_posix()

    @property
    def coord(self):
        """Attribute indicating the tree coordinates for this node.

        The tree coordinates of a node are expressed as a tuple of the
        indices of the node and its ancestors, for example:
        A grandchild node with nodepath 
        `/root.name/root.childs[2].name/root.childs[2].childs[0].name` 
        would have coord `(2,0)`.
        The root node coord is an empty tuple: `()`

        :returns: the tree coordinates for this node.
        :rtype: tuple 
        """
        _coord = []
        _node = self
        while _node.parent:
            _idx = _node.parent.childs.index(_node)
            _coord.insert(0, _idx)
            _node = _node.parent
        return tuple(_coord)


    def get_data(self, *keys):
        """Get a value from the instance `data` dict. 

        Nested values are accessed by specifying the keys in sequence. 
        e.g. `node.get_data("country", "city")` would access
        `node.data["country"]["city"]`

        :param keys: the `data` dict keys referencing the required value.
        :type keys: str 
        :returns: the value accessed by `keys` in `data`. 
        """
        if not keys:
            _val = self.data
        _datadict = self.data
        for _key in keys:
            _val = _datadict.get(_key, None)
            if isinstance(_val, dict):
                _datadict = _val
            else:
                break
        if isinstance(_val, dict):
            _val = copy.deepcopy(_val)
        return _val


    def set_data(self, *keys, value):
        """Set a value in the instance `data` dict.

        :param keys: the `data` dict keys referencing the value in the `data` dict.
        :type keys: str 
        :param value: the value to be set in the `data` dict. Note that
            `value` is a keyword-only argument.
        :returns: `True` if successful. 
        """
        _datadict = self.data
        for ii, _key in enumerate(keys):
            if ii==len(keys)-1:
                _datadict[_key] = value
            else:
                if _key not in _datadict:
                    _datadict[_key] = {}
                _datadict = _datadict[_key]
        return True


    @property
    def _root(self):
        """Attribute referencing the root node of the tree.

        :returns: the root node of the tree containing this instance.
        :rtype: Node
        """
        _n = self
        while _n.parent:
            _n = _n.parent
        return _n


    @property
    def ancestors(self):
        """Attribute referencing the tree ancestors of the node instance.

        :returns: list of node ancestors in sequence, first item is 
            the current node instance (`self`), the last item is root.
        :rtype: list of Node references
        """
        # return list of ancestor nodes starting with self.parent and ending with root
        _ancestors=[]
        _n = self
        while _n.parent:
            _n = _n.parent
            _ancestors.append(_n)
        return _ancestors


    def get_child_by_name(self, childname):
        """Get a child node of the current instance by its name.

        :param childname: the name of the required child node.
        :type childname: str
        :returns: the first child node found with name `childname`.
        :rtype: Node or None
        """
        _childs = [_child for _child in self.childs if _child.name==childname]
        if len(_childs)>1:
            logger.warning("%s.get_child_by_name: node:«%s» has more than 1 childnode with name=«%s»." % (self.__class__.__name__, self.name, childname))
        if len(_childs)==0:
            _childnode = None
        else:
            _childnode = _childs[0] 
        return _childnode


    def get_node_by_nodepath(self, nodepath):
        """Get a node from a nodepath. 

        Warning: use of this method assumes that sibling nodes have unique names,
        if this is not assured the `get_node_by_coord` method can be used instead.

        |  Example with absolute nodepath: 
        |  `node.get_node_by_nodepath('/root.name/child.name/gchild.name')`
        |  Example with relative nodepath:
        |  `node.get_node_by_nodepath('child.name/gchild.name')`

        :param nodepath: the absolute nodepath, or the nodepath relative 
            to the current node instance.
        :type nodepath: str
        :returns: the node corresponding to `nodepath`.
        :rtype: Node or None
        """
        if nodepath==".":
            return self
        elif nodepath.lstrip().startswith((".", "./")) or not isinstance(nodepath, str):
            logger.warning("%s.get_node_by_nodepath: arg «nodepath»=«%s», not correctly specified." % (self.__class__.__name__, nodepath))
            return None
        _pathlist = list(filter(None, nodepath.split("/")) ) # remove blank strings
        if nodepath.startswith("/"):
            _node = self._root  
            _pathlist.pop(0)  # remove rootnode name
        else:
            _node = self
        for _nodename in _pathlist:
            _node = _node.get_child_by_name(_nodename)
            if _node is None:
                logger.warning("%s.get_node_by_nodepath: node«%s», arg «nodepath»=«%s», cannot find node." % (self.__class__.__name__, self.name, nodepath))
                return None
        return _node


    def get_node_by_coord(self, coord, relative=False):
        """Get a node from a node coord. 

        :param coord: the coordinates of the required node.
        :type coord: tuple or list
        :param relative: `True` if coord is relative to the node instance,
            `False` for absolute coordinates.
        :type relative: bool
        :returns: the node corresponding to `coord`.
        :rtype: Node or None
        """
        if not isinstance(coord, (list, tuple)) or False in list(map(lambda i: type(i)==int, coord)):
            logger.warning("%s.get_node_by_coord: node«%s», arg «coord»=«%s», «coord» must be list or tuple of integers." % (self.__class__.__name__, self.name, coord))
            return None
        if relative:
            _node = self
        else:
            _node = self._root # _node = self.get_rootnode()
        for idx in coord:
            _node = _node.childs[idx]
            if _node is None:
                logger.warning("%s.get_node_by_coord: node«%s», arg «coord»=«%s» not valid." % (self.__class__.__name__, self.name, coord))
                return None
        return _node


    def find_one_node(self, *keys, value, decend=True):
        """Find a node on the branch of the instance with a
        `keys=data` item in the `data` dict. 

        Nested values are accessed by specifying the keys in sequence. 
        e.g. `node.get_data("country", "city")` would access
        `node.data["country"]["city"]`

        :param keys: the `data` dict key(s) referencing the required value.
        :type keys: str 
        :param value: the value corresponding to `keys`. Note that
            `value` is a keyword-only argument.
        :param decend: `decend=True` traverse down the branch sub-tree  
            starting from `self`. `decend=False` traverse up the   
            branch from `self` towards root.
        :type decend: bool 
        :returns: the first node found with `keys=data` in the `data` dict. 
        :rtype: Node or None 
        """
        if decend:
            traversal = self
        else:
            traversal = self.ancestors
        for _node in traversal:
            _val = _node.get_data(*keys)
            if _val == value:
                return _node
        return None


    def to_texttree(self, indent=3, func=True):
        """Method returning a text representation of the (sub-)tree  
        rooted at the current node instance (`self`).

        :param indent: the indentation width for each tree level.
        :type indent: int
        :param func: function returning a string representation for 
            each node. e.g. `func=lambda n: str(n.coord)`
            would show the node coordinates. 
            `func=True` node.name displayed for each node. 
            `func=False` no node representation, just
            the tree structure is displayed.
        :type func: function or bool
        :returns: a string representation of the tree.
        :rtype: str
        """
        if indent<2:
            indent=2
        if func is True:  # default func prints node.name
            func = lambda n: " {}".format(n.name)
        _text = ""
        local_root_level = len(self.ancestors) 
        for node in self: 
            level = len(node.ancestors) - local_root_level
            if level>0:
                _text += ("." + " "*(indent-1))*(level-1) + "+" + "-"*(indent-1)
            _text += "|"
            if func and callable(func):
                _text += func(node)
            _text += "\n"
        return _text


    def from_treedict(self, treedict):
        if "data" in treedict:
            self.data = collections.defaultdict(dict, treedict["data"])
        for key, val in treedict.items():
            if key in ["parent", "childs", "data"]:
                continue
            setattr(self, key, val)
        if "childs" in treedict.keys():
            for _childdict in treedict["childs"]:
                #self.childs.append( self.__class__(parent=self, treedict=_childdict) )
                self.__class__(parent=self, treedict=_childdict)

    def to_treedict(self, recursive=True):
        # NOTE: replace vars(self) with self.__dict__ ( and self.__class__.__dict__ ?)
        _dct = {k:v for k, v in vars(self).items() if k not in ["parent", "childs"]}
        if recursive and self.childs:
            _dct["childs"] = []
            for _child in self.childs:
                _dct["childs"].append( _child.to_treedict(recursive=recursive) )
        return _dct 

    def to_json(self, filepath, default=str):
        pass

    # def from_json(self, filepath):
    #     err = ""
    #     _treedict = None
    #     if isinstance(filepath, str) and os.path.isfile(filepath):
    #         try:
    #             with open(filepath, 'r') as _fh:
    #                 _treedict = json.load(_fh)
    #         except Exception as err: 
    #             pass
    #     if not _treedict:
    #         logger.warning("%s.from_json: node«%s», cannot open «filepath»=«%s», %s." % (self.__class__.__name__, self.name, filepath, err))
    #         return False
    #     else:
    #         self.from_treedict(treedict=_treedict)
    #         return True

    def tree_compare(self, othertree):
        """Compare the (sub-)tree rooted at `self` with another tree.

        `tree_compare` converts the trees being compared into JSON string
        representations, and uses `difflib.SequenceMatcher().ratio()` to
        calculate a measure of the similarity of the strings.

        :param othertree: the other tree for comparison.
        :type othertree: Node
        :returns: similarity of the trees as a number between 0 and 1. 
        :rtype: float 
        """
        return SequenceMatcher(None, 
                                json.dumps(self.to_treedict(), default=str), 
                                json.dumps(othertree.to_treedict(), default=str)
                                ).ratio()


    @classmethod
    def setup_yaml(cls):
        def yamlnode_constructor(loader, yamlnode) :
            fields = loader.construct_mapping(yamlnode, deep=True)
            return  cls(**fields)
        yaml.SafeLoader.add_constructor('!'+cls.__name__, yamlnode_constructor)
       

    @classmethod
    def yaml2tree(cls, yamltree):
        """Class method that creates a tree from YAML.

        | # Example yamltree data:
        | - !Node &root
        |   name: "root node"
        |   parent: null
        |   data:
        |     testpara: 111
        | - !Node &child1
        |   name: "child node"
        |   parent: *root
        | - !Node &gc1
        |   name: "grand-child node"
        |   parent: *child1

        :param yamltree: a string of YAML describing the nodes in the
            tree, or the path to a file containing the data.
        :type yamltree: str
        :returns: the root node of the tree. 
        :rtype: Node 
        """
        if not cls.YAML_setup:
            cls.setup_yaml()
            cls.YAML_setup = True 
        if os.path.isfile(yamltree):
            with open(yamltree) as fh:
                yaml_data = fh.read()
        else:
            yaml_data = yamltree
        list_of_nodes = yaml.safe_load(yaml_data)
        yamltree_root = list_of_nodes[0]
        return yamltree_root


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    logger.addHandler(ch)

    SIMPLE_TREE = True

    if SIMPLE_TREE:

        rootnode   = Node('ROOT (level 0, the "top" of the tree)')
        Node("1st child (level 1, leaf node)", parent=rootnode)
        child2 = Node("2nd child (level 1)", rootnode)
        Node("grand-child1 (level 2, leaf node)", child2)
        Node("grand-child2 (level 2, leaf node)", child2)
        child3 = Node("3rd child (level 1)", rootnode)
        Node("another child (level 1, leaf node)", rootnode)
        grandchild3 = Node(parent=child3, name="grand-child3 (level 2")
        ggrandchild = Node("great-grandchild (level 3)", grandchild3)
        Node("great-great-grandchild (level4, leaf node)", ggrandchild)
        Node("great-grandchild2 (level 3, leaf node)", grandchild3)

        print(rootnode.to_texttree())
        # for ii, node in enumerate(rootnode):
        #     print("{} top-down «{}»".format(ii, node.name))
        # for ii, node in enumerate(reversed(rootnode)):
        #     print("{} bottom-up «{}»".format(ii, node.name))


