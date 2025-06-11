#-------------------------------------------------------------------------------
# zimport v0.1.10 20250611
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------
# refer to https://stackoverflow.com/questions/57651488/how-to-understand-pythons-module-lookup
# refer to https://docs.python.org/3/reference/import.html#the-meta-path
# refer to https://peps.python.org/pep-0302/

__version__ = '0.1.10'

import io, os, sys, importlib, time, shutil
import ctypes
import pathlib
import builtins, tokenize

from .main_impl import hook_fileio
from .main_impl import detour
from .main_impl import extract
from .util.path import path_exists_native, find, exists, slashpath
# from .util.cache import init_cached_dir, get_cached_dir, encache_path, decache_path
from .util import cache

import zimport.util.cache as CACHE
import zimport.util.zip as ZIP

DBG = False

from . import main_impl
from . import pathfinder
from . import pathfinder_impl

def debug(debug=True) :
    global DBG
    DBG = debug
    main_impl.DBG = debug
    pathfinder.DBG = debug
    pathfinder_impl.DBG = debug
    from .util import zip
    from .util import bootstrap
    from .util import path
    from .util import compile
    bootstrap.DBG = debug
    compile.DBG = debug


########################################





########################################

PY_VERSION_NUM = f"{sys.version_info.major}{sys.version_info.minor}"
PY_CACHESURFIX = '.cpython-' + PY_VERSION_NUM
#PYPYD_SUFFIXES = [s[0] for s in imp.get_suffixes() if s[2] == imp.C_EXTENSION] # imp deprecated since version 3.4, removed in version 3.12.
PYPYD_SUFFIXES = importlib.machinery.EXTENSION_SUFFIXES
#print(f"PYPYD_SUFFIXES ::: {PYPYD_SUFFIXES}") # ex) PYPYD_SUFFIXES ::: ['.cp311-win_amd64.pyd', '.pyd']

