import copy
from datetime import datetime, timezone
import hashlib
import logging
import operator

logger = logging.getLogger(__name__)

import pymongo
from bson.objectid import ObjectId
from bson.errors import InvalidId

from .node import Node, NodeAttr, TreeAttr


class MongoNode(Node):
    host = TreeAttr("vn")
    port = TreeAttr("vn")
    db = TreeAttr("vn")
    collection = TreeAttr("vn")
    _id = NodeAttr("vn")
    vn_uri = NodeAttr("vn")

    def __init__(self, name=None, parent=None, data=None, treedict=None, 
            host=None, port=None, db=None, collection=None, vn_uri=None):
        super().__init__(name, parent, data, treedict)
        if host:
            self.host = host
        if port:
            self.port = port
        if db:
            self.db = db
        if collection:
            self.collection= collection
        if vn_uri:
            self.vn_uri = vn_uri
            self._id = vn_uri_to_id(vn_uri)
        elif not self._id:
            self._id = ObjectId()

    @property
    def db_uri(self):
        _db_uri = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "collection": self.collection,
            "_id": self._id,
        }
        return _db_uri

    # @db_uri.setter
    # def db_uri(self, value):
    #     pass
        # if not self.host:
        #     self.host = value["host"]
        # if not self.port:
        #     self.port = value["port"]
        # if not self.db:
        #     self.db = value["db"]
        # if not self.collection:
        #     self.collection = value["collection"]

    # def get_data(self, *keys, db_load=False):
    #     if db_load:
    #         self.db_load()
    #     if not keys:
    #         #return copy.deepcopy(self.data)
    #         _val = self.data
    #     _datadict = self.data
    #     for _key in keys:
    #         _val = _datadict.get(_key, None)
    #         if isinstance(_val, dict):
    #             _datadict = _val
    #         else:
    #             break
    #     if isinstance(_val, dict):
    #         _val = copy.deepcopy(_val)
    #     if _val is None and not db_load:
    #         _val = self.get_data(*keys, db_load=True)
    #     return _val

    def get_data(self, field, load=False):
        """

        :param field: use MongoDB dot notation to access embedded field.
        :type field: str         
        refs:
        https://docs.mongodb.com/manual/core/document/#document-dot-notation
        """
        keys = field.split(".")
        if load:
            self.db_load()
        _val = super().get_data(*keys)
        if not load and _val is None:
            _doc = find_by_id(self.db_uri)
            for _key in keys:
                _val = _doc.get(_key, None)
                if isinstance(_val, dict):
                    _doc = _val
                else:
                    break
        return _val


    def set_data(self, field, value):
        """

        :param field: use MongoDB dot notation to set embedded field.
        :type field: str         
        refs:
        https://docs.mongodb.com/manual/core/document/#document-dot-notation
        """
        try:
            retval = db_operation(self.db_uri, 'update_one', 
                        update={"$set": {field: value}},
                        upsert=False)
        except Exception as err:
            logger.error('%s.set_data %s; %s' % (self.__class__.__name__, str(self.db_uri), err))
            return False
        keys = field.split(".")
        _val = super().set_data(*keys, value=value)
        # _datadict = self.data
        # for ii, _key in enumerate(keys):
        #     if ii==len(keys)-1:
        #         _datadict[_key] = value
        #     else:
        #         _datadict = _datadict.setdefault(_key, {})
        return retval


    def db_insert(self, recursive=False):
        if recursive:
            retval = list(map(operator.methodcaller('db_insert', recursive=False), self))
            retval = retval[0]
        else:
            #_db_uri = vn_config.get_db_uri(**self.db_uri)
            _db_uri = self.db_uri
            self.set_data("vn", "vn_timestamp", value=datetime.now(timezone.utc))
            _doc = self.get_data()
            if "_id" not in _doc and _db_uri["_id"] is not None:
                _doc["_id"] = _db_uri["_id"]
            if self.childs:
                _doc["childs"] = []
                for _child in self.childs:
                    _doc["childs"].append(_child._id)
            _doc["parent"] = self.parent and self.parent._id
            try:
                retval = db_operation(_db_uri, 'insert_one', document=_doc)
            except pymongo.errors.DuplicateKeyError as err:
                logger.error('%s.db_insert %s; %s' % (self.__class__.__name__, str(_db_uri), err))
                return False
            logger.debug('%s.db_insert %s' % (self.__class__.__name__, str(_db_uri)))
            #retval = retval.inserted_id
            if retval: 
                #self._id = str(retval.inserted_id)
                retval = retval.inserted_id
        return retval 


    def db_delete(self, recursive=False):
        if recursive:
            retval = list(map(operator.methodcaller('db_delete', recursive=False), self))
            retval = retval[0]
        else:
            #_db_uri = vn_config.get_db_uri(**self.db_uri)
            _db_uri = self.db_uri
            retval = db_operation(_db_uri, 'find_one_and_delete')
            logger.debug('%s.db_delete %s' % (self.__class__.__name__, str(_db_uri)))
            if retval:
                retval = retval["_id"]
        return retval 


    def db_update(self, timestamp=False):
        #_db_uri = vn_config.get_db_uri(**self.db_uri)
        _db_uri = self.db_uri
        if timestamp:
            self.set_data("vn", "vn_timestamp", value=datetime.now(timezone.utc))
        _doc = self.get_data()
        if "_id" not in _doc:
            _doc["_id"] = _db_uri["_id"]
        if self.childs:
            _doc["childs"] = []
            for _child in self.childs:
                _doc["childs"].append(_child._id)
        try:
            retval = db_operation(_db_uri, 'update_one', 
                        update={"$set": _doc},
                        upsert=True)
        except pymongo.errors.DuplicateKeyError as err:
            logger.error('%s.db_insert %s; %s' % (self.__class__.__name__, str(_db_uri), err))
            return False
        logger.debug('%s.insert %s' % (self.__class__.__name__, str(_db_uri)))
        return retval.acknowledged 

    def db_load(self, recursive=False):
        # if not self.db_uri.get("_id", None):
        #     return None
        if recursive:
            _dsdoc = list(map(operator.methodcaller('db_load', recursive=False), self))
            _dsdoc = _dsdoc[0]
        else:
            # if not self.db_uri:
            #     print(self.data)
            #_db_uri = vn_config.get_db_uri(**self.db_uri)
            _db_uri = self.db_uri
            _dsdoc = find_by_id(_db_uri)
            if not _dsdoc:
                logger.error('%s.db_load cannot find db document %s' % (self.__class__, str(_db_uri)))
                return False
            for _key, _val in _dsdoc.items():
                if _key in ["parent", "childs", "_id", "db_uri"]:
                    continue
                if _key in self.data: # no clobber, only merge dicts
                    if isinstance(self.data[_key], dict) and isinstance(_val, dict):
                        _val.update(self.data[_key])
                    else:
                        continue
                self.set_data(_key, value=_val)
        return _dsdoc

    def find_by_id(self, _id):
        _doc = find_by_id(self.db_uri, _id)
        return _doc

    @classmethod
    def node_from_db(cls, host, port, db, collection, _id, parent=None, load=False):
        db_uri = {
            "host": host,
            "port": port,
            "db": db,
            "collection": collection,
            "_id": _id,            
        }
        _doc = find_by_id(db_uri)
        if not _doc:
            return None
        child_ids = copy.copy(_doc.get("childs", []))
        if "childs" in _doc:
            del _doc["childs"]
        if "parent" in _doc:
            del _doc["parent"]
        if load:
            tdict = { "data": _doc }
        else:
            tdict = { "data": {} }
            for key in ["name", "vn"]:
                if key in _doc:
                    tdict["data"][key] = _doc.get(key)
        new_node = cls(treedict=tdict, parent=parent)
        for _child_id in child_ids:
            db_uri["_id"] = _child_id
            cls.node_from_db(**db_uri, parent=new_node)
        return new_node





