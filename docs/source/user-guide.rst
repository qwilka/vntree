User Guide
============


.. contents:: :local:

The Node class
--------------

The `Node` class is the fundemental unit of `vntree`, it creates node 
instances.  Node instances are composed together to create a tree.  
The nodes in a tree are linked by specifying the parent of each node.
A node consists of the following components, that are specified in order
as arguments when the `Node` class is invoked:

#. `name` - a string specifying the name of the node.
#. `parent` - a reference to the the parent node. The root node has no parent.
#. `data` - an optional dictionary containing node data.

Some points to be noted about the `vntree.Node` class:

* Each node has a `childs` attribute, which is a `list` containing the children of the node.
* If `node.childs=[ ]`, then `node` has no children. This type of node is sometimes referred to as a `leaf` node.

Creating trees
--------------

with Python code
^^^^^^^^^^^^^^^^

The following code imports the `Node` class and creates a root (top-level) node:

.. code-block:: python

    from vntree import Node
    rootnode = Node("root-node")
    print(f"The name of the root node is «{rootnode.name}»")

The output from this code is::

    The name of the root node is «root-node»

To create a level-2 child node, we need to instantiate a `Node` specifying
the root node as parent:

.. code-block:: python

    Node("The first child", rootnode)
    print(rootnode.to_texttree())

The `to_texttree` method invoked on `rootnode` prints a text representation
of the tree::

    | root-node
    +--| The first child

Note that it is not necessary to retain a reference to non-root nodes, since
references to child nodes are retained in the parent `childs` list.  However,
it can be convenient to retain an explicit reference to each node
when constructing a tree with code. In this case, to create a level-3 child of
`The first child`, we know that the parent in this case is the
first child of the root node:

.. code-block:: python

    c1 = rootnode.childs[0]
    gc1 = Node("first grand-child", c1)
    print(rootnode.to_texttree())

The tree now looks like this::

    | root-node
    +--| The first child
    .  +--| first grand-child


with a Python dictionary
^^^^^^^^^^^^^^^^^^^^^^^^

The `Node` class has a fourth optional argument `treedict` that creates
a tree from a Python dictionary representation:

.. code-block:: python

    tdict = {
        "name": "ROOT",
        "data": {
            "meta1": 1234,
        },
        "childs": [
            {
                "name": "child1",
                "childs": [{"name":"gc1"}, {"name":"gc2"}],
            },
            {
                "name": "child2",
                "data": {"test1": "this is test data"},
                "childs": [{"name":"another gc", "childs":[{"name":"ggc1"}]} ],
            },
        ]
    }
    rootnode = Node(treedict=tdict)
    print(rootnode.to_texttree())

The tree output from this code is::

    | ROOT
    +--| child1
    .  +--| gc1
    .  +--| gc2
    +--| child2
    .  +--| another gc
    .  .  +--| ggc1


with YAML
^^^^^^^^^^^^^^^^^^^^^^^^

Creating a tree with a Python dictionary can be inconvenient, due to nesting
in `childs`. An alternative that avoids the nesting problem (apart from 
explicit Python code), is to use
`YAML <https://en.wikipedia.org/wiki/YAML>`_
to specify a list of nodes:

.. code-block:: python

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
    ytree = Node.yaml2tree(yamltree)   # NOTE: yaml2tree is a class method invoked on Node
    print(ytree.to_texttree())

The tree output from the YAML data is::

    | root node
    +--| child 1
    +--| second child
    .  +--| grand child
    +--| third child

Alternatively, the YAML data can be stored in a file. In this case
the `yamltree` argument specifies the path to the YAML file:

.. code-block:: python

    ytree = Node.yaml2tree("/home/stephen/tree-nodes.yaml")

