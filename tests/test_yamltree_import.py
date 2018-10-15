import unittest

import yaml

from vntree import Node

Node.setup_yaml()

yamltree = """
- !Node &root
  name: "root node"
  parent: null
  data:
    testval1: 111
    testval2: 222
- !Node &n0
  name: "child 1"
  parent: *root
- !Node &n1
  parent: *root
  data:
    name: "second child"
    astring: "testing..."
- !Node &n2
  parent: *root
  data:
    name: "third child"
    astring: "testing..."
- !Node 
  parent: *n1
  data:
    name: "grand child"
    test: 1234
"""

rootnode = Node('root node', data={"testval1": 111, "testval2": 222})
n0 = Node('child 1', rootnode)
n1 = Node(parent=rootnode, data={"name": "second child", "astring": "testing..."})
n2 = Node(parent=rootnode, data={"name": "third child", "astring": "testing..."})
Node(parent=n1, data={"name": "grand child", "test": 1234})


class BasicTests(unittest.TestCase):

    def test_yamltree_compare(self):
        ytreeroot = Node.import_yamltree(yamltree)
        self.assertFalse(ytreeroot is rootnode)
        self.assertEqual(rootnode.string_diff(ytreeroot), 1.0)


if __name__ == '__main__':
    unittest.main()
