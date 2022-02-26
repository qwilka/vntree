"""
Copyright © 2018-2021 Stephen McEntee
Licensed under the MIT license. 
See «vntree» LICENSE file for details https://github.com/qwilka/vntree/blob/master/LICENSE
"""
#import collections
import copy
from difflib import SequenceMatcher
import json
import itertools
import logging
import os
import pathlib 
import pickle
import textwrap
#from typing_extensions import Concatenate
import uuid

from .utilities import get_numeric

logger = logging.getLogger(__name__)

try:
    import yaml
    yaml_imported = True
except ImportError as err:
    logger.warning("PyYAML not installed (see https://pyyaml.org/); %s" % (err,) )
    yaml_imported = False


# # wrt: https://github.com/python/cpython/blob/3.8/Lib/inspect.py
# class _empty:
#     """Marker object for undefined value."""


# # https://docs.python.org/3/library/json.html
# class VntreeEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if obj is _empty:
#             return {str(_empty):True}
#         return json.JSONEncoder.default(self, obj)

# def as_vntree(obj):
#     if isinstance(obj, dict) and str(_empty) in obj:
#         return _empty
#     return obj



class NodeAttr:
    """Descriptor class for node attributes. 
    
    NodeAttr attributes are stored in the node instance `data` dictionary. 
    This facilitates serialization and persistance of the tree.

    :param ns: namespace for storing attribute in a nested dictionary in `data`.
                `ns=None` for top-level attributes.
    :type ns: str or None
    :param initial: optional default value.
    """
    def __init__(self, ns=None, initial=None):
        self.ns = ns
        self.initial = initial  
    def __get__(self, instance, owner):
        if self.ns in instance.data and isinstance(instance.data[self.ns], dict):
            _value = instance.data[self.ns].get(self.name, self.initial)
        else:
            #logger.error("%s.__get__ «%s»; ns «%s» not in %s" % (self.__class__.__name__, self.name, self.ns, instance))
            _value = instance.data.get(self.name, self.initial)
        return _value
    def __set__(self, instance, value):
        if self.ns:
            if self.ns not in instance.data:
                instance.data[self.ns] = {}
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
    def __init__(self, ns="_vntree", initial=None):
        super().__init__(ns, initial=initial)
    def __get__(self, instance, owner):
        _value = super().__get__(instance._root, owner)
        # if _value is None and instance.parent:
        #     _value = getattr(instance.parent, self.name)
        return _value
    def __set__(self, instance, value):
        if instance is not instance._root: #if instance is not instance.get_rootnode():
            logger.warning("%s.__set__: non-root node «%s» set value «%s»=«%s»" % (self.__class__.__name__, instance.name, self.name, value))
        super().__set__(instance._root, value)



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
    name = NodeAttr("_vntree")
    _id = NodeAttr("_vntree")
    _vntree_fpath = TreeAttr("_vntree")


    def __init__(self, name="", parent=None, data=None, 
                treedict=None, fpath=None, _id=None):
        if data and isinstance(data, dict):
            #self.data = collections.defaultdict(dict, copy.deepcopy(data))
            self.data = copy.deepcopy(data)
        else:
            self.data = {}
        if name:
            self.name = str(name)
        elif not getattr(self, "name", None) and name is None:
            self.name = ""
        self.childs = []
        ##print("in Node parent=",parent)
        ##print("issubclass(parent.__class__, Node)=",issubclass(parent.__class__, Node))
        if parent and issubclass(parent.__class__, Node):
            parent.add_child(self)
            ##print("in Node self.parent=",self.parent)
        elif parent is None:
            self.parent = None
        else:
            raise TypeError("{}.__init__: instance «{}» argument «parent» type not valid: {}".format(self.__class__.__name__, name, type(parent)))
        if callable(name):
            self.name = str(name(self))
        if treedict and isinstance(treedict, dict):
            self.from_treedict(treedict)
        if fpath and isinstance(fpath, str):
            self._vntree_fpath = fpath
        # if self._id is None:
        #     if _id is None:
        #         self._id = str(uuid.uuid4())
        #     else:
        #         self._id = _id
        if _id:
            self._id = _id
        elif self._id is None:
            self._id = str(uuid.uuid4())


    def __repr__(self):
        return "{} «{}» coord={}".format(self.__class__.__name__, self.name, self._coord)


    def __iter__(self): 
        yield self  
        for node in itertools.chain(*map(iter, self.childs)):
            yield node


    def __reversed__(self):  
        for node in itertools.chain(*map(reversed, reversed(self.childs))):
            yield node
        yield self 


    def __len__(self):
        """ len(node) is the number of nodes in the sub-tree with root «node».
        """
        return sum([1 for n in self])


    def add_child(self, node, *, idx=None, check_id=False):
        """Add a child node to the current node instance.

        :param node: the child node instance.
        :type node: Node
        :param idx: positional index for inserting node in self.childs
        :type idx: int
        :returns: The new child node instance.   
        :rtype: Node 
        """
        if not issubclass(node.__class__, Node):
            raise TypeError("{}.add_child: arg «node»=«{}», type {} not valid.".format(self.__class__.__name__, node, type(node)))
        _newnode = None
        if check_id:
            for _n in node:
                _dup = self._root.get_node_by_id(_n._id)
                if _dup:
                    logger.warning("%s.add_child: instance:«%s», duplicate _id in tree, re-assigning _id of new child node «%s»." % (self.__class__.__name__, self.name, node.name))
                    break
            if _dup:
                _newnode = node.clone()
                for _n in _newnode:
                    _n._id = str(uuid.uuid4())
        if _newnode is None:
            _newnode = node
        if idx is None:
            self.childs.append(_newnode)
        elif isinstance(idx, int) and idx < len(self.childs):
            self.childs.insert(idx, _newnode)
        else:
            raise ValueError("{}.add_child: cannot add node «{}», argument «idx»={} not correctly specified.".format(self.__class__.__name__, _newnode.name, idx))
        _newnode.parent = self
        return _newnode    


    # def add_tree(self, tree, *, idx=None):
    #     for _n in tree:
    #         _dup = self._root.get_node_by_id(_n._id)
    #         if _dup:
    #             _new_id = str(uuid.uuid4())
    #             logger.warning("%s.add_tree: node:«%s» duplicate _id «%s» identified, changing to «%s»." % (self.__class__.__name__, _n.name, _n._id, _new_id))
    #             _n._id = _new_id
    #     self.add_child(tree, idx=idx)


    def clone(self, change_id=False):
        """Return a deep copy of the sub-tree rooted at this node instance.

        :param change_id:  if `True` set new _id for all nodes in the new tree.
        :type change_id: bool
        :returns: Copy of the sub-tree rooted at this node instance.
        :rtype: Node 
        """
        _newtree = copy.deepcopy(self)
        if change_id:
            for _n in _newtree:
                _n._id = str(uuid.uuid4())
        return _newtree


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
    def _path(self):
        """Attribute indicating the absolute node path for this node. 
        
        Note that the absolute node path starts with a forward slash 
        followed by the root node's name: e.g: 
        `/root.name/child.name/grandchild.name`
        Warning: it should be noted that use of _path assumes  
        that sibling nodes have unique names. If unique node paths
        cannot be assured, use node attribute «_coord» instead.

        :returns: The absolute node path for this node.
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
    def _coord(self):
        """Attribute indicating the tree coordinates for this node.

        The tree coordinates of a node are expressed as a tuple of the
        indices of the node and its ancestors, for example:
        A grandchild node with node path 
        `/root.name/root.childs[2].name/root.childs[2].childs[0].name` 
        would have coordinates `(2,0)`.
        The root node _coord is an empty tuple: `()`

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


    @property
    def _level(self):
        """Attribute indicating the tree `level` for this node instance.

        Note that the root node is defined as level 1.

        :returns: the node `level`.
        :rtype: int 
        """
        return len(self._coord) + 1


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
            #_val = _datadict.get(_key, _empty)
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
                # if _key not in _datadict:
                #     _datadict[_key] = {}
                # _datadict = _datadict[_key]
                _datadict = _datadict.setdefault(_key, {})
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
    def _ancestors(self):
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


    def get_node_by_id(self, _id):
        for _n in self:
            if _n._id == _id:
                return _n
        


    def get_node_by_path(self, path):
        """Get a node from a node path. 

        Warning: use of this method assumes that sibling nodes have unique names,
        if this is not assured the `get_node_by_coord` method can be used instead.

        |  Example with absolute node path: 
        |  `node.get_node_by_path('/root.name/child.name/gchild.name')`
        |  Example with relative node path:
        |  `node.get_node_by_path('child.name/gchild.name')`

        :param path: the absolute node path, or the node path relative 
            to the current node instance.
        :type path: str
        :returns: the node corresponding to `path`.
        :rtype: Node or None
        """
        if path==".":
            return self
        elif path.lstrip().startswith((".", "./")) or not isinstance(path, str):
            logger.warning("%s.get_node_by_path: arg «path»=«%s», not correctly specified." % (self.__class__.__name__, path))
            return None
        _pathlist = list(filter(None, path.split("/")) ) # remove blank strings
        if path.startswith("/"):
            _node = self._root  
            _pathlist.pop(0)  # remove rootnode name
        else:
            _node = self
        for _nodename in _pathlist:
            _node = _node.get_child_by_name(_nodename)
            if _node is None:
                logger.warning("%s.get_node_by_path: node«%s», arg `path`=«%s», cannot find node." % (self.__class__.__name__, self.name, path))
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
            traversal = self._ancestors
        for _node in traversal:
            _val = _node.get_data(*keys)
            if _val == value:
                return _node
        return None


    def find_one_node_by_name(self, name, decend=True):
        _node = self.find_one_node("_vntree", "name", value=name, decend=decend)
        return _node


    def to_texttree(self, indent=3, func=True, symbol='ascii'):
        """Method returning a text representation of the (sub-)tree  
        rooted at the current node instance (`self`).

        :param indent: the indentation width for each tree level.
        :type indent: int
        :param func: function returning a string representation for 
            each node. e.g. `func=lambda n: str(n._coord)`
            would show the node coordinates. 
            `func=True` node.name displayed for each node. 
            `func=False` no node representation, just
            the tree structure is displayed.
        :type func: function or bool
        :param symbol: tuple of tree symbol characters.
            `None` or 'ascii' gives a preformed ascii tree, equivalent to tuple :code:`(|, +, |, |, |, -, .)`.
            'box' preformed with box-drawing characters, equivalent to tuple :code:`(┬, └, ┬, ├, └, ─, ⋅)`.
            'unicode' preformed with unicode characters.
        :type symbol: tuple or str or None
        :returns: a string representation of the tree.
        :rtype: str
        """
        if indent<2:
            indent=2
        if func is True:  # default func prints node.name
            func = lambda n: " {}".format(n.name)
        if isinstance(symbol, (list, tuple)):
            s_root, s_branch, s_spar, s_fnode  = symbol
        elif symbol=="unicode":
            # ┬ └ ┬ ├ └ ─ ⋅
            s_root, s_branch, s_fnode, s_mnode, s_lnode, s_spar, s_level  = (
                "\u252c", "\u2514", "\u252c", "\u251c", "\u2514", "\u2500", "\u22c5")
        elif symbol=="box": # https://en.wikipedia.org/wiki/Box-drawing_character
            # ┬ └ ┬ ├ └ ─ ⋅
            s_root, s_branch, s_fnode, s_mnode, s_lnode, s_spar, s_level  = (
                "\u252c", "\u2514", "\u252c", "\u251c", "\u2514", "\u2500", "\u22c5")
        else:
            s_root, s_branch, s_fnode, s_mnode, s_lnode, s_spar, s_level  = (
                "|", "+", "|", "|", "|", "-", ".")
        _text = ""
        #local_root_level = len(self.ancestors)
        local_root_level = self._level 
        for _n in self: 
            #level = len(node.ancestors) - local_root_level
            level = _n._level - local_root_level
            if level==0:
                _text += s_root
            #elif _n.parent.childs[0] == _n and len(_n.parent.childs)>1:   # first child
            elif _n.parent.childs[0] == _n:
                #s_spar="f"
                _text += (  (s_level + " "*(indent-1))*(level-1) 
                            + s_branch 
                            + s_spar*(indent-1) 
                            + s_fnode)
            elif _n.parent.childs[-1] == _n and len(_n.childs)==0:   # last child, no children
                #s_spar="l"
                _text += ( (s_level + " "*(indent-1))*(level) 
                            + s_lnode )
            elif _n.parent.childs[-1] == _n:   # last child, has children
                #s_spar="l"
                _text += ( (s_level + " "*(indent-1))*(level) 
                            + s_mnode )
                            #+ s_spar*(indent-1) )
            # elif level>0:
            #     _text += (s_level + " "*(indent-1))*(level-1) + s_branch + s_spar*(indent-1)
            else:
                #_text += s_fnode
                #s_spar="m"
                _text += ( (s_level + " "*(indent-1))*(level) 
                            + s_mnode )
                            #+ s_spar*(indent-1) )
            if func and callable(func):
                _text += func(_n)
            _text += "\n"
        return _text


    def show(self):
        """Print out a text representation of the tree using to_texttree().
        """
        print(self.to_texttree())


    def from_treedict(self, treedict):
        if "data" in treedict:
            #self.data = collections.defaultdict(dict, treedict["data"])
            _nodedata = copy.deepcopy(treedict["data"])
            # if new_id and "_id" in _nodedata["_vntree"]:
            #     _nodedata["_vntree"].pop("_id")
            self.data = _nodedata
        for key, val in treedict.items():
            if key in ["parent", "childs", "data"]:
                continue
            setattr(self, key, val)
        if "childs" in treedict.keys():
            for _childdict in treedict["childs"]:
                #self.childs.append( self.__class__(parent=self, treedict=_childdict) )
                self.__class__(parent=self, treedict=_childdict)


    def to_treedict(self, recursive=True, treemeta=True, dataonly=False):
        # NOTE: replace vars(self) with self.__dict__ ( and self.__class__.__dict__ ?)
        if dataonly:
            _dct = {"data": copy.deepcopy(self.data)}
        else:
            _dct = {k:copy.deepcopy(v) for k, v in vars(self).items() if k not in ["parent", "childs"]}
        if "_vntree" in _dct["data"]:
            if not treemeta:
                _dct["data"].pop("_vntree")
            # elif not _id:
            #     _dct["data"]["_vntree"].pop("_id")
        _dct["childs"] = []
        if recursive and self.childs:
            #_dct["childs"] = []
            for _child in self.childs:
                _dct["childs"].append( _child.to_treedict(recursive=recursive, treemeta=treemeta, dataonly=dataonly) )
        return _dct 


    def to_JSON(self, filepath=None, treemeta=True, dataonly=False, cls=None, default=None):
        _treedict = self.to_treedict(treemeta=treemeta, dataonly=dataonly)
        if filepath is None:
            #return json.dumps(_treedict, default=default, cls=VntreeEncoder)
            return json.dumps(_treedict, default=default, cls=cls)
        else:
            with open(filepath, 'w') as _fh:
                #json.dump(_treedict, _fh, default=default, cls=VntreeEncoder)
                json.dump(_treedict, _fh, default=default, cls=cls)
            return os.path.abspath(filepath)


    @classmethod
    def from_JSON(cls, filepath, object_hook=None):
        err = ""
        _treedict = None
        if isinstance(filepath, str) and os.path.isfile(filepath):
            try:
                with open(filepath, 'r') as _fh:
                    #_treedict = json.load(_fh, object_hook=as_vntree)
                    _treedict = json.load(_fh, object_hook=object_hook)
            except Exception as err: 
                logger.warning("%s.from_json: cannot open «filepath»=«%s», %s." % (cls.__name__, filepath, err))
        elif isinstance(filepath, str):
            try:
                _treedict = json.loads(filepath, object_hook=object_hook)
            except Exception as err: 
                logger.warning("%s.from_json: does not appear to be valid JSON «%s», %s." % (cls.__name__, filepath[:100], err))
        if not _treedict:
            #logger.warning("%s.from_json: cannot open «filepath»=«%s», %s." % (cls.__name__, filepath, err))
            return False
        else:
            rootnode = cls(treedict=_treedict)
            return rootnode


    def tree_compare(self, othertree, treemeta=False):
        """Compare the (sub-)tree rooted at `self` with another tree.

        `tree_compare` converts the trees being compared into JSON string
        representations, and uses `difflib.SequenceMatcher().ratio()` to
        calculate the similarity metric.

        :param othertree: the other tree for comparison.
        :type othertree: Node
        :param treemeta: include private vntree metadata in comparison.
        :type treemeta: bool
        :returns: similarity of the trees as a number between 0 and 1. 
        :rtype: float 
        """
        return SequenceMatcher(None, 
                json.dumps(self.to_treedict(treemeta=treemeta), default=str), 
                json.dumps(othertree.to_treedict(treemeta=treemeta), default=str)
                ).ratio()


    def savefile(self, filepath=None, enforceext=False, protocol=4):
        """Save (dump) the tree in a pickle file.

        Note: This method saves the complete tree even when invoked on
        a non-root node.
        Note: It is recommended to use the extension `.vn3` for this type of file.

        :param filepath: the file path for the pickle file. 
            If `filepath=None` use `self._vntree_fpath` attribute, if set.
        :type filepath: str or None   
        :param enforceext: if True, enforce filename extension .vn3
        :type enforceext: bool    
        :param protocol: pickle protocol version number
        :type protocol: int   
        :returns: `True` if successful. 
        :rtype: bool
        """
        froot, fext = os.path.splitext(filepath)
        if enforceext and fext != ".vn3":
            filepath = froot + ".vn3"
        if filepath:
            self._vntree_fpath = os.path.abspath(filepath)
        # if not _pfpath:
        #     logger.error("%s.save: «%s» file path «%s» not valid." % (self.__class__.__name__, self.name, _pfpath))
        #     return False
        try:
            with open(self._vntree_fpath, "wb") as pf:
                pickle.dump(self._root.to_treedict(treemeta=True), pf, protocol=protocol) 
        except Exception as err:
            logger.error("%s.savefile: arg `filepath`=«%s» `self._vntree_fpath`=«%s» error: %s" % (self.__class__.__name__, filepath, self._vntree_fpath, err))
            return False
        return True       


    @classmethod
    def openfile(cls, filepath):
        """Class method that opens (load) a vntree pickle file.

        :param filepath: the file path for the pickle file. 
        :type filepath: str         
        :returns: root node of tree or `False` if failure. 
        :rtype: Node or bool
        """
        if not os.path.isfile(filepath):
            logger.error("%s.openfile: arg `filepath`=«%s» not valid." % (cls.__name__, filepath))
            return False
        try:
            with open(filepath, "rb") as pf:
                pkldata = pickle.load(pf)
            rootnode = cls(treedict=pkldata)
            rootnode._vntree_fpath = os.path.abspath(filepath)
        except Exception as err:
            logger.error("%s.openfile: data in file «%s» not valid: %s" % (cls.__name__, filepath, err))
            return False
        return rootnode            


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


    def tree2yaml(self, fpath=None, treemeta=False):
        """Create YAML format representation of the tree.

        :param fpath: an optional filepath for saving the YAML.
        :type fpath: str or None
        :param treemeta: if True, retain node metadata _vntree.
        :type treemeta: bool
        :returns: YAML representation of the tree (fpath=None),
            or the absolute filepath if `fpath` is specified. 
        :rtype: str 
        """
        def make_anchor(node):
            anchor = "coord"
            for _c in node._coord:
                anchor += "-" + str(_c)
            return anchor
        yltree = "# «vntree» YAML format, see https://github.com/qwilka/vntree\n"
        for _n in self:
            _ncopy = _n.copy()
            delattr(_ncopy, "childs")
            delattr(_ncopy, "parent")
            if not treemeta and "_vntree" in _ncopy.data:
                del _ncopy.data["_vntree"]
            _yl = yaml.dump(_ncopy, default_flow_style=False)
            _n_yl = '!'+_n.__class__.__name__  + " &" + make_anchor(_n)
            if _n.parent:
                _n_yl += "\nparent: " + "*" + make_anchor(_n.parent)
            _n_yl += _yl[_yl.index("\n"):]
            yltree += _n_yl
        yltree = textwrap.indent(yltree, "  ")
        yltree = yltree.strip()
        yltree = yltree.replace("\n  !", "\n- !")
        retVal = yltree
        if fpath:
            _abspath = os.path.abspath(fpath) 
            # _dir, _fname = os.path.split(_abspath)
            # if os.path.isdir(_dir):
            with open(_abspath, 'w') as fh:
                fh.write(yltree)
            retVal = _abspath
        return retVal


    @classmethod
    def txt2tree(cls, txttree):
        """Build a tree from comma-separated lines of text.

        Each comma-separated line of text defines a node, as follows:
        parent-name, node-name, var1="data variable 1", var2=22

        The root node is defined first, with an empty «parent-name» field.
        For sub-nodes, the parent node must already be defined.

        Example:

        txttree = '''
        ,The World,population=7762609412
        The World,Europe
        Europe,Belgium,capital=Brussels,population=11515793
        The World,South America
        South America,Chile,capital=Santiago,HDI=0.851
        Europe,Greece,population=10768477
        '''

        rootnode = Node.txt2tree(txttree)
        print(rootnode.to_texttree())

        | The World
        +--| Europe
        .  +--| Belgium
        .  .  | Greece
        .  | South America
        .  +--| Chile
        """
        _rootnode = None
        for _line in txttree.splitlines():
            if "," not in _line: continue
            _parname, _name, *_dlist  = _line.split(",")
            _parname = _parname.strip()
            _name = _name.strip()
            _data = {}
            for _field in _dlist:
                k,v = _field.split("=")
                _num = get_numeric(v)
                if _num is not False:
                    v = _num
                _data[k.strip()] = v
            if _rootnode:
                if _parname:
                    _par = _rootnode.find_one_node_by_name(_parname)
                    _n = cls(_name, _par, data=_data)
                else:
                    logger.error("%s.txt2tree: invalid txttree (only 1 root permitted)  %s" % (cls.__name__, _line))
            else:
                _rootnode = cls(_name, None, data=_data)
        return _rootnode



if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    logger.addHandler(ch)

    SIMPLE_TREE_TOP_DOWN = True
    SIMPLE_TREE_BOTTOM_UP = True

    if SIMPLE_TREE_TOP_DOWN or SIMPLE_TREE_BOTTOM_UP:
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
        print()
        print(rootnode.to_texttree())

    if SIMPLE_TREE_TOP_DOWN:
        print("\nTree iterate top-down:")
        for ii, node in enumerate(rootnode):
            print("{} top-down «{}»".format(ii, node.name))

    if SIMPLE_TREE_BOTTOM_UP:
        print("\nTree iterate bottom-up:")
        for ii, node in enumerate(reversed(rootnode)):
            print("{} bottom-up «{}»".format(ii, node.name))


