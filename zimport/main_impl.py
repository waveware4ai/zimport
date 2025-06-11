#-------------------------------------------------------------------------------
# zimport v0.1.10 20250611
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------
import io, os, sys, time, shutil, builtins
import zipfile
import pathlib
from .util.path import path_exists_native, slashpath, find

DBG = False

########################################

ZIP_IMPORTED_STRING = [".z/", ".zip/", ".z\\", ".zip\\"]
# ZIP_IMPORTED_STRING = [".z/", ".z\\"]
ZIP_IMPORTED_CACHES = ["/.cache/", "\\.cache\\"]
def is_zip_path(path) : # return just true, path == a.zip/a/b/c.x
    if not any (tok in path for tok in ZIP_IMPORTED_STRING) : return False # if not (".z/" in path or ".zip/" in path or ".z\\" in path or ".zip\\" in path) : return False
    if any (tok in path for tok in ZIP_IMPORTED_CACHES) : return False
    return True

def is_cac_path(path) : # return just true, path == a.zip/a/b/c.x
    if not any (tok in path for tok in ZIP_IMPORTED_STRING) : return False
    if any (tok in path for tok in ZIP_IMPORTED_CACHES) : return True
    return False

########################################
def extract(zip_path, zip_cached_path, ent_path) :
    try:
        with zipfile.ZipFile(zip_path) as zip_file:
            zip_file.extract(ent_path, zip_cached_path)
    except FileNotFoundError:
        print(f"[HOOK:::zip][ERROR] zip file not found: {zip_path}", file=sys.stderr)
    except zipfile.BadZipFile:
        print(f"[HOOK:::zip][ERROR] bad zip file: {zip_path}", file=sys.stderr)
    except Exception as e:
        print(f"[HOOK:::zip][ERROR] extracting {ent_path} from {zip_path}: {e}", file=sys.stderr)

def extract_post(bin_path) :
    if not os.path.exists(bin_path) : return
    path_only = bin_path[:bin_path.rfind('/')] # a/b/c/d.exe to a/b/c
    name_only = bin_path[bin_path.rfind('/'):] # a/b/c/d.exe to /d.exe
    if name_only.endswith('.exe') :
        if ('ffmpeg' in name_only) : # case of ffmpeg-win-x86_64-v?.?.exe to ffmpeg.exe
            shutil.copy(bin_path, ''.join([path_only , '/ffmpeg.exe']))
    pass

########################################
def hook_fileio(zimport, name, is_string_path, is_stderr_print, orgfunc) :
    ZIP_NTRY_INFO = zimport.ZIP_NTRY_INFO
    ZIP_STAT_INFO = zimport.ZIP_STAT_INFO
    ZIPCACHED_DIR = zimport.cached_dir

    def funcwithstring(*args, **kwargs):
        claz = type(args[0])
        path = args[0]
        hook = orgfunc
        if claz is not str: return hook(*args, **kwargs)  # type of Path class
        if path.startswith('.'): return hook(*args, **kwargs)  # relative path
        if is_zip_path(path):
            args, ret = bypass(hook, name, *args, **kwargs)
            if DBG : print("[HOOK:z:zip] {} {}, {}".format(name, args, kwargs), file = sys.stderr if is_stderr_print else sys.stdout)
        else:
            ret = hook(*args, **kwargs)
            if DBG : print("[HOOK:x:org] {} {}, {}".format(name, args, kwargs), file = sys.stderr if is_stderr_print else sys.stdout)
        return ret

    def funcwithpath(*args, **kwargs):  # for sklearn
        path = args[0].as_posix()
        hook = orgfunc
        if path.startswith('.'): return hook(*args, **kwargs)  # relative path
        if is_zip_path(path):
            args, ret = bypass(hook, name, *args, **kwargs)
            if DBG : print("[HOOK:z:zip] {} {}, {}".format(name, args, kwargs), file = sys.stderr if is_stderr_print else sys.stdout)
        else:
            ret = hook(*args, **kwargs)
            if DBG : print("[HOOK:x:zip] {} {}, {}".format(name, args, kwargs), file = sys.stderr if is_stderr_print else sys.stdout)
        return ret

    def bypass(hook, name, *args, **kwargs):
        isString = True if type(args[0]) is str else False
        org_path = args[0]
        zip_path, ent_path, new_path = zimport.encache_path(org_path)
        if DBG : print(f"[HOOK:::zip] org_path [{org_path}] == [{zip_path}] + [{ent_path}]")
        if DBG : print(f"[HOOK:::zip] new_path [{new_path}]")
        if not zip_path in ZIP_NTRY_INFO :
            return args, hook(*args, **kwargs)
        zip_list = ZIP_NTRY_INFO[zip_path]
        isfolder = True if (''.join([ent_path, '/'])) in zip_list else False
        if not "stat" in name :
            if not path_exists_native(new_path):  # path_exists_native, os.path.exists or builtins_exists ???
                if isfolder:
                    os.makedirs(new_path, exist_ok=True)
                elif ent_path in zip_list:
                    print("[HOOK:::zip] cache {} [{}]".format(name, new_path), file=sys.stderr)
                    extract(zip_path, ZIPCACHED_DIR(zip_path), ent_path)
                    extract_post(''.join([ZIPCACHED_DIR(zip_path) , '/', ent_path]))
            args = tuple([(new_path if isString else pathlib.Path(new_path)) if idx == 0 else v for idx, v in enumerate(args)])
            return args, hook(*args, **kwargs)
        else :
            if not zip_path in ZIP_STAT_INFO :
                print("[HOOK:::zip] cache error {} [{}]".format(name, zip_path), file=sys.stderr)
                return args, hook(*args, **kwargs)
            entries = ZIP_STAT_INFO[zip_path]
            neopath = (ent_path + "/") if isfolder else ent_path
            if not neopath in entries : # if exists neopath, make a dir/file
                if not path_exists_native(new_path):  # path_exists_native, os.path.exists or builtins_exists ???
                    if isfolder:
                        os.makedirs(new_path, exist_ok=True)
                    elif ent_path in zip_list:
                        print("[HOOK:::zip] cache {} [{}]".format(name, new_path), file=sys.stderr)
                        extract(zip_path, ZIPCACHED_DIR(zip_path), ent_path)
                        extract_post(''.join([ZIPCACHED_DIR(zip_path), '/', ent_path]))
                args = tuple([(new_path if isString else pathlib.Path(new_path)) if idx == 0 else v for idx, v in enumerate(args)])
                return args, hook(*args, **kwargs)
            stat = entries[neopath]
            return args, stat

    hook_func = funcwithstring if is_string_path else funcwithpath
    zimport.register_hook(name, orgfunc, hook_func)
    return hook_func