def db_operation(db_uri, operation, **kwargs):
    # if not db_uri:
    #     db_uri = {  "host":"localhost",
    #                 "port":27017,
    #                 "db":"test_database",
    #                 "collection":"testitems"}
    retval = None
    dbclient = pymongo.MongoClient(db_uri["host"], db_uri["port"])
    db = dbclient[db_uri["db"]]
    dbcoll = db[db_uri["collection"]]
    if operation in ['count', 'find', 'find_one', 'find_one_and_delete',
                     'delete_one', 'delete_many',
                     'update_one', 'replace_one']:
        # http://api.mongodb.com/python/current/api/pymongo/collection.html
        _extra_kwargs = {}
        if "filter" not in kwargs and "_id" in db_uri:
            _extra_kwargs["filter"] = {"_id": db_uri["_id"]}
        retval = getattr(dbcoll, operation)(**kwargs, **_extra_kwargs)
        logger.debug("db_operation: %s returned %s" % (operation, str(retval)[:50]))
    elif operation in ['insert_one', 'insert_many', 'create_index']:
        # http://api.mongodb.com/python/current/api/pymongo/collection.html
        retval = getattr(dbcoll, operation)(**kwargs)
        logger.debug("db_operation: %s returned %s" % (operation, str(retval)[:50]))
    elif operation.__name__ in  ['fstree_to_db', 'dbtree_to_Nodes']:
        retval = operation(dbcoll=dbcoll, **kwargs)
        logger.debug("db_operation: %s returned %s" % (operation.__name__, retval))
    else:
        logger.warning('db_operation operation not available: %s', operation)
    dbclient.close()
    return retval


def find_by_id(db_uri, _id=None):
    if not _id:
        if "_id" in db_uri:
            _id = db_uri["_id"]
        else:
            return False
    dbclient = pymongo.MongoClient(db_uri["host"], db_uri["port"])
    db = dbclient[db_uri["db"]]
    dbcoll = db[db_uri["collection"]] 
    returnVal = dbcoll.find_one(filter={"_id":_id})
    if returnVal is None and isinstance(_id, str):
        try:
            obj_id = ObjectId(_id)
        except InvalidId as err:
            logger.warning("find_by_id: %s; _id=%s; %s" % (str(db_uri), _id, err))
            returnVal = None
        else:
            returnVal = dbcoll.find_one(filter={"_id": obj_id})
    return returnVal


def vn_uri_to_id(ss):
    _hash = hashlib.md5(ss.encode()).hexdigest()
    return _hash
