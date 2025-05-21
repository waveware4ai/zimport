# zimport

zimport is used to load and manage python packages from zip-archives.
in other words, it allows you to manage python packages like java jars.
and, it supports not only reading files inside zip-archive, but also dynamic library(.dll, .pyd, .so) loading.

zimport has been tested on python v3.8 to v3.12, on windows/linux.
also, when I tested it on various versions of pytorch, pandas, onnx, scipy, and scikitrun, it worked without any problems.

If users find bugs or problems while using the app, please leave an Issue.

History
------------
2025/05/21 v0.1 released

Installation
------------

1. copy zimport.zip to [python excutable path]/lib
2. append [python excutable path]/python3xx.pth (for python 3.11 python311.pth)
```python
./lib/site-packages.zimport.v0.1.zip
```
3. run python console then, type 'import zimport'
```python
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
Example (build pytorch zip-archive) 
------------
1. delete or move all files in [python excutable path]/lib/site-packages to another location.
   (This is because files stored in site-packages must be deleted after creating the zip archive.)
2. download torch and dependencies via pip. Here we will use torch version 2.3.1.
```python
python -m pip install torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu118
```
3. Once the download is complete, check that the package is working properly.
```python
python -c "import torch;print(torch.__version__);print(torch.cuda.is_available());print(torch.cuda.get_device_name(0));"
2.3.1+cu118
True
NVIDIA GeForce RTX 2080
```
4. Now go into site-packages and zip-archive all the files and empty site-packages
```python
cd [python excutable path]/lib/site-packages
zip -r ../site-packages.torch.v2.3.1+cu118.zip *
rm -rf *
```
5. There are two ways to register sys.path for loading zip-archive.
The first way is to register in python3xx.pth. Add the content as follows.
```python
./lib/site-packages.torch.v2.3.1+cu118.zip
```
The second method is to add dynamically. Add it to sys.path in python colsole as shown below.
```python
import os, sys
sys.path.append(os.path.join(os.getcwd(), "lib/site-packages.torch.v2.3.1+cu118.zip"))
```
You can check that both are registered through sys.path.
```python
>>> for i in range(len(sys.path)) : print(f"[{i}] : {sys.path[i]}")
[0] : X:\python\portable.python.v3.11.09.x64.win
[1] : X:\python\portable.python.v3.11.09.x64.win\python311.zip
[2] : X:\python\portable.python.v3.11.09.x64.win\DLLs
[3] : X:\python\portable.python.v3.11.09.x64.win\Lib
[4] : X:\python\portable.python.v3.11.09.x64.win\lib\site-packages
[5] : X:\python\portable.python.v3.11.09.x64.win\lib\site-packages.pip.zip
[6] : X:\python\portable.python.v3.11.09.x64.win\lib\site-packages.zimport.v0.1.zip
[7] : X:\python\portable.python.v3.11.09.x64.win\lib/site-packages.torch.v2.3.1+cu118.zip
```
6. The final step is to import the pytorch module.
```
>>> import zimport, os, sys
[INF] zimport installed ...
[INF] zimport cache_dir ::: [X:/python/portable.python.v3.11.09.x64.win/.cache] from find('.cache')
>>> sys.path.append(os.path.join(os.getcwd(), "lib/site-packages.torch.v2.3.1+cu118.zip"))
>>> import torch
>>> print(torch.__version__)
2.3.1+cu118
>>> print(torch.cuda.is_available())
True
>>> print(torch.cuda.get_device_name(0))
NVIDIA GeForce RTX 2080
>>>
```
If you added path to python3xx.pth, you can call it elegantly in one line.
```
python -c "import zimport;import torch;print(torch.__version__);print(torch.cuda.is_available());print(torch.cuda.get_device_name(0));"
2.3.1+cu118
True
NVIDIA GeForce RTX 2080
>>>
```

Usage
------------
```pyton
zimport.install()                # Since it is installed at the same time as import, there is no need to use it in general cases.
zimport.debug(True/False)        # Used to perform debugging. The default is False.
zimport.invalidate_caches()      # Used to clear cache information. Mainly needed for reloading when modifying .py.
zimport.precache_dll(PATH)       # This pre-caches the dll. Normally you won't need to do this.
zimport.precache_file(PATH)      # This pre-caches the file. Normally you won't need to do this.
zimport.precache_directory(PATH) # This pre-caches the directory. Normally you won't need to do this.
```

Save your Storage
------------
<p float="middle">
    <img src="resources\torch before after.png" alt="torch before after" width="100%"/>
</p>
