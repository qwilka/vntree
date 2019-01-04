import itertools
import sys

from simple_tree import Node

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

    def __reversed__(self):  
        for node in itertools.chain(*map(reversed, self.children)):
            yield node
        yield self 

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



            


if __name__ == '__main__':

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

