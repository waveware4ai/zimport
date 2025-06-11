#-------------------------------------------------------------------------------
# zimport v0.1.10 20250611
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------
# import _frozen_importlib as _bootstrap
# import _frozen_importlib_external as _bootstrap_external
import sys
from importlib import _bootstrap
from importlib import _bootstrap_external

DBG = False

def modulespec(*args, **kwargs) :
    try :
        ret = _bootstrap.ModuleSpec(*args, **kwargs)
        return ret
    except Exception as e :
        if DBG : print(f"[_bootstrap] modulespec : {args} ::: {e}", file = sys.stderr)
        return None

def spec_from_loader(*args, **kwargs) :
    try :
        ret = _bootstrap.spec_from_loader(*args, **kwargs)
        return ret
    except Exception as e :
        if DBG : print(f"[_bootstrap] spec_from_loader : {args} ::: {e}", file = sys.stderr)
        return None

def exec(*args, **kwargs)  :
    try :
        ret = _bootstrap._exec(*args, **kwargs)
        return ret
    except Exception as e :
        #if DBG : print(f"[_bootstrap] exec : {args} ::: {e}", file = sys.stderr)
        return None

def load_module_shim(*args, **kwargs)  :
    try :
        ret = _bootstrap._load_module_shim(*args, **kwargs)
        return ret
    except Exception as e :
        if DBG : print(f"[_bootstrap] load_module_shim : {args} ::: {e}", file = sys.stderr)
        return None

class LoaderBasics: # _bootstrap_external._LoaderBasics
    pass

