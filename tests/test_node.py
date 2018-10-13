import unittest

from vntree import Node


rootnode = Node('ROOT (level 0, the "top" of the tree)')
Node("1st child (level 1, leaf node)", parent=rootnode)
child2 = Node("2nd child (level 1)", rootnode)
Node("grand-child1 (level 2, leaf node)", child2)
Node("grand-child2 (level 2, leaf node)", child2)
child3 = Node("3rd child (level 1)", rootnode)
Node("another child (level 1, leaf node)", rootnode)
grandchild3 = Node(parent=child3, name="grand-child3 (level 2")
ggrandchild = Node("great-grandchild (level 3)", grandchild3)
Node("great-great-grandchild (level4, leaf node)", ggrandchild)
Node(None, grandchild3, {"name":"name-in-data"})


class BasicTests(unittest.TestCase):

    def test_texttree(self):
        _texttree = """|---ROOT (level 0, the "top" of the tree)\n.   |---1st child (level 1, leaf node)\n.   |---2nd child (level 1)\n.   .   |---grand-child1 (level 2, leaf node)\n.   .   |---grand-child2 (level 2, leaf node)\n.   |---3rd child (level 1)\n.   .   |---grand-child3 (level 2\n.   .   .   |---great-grandchild (level 3)\n.   .   .   .   |---great-great-grandchild (level4, leaf node)\n.   .   .   |---name-in-data\n.   |---another child (level 1, leaf node)\n"""
        self.assertEqual(rootnode.to_texttree(), _texttree)

    def test_roundtrip(self):
        newtreedict = rootnode.to_treedict()
        newtree = Node(treedict=newtreedict)
        self.assertFalse(newtree is rootnode)
        self.assertEqual(rootnode.string_diff(newtree), 1.0)


if __name__ == '__main__':
    unittest.main()


