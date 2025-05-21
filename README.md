# zimport

zimport is used to load and manage python packages from zip-archives.

Installation
------------

1. copy zimport.zip to [python excutable path]/lib
2. append [python excutable path]/python3xx.pth (for python 3.11 python311.pth)
```
./lib/site-packages.zimport.v0.1.zip
```
3. run python console then, type 'import zimport'
```
X:\portable.python.v3.11.09.x64.win>python
Python 3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import zimport
[INF] zimport installed ...
[INF] zimport cache_dir ::: [X:/portable.python.v3.11.09.x64.win/.cache] from find('.cache')
>>> zimport.__version__
'0.1'
>>>
```

