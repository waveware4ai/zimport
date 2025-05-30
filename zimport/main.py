#-------------------------------------------------------------------------------
# zimport v0.1.4 20250531
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------
# refer to https://stackoverflow.com/questions/57651488/how-to-understand-pythons-module-lookup
# refer to https://docs.python.org/3/reference/import.html#the-meta-path
# refer to https://peps.python.org/pep-0302/

import io, os, sys, importlib, time
import ctypes
import pathlib
import builtins, tokenize

from .main_impl import hook_fileio
from .main_impl import detour
from .util.path import path_exists_native, find
from .util.zip import zipstaties
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

CACHE_DIR_ROOT = None 

def set_cache_dir(path) :
    global CACHE_DIR_ROOT
    CACHE_DIR_ROOT = path
    if not path_exists_native(CACHE_DIR_ROOT) :
        os.makedirs(CACHE_DIR_ROOT, exist_ok=True)    

def auto_cache_dir() :
    global CACHE_DIR_ROOT
    if "PROJECT_HOME" in os.environ :
        FROM_STRING = "os.environ['PROJECT_HOME']"
        os.environ["PROJECT_HOME"] = os.environ["PROJECT_HOME"].replace('\"', '')
        if path_exists_native(os.path.dirname(os.environ["PROJECT_HOME"]) + '/' + ".cache") : # if find subdir/.cache
            os.environ["PROJECT_HOME"] = os.path.abspath(os.path.dirname(os.environ["PROJECT_HOME"])).replace('\\', '/')
        CACHE_DIR_ROOT = os.environ["PROJECT_HOME"] + '/' + ".cache"
    elif find(".cache") :
        FROM_STRING = "find('.cache')"
        CACHE_DIR_ROOT = find(".cache")
    else :
        FROM_STRING = "os.path.dirname(sys.executable)"
        CACHE_DIR_ROOT = os.path.dirname(sys.executable) + "/.cache" # os.path.dirname(sys.executable) + "/../.cache" 
    
    CACHE_DIR_ROOT = CACHE_DIR_ROOT.replace('\\', '/')
    print(f"[INF] zimport cache_dir ::: [{CACHE_DIR_ROOT}] from {FROM_STRING}", file=sys.stderr)
    if not path_exists_native(CACHE_DIR_ROOT) :
        os.makedirs(CACHE_DIR_ROOT, exist_ok=True)

def cached_dir(path) : # a/b/c.z/d to library.dir/.cache/a/b/c.z/d
    # if CACHE_DIR_ROOT is None : auto_cache_dir()
    z = path[path.rfind('/'):] # path = c:/a/b/c.z, z = /c.z
    p = None
    if CACHE_DIR_ROOT :
        p = ''.join([CACHE_DIR_ROOT, z])
    else :
        p = ''.join([path, "/../", ".cache", z])
    return p

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

        print("[INF] zimport installed ...", file=sys.stderr)
        if CACHE_DIR_ROOT is None : auto_cache_dir()
        self.ZIP_REG_NAMES = set()
        self.ZIP_NTRY_INFO = {}
        self.ZIP_STAT_INFO = {}
        self.install_hook()
        self.install_thirdparty_support_pip()
        self.install_importer()


    def install_hook(self):
        builtins.open = hook_fileio(self, "open", True, False, builtins.open)
        os.stat = hook_fileio(self, "stat", True, False, os.stat)
        if os.name == "nt" : os.add_dll_directory = hook_fileio(self, "adll", True, True, os.add_dll_directory)  # for torch, numpy
        if os.name == "nt" : ctypes.WinDLL = hook_fileio(self, "wdll", True, True, ctypes.WinDLL)  # for scipy
        ctypes.CDLL = hook_fileio(self, "cdll", True, True, ctypes.CDLL)
        pathlib.Path.read_text = hook_fileio(self, "read (path)", False, True, pathlib.Path.read_text)  # for sklearn
        pathlib.Path.read_bytes = hook_fileio(self, "bytes(path)", False, True, pathlib.Path.read_bytes)
        tokenize._builtin_open = builtins.open # 20250520 torch/_dynamo/config.py patch
        importlib.machinery.FileFinder.find_spec = detour(self, "FileFinder.find_spec", importlib.machinery.FileFinder.find_spec)

        os.path.exists = detour(self, "os.path.exists", os.path.exists)  # ...
        #os.path.dirname = detour(self, "os.path.dirname", os.path.dirname)  # ...
        #os.path.realpath  = detour(self, "os.path.realpath", os.path.realpath) # ...
        #os.listdir = detour(self, "os.listdir", os.listdir) # 20250521 transformers patch
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
        return cached_dir(path)

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
            ntry, stat = ZIP.zipentriesbycase(zip, True, False, True, False)
            self.ZIP_REG_NAMES.add(zip)
            self.ZIP_NTRY_INFO[zip] = ntry
            self.ZIP_STAT_INFO[zip] = stat
            self.addsystempath(zip, ntry.keys())
        except Exception as e :
            print(f"[ERR] addarchive {zip} ::: {e}", file = sys.stderr)

    def fixarchive(self, zip) :
        try:
            ntry, stat = ZIP.zipentriesbycase(zip, True, False, True, False)
            self.ZIP_NTRY_INFO[zip] = ntry
            self.ZIP_STAT_INFO[zip] = stat
        except :
            self.ZIP_NTRY_INFO.pop(zip, None)
            self.ZIP_STAT_INFO.pop(zip, None)

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
        lst = [p for p in ent if (p.endswith(".dll") or p.endswith(".so") or (".so." in p) or p.endswith(".dylib") or p.endswith(".exe"))]
        tmp = [p.replace('/', '.') for p in lst]
        for idx in range(len(lst)):
            dll = lst[idx]  # a/b/c.dll'
            dot = tmp[idx]  # a.b.c
            pth = zip + "/" + dll  # zipped path. ie, library.dir/x.y.z/a/b/c.dll
            pth = path(zip + "/" + dll)  # cached path. ie, library.dir/.cache/x.y.z/a/b/c.dll
            unq.add(os.path.dirname(pth))
        if 0 < len(unq):
            for dir in unq:
                if os.name == "nt" : os.add_dll_directory(dir)
                addsyspath(os.path.abspath(dir) if os.name == "nt" else dir)
                if DBG : print("[INF] add PATH [" + dir + "]")

        for dir in [p for p in sys.path if not (p.endswith(".z") or p.endswith(".zip"))]: addsyspath(os.path.abspath(dir) if os.name == "nt" else dir)
        addsyspath(os.path.abspath(os.path.dirname(sys.executable)))  # python.exe installed dir
        addsyspath(os.path.abspath(os.path.dirname(sys.executable) + "/library/bin"))
        if DBG : 
            paths = os.environ["PATH"].split(';' if os.name == "nt" else ':')
            for i in range(len(paths)) :
                print(f"[PATH][{i}] : {paths[i]}")

    def path_maker(self, org_path) :
        return path_maker(self.ZIP_REG_NAMES, org_path)

    def invalidate_caches(self) :
        invalidate_caches()

