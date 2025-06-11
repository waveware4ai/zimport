#-------------------------------------------------------------------------------
# zimport v0.1.10 20250611
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------
import os, sys
import importlib, inspect, traceback
import typing # typing added in version 3.5, https://docs.python.org/3/library/typing.html

DBG = False

def ismod(path : str) -> bool :
    try:
        m = importlib.import_module(path)
        if m is None : return False
        inspect.ismodule(m)
        return inspect.ismodule(m) #m.__name__ == 'pathlib'
    except Exception as e:
        return False

def isclz(head : str, tail : str) -> bool :
    try:
        m = importlib.import_module(head)
        c = getattr(m, tail)
        return inspect.isclass(c)
    except Exception as e:
        return False

def isfun(module_or_class : object, tail : str) -> bool :
    try:
        if module_or_class is None : return False
        f = getattr(module_or_class, tail)
        return inspect.isfunction(f) or inspect.isbuiltin(f) #True
    except Exception as e:
        return False

def getmod(path : str) -> object :
    try:
        m = importlib.import_module(path)
        return m
    except Exception as e:
        return None

def getclz(head : str, tail : str) -> object :
    try:
        m = importlib.import_module(head)
        c = getattr(m, tail)
        return c
    except Exception as e:
        return None

########################################

def decompose(funcpath : str) -> tuple[object, object, object] : # dotted path : a.b.c -> a.b and c
    if (funcpath is None) : return (None, None, None)
    sep = funcpath.split(".")
    mod = None
    cls = None
    fun = None
    for i in range(len(sep)) :
        try :
            head = '.'.join(sep[:i+1])
            tail = sep[i+1] if i+1 < len(sep) else ''
            cur_is_m = ismod(head)
            if cur_is_m : mod = getmod(head)
            cur_is_c = isclz(head, tail)
            if cur_is_c : cls = getclz(head, tail)
            cur_is_f = isfun(cls if cls is not None else mod, tail)
            if cur_is_f : fun = tail
            if False : print(f"[{i}] [{head}/{tail}] m[{cur_is_m}] c[{cur_is_c}] f[{cur_is_f}]")
        except Exception as e:
            pass

    if DBG :print(f"[INF] [{funcpath}] == m[{'' if mod is None else mod.__name__}] c[{'' if cls is None else cls.__name__}] f[{'' if fun is None else fun}]", file=sys.stdout)
    return (mod, cls, fun)

def set(mod : object, cls : object, fun : str, val : object) -> None :
    if mod is None and cls is None : return
    if cls is not None : setattr(cls, fun, val)
    else               : setattr(mod, fun, val)
    pass

def get(mod : object, cls : object, fun : str) -> object :
    if mod is None and cls is None : return
    if cls is not None : return getattr(cls, fun)
    else               : return getattr(mod, fun)
    pass

if __name__ == '__main__':
    DBG = True
    import zimport
    print('----------')
    mod, cls, fun = decompose("pathlib")
    mod, cls, fun = decompose("pathlib.Path")
    mod, cls, fun = decompose("pathlib.Path.read_text")
    mod, cls, fun = decompose("pathlib.Path.read_bytes")
    mod, cls, fun = decompose("importlib.machinery.FileFinder.find_spec")
    mod, cls, fun = decompose("builtins.open")
    mod, cls, fun = decompose("zimport.util.zip.is_ziparchive_deep")
    mod, cls, fun = decompose("zimport.util.zip.ZipReader.open_resource")
    print('----------')
    pass

'''
----------
[INF] [pathlib] == m[pathlib] c[] f[]
[INF] [pathlib.Path] == m[pathlib] c[Path] f[]
[INF] [pathlib.Path.read_text] == m[pathlib] c[Path] f[read_text]
[INF] [pathlib.Path.read_bytes] == m[pathlib] c[Path] f[read_bytes]
[INF] [importlib.machinery.FileFinder.find_spec] == m[importlib.machinery] c[FileFinder] f[find_spec]
[INF] [builtins.open] == m[builtins] c[] f[open]
[INF] [zimport.util.zip.is_ziparchive_deep] == m[zimport.util.zip] c[] f[is_ziparchive_deep]
[INF] [zimport.util.zip.ZipReader.open_resource] == m[zimport.util.zip] c[ZipReader] f[open_resource]
----------
'''