"""`vntree` is a simple tree data structure coded in Python.
"""
import logging

logger = logging.getLogger(__name__)

__version__ = "0.3.0"
__license__ = "MIT"
__copyright__ = "Copyright 2018-2019 Stephen McEntee"
__author__ = "Stephen McEntee"
__email__ = "stephenmce@gmail.com"
__description__ = """«vntree» is a simple tree data structure in Python."""
__url__ = "https://github.com/qwilka/vn-tree"

from .node import Node, NodeAttr, TreeAttr

try:
    #from .mongo import MongoNode
    from . import mongo
except ImportError as err:
    logger.warning("Cannot import MongoNode; %s" % (err,) )

