#-------------------------------------------------------------------------------
# zimport v0.1.4 20250531
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------

import os, sys

__version__ = '0.1.4'
__all__ = ["main"]

if sys.version_info < (3,9):
    raise Exception("[ERR] zimport requires Python 3.9 or greater ...")

# from .main import install, debug, setcachedir, precache_dll, precache_file, precache_directory

from .main import install, debug, precache_dll, precache_file, precache_directory, invalidate_caches
install()
debug(False)
