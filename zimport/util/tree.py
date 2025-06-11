#-------------------------------------------------------------------------------
# zimport v0.1.10 20250611
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------
import os, sys
if not os.path.dirname(__file__) in sys.path : sys.path.append(os.path.dirname(__file__))
import typing # typing added in version 3.5, https://docs.python.org/3/library/typing.html
from typing import Self
from typing import overload

DBG = False
ROOT_SIGNATURE = '/'
class Tree :
    def __init__(self, name : str = None, data = None):
        if name is not None and '/' in name :
            raise Exception(f"[ERR] name can't contains '/' [{name}]")
        self._supr = None
        self._name = name if name is not None else ''
        self._dict = dict()
        self._data = data

    def root(self) -> Self :
        if self.supr() is None : return self
        return self.supr().root()

    def supr(self) : return self._supr
    def name(self) : return self._name
    def dict(self) : return self._dict
    def get(self) : return self._data
    def set(self, o) : self._data = o; return self

    def _nomalized(self, name : str) -> str : # remove ROOT_SIGNATURE or last '/'
        if name.startswith(ROOT_SIGNATURE): name = name[1:]
        if name.endswith('/') : name = name[:-1]
        return name

    def add(self, name : str, data = None) -> Self : # add only one tree item
        if name is None :
            print(f"[ERR] tree is None ...", file=sys.stderr)
            return None
        name = self._nomalized(name)
        if (name in self.dict().keys()) :
            if DBG : print(f"[INF] tree [{self.path()}] already has sub-tree [{name}] ...", file=sys.stderr)
            return self.dict()[name]
        return self.addtree(Tree(name, data))

    def addpath(self, path : str, data = None) -> Self : # add path hierarchy tree item ie, a/b/c/d
        if path is None or len(path) == 0 : return None
        paths = self._nomalized(path).split('/')
        return _addpath(self, paths, data)

    def addtree(self, tree : Self) -> Self : # add only one tree item
        if tree is None :
            print(f"[ERR] tree is None ...", file=sys.stderr)
            return None
        if (tree.name() in self.dict().keys()) :
            if DBG : print(f"[INF] tree [{self.path()}] already has sub-tree [{tree.name()}] ...", file=sys.stderr)
            return self.dict()[tree.name()]
        tree._supr = self
        self._dict[tree.name()] = tree
        return tree

    def remove(self, name : str) -> None :
        if path is None : return
        name = self._nomalized(name)
        if not name in self.dict().keys() : return
        self.dict().pop(name)
        pass

    def find(self, path : str) -> Self : # find full path ie, /a/b/c or a/b/c
        if path is None or len(path) == 0 : return None
        paths = self._nomalized(path).split('/')
        return _find(self, paths)

    def path(self, subpath : str = None) -> str:
        return path(self, subpath)

    def debug(self) -> None :
        debug(self, 0, False)

    def debug_detail(self) -> None :
        debug(self, 0, True)

########################################

def _addpath(tree : Tree, paths : list, data = None, depth : int = 0) -> Tree : # add path hierarchy tree item ie, a/b/c/d
    name = paths[depth]
    if (name in tree.dict().keys()) :
        return _addpath(tree.dict()[name], paths, data, depth+1) if depth+1 < len(paths) else tree.dict()[name]
    else :
        t = tree.add(name) if depth+1 < len(paths) else tree.add(name, data)
        return _addpath(t, paths, data, depth+1) if depth+1 < len(paths) else t
    pass

def _find(tree : Tree, paths : list, depth : int = 0) -> Tree :
    name = paths[depth]
    if (name in tree.dict().keys()) :
        t = tree.dict()[name]
        return _find(t, paths, depth+1) if depth+1 < len(paths) else t
    else :
        return None
    pass

def path(tree : Tree, subpath : str = None) -> str:
    if tree._supr is None :
        return tree.name() + ('' if subpath is None else ROOT_SIGNATURE + subpath)
    else :
        return tree.supr().path(tree.name() + ('' if subpath is None else '/' + subpath))

def debug(tree : Tree, dep : int = 0, detail_display : bool = False) :
    if (0 < dep) :
        if detail_display :
            print(f"{space(dep)}{tree.name()} ({'' if tree.get() is None else tree.get()}) ::: [{tree.path()}]", file=sys.stdout)
        else      :
            print(f"{space(dep)}{tree.name()} ::: [{tree.path()}]", file=sys.stdout)
    for k, v in tree.dict().items():
        debug(v, dep + 1, detail_display)

def space(dep) :
    s = ''
    dep = dep - 1
    for i in range(dep) : s += '    ' if i+1 < dep else '  + '
    return s

########################################

def _test01() :
    print("------------")
    t = Tree()
    t.add('a', 'a').add('b', 'b')
    t.find('/a/b').add('/c').add('1', 1)
    t.find('/a/').find('/b').add('c').add('2', 2)
    t.find('/a/').find('b/').find('c/').add('3', 3)
    t.find('a/b/c').add('4', 4)
    t.find('a/b/').add('c', 'c')
    t.find('a/b/').find('/c/').set('c')
    t.debug()
    print("------------")
    t.find('/a/b/').remove('/c/')
    t.find('/a/').remove('b/')
    t.debug()
    print("------------")
    t.addpath('w/x/y').addpath('z', 'value')
    t.addpath('w/x/y').addpath('o', 'value')
    t.debug()
    pass

def _test02(file : str) :
    import zip as ZIP
    ntry, stat, tree = ZIP.zipinfo(file)
    if False : tree.debug()

import times
if __name__ == '__main__':
    stt = times.current_milli()
    _test01()
    #_test02(os.path.join(os.environ["PROJECT_HOME"].replace('\"', ''), "lib.p12/site-packages.transformers-4.52.3.z"))
    #_test02(os.path.join(os.environ["PROJECT_HOME"].replace('\"', ''), "lib.p12/site-packages.torch-2.6.0+cu126.z"))
    end = times.current_milli()
    print(f"[INF] elapsed time {(end - stt)} ms ...")
    pass