########################################

import zimport.util.module as module
def detour(zimport, hookname : str) :
    ZIP_NTRY_INFO = zimport.ZIP_NTRY_INFO
    ZIP_STAT_INFO = zimport.ZIP_STAT_INFO
    ZIP_NTRY_TREE = zimport.ZIP_NTRY_TREE
    ZIPCACHED_DIR = zimport.cached_dir

    mod, clz, fun = module.decompose(hookname)
    orgfunc = module.get(mod, clz, fun)

    def hook(*args, **kwargs) :
        def open(p): f = builtins.open(p); n = f.name; f.close(); return n.replace('\\', '/')
        path = slashpath(args[0])
        is_c = is_cac_path(path)
        is_z = is_zip_path(path)

        if (hookname == "tokenize._builtin_open") :
            if False : pass
            elif is_c :
                zip_path, ent_path, new_path = zimport.decache_path(path)
                if DBG : print(f"[INF:::detour] [{hookname}] ::: {path} -> {new_path}")
                args = tuple([new_path if idx == 0 else v for idx, v in enumerate(args)])
            elif is_z :
                pass
            else :
                pass
            return builtins.open(*args, **kwargs)

        if (hookname == "importlib.machinery.FileFinder.find_spec") : # 20250531 torchvision patch
            if False : pass
            elif is_c :
                zip_path, ent_path, new_path = zimport.decache_path(path)
                if DBG : print(f"[INF:::detour] [{hookname}] ::: {path} -> {new_path}")
                args[0].path = new_path
            elif is_z :
                zip_path, ent_path, new_path = zimport.encache_path(path)
                if DBG : print(f"[INF:::detour] [{hookname}] ::: {path} -> {new_path}")
                args[0].path = new_path
            else :
                pass
            return orgfunc(*args, **kwargs)

        if (hookname == "os.path.exists") :
            if False : pass
            elif is_c :
                ret = path_exists_native(path)
                if DBG : print(f"[INF:::detour] [{hookname}] ::: {path} -> {ret}")
                return ret
            elif is_z :
                zip_path, ent_path, new_path = zimport.encache_path(path)
                if zip_path in ZIP_NTRY_INFO:
                    ret = (ent_path) in ZIP_NTRY_INFO[zip_path] or (ent_path + '/') in ZIP_NTRY_INFO[zip_path]
                    if DBG : print(f"[INF:::detour] [{hookname}] ::: {path} -> {ret}")
                    return ret
                return False
            else :
                pass
            return orgfunc(*args, **kwargs)

        if (hookname == "os.path.isdir") :
            if False : pass
            elif is_c :
                zip_path, ent_path, new_path = zimport.decache_path(path)
                ret = zip_path in ZIP_NTRY_INFO and (ent_path + '/') in ZIP_NTRY_INFO[zip_path]
                if DBG : print(f"[INF:::detour] [{hookname}] ::: {path} -> {ret}")
                return ret
            elif is_z :
                zip_path, ent_path, new_path = zimport.encache_path(path)
                ret = zip_path in ZIP_NTRY_INFO and (ent_path + '/') in ZIP_NTRY_INFO[zip_path]
                if DBG : print(f"[INF:::detour] [{hookname}] ::: {path} -> {ret}")
                return ret
            else :
                pass
            return orgfunc(*args, **kwargs)

        if (hookname == "os.path.isfile") : # 20250606 transformers requires this patch !!!
            if False : pass
            elif is_c :
                zip_path, ent_path, new_path = zimport.decache_path(path)
                ret = zip_path in ZIP_NTRY_INFO and (ent_path) in ZIP_NTRY_INFO[zip_path]
                if DBG : print(f"[INF:::detour] [{hookname}] ::: {path} -> {ret}")
                return ret
            elif is_z :
                zip_path, ent_path, new_path = zimport.encache_path(path)
                ret = zip_path in ZIP_NTRY_INFO and (ent_path) in ZIP_NTRY_INFO[zip_path]
                if DBG : print(f"[INF:::detour] [{hookname}] ::: {path} -> {ret}")
                return ret
            else :
                pass
            return orgfunc(*args, **kwargs)

        if (hookname == "os.listdir") : # 20250602 transformers patch
            if False : pass
            elif is_c :
                zip_path, ent_path, new_path = zimport.decache_path(path)
                if zip_path in ZIP_NTRY_INFO and (ent_path + '/') in ZIP_NTRY_INFO[zip_path]:
                    t = ZIP_NTRY_INFO[zip_path][ent_path + '/']['_tr']
                    ret = list(t.dict().keys())
                    ret.sort()
                    if DBG : print(f"[INF:::detour] [{hookname}] ::: {path} -> {ret}", file=sys.stdout)
                    return ret
                pass
            elif is_z :
                zip_path, ent_path, new_path = zimport.encache_path(path)
                if zip_path in ZIP_NTRY_INFO and (ent_path + '/') in ZIP_NTRY_INFO[zip_path]:
                    t = ZIP_NTRY_INFO[zip_path][ent_path + '/']['_tr']
                    ret = list(t.dict().keys())
                    ret.sort()
                    if DBG : print(f"[INF:::detour] [{hookname}] ::: {path} -> {ret}", file=sys.stdout)
                    return ret
                pass
            else :
                pass
            return orgfunc(*args, **kwargs)

        if (hookname == "os.path.join") :
            if False : pass
            elif is_c :
                return orgfunc(*args, **kwargs)
            elif is_z :
                ret = orgfunc(*args, **kwargs)
                if (ret.endswith(".dll") or ret.endswith(".so") or (".so." in ret) or ret.endswith(".dylib")) : #  or ret.endswith(".exe")) : # causeof pip/_vendor/distlib/resources.ZipResourceFinder, do not join to .cache with .exe extension
                    zip_path, ent_path, new_path = zimport.encache_path(ret)
                    if DBG : print(f"[INF:::detour] [{hookname}] ::: {ret} -> {new_path}")
                    return new_path
                return ret
            else :
                pass
            return orgfunc(*args, **kwargs)

        if (hookname == "os.path.dirname") :
            if False : pass
            elif is_c :
                # zip_path, ent_path, new_path = zimport.decache_path(path)
                # if zip_path in ZIP_NTRY_INFO and ((ent_path) in ZIP_NTRY_INFO[zip_path] or (ent_path + '/') in ZIP_NTRY_INFO[zip_path]):
                #     args = tuple([new_path if idx == 0 else v for idx, v in enumerate(args)])
                # if DBG : print(f"[INF:::detour] [{hookname}] ::: {path} -> {args}")
                return orgfunc(*args, **kwargs)
            elif is_z :
                # zip_path, ent_path, new_path = zimport.encache_path(path)
                # if zip_path in ZIP_NTRY_INFO and ((ent_path) in ZIP_NTRY_INFO[zip_path] or (ent_path + '/') in ZIP_NTRY_INFO[zip_path]):
                #     args = tuple([new_path if idx == 0 else v for idx, v in enumerate(args)])
                # if DBG : print(f"[INF:::detour] [{hookname}] ::: {path} -> {args}")
                return orgfunc(*args, **kwargs)
            else :
                pass

        ret = orgfunc(*args, **kwargs)
        return ret

    module.set(mod, clz, fun, hook)
    zimport.register_hook(hookname, orgfunc, hook)
    return hook

