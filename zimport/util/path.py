#-------------------------------------------------------------------------------
# zimport v0.1.10 20250611
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------
import os, sys, time, timeit
import io, _io
# import _frozen_importlib as _bootstrap
# import _frozen_importlib_external as _bootstrap_external
from importlib import _bootstrap
from importlib import _bootstrap_external
import pathlib
import _frozen_importlib_external

def slashpath(p : object) -> str:
    if False : pass
    elif (type(p) is str) : pass
    elif (type(p) is pathlib.PosixPath) :
        p = p.as_posix() # must be check
    elif (type(p) is pathlib.WindowsPath) :
        p = p.as_posix()
    elif (type(p) is _frozen_importlib_external.FileFinder) : p = p.path
    else :
        print(f"[ERR:::slashpath@path] --- !!! @@@ ### must be check path [{p}]", file=sys.stderr)

    a = os.path.abspath(p)
    u = a.replace('\\', '/') # to unix '/' path
    return u

def path_exists_native(p) : # exists directory or file
    try : # refer to https://happytest-apidoc.readthedocs.io/en/latest/_modules/_frozen_importlib_external/
        stat = _bootstrap_external._path_stat(p)
        return True
    except :
        return False

def path_split(path):
    head, _, tail = path.rpartition('/')
    return head, tail

def path_join(*path_parts):
    return '/'.join([part.rstrip('/') for part in path_parts if part])

def virtual_path_split(p) : #
    # for benchmark, https://stackoverflow.com/questions/28859095/most-efficient-method-to-check-if-dictionary-key-exists-and-process-its-value-if
    if p is None or len(p) == 0 : print(f"[ERR] invalid path {p!r}");  return '', ''
    real = p.rstrip('/')  # real file in filesystem, generally .zip/.z
    virt = []             # virtual path, dir/file
    while True :
        if path_exists_native(real) :
            return real, '/'.join(virt) # ex, a/b/c.z/d to a/b/c.z and d
        else :
            dir, _, sub = real.rpartition('/')
            real = dir
            virt.insert(0, sub)
            if len(real) == 0 : return real, '/'.join(virt) # error! ie, a/b/c.z/d to '' and a/b/c.z/d

def find(path) :
    dir = None
    if   os.path.exists(__file__ + "/./" + path)              : dir = os.path.abspath(__file__ + "/./" + path).replace('\\', '/')
    elif os.path.exists(__file__ + "/../" + path)             : dir = os.path.abspath(__file__ + "/../" + path).replace('\\', '/')
    elif os.path.exists(__file__ + "/../../" + path)          : dir = os.path.abspath(__file__ + "/../../" + path).replace('\\', '/')
    elif os.path.exists(__file__ + "/../../../" + path)       : dir = os.path.abspath(__file__ + "/../../../" + path).replace('\\', '/')
    elif os.path.exists(__file__ + "/../../../../" + path)    : dir = os.path.abspath(__file__ + "/../../../../" + path).replace('\\', '/')
    elif os.path.exists(__file__ + "/../../../../../" + path) : dir = os.path.abspath(__file__ + "/../../../../../" + path).replace('\\', '/')
    return dir

def exists(base : str, dirs : list, name : str) :
    for d in dirs :
        p = os.path.abspath('/'.join([base, d, name])).replace('\\', '/')
        if os.path.exists(p) :
            return p
    return None