class zimport(object):
    __instance__ = None

    def __new__(cls, *args, **kwargs):
        if hasattr(cls, "_instance"): return cls._instance
        if False : print(f"invoke as singletone(__new__) ::: {cls.__name__}")
        cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        cls = type(self)
        if hasattr(cls, "_init"): return
        if False : print(f"invoke as singletone(__init__) ::: {cls.__name__}")
        cls._init = True
        zimport.__instance__ = self

        print(f"[INF] zimport installed {__version__} ...", file=sys.stderr)

        if cache.CACHE_DIR_ROOT is None : cache.init_cached_dir()
        self.ZIP_REG_NAMES = set()
        self.ZIP_NTRY_INFO = {}
        self.ZIP_STAT_INFO = {}
        self.ZIP_NTRY_TREE = {}
        self.install_hook()
        self.install_thirdparty_support_pip()
        self.install_importer()


    def install_hook(self):
        builtins.open = hook_fileio(self, "builtins.open", True, False, builtins.open)
        os.stat = hook_fileio(self, "os.stat", True, False, os.stat)
        if os.name == "nt" : os.add_dll_directory = hook_fileio(self, "os.add_dll_directory", True, True, os.add_dll_directory)
        if os.name == "nt" : ctypes.WinDLL = hook_fileio(self, "ctypes.WinDLL", True, True, ctypes.WinDLL)
        ctypes.CDLL = hook_fileio(self, "ctypes.CDLL", True, True, ctypes.CDLL)
        pathlib.Path.read_text = hook_fileio(self, "pathlib.Path.read_text", False, True, pathlib.Path.read_text)
        pathlib.Path.read_bytes = hook_fileio(self, "pathlib.Path.read_bytes", False, True, pathlib.Path.read_bytes)

        detour(self, "tokenize._builtin_open")
        detour(self, "importlib.machinery.FileFinder.find_spec")
        detour(self, "os.path.exists")
        detour(self, "os.path.isdir")
        detour(self, "os.path.isfile")
        detour(self, "os.listdir")
        detour(self, "os.path.join")
        detour(self, "os.path.dirname")
        pass

    def install_importer(self):
        from zimport import pathfinder
        sys.path_importer_cache.clear() # very important, if disable occur happen ghost effect, ie, debug mode sucess, normal mode fail
        sys.path_hooks.insert(0, pathfinder.PathFinder)
        pass

    def install_thirdparty_support_pip(self):
        try :
            from zimport import pathfinder
            from pip._vendor.distlib import resources # pip support
            sys.path_importer_cache.clear() # very important, if disable occur happen ghost effect, ie, debug mode sucess, normal mode fail
            resources._finder_registry[pathfinder.PathFinder] = resources.ZipResourceFinder
        except :
            pass
        pass

    ####

    def cached_dir(self, path) : # a/b/c.z/d to library.dir/.cache/a/b/c.z/d
        return cache.get_cached_dir(path)

    ####

    def getentries(self, zip) : # path must be .z/.zip file path with all unix separator '/' not '\'
        if zip in self.ZIP_NTRY_INFO :
            zent = self.ZIP_NTRY_INFO[zip]
            return zent
        else :
            if DBG: print(f"[INF] new zip-archive {zip} ::: {zip}")
            self.addarchive(zip)
            zent = self.ZIP_NTRY_INFO[zip]
            return zent

    def addarchive(self, zip) : # path must be .z/.zip file path with all unix separator '/' not '\'
        try :
            if zip in self.ZIP_NTRY_INFO :
                print(f"[ERR] already has ntry {zip}", file=sys.stderr)
            if zip in self.ZIP_STAT_INFO :
                print(f"[ERR] already has stat {zip}", file=sys.stderr)
            ntry, stat, tree = ZIP.zipinfo(zip)
            self.ZIP_REG_NAMES.add(zip)
            self.ZIP_NTRY_INFO[zip] = ntry
            self.ZIP_STAT_INFO[zip] = stat
            self.ZIP_NTRY_TREE[zip] = tree
            self.addsystempath(zip, ntry.keys())
        except Exception as e :
            print(f"[ERR] addarchive {zip} ::: {e}", file = sys.stderr)

    def fixarchive(self, zip) :
        try:
            ntry, stat, tree = ZIP.zipinfo(zip)
            self.ZIP_NTRY_INFO[zip] = ntry
            self.ZIP_STAT_INFO[zip] = stat
            self.ZIP_NTRY_TREE[zip] = tree
        except :
            self.ZIP_NTRY_INFO.pop(zip, None)
            self.ZIP_STAT_INFO.pop(zip, None)
            self.ZIP_NTRY_TREE.pop(zip, None)

    def addsystempath(self, zip, ent) :
        def path(p): f = builtins.open(p); n = f.name; f.close(); return n.replace('\\', '/')
        unq = set()
        lst = [p for p in ent if p.endswith(".pyd")]
        tmp = [p.replace(PYPYD_SUFFIXES[0], '').replace('/', '.') for p in lst]
        for idx in range(len(lst)):
            pyd = lst[idx]  # a/b/c.cp311-win_amd64.pyd'
            dot = tmp[idx]  # a.b.c
            pth = zip + "/" + pyd  # zipped path. ie, library.dir/x.y.z/a/b/c.cp311-win_amd64.pyd
            pth = path(zip + "/" + pyd)  # cached path. ie, library.dir/.cache/x.y.z/a/b/c.cp311-win_amd64.pyd
            unq.add(os.path.dirname(pth))
        lst = [p for p in ent if (p.endswith(".dll") or p.endswith(".so") or (".so." in p) or p.endswith(".dylib") or p.endswith(".exe"))] # or p.endswith(".pyx") or p.endswith(".pxd")
        tmp = [p.replace('/', '.') for p in lst]
        for idx in range(len(lst)):
            dll = lst[idx]  # a/b/c.dll'
            dot = tmp[idx]  # a.b.c
            pth = zip + "/" + dll  # zipped path. ie, library.dir/x.y.z/a/b/c.dll
            pth = path(zip + "/" + dll)  # cached path. ie, library.dir/.cache/x.y.z/a/b/c.dll
            # unq.add(os.path.dirname(pth)) # resource problem here ~~~
        if 0 < len(unq):
            for dir in unq:
                if os.name == "nt" : os.add_dll_directory(dir) # if too many call, will see an err
                addsyspath(os.path.abspath(dir) if os.name == "nt" else dir) # is this absolutely necessary?
                if False and DBG : print(f"[INF] add PATH [{dir}]")

        for dir in [p for p in sys.path if not (p.endswith(".z") or p.endswith(".zip"))]: addsyspath(os.path.abspath(dir) if os.name == "nt" else dir)
        addsyspath(os.path.abspath(os.path.dirname(sys.executable)))  # python.exe installed dir
        addsyspath(os.path.abspath(os.path.dirname(sys.executable) + "/library/bin"))
        if False and DBG :
            paths = os.environ["PATH"].split(';' if os.name == "nt" else ':')
            for i in range(len(paths)) :
                print(f"[PATH][{i}] : {paths[i]}")

    def encache_path(self, org_path) :
        return cache.encache_path(self.ZIP_REG_NAMES, org_path)

    def decache_path(self, cac_path) :
        return cache.decache_path(self.ZIP_REG_NAMES, cac_path)

    def invalidate_caches(self) :
        invalidate_caches()

    def register_hook(self, hookname, org_func, hookfunc) :
        return register_hook(hookname, org_func, hookfunc)

