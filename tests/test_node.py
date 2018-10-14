import unittest

from vntree import Node


rootnode   = Node('ROOT')
Node("1st child", parent=rootnode)
child2 = Node("2nd child", rootnode)
Node("grand-child1", child2)
Node("grand-child2", child2)
child3 = Node("3rd child", rootnode)
Node("another child", rootnode)
grandchild3 = Node(parent=child3, name="grand-child3")
ggrandchild = Node("great-grandchild", grandchild3)
Node("great-great-grandchild", ggrandchild)
Node(None, grandchild3, {"name":"name-in-data"})


class BasicTests(unittest.TestCase):

    def test_texttree(self):
        _texttree = """| ROOT\n+--| 1st child\n+--| 2nd child\n.  +--| grand-child1\n.  +--| grand-child2\n+--| 3rd child\n.  +--| grand-child3\n.  .  +--| great-grandchild\n.  .  .  +--| great-great-grandchild\n.  .  +--| name-in-data\n+--| another child\n"""
        self.assertEqual(rootnode.to_texttree(), _texttree)

    def test_roundtrip(self):
        newtreedict = rootnode.to_treedict()
        newtree = Node(treedict=newtreedict)
        self.assertFalse(newtree is rootnode)
        self.assertEqual(rootnode.string_diff(newtree), 1.0)


if __name__ == '__main__':
    unittest.main()


