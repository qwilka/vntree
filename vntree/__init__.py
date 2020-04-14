"""`vntree` is a simple tree data structure coded in Python.
"""
import logging

logger = logging.getLogger(__name__)

__version__ = "0.4.0"
__license__ = "MIT"
__copyright__ = "Copyright 2018-2020 Stephen McEntee"
__author__ = "Stephen McEntee"
__email__ = "stephenmce@gmail.com"
__description__ = """«vntree» is a simple tree data structure in Python."""
__url__ = "https://github.com/qwilka/vntree"

from .node import Node, NodeAttr, TreeAttr


try:
    from .sqlite import SqliteNode
except ImportError as err:
    logger.warning("Cannot import vntree.SqliteNode, check required module «sqlitedict»; %s" % (err,) )

try:
    from .mongo import MongoNode
except ImportError as err:
    logger.warning("Cannot import vntree.MongoNode, check required module «pymongo»; %s" % (err,) )

