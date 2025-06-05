#-------------------------------------------------------------------------------
# zimport v0.1.8 202506xx
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------

import os, sys

__version__ = '0.1.8'
__all__ = ["main"]

if sys.version_info < (3,9):
    raise Exception("[ERR] zimport requires Python 3.9 or greater ...")

from .main import install, uninstall, debug, zimport_set_cache_dir, zimport_clear_cache, zimport_extract_to_cache
install()
debug(False)