########################################


def install() :
    return getInstance()

def getInstance() : 
    if zimport.__instance__ is None: zimport()
    return zimport.__instance__


######################################## part of sys.path

cacheofpath = dict()

def invalidate_caches():
    if False : print(f"[INF] invalidate_caches ...")
    if True : sys.path_importer_cache.clear()
    if False : importlib.invalidate_caches()   # danger code
    cacheofpath.clear()

def path_maker(ziparchive, org_path):
    if org_path in cacheofpath: return cacheofpath[org_path]  # search cache
    abs_path = os.path.abspath(org_path)
    unixpath = abs_path.replace('\\', '/')
    zip_path = ''
    ent_path = ''
    for p in ziparchive:
        if unixpath.startswith(p):  # a.zip/a/b/c.x startswith a.zip
            zip_path = p
            ent_path = unixpath.replace(''.join([p, '/']), '')  # ent_path = unixpath.replace(p + '/', '')
            break
    new_path = '/'.join([cached_dir(zip_path), ent_path])  # new_path = cachedir(zip_path) + '/' + ent_path
    new_path = os.path.abspath(new_path).replace('\\', '/')
    cacheofpath[org_path] = zip_path, ent_path, new_path  # save cache
    return zip_path, ent_path, new_path

# def getsyspath():
#     ziparchive = []
#     zipentries = dict()
#     for p in sys.path:
#         if os.path.isfile(p) and (p.endswith(".z") or p.endswith(".zip")):
#             zip = zipfile.ZipFile(p)
#             zipentries[p.replace('\\', '/')] = zip.namelist()
#             zip.close()
#             ziparchive.append(p.replace('/', '\\'))
#             ziparchive.append(p.replace('\\', '/'))
#     return ziparchive, zipentries

def addsyspath(path) :
    paths = os.environ["PATH"].split(';' if os.name == "nt" else ':')
    if not (path in paths) :
        os.environ["PATH"] += path + (';' if os.name == "nt" else ':')
        if False : print(f"[INF] add PATH : {path}")

def precache_dll(dll, debug=True) : # preload pyd, dll, so
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

def precache_file(fle, debug=True) : # preload
    zim = getInstance()
    fle = fle.replace('\\','/')
    pth = None
    if zim is None : print("[ERR] try zimport.install() ...", file=sys.stderr); return None
    def copy(p) : f = builtins.open(p); n = f.name; f.close(); return n.replace('\\', '/')
    for z in zim.ZIP_NTRY_INFO:
        lst = zim.ZIP_NTRY_INFO[z]
        lst = [z + "/" + p for p in lst if p.endswith(fle)]
        for fle in lst:
            pth = copy(fle)
            if debug :print("[COPY::file] {}".format(pth), file=sys.stderr)
        if 0 < len(lst) :
            break
    if not pth :
        print(f"[COPY::file] cannot found file {fle}", file=sys.stderr)
    return pth

def precache_directory(dir, debug=True) : # preload
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
