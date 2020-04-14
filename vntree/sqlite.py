"""
Copyright © 2018-2020 Stephen McEntee
Licensed under the MIT license. 
See «vntree» LICENSE file for details:
https://github.com/qwilka/vntree/blob/master/LICENSE

References:
https://github.com/RaRe-Technologies/sqlitedict 
"""
import copy
#from datetime import datetime, timezone
#import hashlib
import logging
#import operator
import os
#import pickle
#import sqlite3
#import zlib 

logger = logging.getLogger(__name__)

import sqlitedict

from .node import Node, NodeAttr, TreeAttr


# def sqlitedict_encode(obj):
#     return sqlite3.Binary(zlib.compress(pickle.dumps(obj, protocol=4)))


# def sqlitedict_decode(pklobj):
#     return pickle.loads(zlib.decompress(bytes(pklobj)))


class SqliteNode(Node):

    def __init__(self, name=None, parent=None, data=None, 
                treedict=None, fpath=None, nodeid=None):
        super().__init__(name, parent, data, treedict, fpath, nodeid)
        # if self._vntree_fpath and os.path.isfile(self._vntree_fpath):
        #     self.insert_data()


    def get_data(self, *keys):
        """Get a value from the instance `data` dict. 

        Nested values are accessed by specifying the keys in sequence. 
        e.g. `node.get_data("country", "city")` would access
        `node.data["country"]["city"]`

        :param keys: the `data` dict keys referencing the required value.
        :type keys: str 
        :returns: the value accessed by `keys` in `data`. 
        """
        # _loaded = self.data["_treemeta"].get("loaded", False)
        # if _loaded is False:
        #     self.load_data()
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
                # if _key not in _datadict:
                #     _datadict[_key] = {}
                # _datadict = _datadict[_key]
                _datadict = _datadict.setdefault(_key, {})
        return True



    def insert_data(self):
        tablename = self._root.get_data("_treemeta", "tablename")
        #print(f"insert_data tablename={tablename} self._nodeid={self._nodeid}")
        with sqlitedict.SqliteDict(self._vntree_fpath, tablename=tablename) as _vndict:
            _vndict[self._nodeid] = self.data
            _vndict.commit()

    def load_data(self):
        tablename = self._root.data["_treemeta"]["tablename"]
        with sqlitedict.SqliteDict(self._vntree_fpath, tablename=tablename) as _vndict:
            _data = copy.deepcopy(_vndict[self._nodeid])
            _data.update(self.data)
            self.data.update(_data)


    def from_skdict(self, treedict):
        if "data" in treedict:
            #self.data = collections.defaultdict(dict, treedict["data"])
            self.data = copy.deepcopy(treedict["data"])
        for key, val in treedict.items():
            if key in ["parent", "childs", "data"]:
                continue
            setattr(self, key, val)
        if "childs" in treedict.keys():
            for _childdict in treedict["childs"]:
                #self.childs.append( self.__class__(parent=self, treedict=_childdict) )
                self.__class__(parent=self, treedict=_childdict)

    def to_skdict(self):
        # NOTE: replace vars(self) with self.__dict__ ( and self.__class__.__dict__ ?)
        # _dct = {k:copy.deepcopy(v) for k, v in vars(self).items() if k not in ["parent", "childs"]}
        # if not treemeta and "_treemeta" in _dct["data"]:
        #     _dct["data"].pop("_treemeta")
        _dct = {"data":{}}
        _dct["data"]["name"] = self.name
        _dct["data"]["_treemeta"] = self.data["_treemeta"]
        if self.childs:
            _dct["childs"] = []
            for _child in self.childs:
                _dct["childs"].append( _child.to_skdict() )
        return _dct 



    def savefile(self, fpath=None, enforceext=False, tablename='vntree0', flag='c'):
        """Save (dump) the tree in a sqlite3 file.

        Note: This method saves the complete tree even when invoked on
        a non-root node.
        Note: It is recommended to use the extension `.vn4` for this type of file.

        :param fpath: the file path for the pickle file. 
            If `fpath=None` use `self._vntree_fpath` attribute, if set.
        :type fpath: str or None   
        :param enforceext: if True, enforce filename extension .vn3
        :type enforceext: bool    
        :returns: `True` if successful. 
        :rtype: bool
        """
        if fpath:
            _fpath = os.path.abspath(fpath)
            if enforceext:
                froot, fext = os.path.splitext(_fpath)
                if fext != ".vn4":
                    _fpath = froot + ".vn4"
        else:
            _fpath = self._vntree_fpath
        self._root.set_data("_treemeta", "tablename", value=tablename)
        try:
            #with sqlitedict.SqliteDict(self._vntree_fpath, encode=sqlitedict_encode, decode=sqlitedict_decode) as _vndict:
            #print(f"_fpath={_fpath}")
            with sqlitedict.SqliteDict(_fpath, tablename=tablename, flag=flag) as _vndict:
                newdata = self._root.to_skdict()
                newdata["data"]["_treemeta"]["_vntree_fpath"] = _fpath
                newdata["data"]["_treemeta"]["tablename"] = tablename
                # print(f"newdata={newdata}")
                # if "_vntree" in _vndict:
                #     del _vndict["_vntree"]
                _vndict["_vntree"] = newdata
                #_vndict["_vntree"] = "this is a test"
                _vndict.commit()
        except Exception as err:
            logger.error("%s.savefile: arg `fpath`=«%s» `self._vntree_fpath`=«%s» error: %s" % (self.__class__.__name__, fpath, self._vntree_fpath, err))
            return False
        self._vntree_fpath = _fpath
        for _n in self._root:
            _n.insert_data()
        return True   


    @classmethod
    def openfile(cls, fpath, tablename='vntree0', flag='c'):
        """Class method that opens (load) a vn4 (sqlite) file.

        :param fpath: the file path for the vn4 file. 
        :type fpath: str         
        :returns: root node of tree or `False` if failure. 
        :rtype: Node or bool
        """
        if not os.path.isfile(fpath):
            logger.error("%s.openfile: arg `fpath`=«%s» not valid." % (cls.__name__, fpath))
            return False
        try:
            #with sqlitedict.SqliteDict(fpath, encode=sqlitedict_encode, decode=sqlitedict_decode) as _vndict:
            with sqlitedict.SqliteDict(fpath, tablename=tablename, flag=flag) as _vndict:
                print(f"_vndict={_vndict}")
                pkldata = _vndict["_vntree"]
                #rootnode = _vndict["_vntree"] 
            #print(f"type(pkldata)={type(pkldata)}")
            #print(pkldata)
            rootnode = cls(treedict=pkldata)
            rootnode._vntree_fpath = os.path.abspath(fpath)
        except Exception as err:
            logger.error("%s.openfile: data in file «%s» not valid: %s" % (cls.__name__, fpath, err))
            return False
        for _n in rootnode:
            _n.load_data()
        return rootnode 

