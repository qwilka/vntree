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


Traverse tree
--------------

Each node in a `vntree` can act as a generator, facilitating traveral of
the (sub-)tree rooted at the node instance.

top-down traversal
^^^^^^^^^^^^^^^^^^

For top-down tree traversal (starts at the root node),
apply the root node directly in a `for` loop. For example:

.. code-block:: python

    print(rootnode.to_texttree())
    for n in rootnode:
        print(f"name=«{n.name}» coord={n._coord} level={n._level}")

This code gives output::

    | ROOT
    +--| child1
    .  +--| gc1
    .  +--| gc2
    +--| child2
    .  +--| another gc
    .  .  +--| ggc1

    name=«ROOT» coord=() level=1
    name=«child1» coord=(0,) level=2
    name=«gc1» coord=(0, 0) level=3
    name=«gc2» coord=(0, 1) level=3
    name=«child2» coord=(1,) level=2
    name=«another gc» coord=(1, 0) level=3
    name=«ggc1» coord=(1, 0, 0) level=4


bottom-up traversal
^^^^^^^^^^^^^^^^^^^

For bottom-up tree traversal,
apply the Python built-in
`reversed <https://docs.python.org/3/library/functions.html#reversed>`_ 
function to the root node in a `for` loop. For an example using the
same tree as the top-down traversal example:

.. code-block:: python

    for n in reversed(rootnode):
        print(f"name=«{n.name}» coord={n._coord} level={n._level}")

This code gives output::

    name=«gc1» coord=(0, 0) level=3
    name=«gc2» coord=(0, 1) level=3
    name=«child1» coord=(0,) level=2
    name=«ggc1» coord=(1, 0, 0) level=4
    name=«another gc» coord=(1, 0) level=3
    name=«child2» coord=(1,) level=2
    name=«ROOT» coord=() level=1


Persistence
--------------

Save tree
^^^^^^^^^^^^^^^^^^

A tree can be saved as a Python
`pickle <https://docs.python.org/3/library/pickle.html>`_
file. 
For example:

.. code-block:: python

    rootnode.savefile("mytree.vnpkl")

Notes:

#. It is recommended to use the extension `.vnpkl` for this type of file.
#. Invoking `savefile` on a node instance saves the complete tree.
#. `savefile` sets a vntree metadata TreeAttr attribute (`_vnpkl_fpath`) that contains the full path of the pickle file.
#. After the first `savefile` invocation it is not necessary to specify argument `filepath` again, attribute `_vnpkl_fpath` will be used instead.

Open tree file
^^^^^^^^^^^^^^^^^^

A tree can be loaded from a `vnpkl` file by using the class method
`openfile` as follows:

.. code-block:: python

    rootnode = Node.openfile("mytree.vnpkl")

Notes:

#. `openfile` is invoked on the class: `Node.openfile(filepath)`
#. `openfile` re-sets the vntree metadata TreeAttr attribute `_vnpkl_fpath` to the current file path.
