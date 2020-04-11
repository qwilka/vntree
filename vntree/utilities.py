"""
"""
#import copy
#import functools
import hashlib
#import inspect
import json
import pickle


def dict2hash(obj):
    """Calculate a hash value for a dictionary."""
    adjson = json.dumps(obj, sort_keys=True, default=str)
    m = hashlib.md5()
    m.update(adjson.encode())
    _hash = m.hexdigest()
    print(f"adjson={adjson}")
    print(f"_hash={_hash}")
    return _hash


def dict2hash2(obj):
    """Calculate a hash value for a dictionary."""
    sdict = dict(sorted(obj.items()))
    pkl = pickle.dumps(sdict)
    m = hashlib.md5()
    m.update(pkl)
    _hash = m.hexdigest()
    return _hash

