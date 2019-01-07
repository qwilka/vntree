from datetime import datetime
import os
import tempfile
import unittest

from vntree import Node


rootnode   = Node('ROOT')
rootnode.set_data("datetime", value=datetime.now())
Node("1st child", parent=rootnode, data={"para1":"TEST parameter"})
child2 = Node("2nd child", rootnode)
Node("grand-child1", child2, {"testvar":1234})
Node("grand-child2", child2)
child3 = Node("3rd child", rootnode)
child3.set_data("vn", "fs_path", value="/one/two/three.txt")
Node("another child", rootnode)
grandchild3 = Node(parent=child3, name="grand-child3")
ggrandchild = Node("great-grandchild", grandchild3)
Node(lambda n: f"great-great-grandchild {n._coord}", ggrandchild)
Node(None, grandchild3, {"name":"name-in-data"})
ggrandchild.add_child(Node("child-on-level5"))


class BasicTests(unittest.TestCase):

    def test_texttree(self):
        _texttree = """| ROOT\n+--| 1st child\n+--| 2nd child\n.  +--| grand-child1\n.  +--| grand-child2\n+--| 3rd child\n.  +--| grand-child3\n.  .  +--| great-grandchild\n.  .  .  +--| great-great-grandchild (2, 0, 0, 0)\n.  .  .  +--| child-on-level5\n.  .  +--| name-in-data\n+--| another child\n"""
        self.assertEqual(rootnode.to_texttree(), _texttree)

    def test_roundtrip(self):
        newtreedict = rootnode.to_treedict()
        newtree = Node(treedict=newtreedict)
        self.assertFalse(newtree is rootnode)
        self.assertEqual(rootnode.tree_compare(newtree), 1.0)


class DumpLoad(unittest.TestCase):

    def test_pickle_roundtrip(self):
        pkl_fh = tempfile.NamedTemporaryFile(suffix=".vnpkl", delete=False)
        rootnode.savefile(pkl_fh.name)
        #print("rootnode.to_treedict", rootnode.to_treedict())
        #pickle_filepath = rootnode._vnpkl_fpath
        #print("pkl_fh.name", pkl_fh.name)
        #print("rootnode._vnpkl_fpath", rootnode._vnpkl_fpath)
        newtree = Node.openfile(rootnode._vnpkl_fpath)
        #print(newtree.to_texttree())
        os.remove(pkl_fh.name)
        self.assertFalse(newtree is rootnode)
        self.assertEqual(rootnode.tree_compare(newtree), 1.0)



if __name__ == '__main__':
    unittest.main()


