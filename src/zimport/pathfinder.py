#-------------------------------------------------------------------------------
# zimport v0.1.1 20250526
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------
import io, os, sys, importlib, time

import zimport.util.zip as ZIP
import zimport.util.bootstrap as BOOTSTRAP
import zimport.util.path as PATH

import types
import builtins

from zimport import pathfinder_impl

# from importlib import _bootstrap
# from importlib import _bootstrap_external

from zimport import main

DBG = False
# ENTRIES_BY_ZIP = dict()

class PathFinder(): #_bootstrap_external._LoaderBasics/LoaderBasics
    def __init__(self, path):
        path = path.replace('\\', '/') if path is not None else None
        real, virt = PATH.virtual_path_split(path)
        if not isinstance(path, str):
            raise ZIP.ZipException(f"zip loader exception", path=path)
        if not path:
            raise ZIP.ZipException(f"zip loader exception", path=path)
        if not ZIP.is_ziparchive(real) :
            raise ZIP.ZipException(f"zip loader exception", path=path)

        zimport = main.getInstance()
        zimport.invalidate_caches()
        self.real = real                       # real file in filesystem, generally .zip/.z
        self.virt = virt + '/' if virt else '' # virt path is always directory not file
        self.zent = zimport.getentries(real)   # zip entries with 'real' zip path key
        if DBG : print(f"[INF] new loader {real} ::: {virt}")

    def find_spec(self, fullname, target=None):
        has = pathfinder_impl.has_module_is_packge(self, fullname)

        if has is None: # None : not found
            mod_path = pathfinder_impl.get_path_for_module(self, fullname)
            if (mod_path + '/') in self.zent : # this path represent a directory?
                path = f'{self.real}/{mod_path}'
                spec = BOOTSTRAP.modulespec(name=fullname, loader=None, is_package=True)
                spec.submodule_search_locations.append(path) # invoke new loader(path)
            else: # is package or not
                spec = None # the module cannot be found.
        else:
            mod_path = pathfinder_impl.get_module_filename(self, fullname)  # 14mhz

            if mod_path.endswith(".pyd") :
                spec = BOOTSTRAP.modulespec(fullname, self, origin=mod_path, is_package=False)
            else :
                spec = BOOTSTRAP.spec_from_loader(fullname, self, is_package=has)  # invoke get_filename

        if DBG and spec : print(f"[INF:::pathfinder] find_spec : {self.real.rpartition('/')[2]}:::{self.virt}:::{fullname}:::{spec}")
        return spec

    ########################################

    def get_filename(self, fullname):
        mod_path = pathfinder_impl.get_module_filename(self, fullname) #14mhz
        if DBG : print(f"[INF:::pathfinder] get_filename : {self.real.rpartition('/')[2]}:::{self.virt}:::{fullname} -> {mod_path.rpartition('/')[2]}")
        return mod_path

    def get_code(self, fullname):
        code, ispackage, mod_path = pathfinder_impl.get_module_code(self, fullname)
        if DBG : print(f"[INF:::pathfinder] get_code : {self.real.rpartition('/')[2]}:::{self.virt}:::{fullname} -> {mod_path.rpartition('/')[2]}")
        return code

    def get_data(self, pathname):
        data, mod_path = pathfinder_impl.get_data(self, pathname)
        if DBG : print(f"[INF:::pathfinder] get_data : {self.real.rpartition('/')[2]}:::{self.virt}:::{pathname} -> {mod_path.rpartition('/')[2]}")
        return data

    def get_source(self, fullname):# the source code for the specified module
        src, mod_path = pathfinder_impl.get_source(self, fullname)
        if DBG : print(f"[INF:::pathfinder] get_source : {self.real.rpartition('/')[2]}:::{self.virt}:::{fullname} -> {mod_path.rpartition('/')[2]}")
        return src

    def get_resource_reader(self, fullname):
        reader = pathfinder_impl.get_resource_reader(self, fullname)
        if DBG : print(f"[INF:::pathfinder] get_resource_reader : {self.real.rpartition('/')[2]}:::{self.virt}:::{fullname}")
        return reader

    ########################################

    def is_package(self, fullname):
        pass

    def create_module(self, spec):
        module = types.ModuleType(spec.name)
        module.__spec__ = spec
        return module

    def exec_module(self, module):
        spec = module.__spec__

        if spec is None or spec.origin is None :
            if DBG: print(f"[INF:::pathfinder] err : spec is null {[module, ]}", file=sys.stderr)
            pass    

        if DBG: print(f"[INF:::pathfinder] exec_module : {spec.name} ::: {spec.origin}")

        if spec.origin.endswith("__init__.py") : # 20240930 pyworld patch
            pydname = '/'.join([spec.name, spec.name.rpartition('.')[2] + pathfinder_impl._PYTHON__PY_DLL_])
            if pydname in self.zent :
                replace_pyd = '/'.join([self.real, pydname])
                if DBG : print(f"[INF:::pathfinder] exec_module : replace [{spec.origin}] to [{replace_pyd}]", file=sys.stderr)
                spec.origin = replace_pyd

        if spec.origin.endswith(".pyd") or spec.origin.endswith(".so") or (".so." in spec.origin) or spec.origin.endswith(".dylib") : # 20250514 linux patch
            def path(p): f = builtins.open(p); n = f.name; f.close(); return n.replace('\\', '/')
            name = path(spec.origin);
            #import imp
            #m = imp.load_dynamic(module.__name__, name) # imp deprecated since version 3.4, removed in version 3.12.
            m = self.custom_load_dynamic(module.__name__, name)
            if DBG : print(f"[INF:::exec_module@pathfinder] load {[name,]}", file=sys.stderr)
            return m
        else :
            code = self.get_code(module.__name__)
            if code is None: raise ImportError('cannot load module {!r} when get_code() returns None'.format(module.__name__))
            BOOTSTRAP.call_with_frames_removed(spec.origin, exec, code, module.__dict__)

    def load_module(self, fullname):
        return BOOTSTRAP.load_module_shim(self, fullname)

    #https://stackoverflow.com/questions/60158932/how-to-replace-usages-of-deprecated-imp-load-dynamic
    #https://stackoverflow.com/questions/24166080/importing-dll-into-python-3-without-imp-load-dynamic
    #https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
    def custom_load_dynamic(name, path, fullname):
        if DBG : print(f"[INF:::custom_load_dynamic@pathfinder] name[{name}] path[{path}] file[{file}]")
        spc = importlib.util.spec_from_file_location(path, fullname)
        mod = importlib.util.module_from_spec(spc)
        sys.modules[path] = mod
        spc.loader.exec_module(mod)
        return mod

    ########################################

    def invalidate_caches(self) :
        try:
            zimport = main.getInstance()
            zimport.fixarchive(self.real)
            self.zent = zimport.getentries(self.real)
        except :
            self.zent = {}

    def __repr__(self):
        return f'<zimporter object "{self.real}/{self.virt}">'

    ########################################

