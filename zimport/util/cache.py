#-------------------------------------------------------------------------------
# zimport v0.1.10 20250611
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------
import os, sys, shutil
if not os.path.dirname(__file__) in sys.path : sys.path.append(os.path.dirname(__file__))
import typing # typing added in version 3.5, https://docs.python.org/3/library/typing.html

from path import exists, slashpath, path_exists_native

CACHE_DIR_NAME = '.cache'
CACHE_DIR_ROOT = None

def init_cached_dir() :
    global CACHE_DIR_ROOT
    if "PROJECT_HOME" in os.environ :
        FROM_STRING = "os.environ['PROJECT_HOME']"
        os.environ["PROJECT_HOME"] = os.environ["PROJECT_HOME"].replace('\"', '') # remove '"'
        CACHE_DIR_ROOT = exists(os.environ["PROJECT_HOME"], ['.', '..', 'lib', 'lib/site-packages'], CACHE_DIR_NAME)
        if CACHE_DIR_ROOT is None : CACHE_DIR_ROOT = os.environ["PROJECT_HOME"] + '/' + CACHE_DIR_NAME
    else :
        FROM_STRING = "os.path.dirname(sys.executable)"
        CACHE_DIR_ROOT = exists(os.path.dirname(sys.executable), ['.', '..', 'lib', 'lib/site-packages'], CACHE_DIR_NAME)
        if CACHE_DIR_ROOT is None : CACHE_DIR_ROOT = os.path.dirname(sys.executable) + '/' + CACHE_DIR_NAME

    CACHE_DIR_ROOT = slashpath(CACHE_DIR_ROOT)
    if not path_exists_native(CACHE_DIR_ROOT) : os.makedirs(CACHE_DIR_ROOT, exist_ok=True)
    print(f"[INF] zimport cache_dir ::: [{CACHE_DIR_ROOT}] from {FROM_STRING}", file=sys.stderr)

def set_cached_dir(path) :
    global CACHE_DIR_ROOT
    path = slashpath(path)
    if not CACHE_DIR_NAME in path :
        print(f"[INF:::cache] name of the path should be the /{CACHE_DIR_NAME} as the last path. ...", file=sys.stderr)
        return
    if not path_exists_native(path) : os.makedirs(path, exist_ok=True)
    CACHE_DIR_ROOT = path
    pass

def del_cached_dir() :
    if not path_exists_native(CACHE_DIR_ROOT) : return
    for f in os.listdir(CACHE_DIR_ROOT):
        try:
            path = os.path.join(CACHE_DIR_ROOT, f)
            shutil.rmtree(path)
        except Exception :
            pass

def get_cached_dir(path) : # a/b/c.z/d to library.dir/.cache/a/b/c.z/d
    if path is None : print(f"[ERR:::cache] invalid get_cached_dir [{path}] ... ", file=sys.stderr); return None
    z = path[path.rfind('/'):]               # drv:/a/b/c.z to /c.z
    if CACHE_DIR_ROOT :
        return slashpath(''.join([CACHE_DIR_ROOT, z]))
    else :
        return slashpath(''.join([path, '/../', CACHE_DIR_NAME, z]))

########################################
bankofpath = dict()
def clear_bank() -> None :
    bankofpath.clear()

def encache_path(ziparchive, path : str) -> tuple: # convert to en-cache path
    if path in bankofpath: return bankofpath[path]
    unxpath = slashpath(path)     # to drv:/1/2/3/x.zip/a/b/c
    zippath = None                # drv:/1/2/3/x.zip
    entpath = None                # a/b/c
    newpath = None                # to drv:/work/.cache/x.zip/a/b/c
    for p in ziparchive:
        if unxpath.startswith(p): # x.zip/a/b/c.x startswith a.zip
            zippath = p
            entpath = unxpath.replace(''.join([p, '/']), '') if unxpath != p else ''
            break
    newpath = None if zippath is None else ('/' if entpath != '' else '').join([get_cached_dir(zippath), entpath])
    if newpath is None :
        print(f"[ERR:::cache] invalid encache path [{path}] ... ", file=sys.stderr); return None, None, path
    bankofpath[path] = zippath, entpath, newpath  # save cache
    return zippath, entpath, newpath

def decache_path(ziparchive, path) -> tuple : # convert to de-cache path
    if path in bankofpath: return bankofpath[path]
    unxpath = slashpath(path)                                                   # to drv:/work/.cache/x.zip/a/b/c
    tmppath = unxpath[unxpath.rfind(CACHE_DIR_NAME) + len(CACHE_DIR_NAME) + 1:] # to x.zip/a/b/c
    z, _, e = tmppath.partition('/')  # to x.zip + / + a/b/c
    zippath = None                    # drv:/1/2/3/x.zip
    entpath = e                       # a/b/c
    newpath = None                    # drv:/1/2/3/x.zip + / + a/b/c
    for p in ziparchive :
        if p.endswith(z) :            # x.zip endswith drv:/1/2/3/x.zip
            zippath = p
            newpath = ('/' if entpath != '' else '').join([zippath, entpath])
            break
    if newpath is None : 
        print(f"[ERR:::cache] invalid decache path [{path}] ... ", file=sys.stderr); return None, None, path
    bankofpath[path] = zippath, entpath, newpath  # save cache
    return zippath, entpath, newpath

########################################

def _test(path : str) :
    # path = slashpath(path)
    zips = ['c:/a/b.zip', 'c:/1/2/3/x.zip', 'c:/1/2/3/x.z']
    encp = encache_path(zips, path)[2]
    decp = decache_path(zips, encp)[2]
    print(f"[{path}] to [{encp}] to [{decp}]")
    pass

import times
if __name__ == '__main__':
    init_cached_dir()
    stt = times.current_milli()
    print('----------')
    _test('c:\\1\\2\\3\\x.zip\\a\\b\\c')
    _test('c:\\1\\2\\3\\x.zip\\a\\b\\c\\')
    _test('c:/1\\2//3\\x.z\\a\\b\\\\c\\\\')
    _test('c:\\1\\2\\3\\x.zip')
    _test('c:\\1\\2\\3\\x.zip\\')
    _test('c:\\1\\2\\3\\x.z\\\\')
    print('----------')
    end = times.current_milli()
    print(f"[INF] elapsed time {(end - stt)} ms ...")
    pass

"""
[INF] zimport cache_dir ::: [W:/src.zimport.p12/.cache] from os.environ['PROJECT_HOME']
[c:\\1\\2\\3\\x.zip\\a\\b\\c] to [W:/src.zimport.p12/.cache/x.zip/a/b/c] to [c:/1/2/3/x.zip/a/b/c]
[c:\\1\\2\\3\\x.zip\\a\\b\\c\\] to [W:/src.zimport.p12/.cache/x.zip/a/b/c] to [c:/1/2/3/x.zip/a/b/c]
[c:\\1\\2\\3\\x.zip\\a\\b\\\\c\\\\] to [W:/src.zimport.p12/.cache/x.zip/a/b/c] to [c:/1/2/3/x.zip/a/b/c]
[c:\\1\\2\\3\\x.zip] to [W:/src.zimport.p12/.cache/x.zip] to [c:/1/2/3/x.zip]
[c:\\1\\2\\3\\x.zip\\] to [W:/src.zimport.p12/.cache/x.zip] to [c:/1/2/3/x.zip]
[c:\\1\\2\\3\\x.zip\\\\] to [W:/src.zimport.p12/.cache/x.zip] to [c:/1/2/3/x.zip]
[INF] elapsed time 0 ms ...
"""