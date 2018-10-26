"""
https://github.com/yaml/pyyaml
https://pyyaml.org/wiki/PyYAMLDocumentation
https://stackoverflow.com/questions/19439765/is-there-a-way-to-construct-an-object-using-pyyaml-construct-mapping-after-all-n
https://stackoverflow.com/questions/7224033/default-constructor-parameters-in-pyyaml
https://stackoverflow.com/questions/42218249/cant-construct-object-from-parameter-in-constructor-called-by-pyyaml
"""
from vntree import Node

import yaml


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



#for ii, dd in enumerate(yaml.load_all(yy)):
#	print(ii, dd)

# list_of_nodes = yaml.safe_load(yaml_data)
# #list_of_nodes = yaml.load(yaml_data)
# print(list_of_nodes)
# rootnode = list_of_nodes[0]

rootnode = Node.import_yamltree(yamltree)

print(rootnode.to_texttree(func=False )) # func=False supress printing node names
print(rootnode.to_texttree(func=lambda n: "{}, coord={}".format(n.name, n.coord)) )
