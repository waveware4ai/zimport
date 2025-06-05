#-------------------------------------------------------------------------------
# zimport v0.1.8 20250607
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
    sep = funcpath.split(".")
    mod = None
    cls = None
    fun = None
    for i in range(len(sep)-1) :
        try :
            head = '.'.join(sep[:i+1])
            tail = sep[i+1]
            cur_is_m = ismod(head)
            if cur_is_m : mod = getmod(head)
            cur_is_c = isclz(head, tail)
            if cur_is_c : cls = getclz(head, tail)
            cur_is_f = isfun(cls if cls is not None else mod, tail)
            if cur_is_f : fun = tail

            if DBG :print(f"[{i}] [{head}/{tail}] m[{cur_is_m}] c[{cur_is_c}] f[{cur_is_f}]")
        except Exception as e:
            pass
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
    mod, cls, fun = decompose("pathlib.Path.read_text")
    print('----------')
    mod, cls, fun = decompose("pathlib.Path.read_bytes")
    print('----------')
    mod, cls, fun = decompose("importlib.machinery.FileFinder.find_spec")
    print('----------')
    mod, cls, fun = decompose("builtins.open")
    print('----------')
    pass

