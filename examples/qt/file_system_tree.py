"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See «vntree» LICENSE file for details https://github.com/qwilka/vntree/blob/master/LICENSE
"""
import logging
import fnmatch
import json
import os
import pathlib
import uuid
logger = logging.getLogger(__name__)
try:
    from scandir import scandir, walk
except ImportError:
    from os import scandir, walk

# Python3 import weirdness http://stackoverflow.com/questions/16981921/relative-imports-in-python-3
try:   # cannot use relative imports when running this module directly
    from .nodes import VnNode, node_from_pathlist
except (SystemError, ImportError):
    from nodes import VnNode, node_from_pathlist


class FsNode(VnNode):
    """Node class adapted for creating a file-system tree."""
    def __init__(self, filepath, parent=None, metadata=None, 
                       numcols=1, UUID=None):
        super().__init__(os.path.basename(filepath), parent, metadata, numcols)
        self.set_path(filepath)
        self.set_UUID(UUID)

    def get_path(self, path_rel=None):
        if path_rel:
            return os.path.relpath(self._path, path_rel)
        else:
            return self._path

    def set_path(self, filepath):
        # Windows path complications, convert to Posix
        # require escape for backslash, so '\\' = '\'
        if fnmatch.fnmatch(filepath, "[a-z|A-Z]:*") or (
              '\\' in filepath and '/' not in filepath ) :
            ppath = pathlib.PureWindowsPath(filepath)
            self._name = ppath.name # fix name
            if ppath.drive:
                self.set_data(path_drive_orig=ppath.drive)
                ppath = ppath.relative_to(ppath.drive)
            filepath = ppath.as_posix()
            if not filepath.startswith('/'): filepath = '/' + filepath
        self._path = filepath
        self.set_data(path=self._path)
        
    def get_UUID(self):
        return self._UUID

    def set_UUID(self, UUID=None):
        if UUID:
            if isinstance(UUID, uuid.UUID):
                self._UUID = UUID.hex
            else:
                self._UUID = uuid.UUID(UUID).hex
        else:
            # Warning: uuid.uuid3 is repeatable and potentially not unique.
            self._UUID = uuid.uuid3(uuid.NAMESPACE_URL, self._path).hex
            #self._UUID = uuid.uuid4().hex
        self.set_data(UUID=self._UUID)



def make_file_system_tree(path_rootdir='.', excludedirs=[]):
    """Make a visinum file-system tree.'
    
    Parameters
    ----------
    path_rootdir : str
        Root directory path for the file-system tree.
    excludedirs : list, optional
        List of of directories to be excluded from tree.

    Returns
    -------
    rootNode : FsNode
        Root node of the file-system tree. 
    """
    root_ppath = pathlib.Path(path_rootdir)
    if not root_ppath.is_dir():
        raise AttributeError("cannot locate directory %s" % (root_ppath.as_posix(),))
    root_ppath = root_ppath.resolve()
    root_path = root_ppath.as_posix()
    rootNode = FsNode(root_path,      
               metadata={ "file_name":root_ppath.name,
              "path_orig":root_path, 
              "path_rel":root_ppath.relative_to(root_ppath).as_posix()} )
    for dirpath, dirnames, filenames in walk(path_rootdir, topdown=True):
        dirnames = [x for x in dirnames if x not in excludedirs] # apply excludedirs filter
        dd = pathlib.Path(dirpath).resolve()
        ppath_rel = dd.relative_to(root_ppath)
        foundparent = node_from_pathlist(rootNode, ppath_rel.parts)
        if foundparent:
            for dirname in dirnames:
                ppath = dd.joinpath(dirname)
                path = ppath.as_posix()
                FsNode(path, foundparent, metadata={
                "file_name":dirname,
                "path_orig":path,
                "path_rel":ppath.relative_to(root_ppath).as_posix() } )
            for filename in filenames:
                ppath = dd.joinpath(filename)
                path = ppath.as_posix()
                FsNode(path, foundparent, metadata={
                "file_name":filename,
                "path_orig":path,
                "path_rel":ppath.relative_to(root_ppath).as_posix() } )
        foundparent = node_from_pathlist(rootNode, ppath_rel.parts)
        for filename in filenames:
            pass
    return rootNode


def fstree_from_vndict(vndict, _rootNode=None, _parent=None):
    """Create a tree of FsNodes from a Vndict format dictionary. 

    Parameters
    ----------
    vndict : dict
        VnDict format dictionary describing the file-system tree.
    _rootNode : FsNode, optional
        Do not set: for internal recursive use only.
    _parent : FsNode, optional
        Do not set: for internal recursive use only.

    Returns
    -------
    rootNode : FsNode
        Root node of the file-system tree. 
    """
    metadata = {k:v for k, v in vndict.items() if k != "_childs"}
    node = FsNode(metadata["path"], parent=_parent, metadata=metadata)
    if not _rootNode:
        _rootNode = node
    if "_childs" in vndict:
        for child in vndict["_childs"]:
            fstree_from_vndict(child, _rootNode, node)
    return _rootNode


def fstree_from_JSON(fpath):
    """Create a tree of FsNodes from a JSON file containing a 
    Vndict format dictionary.

    Parameters
    ----------
    fpath : str
        Path to the JSON file containing Vndict data.

    Returns
    -------
    rootNode : FsNode
        Root node of the file-system tree. 
    """
    with open(fpath, 'r') as jfile:
        dict_ = json.load(jfile)
    return fstree_from_vndict(dict_)


if __name__ == '__main__':
    # Each line below is a test, un-comment line to run test as required
    print(make_file_system_tree('.').to_texttree(printdata=30))  # printdata=30
    #for node in list(make_file_system_tree('.')): print(node.get_name())
    #print(json.dumps(make_file_system_tree().to_vndict(), sort_keys=False, indent=2 ))
    #print(make_file_system_tree("/home/develop/Downloads/MBES_data").to_texttree())


    # save a file-system tree in a JSON file
    """rootNode = make_file_system_tree('.')
    print('rootNode=', rootNode.name)
    rootNode.to_JSON('/home/develop/Downloads/MBES_data/tree_directory.json')"""

