#-------------------------------------------------------------------------------
# zimport v0.1.10 20250611
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------
import os, sys, time
import typing # typing added in version 3.5, https://docs.python.org/3/library/typing.html

def current_milli() -> int:
    return time.time_ns() // 1000000

