"""
Copyright © 2018 Stephen McEntee
Licensed under the MIT license. 
See «vn-tree» LICENSE file for details:
https://github.com/qwilka/vn-tree/blob/master/LICENSE
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


class TreeAttr:
    """Descriptor class for top-level Node attributes (like the «Node.name» attribute).
    Ensures that Node attributes are stored in the «data» dictionary, facilitating serialization
    and persistance.
    """
    def __init__(self, ns=None):
        self.ns = ns    # ns=None put attribute directly in instance.data.get without namespacing
    def __get__(self, instance, owner):
        if self.ns in instance.data and isinstance(instance.data[self.ns], dict):
            _meta = instance.data[self.ns].get(self.name, None)
        else:
            #logger.error("%s.__get__ «%s»; ns «%s» not in %s" % (self.__class__.__name__, self.name, self.ns, instance))
            _meta = instance.data.get(self.name, None)
        return _meta
    def __set__(self, instance, value):
        if self.ns:
            instance.data[self.ns][self.name] = value
        else:
            instance.data[self.name] = value
    def __set_name__(self, owner, name):
        self.name = name


class Node:
    """Node class for tree data structure.  
    """
    name = TreeAttr()

    def __init__(self, name=None, parent=None, data=None, 
                treedict=None):
        if data and isinstance(data, dict):
            self.data = collections.defaultdict(dict, data) # copy.deepcopy(data)
        else:
            self.data = {}
        if name:
            self.name = str(name)
        # elif "name" in self.data:
        #     self.name = self.data["name"]
        # else:
        #     self.name = ""
        self.childs = []
        #if parent and isinstance(parent, self.__class__):
        #if parent and isinstance(self, parent.__class__):  #TODO allow mixed node types
        if parent and issubclass(parent.__class__, Node):
            parent.add_child(self)
        elif parent is None:
            self.parent = None
        else:
            raise TypeError("{}.__init__: instance «{}» argument «parent» type not valid: {}".format(self.__class__.__name__, name, type(parent)))
        # if parent:
        #     if isinstance(parent, self.__class__):
        #         _parent = parent
        #     elif isinstance(parent, str):
        #         _parent = self.get_node_by_nodepath(parent)
        #     elif isinstance(parent, (list, tuple)):
        #         _parent = self.get_node_by_coord(parent)
        #     else:
        #         raise TypeError("{}.__init__: instance «{}» argument «parent» type not valid: {}".format(self.__class__.__name__, name, type(parent)))
        #     _parent.add_child(self)
        # else:
        #     self.parent = None
        if self.name is None:
            self.name = str(self.coord)
        if treedict and isinstance(treedict, dict):
            #self.from_treedict(treedict, parent)
            self.from_treedict(treedict)
        # # if yamldata:
        # #     self.import_yaml(yamldata)
        # self._nodepath_warn = True  # neeeds to be in root
        # if not self.name:
        #     raise ValueError("{}.__init__: «name» argument not correctly specified; {}".format(self.__class__.__name__, self.name))


    def __str__(self):
        #_level = len(self.get_ancestors())
        return "{} coord={} «{}»".format(self.__class__.__name__, self.coord, self.name)

    def __iter__(self): 
        yield self  
        for node in itertools.chain(*map(iter, self.childs)):
            yield node

    def __reversed__(self):  
        for node in itertools.chain(*map(reversed, self.childs)):
            yield node
        yield self 

    def add_child(self, childnode):
        ##if type(childnode) != self.__class__:
        #if not isinstance(childnode, self.__class__):  #TODO allow mixed node types
        if not issubclass(childnode.__class__, Node):
            raise TypeError("{}.add_child: arg «childnode»=«{}», type {} not valid.".format(self.__class__.__name__, childnode, type(childnode)))
        # if (self._nodepath_warn and True in list(map(lambda _n: _n.name == childnode.name, self.childs)) ):
        #     logger.warning("%s.add_child: «%s» has duplicate child node.name = «%s»." % (self.__class__.__name__, self.name, childnode.name))
        #     self._nodepath_warn = False  # avoid multiple warnings
        self.childs.append(childnode)
        childnode.parent = self
        return True    

    def remove_child(self, node):
        self.childs.remove(node)
        return True

    @property
    def nodepath(self):
        """Return this node's nodepath in the form:
        '/rootnode.name/childnode.name/grandchildnode.name'
        WARNING: use of nodepath assumes that sibling nodes have unique names.
        """
        # NOTE returns full nodepath in form 
        _path = pathlib.PurePosixPath(self.name)
        _node = self
        while _node.parent:
            _path = _node.parent.name / _path
            _node = _node.parent
        _path = pathlib.posixpath.sep / _path
        return _path.as_posix()

    @property
    def coord(self):
        _coord = []
        _node = self
        while _node.parent:
            _idx = _node.parent.childs.index(_node)
            _coord.insert(0, _idx)
            _node = _node.parent
        return tuple(_coord)


    def get_data(self, *keys):
        if not keys:
            #return copy.deepcopy(self.data)
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
        # Note that «value» is a keyword-only argument
        _datadict = self.data
        for ii, _key in enumerate(keys):
            if ii==len(keys)-1:
                _datadict[_key] = value
            else:
                if _key not in _datadict:
                    _datadict[_key] = {}
                _datadict = _datadict[_key]
        return True

    def get_rootnode(self):
        if self.parent is None:
            return self
        else:
            return self.get_ancestors()[-1]
    
    def get_ancestors(self):
        # return list of ancestor nodes starting with self.parent and ending with root
        ancestors=[]
        _curnode = self
        while _curnode.parent:
            _curnode = _curnode.parent
            ancestors.append(_curnode)
        return ancestors

    def get_child_by_name(self, childname):
        _childs = [_child for _child in self.childs if _child.name==childname]
        if len(_childs)>1:
            logger.warning("%s.get_child_by_name: node:«%s» has more than 1 childnode with name=«%s»." % (self.__class__.__name__, self.name, childname))
        if len(_childs)==0:
            _childnode = None
        else:
            _childnode = _childs[0] # return first node found with name childname
        return _childnode

    def get_node_by_nodepath(self, nodepath):
        """Get node from nodepath 
        e.g. nodepath="/rootnode.name/child.name/gchild.name" (absolute path)
        nodepath="child.name/gchild.name" (relative path)
        WARNING: use of this method assumes that sibling nodes have unique names,
        if this is not the case «get_node_by_coord» can be used instead.
        """
        if nodepath==".":
            return self
        elif nodepath.lstrip().startswith((".", "./")) or not isinstance(nodepath, str):
            logger.warning("%s.get_node_by_nodepath: arg «nodepath»=«%s», not correctly specified." % (self.__class__.__name__, nodepath))
            return None
        _pathlist = list(filter(None, nodepath.split("/")) ) # remove blank strings
        # print("nodepath", nodepath)
        # print(_pathlist)
        if nodepath.startswith("/"):
            _node = self.get_rootnode()
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
        if not isinstance(coord, (list, tuple)) or False in list(map(lambda i: type(i)==int, coord)):
            logger.warning("%s.get_node_by_coord: node«%s», arg «coord»=«%s», «coord» must be list or tuple of integers." % (self.__class__.__name__, self.name, coord))
            return None
        if relative:
            _node = self
        else:
            _node = self.get_rootnode()
        for idx in coord:
            _node = _node.childs[idx]
            if _node is None:
                logger.warning("%s.get_node_by_coord: node«%s», arg «coord»=«%s» not valid." % (self.__class__.__name__, self.name, coord))
                return None
        return _node


    def find_one_node(self, *keys, value):
        # Note that «value» is a keyword-only argument
        for _node in self:
            _val = _node.get_data(*keys)
            if _val == value:
                return _node
        return None

    def to_texttree(self, indent=3, func=True):
        if indent<2:
            indent=2
        if func is True:  # default func prints node.name
            func = lambda n: " {}".format(n.name)
        _text = ""
        local_root_level = len(self.get_ancestors())
        for node in self: 
            level = len(node.get_ancestors()) - local_root_level
            #treetext += ("." + " "*3)*level + "|---{}\n".format(node.name)
            #_text += ("." + " "*(indent-1))*level + "|" + "-"*(indent-1)
            #_text += ("." + " "*(indent-2))*level 
            if level>0:
                _text += ("." + " "*(indent-1))*(level-1) + "+" + "-"*(indent-1)
            _text += "|"
            # if name:
            #     _text += "{}".format(node.name)
            if func and callable(func):
                _text += func(node)
            _text += "\n"
        return _text

    #def from_treedict(self, treedict, parent=None):   # TODO parent not used??
    def from_treedict(self, treedict):
        if "data" in treedict:
            self.data = collections.defaultdict(dict, treedict["data"])
        #self.name = "name not set"  # default values for name and data, should be over-written
        #self.data = {}
        for key, val in treedict.items():
            if key in ["parent", "childs", "data"]:
                continue
            setattr(self, key, val)
        # if parent:
        #     parent.add_child(self)
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

    def string_diff(self, othertree):
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
    def import_yamltree(cls, yamltree):
        list_of_nodes = yaml.safe_load(yamltree)
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


