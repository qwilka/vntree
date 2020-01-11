"""
Copyright © 2015 Qwilka Ltd. All rights reserved.
Any unauthorised copying or distribution is strictly prohibited.
Author: Stephen McEntee <stephenmce@gmail.com> 
"""
import logging
logger = logging.getLogger(__name__)
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt


if __name__ != "__main__":
    from .nodes import Node, VnNode
    from .file_system_tree import fstree_from_JSON


class TreeModel(QAbstractItemModel):

    def __init__(self, rootNode, parent=None, 
                 headers=("name", "data") ):
        super().__init__(parent)
        #assert isinstance(root, Node), "TreeModel root must be type Node"
        self.rootItem = rootNode
        self.rootIndex = QModelIndex() 
        self.dirty = False
        self.headers = headers

    def columnCount(self, parent=QModelIndex()):
        if parent and parent.isValid():
            return parent.internalPointer().column_count()
        else:
            return len(self.headers)

    def data(self, index, role):
        if not index.isValid():
            return None
        item = self.getItem(index)
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.column()==0:
                return item.name
            else:
                return str( item.get_data(index.column()-1) )

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.rootItem

    def flags(self, index):
        return (Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable |
                Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.headers[section]

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid() and parent.column() != 0:
            return QModelIndex()
        parentItem = self.getItem(parent)
        childItem = parentItem.get_child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        node = self.getItem(index)
        parentItem = node.get_parent()
        if parentItem == self.rootItem:
            return QModelIndex()
        return self.createIndex(parentItem.child_idx(), 0, parentItem)

    def removeChildren(self, position, count):
        raise NotImplementedError("removeChildren")

    def rowCount(self, parent=QModelIndex()):
        parentItem = self.getItem(parent)
        return parentItem.count_child()

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False
        item = self.getItem(index)
        if index.column() == 0:
            success = item.set_name(value)
        else:
            success = item.set_data(index.column()-1, value)
        if success:
            self.dataChanged.emit(index, index)
        return success


class VnTreeModel(TreeModel):

    def __init__(self, rootNode, parent=None, numcols=1):
        super().__init__(parent)
        # QTreeView does not display the tree root. 
        # Setup a new node called 'invisibleRoot' to act as the dummy root
        # node for QTreeView, if it does not already exist.
        if not rootNode:  # setup an empty tree model
            self.rootItem = self.setup_invisibleRootNode()
        elif rootNode.name == 'invisibleRoot':  # rootNode==invisibleRootNode
            self.rootItem = rootNode
        else:  # re-parent rootNode underneath invisibleRootNode
            self.rootItem = self.setup_invisibleRootNode(rootNode)
        self.rootIndex = QModelIndex() 
        self.dirty = False
        self._numcols = numcols

    def columnCount(self, parent=QModelIndex()):
        return self._numcols

    def data(self, index, role):
        if not index.isValid():
            return None
        item = self.getItem(index)
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.column()==0:
                return item.name
            else:
                data_ = item.get_data()
                return str( data_ )
        elif role == Qt.UserRole:
            data_ = item.get_data()
            # filtering out 'visinum_childs' and 'visinum_parent' to avoid expanding 
            # DbDocFileMetadata objects in MetadataDelegate (metadata_view.py)
            if 'visinum_childs' in data_:
                #data_['childs'] = str(data_['childs'])
                list_ = []
                for itm in data_['visinum_childs']:
                    list_.append(str(itm))
                data_['visinum_childs'] = list_
            if 'visinum_parent' in data_:
                data_['visinum_parent'] = str(data_['visinum_parent'])
            return str( data_ )


    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False
        item = self.getItem(index)
        if index.column() == 0:
            success = item.set_name(value)
        else:
            success = item.set_data(value)
        if success:
            self.dataChanged.emit(index, index)
        return success

    def flags(self, index):
        return (Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable |
                Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled)

    def insertRows(self, position, numrows, parent=None, nodes=None):
        """insert rows from starting position (row index) and number given by nrows"""
        if not parent:
            parent = self.rootIndex
        parentItem = self.getItem(parent)
        if nodes and isinstance(nodes, (list, tuple)):  
            nodeslist = nodes
        elif nodes:
            nodeslist = [nodes]
        self.beginInsertRows(parent, position, position + numrows - 1)
        for row in range(numrows):
            nrows = parentItem.count_child()
            if nodes:
                success = parentItem.insert_child(nodeslist[row], nrows)
            else:
                success = parentItem.insert_child( 
                       VnNode("new node" + str(nrows+1)), position+row)
        self.endInsertRows()
        return success


    @staticmethod
    def setup_invisibleRootNode(realrootNode=None):
        invisibleRootNode = VnNode('invisibleRoot')
        invisibleRootNode.set_data(description="Dummy node for QTreeWidget invisibleRootItem.")
        if realrootNode:        
            invisibleRootNode.insert_child(realrootNode)
        return invisibleRootNode


class FsTreeModel(VnTreeModel):

    def __init__(self, rootNode, parent=None, numcols=1):
        super().__init__(rootNode, parent, numcols)

    def flags(self, index):
        return (Qt.ItemIsEnabled | Qt.ItemIsSelectable )



def fstreemodel_from_JSON(filepath):
    treenodes = fstree_from_JSON(filepath)
    return FsTreeModel(treenodes)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QTreeView  
    from nodes import tree_from_dict, VnNode
    from file_system_tree import make_file_system_tree

    if False:
        dtree = {'First name': 'Maximus',
            'Last name': 'Mustermann',
            'Nickname': 'Max',
            'Address':{
                'Street': 'Musterstr.',
                'House number': 13,
                'Place': 'Orthausen',
                'Zipcode': 76123},
            'An Object': "i am a 'float'",
            'Great-grandpa':{
            'Grandpa':{
            'Pa': 'Child'}}
        }
        treenodes = tree_from_dict(dtree)
        print(treenodes.name)
        print(treenodes.get_data())
        model = TreeModel(treenodes)
        print(treenodes.to_texttree())
    else:
        treenodes = make_file_system_tree('../')
        model = VnTreeModel(treenodes)
        print(treenodes.name)
        print(treenodes.get_data())
    app = QApplication(sys.argv)
    treeView = QTreeView()
    treeView.show()
    treeView.setModel(model)
    sys.exit(app.exec_())


