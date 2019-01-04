Introduction
============


Installation
--------------

To install the `vntree` module run::

    pip install vntree

Basics
--------------
Usage as follows...

>>> from vntree import Node
>>> rootnode = Node("The Root Node")    # the root node has no parent
>>> Node("first child", rootnode)       # create a child node
<vntree.node.Node object at 0x7f41aeb37e48>
>>> c2 = Node("child 2", rootnode)      # create another child node
>>> Node("child3", rootnode)            # create 3rd child node
<vntree.node.Node object at 0x7f8ac02799b0>
>>> g1 = Node("grandchild1", c2)        # child of node «child 2»
>>> Node(parent=c2)       # another grandchild node, name not specified
<vntree.node.Node object at 0x7f41aeb4c048>
>>> c1 = rootnode.get_node_by_nodepath("/rootnode/first child")
>>> c1.add_child(Node(name=""))  # grafting an external node into the tree
True
>>> print(rootnode.to_texttree())
| The Root Node
+--| first child
.  +--| ()
+--| child 2
.  +--| grandchild1
.  +--| (1, 1)
+--| child3



References
----------

#. `PyPI <https://pypi.org/project/vntree/>`_
#. `GitHub <https://github.com/qwilka/vn-tree>`_