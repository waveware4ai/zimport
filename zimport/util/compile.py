#-------------------------------------------------------------------------------
# zimport v0.1.10 20250611
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------

DBG = False

import os, sys, time, timeit
import io, _io, _imp
import marshal
# import _frozen_importlib as _bootstrap
# import _frozen_importlib_external as _bootstrap_external
from importlib import _bootstrap
from importlib import _bootstrap_external
from .zip import getbytes, _unpack_uint32
from typing import Optional, Tuple # typing added in version 3.5, https://docs.python.org/3/library/typing.html

def compile_from_py(fullpath, src) : # fullpath : a/b/c.z/d/e.py, src : plain-text
    try:
        src = src.replace(b'\r\n', b'\n').replace(b'\r', b'\n')  # _normalize_line_endings(source)
        bin = compile(src, fullpath, 'exec', dont_inherit=True)
        return bin
    except Exception as e:
        if True: print(f"[ERR:::compile] [{e}] in [{fullpath}] ...", file=sys.stderr)
        return None

NUMBA_CHK_FOR_RECOMPILE = True
ALL_PY_FORCED_RECOMPILE = False

def unmarshal_from_pyc(self, fullpath, virtpath, virtname, data): # fullpath : a/b/c.z/d/e.pyc, virtpath : d/e.pyc, virtname d.e
    # Given the contents of a .py[co] file, unmarshal the data and return the code object.
    # Raises ImportError it the magic word doesn't match, or if the recorded .py[co] metadata does not match the source.
    exc_details = { 'name': virtname, 'path': virtpath, }
    flags = _bootstrap_external._classify_pyc(data, virtname, exc_details)
    hash_based = flags & 0b1 != 0
    if hash_based:
        check_source = flags & 0b10 != 0
        if (_imp.check_hash_based_pycs != 'never' and (check_source or _imp.check_hash_based_pycs == 'always')):
            source_bytes = get_source_code_by_pyc(self, virtpath)
            if source_bytes is not None:
                source_hash = _imp.source_hash(_bootstrap_external._RAW_MAGIC_NUMBER, source_bytes,)
                _bootstrap_external._validate_hash_pyc(data, source_hash, virtname, exc_details)
    else:
        if (ALL_PY_FORCED_RECOMPILE) : return None
        source_bytes = get_source_code_by_pyc(self, virtpath)
        
        if (NUMBA_CHK_FOR_RECOMPILE) and (b" numba" in source_bytes) and (not "numba" in virtname) : #14mhz numba related py must be alwarys recompile ...
            if DBG : print(f"[INF:::pathfinder] forced recompile {virtpath}:::{virtname}:::{fullpath}", file=sys.stderr)
            return None

        py_time, py_size =  get_time_and_size_of_py(self, virtpath)
        if py_time : # pyc time vs zip entry time
            pyc_time = _unpack_uint32(data[8:12])
            pyc_size = _unpack_uint32(data[12:16])
            if (pyc_size != py_size) or 2 < abs(pyc_time - py_time) : # lenient timestamp check
                return None
            else :
                pass

    code = marshal.loads(data[16:])
    if not isinstance(code, UNMARSHAL_CODE_TYPE):
        raise TypeError(f'compiled module {fullpath!r} is not a code object')
    return code
UNMARSHAL_CODE_TYPE = type(unmarshal_from_pyc.__code__)

########################################

def get_source_code_by_pyc(self, path) -> Optional[bytes] :
    #assert path[-1:] in ('c', 'o')  # strip 'c' or 'o' from *.py[co]
    if not path or path[-1:] not in ('c', 'o'):
        return None
    path = path[:-1] # pyc, pyo to py
    if (path in self.zent) :
        ntry = self.zent[path]
        data = getbytes(self.real, ntry)
        return data
    else :
        return None

def get_time_and_size_of_py(self, path) -> Tuple[int, int] :
    #assert path[-1:] in ('c', 'o')  # strip 'c' or 'o' from *.py[co]
    if not path or path[-1:] not in ('c', 'o'):
        return None
    path = path[:-1] # pyc, pyo to py
    if (path in self.zent) :
        ntry = self.zent[path]  # entry
        time = int(ntry["tme"]) # timestamp
        size = int(ntry["dsz"]) # decrypt size
        return time, size
    else :
        return 0, 0