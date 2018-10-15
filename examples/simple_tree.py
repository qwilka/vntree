import itertools
import os
import sys

# A «class» provides the specification for an «object».
# An «object» is a data structure with integrated functions (called «methods» in Python).
class Node:
    """Node class for tree data structure.  
    Ref: https://en.wikipedia.org/wiki/Tree_(data_structure)
    """
    # __init__ is a special method that is called when an «instance» of the class
    # is created. The first «argument» "self" is a reference to the instance object.
    def __init__(self, name, parent=None):
        self.name = name
        self.children = []
        if parent and isinstance(parent, Node):
            parent.add_child(self)
        elif parent is None:
            self.parent = None
        else:
            raise TypeError("Node instance «{}» argument «parent» type not valid: {}".format(name, type(parent)))

    def __str__(self):
        _level = len(self.get_ancestors())
        return "{} level={} «{}»".format(self.__class__.__name__, _level, self.name)

    # __iter__ is a special method that turns the tree into an «iterator».
    # This enables convenient tree traversal (using a "for" loop, for example).
    # "yield" turns the «iterator» into a «generator».
    def __iter__(self): 
        yield self  
        for node in itertools.chain(*map(iter, self.children)):
            yield node 

    def __reversed__(self):  
        for node in itertools.chain(*map(reversed, self.children)):
            yield node
        yield self 

    def add_child(self, newnode):
        self.children.append(newnode)
        newnode.parent = self
        return True    

    def get_ancestors(self):
        ancestors=[]
        _curnode = self
        while _curnode.parent:
            _curnode = _curnode.parent
            ancestors.append(_curnode)
        return ancestors

    def to_texttree(self):
        treetext = ""
        root_level = len(self.get_ancestors())
        for node in self: 
            level = len(node.get_ancestors()) - root_level
            treetext += ("." + " "*3)*level + "|---{}\n".format(node.name)
        return treetext


# This class specifies a "decision tree" through «inheritance» from the 
# "Node" class, re-implementing some of the "Node" properties to 
# change its behaviour.
class DecisionNode(Node):
    """
    Ref: https://en.wikipedia.org/wiki/Decision_tree
    """
    def __init__(self, name, parent=None, type="outcome", p=1, npv=0):
        super().__init__(name, parent)
        self.p = p
        self.npv = npv
        self.ev = self.p * self.npv
        self.type = type
        self.decision = ""

    def to_texttree(self):
        treetext = ""
        root_level = len(self.get_ancestors())
        for node in self:
            if node.type == "chance":
                type_sym = "\u25ef"
            elif node.type == "decision":
                type_sym = "\u25a1"
            elif node.type == "outcome" and node.p==1:
                type_sym = "|"
            elif node.type == "outcome":
                type_sym = "\u25b7"
            level = len(node.get_ancestors()) - root_level
            treetext += ("." + " "*3)*level + "{}---{}".format(type_sym, node)
            if node.type == "decision":
                treetext += "; DECISION: «{}»\n".format(node.decision)
                treetext += " "*4*(level+1) + "|\n"
            elif node.type == "chance":
                treetext += "; EV={}\n".format(node.ev)
            elif node.type == "outcome":
                treetext += "; p={}; NPV={}; EV={}\n".format(node.p, node.npv, node.ev)
                if node.children:
                    treetext += " "*4*(level+1) + "|\n"
            else:
                treetext += "\n"
        return treetext

    @staticmethod # "@" indicates a «decorator» that modifies the method.
    def calculate_ev(node):  # a "staticmethod" does not use the instance reference "self".
        ##print(node)
        if node.children and node.type == "chance":
            node.npv = 0
            for child in node.children:
                node.npv += child.p * child.npv 
        elif node.type == "decision":
            best_npv = -sys.float_info.max
            for child in node.children:
                ##print("decision child", child, child.npv, best_npv, child.npv > best_npv)
                if child.npv > best_npv:
                    best_npv = child.npv
                    best_option = child.name
            node.npv = best_npv
            node.decision = best_option
        elif node.type == "outcome" and node.children:
            node.npv = node.children[0].npv
        node.ev = node.p * node.npv
        return node.name, node.ev