def addsyspath(path) : # must be check, Is this absolutely necessary?
    try:
        paths = os.environ["PATH"].split(';' if os.name == "nt" else ':')
        if not (path in paths):
            os.environ["PATH"] += path + (';' if os.name == "nt" else ':')
            if DBG : print(f"[INF] add PATH [{path}]")
        pass
    except Exception as e:
        if False: traceback.print_exc()
        if DBG: print(f"[INF:::addsyspath@zimport] failed [{e}] with [{path}] ...", file=sys.stderr)

# cacheofpath = dict()
# def encache_path(ziparchive, org_path):
#     if org_path in cacheofpath: return cacheofpath[org_path]  # search cache
#     abs_path = os.path.abspath(org_path)
#     unixpath = abs_path.replace('\\', '/')
#     zip_path = ''
#     ent_path = ''
#     for p in ziparchive:
#         if unixpath.startswith(p):  # a.zip/a/b/c.x startswith a.zip
#             zip_path = p
#             ent_path = unixpath.replace(''.join([p, '/']), '')  # ent_path = unixpath.replace(p + '/', '')
#             break
#     new_path = '/'.join([cached_dir(zip_path), ent_path])  # new_path = cachedir(zip_path) + '/' + ent_path
#     new_path = os.path.abspath(new_path).replace('\\', '/')
#     cacheofpath[org_path] = zip_path, ent_path, new_path  # save cache
#     return zip_path, ent_path, new_path

def encache_path_static(zip_file, org_file):
    abs_path = os.path.abspath(org_file)
    unixpath = abs_path.replace('\\', '/')
    zip_path = ''
    ent_path = ''
    if unixpath.startswith(zip_file):  # a.zip/a/b/c.x startswith a.zip
        zip_path = zip_file
        ent_path = unixpath.replace(''.join([zip_file, '/']), '')  # ent_path = unixpath.replace(p + '/', '')
    new_path = '/'.join([cache.get_cached_dir(zip_path), ent_path])  # new_path = cachedir(zip_path) + '/' + ent_path
    new_path = os.path.abspath(new_path).replace('\\', '/')
    return zip_path, ent_path, new_path

def invalidate_caches():
    if False : print(f"[INF] invalidate_caches ...")
    if True : sys.path_importer_cache.clear()
    if False : importlib.invalidate_caches()   # very danger code
    # cacheofpath.clear()

######################################## instance of singleton

def getInstance() :
    if zimport.__instance__ is None: zimport()
    return zimport.__instance__

def install() :
    return getInstance()

def uninstall() :
    if zimport.__instance__ is None : return
    if sys.path_hooks[0].__qualname__  != "PathFinder" : return
    sys.path_hooks.remove(sys.path_hooks[0])
    cls = type(zimport.__instance__)
    delattr(cls, "_instance")
    delattr(cls, "_init")
    zimport.__instance__ = None
    restore_hook()
    sys.path_importer_cache.clear()
    pass

