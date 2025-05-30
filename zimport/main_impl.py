#-------------------------------------------------------------------------------
# zimport v0.1.4 20250531
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------
import io, os, sys, time, shutil, builtins
import zipfile
import pathlib
from .util.zip import zipstaties
from .util.path import path_exists_native, find

DBG = False

########################################

ZIP_IMPORTED_STRING = [".z/", ".zip/", ".z\\", ".zip\\"]
# ZIP_IMPORTED_STRING = [".z/", ".z\\"]
ZIP_IMPORTED_CACHES = ["/.cache/", "\\.cache\\"]
def is_zip_path(path) : # return just true, path == a.zip/a/b/c.x
    if not any (tok in path for tok in ZIP_IMPORTED_STRING) : return False # if not (".z/" in path or ".zip/" in path or ".z\\" in path or ".zip\\" in path) : return False
    if any (tok in path for tok in ZIP_IMPORTED_CACHES) : return False
    return True

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
        zip_path, ent_path, new_path = zimport.path_maker(org_path)
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
    return funcwithstring if is_string_path else funcwithpath

########################################
def detour(zimport, hookname : str, orgfunc) :
    ZIP_NTRY_INFO = zimport.ZIP_NTRY_INFO
    ZIP_STAT_INFO = zimport.ZIP_STAT_INFO
    ZIPCACHED_DIR = zimport.cached_dir
    def hook(*args, **kwargs) :
        def path(p): f = builtins.open(p); n = f.name; f.close(); return n.replace('\\', '/')
        if (hookname == "FileFinder.find_spec") : # 20250531 torchvision patch
            org_path = args[0].path # org_path = os.path.abspath(args[0].path).replace('\\', '/')
            if is_zip_path(org_path):
                zip_path, ent_path, new_path = zimport.path_maker(org_path)
                if DBG : print(f"[INF:::detour] {hookname}.path [{org_path}] to [{new_path}]", file=sys.stdout)
                args[0].path = new_path
            ret = orgfunc(*args, **kwargs)
            return ret

        if (hookname == "os.path.exists") : # 20250531 cv2 patch
            org_path = args[0] # org_path = os.path.abspath(args[0]).replace('\\', '/')
            zip_path, ent_path, new_path = zimport.path_maker(org_path)
            if ent_path.startswith('cv2/') and zip_path in ZIP_NTRY_INFO :
                zip_list = ZIP_NTRY_INFO[zip_path]
                if ent_path in zip_list:
                    new_path = path(org_path)
                    args = (new_path, )
                    if DBG : print(f"[INF:::detour] {hookname} [{org_path}] to [{new_path}]", file=sys.stdout)

        ret = orgfunc(*args, **kwargs)
        return ret
    return hook
