#-------------------------------------------------------------------------------
# zimport v0.1.10 20250611
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------
import os, sys, importlib

import zimport.util.path as PATH
import zimport.util.zip as ZIP
import zimport.util.compile as COMPILE

DBG = False

#_suffixes = [s[0] for s in imp.get_suffixes() if s[2] == imp.C_EXTENSION] # imp deprecated since version 3.4, removed in version 3.12.
_suffixes = importlib.machinery.EXTENSION_SUFFIXES
#print(f"_suffixes ::: {_suffixes}") # ex) _suffixes ::: ['.cp311-win_amd64.pyd', '.pyd']
_PYTHON_VERSION_ = f"{sys.version_info.major}{sys.version_info.minor}"
_PYCACHE_SUFFIX_ = ".cpython-" + _PYTHON_VERSION_ + ".pyc"
#_PYTHON__PY_DLL_ = [s[0] for s in imp.get_suffixes() if s[2] == imp.C_EXTENSION][0]  # imp deprecated since version 3.4, removed in version 3.12.
_PYTHON__PY_DLL_ = _suffixes[0]
#print(f"_PYTHON__PY_DLL_ ::: {_PYTHON__PY_DLL_}") # ex) _PYTHON__PY_DLL_ ::: .cp311-win_amd64.pyd
_zip_searchorder = \
(
    ('/__init__.pyc', True, True, False),
    ('/__init__.py', False, True, False),
    #('/__init__.pyi', False, True, False), # Do not import, refer PEP-484 document
    ('.pyc', True, False, False),
    ('.py', False, False, False),
    #('.pyi', False, False, False),         # Do not import, refer PEP-484 document
    ('.pyd', False, False, True),
    (_PYTHON__PY_DLL_, False, False, True),
) # suffix, isbytecode, ispackage, isdll

def get_path_for_module(self, fullname):
    return self.virt + fullname.rpartition('.')[2]

def has_module_is_packge(self, fullname):
    path = get_path_for_module(self, fullname)
    for suffix, isbytecode, ispackage, isdll  in _zip_searchorder: #14mhz
        fullpath = path + suffix
        if fullpath in self.zent:
            return ispackage
    return None # cannot found in current zip file

####

def get_module_filename(self, fullname):
    path = get_path_for_module(self, fullname)
    for suffix, isbytecode, ispackage, isdll in _zip_searchorder:
        fullpath = path + suffix
        if fullpath in self.zent :
            toc_entry = self.zent[fullpath]
            modpath = toc_entry["pth"]
            return modpath
        else :
            continue
    if DBG: print(f"[:path_hook] can't find module => {fullname!r}", file=sys.stderr)
    return None

####

def get_module_code(self, fullname : str):
    path = get_path_for_module(self, fullname)
    for suffix, isbytecode, ispackage, isdll  in _zip_searchorder: #14mhz
        fullpath = path + suffix
        pycached = '' # a/b.pyc -> a/__pycache__/b.cpython-311.pyc'
        if isbytecode :
            if ispackage : # '__init__' series
                new_suffix = "__init__" + _PYCACHE_SUFFIX_ # ex) __init__.cpython-311.pyc
                cachedtemp = path.split('/')
                cachedtemp.append("__pycache__")
                cachedtemp.append(new_suffix)
                pycached = ('/').join(cachedtemp)
            else :
                new_suffix =_PYCACHE_SUFFIX_
                cachedtemp = (path + new_suffix).split('/')
                cachedtemp.insert(len(cachedtemp) - 1, "__pycache__")
                pycached = ('/').join(cachedtemp)

        #if suffix == '.pyc' : continue # test code
        #if suffix == '.pyc' and path.endswith('config') : continue # test code

        if pycached in self.zent :
            ntry = self.zent[pycached]
        elif fullpath in self.zent :
            ntry = self.zent[fullpath]
        else : continue

        mpth = ntry["pth"]
        data = ZIP.getbytes(self.real, ntry)
        code = None

        if isbytecode:
            code = COMPILE.unmarshal_from_pyc(self, mpth, fullpath, fullname, data)
            if False : print(f"[:path_hook] unmarshal => {fullpath}", file=sys.stderr)
        else:
            code = COMPILE.compile_from_py(mpth, data)
            if DBG : print(f"[:path_hook] compile => {fullpath}", file=sys.stderr)

        if code is None: # bad magic number or non-matching mtime
            continue
        return code, ispackage, mpth

    if DBG : print(f"[:path_hook] can't find module => {fullname!r}", file=sys.stderr)
    return None

####

def get_data(self, pathname):
    path = pathname.replace('\\', '/')
    fullpath = path[len(self.real + '/'):] if path.startswith(self.real + '/') else path
    if (fullpath in self.zent) :
        ntry = self.zent[fullpath]
        modpath = ntry["pth"]
        data = ZIP.getbytes(self.real, ntry)
        return data, modpath
    else :
        raise OSError(0, '', pathname)

####

def get_source(self, fullname):# the source code for the specified module
    # print("get_src - " + fullname)
    has = has_module_is_packge(self, fullname)
    if has is None : # None : not found
        return None, None
    else : # is package or not
        mod_path = get_path_for_module(self, fullname)
        fullpath = PATH.path_join(mod_path, '__init__.py').replace('\\', '/') if has else f'{mod_path}.py'

        if (fullpath in self.zent) :
            toc_entry = self.zent[fullpath]
            mod_path = toc_entry["pth"]
            src = ZIP.getbytes(self.real, toc_entry).decode()
            return src, mod_path
        else :
            return None, None

####

def get_resource_reader(self, fullname):
    try:
        if has_module_is_packge(self, fullname):
            return ZIP.ZipReader(self, fullname)
    except :
        return None
####