hookforfunc = dict()
def register_hook(hookname, org_func, hookfunc) :
    hookforfunc[hookname] = org_func, hookfunc
    pass

import zimport.util.module as module
def restore_hook() :
    for k, v in hookforfunc.items() :
        mod, clz, fun = module.decompose(k)
        module.set(mod, clz, fun, v[0]) # restore v[0] (original func)
    hookforfunc.clear()
    pass

######################################## cache directory

def zimport_set_cache_dir(path) :
    global CACHE_DIR_ROOT
    if not path_exists_native(path) :
        os.makedirs(path, exist_ok=True)
    CACHE_DIR_ROOT = path
    pass

def zimport_clear_cache() :
    global CACHE_DIR_ROOT
    if not path_exists_native(CACHE_DIR_ROOT) : return
    for f in os.listdir(CACHE_DIR_ROOT):
        try:
            path = os.path.join(CACHE_DIR_ROOT, f)
            shutil.rmtree(path)
        except Exception :
            pass


######################################## manual extract entry to cache directory

def zimport_extract_to_cache(zip, dir, debug=True) : # preload
    zip = os.path.abspath(zip).replace('\\','/')
    dir = dir.replace('\\','/')
    pth = None
    ntry, stat, tree = ZIP.zipinfo(zip)
    lst = ntry
    lst = [zip + "/" + p for p in lst if p.startswith(dir)]
    for f in lst:
        if f.endswith('/') : continue # is directory
        zip_path, ent_path, new_path = encache_path_static(zip, f)
        extract(zip_path, cache.get_cached_dir(zip_path), ent_path)
        if pth is None :
            pth = new_path if len(lst) == 1 else os.path.dirname(new_path)
        if debug :print("[INF::extract] {}".format(new_path), file=sys.stderr)
    if not pth : print(f"[ERR::extract] cannot found entry [{dir}]", file=sys.stderr)
    return pth

######################################## deprecated function

def precache_directory_deprecated(dir, debug=True) : # preload
    zim = getInstance()
    dir = dir.replace('\\','/')
    pth = None
    if zim is None : print("[ERR] try zimport.install() ...", file=sys.stderr); return None
    def copy(p) : f = builtins.open(p); n = f.name; f.close(); return n.replace('\\', '/')
    for z in zim.ZIP_NTRY_INFO:
        lst = zim.ZIP_NTRY_INFO[z]
        lst = [z + "/" + p for p in lst if p.startswith(dir)]
        for fle in lst:
            if fle.endswith('/') : continue # is directory
            out = copy(fle)
            if pth is None : pth = os.path.dirname(out)
            if debug :print("[COPY:::dir] {}".format(out), file=sys.stderr)
        if 0 < len(lst) :
            break
    if not pth :
        print(f"[COPY:::dir] cannot found directory {dir}", file=sys.stderr)
    return pth

def precache_dll_deprecated(dll, debug=True) : # preload pyd, dll, so
    zim = getInstance()
    fle = dll.replace('\\','/')
    pth = None
    if zim is None : print("[ERR] try zimport.install() ...", file=sys.stderr); return None
    def copy(p) : f = builtins.open(p); n = f.name; f.close(); return n.replace('\\', '/')
    for z in zim.ZIP_NTRY_INFO:
        lst = zim.ZIP_NTRY_INFO[z]
        lst = [z + "/" + p for p in lst if (p.endswith(".dll") or p.endswith(".so") or (".so." in p) or p.endswith(".dylib") or p.endswith(".pyd") or p.endswith(".exe"))]
        lst = [z + "/" + p for p in lst if p.endswith(fle)]
        for fle in lst:
            pth = copy(fle)
            if debug : print("[COPY:::dll] {}".format(pth), file=sys.stderr)
            if False : ctypes.WinDLL(pth) # preload test
        if 0 < len(lst) :
            break
    if not pth :
        print(f"[COPY:::dir] cannot found dll {dll}", file=sys.stderr)
    return pth



