Introduction
============

`vntree` is a Python module for creating 
`tree data structures <https://en.wikipedia.org/wiki/Tree_(data_structure)>`_. 


.. contents:: :local:

Installation
--------------

To install the `vntree` module run::

    pip install vntree

Basic Usage
--------------

`vntree` composes trees from `Node` class instances.

.. code-block:: python

    from vntree import Node
    rootnode = Node("root-node")    # the root node has no parent
    c1 = Node("child1", rootnode)   # the first child of the root node
    Node("child2", rootnode)        # the second child of the root
    Node(parent=c1)        # a grandchild (level 2) node without a name

An example of creating a simple tree in the Python console:

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
>>> c1.add_child(Node())  # grafting an external node into the tree
True
>>> print(rootnode.to_texttree())
| The Root Node
+--| first child
.  +--| 
+--| child 2
.  +--| grandchild1
.  +--| 
+--| child3




References
----------

#. `Tree data structures <https://en.wikipedia.org/wiki/Tree_(data_structure)>`_ article on Wikipedia.
#. `PyYAML <https://pyyaml.org/>`_ documentation.