def make_file_system_tree(root_folder, _parent=None):
    """This function makes a tree from folders and files.
    """
    root_node = Node(os.path.basename(root_folder), _parent)
    root_node.path = root_folder
    for item in os.listdir(root_folder):
        item_path = os.path.join(root_folder, item)
        if os.path.isfile(item_path):
            file_node = Node(os.path.basename(item), root_node)
            file_node.path = item_path
        elif os.path.isdir(item_path):
            #folder_path = os.path.join(root_folder, item)
            make_file_system_tree(item_path, _parent=root_node)
    return root_node
            


if __name__ == '__main__':

    SIMPLE_TREE = True
    FILES_FOLDERS_TREE = False
    DECISION_TREE = False
    
    if SIMPLE_TREE:

        rootnode   = Node('ROOT ("top" of the tree)')
        Node("1st child (leaf node)", parent=rootnode)
        child2 = Node("2nd child", rootnode)
        Node("grand-child1 (leaf node)", child2)
        Node("grand-child2 (leaf node)", child2)
        child3 = Node("3rd child", rootnode)
        Node("another child (leaf node)", rootnode)
        grandchild3 = Node(parent=child3, name="grand-child3")
        ggrandchild = Node("great-grandchild", grandchild3)
        Node("great-great-grandchild (leaf node)", ggrandchild)
        Node("great-grandchild2 (leaf node)", grandchild3)

        print()
        print(rootnode.to_texttree())
        print("\nTree iterate top-down:")
        for node in rootnode:
            print(node)
        print("\nTree iterate bottom-up:")
        for node in reversed(rootnode):
            print(node)
        

    if FILES_FOLDERS_TREE:
        # Specify a folder path on your computer in the variable «root_folder».
        # Choose a folder with only a few files and sub-folders, to avoid creating a large tree.
        # Windows users should note that there are complications when specifying a
        # file path in Python, see this link: https://stackoverflow.com/a/46011113
        root_folder = r"/home/develop/Projects/src/visinum/visinum"
        if not os.path.isdir(root_folder):
            print("ERROR: «{}» is not a valid folder!".format(root_folder))
            sys.exit()
        files_folders_tree = make_file_system_tree(root_folder)
        #dummynode = Node("dummynode", files_folders_tree)
        #dummynode.path = ""
        for item in files_folders_tree:
            print(item.path, end="")
            if os.path.isdir(item.path):
                print(" is a FOLDER")
            elif os.path.isfile(item.path):
                print(" is a FILE")
            else:
                raise OSError("«{}» is not a valid file or folder!".format(item))
        print(files_folders_tree.to_texttree())

    if DECISION_TREE:
        # http://www.maxvalue.com/DA_in_CE_20170329.pdf DECISION ANALYSIS IN COST ENGINEERING, John Schuyler, 2017
        ALD_decision = DecisionNode("Acquire and drill | Do not acquire?", type="decision")
        No_acq = DecisionNode("Do not acquire lease", ALD_decision, npv=0)
        tw1_chance = DecisionNode("Acquire and drill", ALD_decision, type="chance")
        tw1_large = DecisionNode("Large field", tw1_chance, p=0.05, npv=360)
        tw1_marg = DecisionNode("Marginal field", tw1_chance, p=0.05, npv=110)
        tw1_dry = DecisionNode("Dry hole", tw1_chance, p=0.9)
        tw2_decision = DecisionNode("Drill test well #2 | drop?", tw1_dry, type="decision")
        tw2_chance = DecisionNode("Drill test well #2", tw2_decision, type="chance")    
        tw2_large = DecisionNode("Large field", tw2_chance, p=0.075, npv=350)
        tw2_marg = DecisionNode("Marginal field", tw2_chance, p=0.075, npv=100)
        tw2_dry = DecisionNode("Dry hole", tw2_chance, p=0.85, npv=-50)
        tw2_drop = DecisionNode("Drop", tw2_decision, npv=-40)
        # for node in acq_lease_drill:
        #     print(node)
        rootnode = ALD_decision
        EVs = list(map(rootnode.calculate_ev, reversed(rootnode)))
        print("EMV for «{}» = ${} million".format(rootnode.decision, rootnode.npv))
        print(rootnode.to_texttree())

