# zimport

zimport is a drop-in replacement and enhancement for Python’s standard zipimport, with support for dynamic libraries.  

zimport is used to load and manage python packages from zip-archives.
in other words, it allows you to manage python packages like java jars.
and, it supports not only reading files inside zip-archive, but also dynamic library(.dll, .pyd, .so) loading.

zimport has been tested on python v3.8 to v3.12, on windows/linux.
also, when I tested it on various versions of pytorch, pandas, onnx, scipy, and scikitrun, it worked without any problems.

Additionally, you can create the most convenient environment possible when using it with PortablePython at the link below.  
https://github.com/waveware4ai/PortablePython  

If Users find bugs or problems while using the library, please leave an Issue.

History
------------
2025/05/21 v0.1.0 : initial released  
2025/05/26 v0.1.1 : support macosx, some minor bug fix  
2025/05/28 v0.1.2 : some minor bug fix  
2025/05/29 v0.1.3 : support packages (yaml; https://github.com/yaml/pyyaml)  
2025/05/31 v0.1.4 : support packages (torch, torchvision; https://pytorch.org/)  
2025/06/02 v0.1.5 : add builtin functions (uninstall(), zimport_set_cache_dir(PATH), zimport_clear_cache() ...)  
2025/06/03 v0.1.6 : support packages (transformers; https://github.com/huggingface/transformers)  
2025/06/06 v0.1.7 : some minor bug fix, performance improvement  
2025/06/07 v0.1.8 : support packages (librosa; https://github.com/librosa/librosa, matplotlib; https://github.com/matplotlib/matplotlib)  
2025/06/08 v0.1.9 : some critical bug fix, support packages (diffusers; https://github.com/huggingface/diffusers, grpc; https://github.com/grpc/grpc/tree/master/src/python/grpcio, numba; https://github.com/numba/numba)  
2025/06/11 v0.1.10 : support packages (cython; https://github.com/cython/cython, av; https://github.com/PyAV-Org/PyAV)

Support & Tested Package
------------
The following major packages have been tested:  
|package name <br> (with dependency)|python & os <br> environment|zimport <br> implemented version|support status <br> (Ｏ, △, Ⅹ)|
|:---:|:---:|:---:|:---:|
|av|p3.10,11,12 (win)|v0.1.10|Ｏ|
|cv2|p3.10,11,12 (win)|v0.1.5|Ｏ|
|cython|p3.10,11,12 (win)|v0.1.10|Ｏ|
|diffusers|p3.10,11,12 (win)|v0.1.9|Ｏ|
|grpc|p3.10,11,12 (win)|v0.1.9|Ｏ|
|librosa|p3.10,11,12 (win)|v0.1.8|Ｏ|
|matplotlib|p3.10,11,12 (win)|v0.1.8|Ｏ|
|numba|p3.10,11,12 (win, linux)|v0.1.9|Ｏ|
|numpy|p3.10,11,12 (win, linux)|v0.1.1|Ｏ|
|onnx|p3.10,11,12 (win)|v0.1.6|△ (not tested enough)|
|pandas|p3.10,11,12 (win)|v0.1.0|Ｏ|
|psutil|p3.10,11,12 (win, linux)|v0.1.2|Ｏ|
|pyworld|p3.10,11,12 (win)|v0.1.1|Ｏ|
|PyQt5|p3.10,11,12 (win)|v0.1.8|Ｏ|
|scikitrun|p3.10,11,12 (win)|v0.1.0|Ｏ|
|scipy|p3.10,11,12 (win)|v0.1.0|Ｏ|
|torch, torchvision, torchaudio|p3.10,11,12 (win, linux)|v0.1.1|Ｏ|
|transformers|p3.10,11,12 (win)|v0.1.6|Ｏ|
|yaml|p3.10,11,12 (win)|v0.1.3|Ｏ|

If you encounter any errors while using it, please be sure to provide feedback.  

Installation (pip install)
------------
1. using pip
```python
python -m pip install zimport
Collecting zimport
  Downloading zimport-0.1.0-py3-none-any.whl.metadata (5.5 kB)
Downloading zimport-0.1.0-py3-none-any.whl (32 kB)
Installing collected packages: zimport
Successfully installed zimport-0.1.0
```
2. run python console then, type 'import zimport'
```python
X:\portable.python.v3.11.09.x64.win>python
>>> import zimport
[INF] zimport installed ...
[INF] zimport cache_dir ::: [X:/portable.python.v3.11.09.x64.win/.cache] from find('.cache')
>>> zimport.__version__
'0.1'
>>>
```
Installation (manual install)
------------
1. copy zimport.zip to [python excutable path]/lib
2. append [python excutable path]/python3xx.pth (for python 3.11 python311.pth)
```python
./lib/site-packages.zimport.v0.1.zip
```
3. run python console then, type 'import zimport'
```python
X:\portable.python.v3.11.09.x64.win>python
>>> import zimport
[INF] zimport installed ...
[INF] zimport cache_dir ::: [X:/portable.python.v3.11.09.x64.win/.cache] from find('.cache')
>>> zimport.__version__
'0.1'
>>>
```
Example (read resource in zip) 
------------
1. First, paste [ReadResource] folder inside [examples/exam.01] into [lib/site-package] folder.
2. \_\_init\_\_.py inside ReadResource has simple contents as follows.
```python
import sys, io, os
def read() :
    path = os.path.dirname(os.path.abspath(__file__))
    #print(path)
    f = open(os.path.join(path, "config.ini"), 'r')
    while True:
        line = f.readline()
        if not line: break
        print(line.strip())
    f.close()
```
3. If you run the code, you will see the following result:
```python
X:\portable.python.v3.11.09.x64.win>python
>>> import ReadResource
>>> ReadResource.read()
[1] This
[2] is a
[3] resource
[4] inner
[5] package
>>> 
```
4. Next, compress the [ReadResource] folder to ../site-packages.ReadResource.z and delete the [ReadResource] folder.
5. If you run python and do the same, you can see that it cannot read internal resources.
```python
X:\portable.python.v3.11.09.x64.win>python
>>> import os, sys
>>> sys.path.append(os.path.join(os.getcwd(), "lib/site-packages.ReadResource.z"))
>>> import ReadResource
>>> ReadResource.read()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "X:\portable.python.v3.11.09.x64.win\lib\site-packages.ReadResource.z\ReadResource\__init__.py", line 6, in read
FileNotFoundError: [Errno 2] No such file or directory: 'X:\\portable.python.v3.11.09.x64.win\\lib\\site-packages.ReadResource.z\\ReadResource\\config.ini'
>>>
```
6. zimport was developed to allow normal reading of internal resources.
```python
X:\!test\portable.python.v3.11.09.x64.win>python
>>> import zimport
[INF] zimport installed ...
[INF] zimport cache_dir ::: [X:/!test/portable.python.v3.11.09.x64.win/.cache] from find('.cache')
>>> import os, sys
>>> sys.path.append(os.path.join(os.getcwd(), "lib/site-packages.ReadResource.z"))
>>> import ReadResource
>>> ReadResource.read()
[1] This
[2] is a
[3] resource
[4] inner
[5] package
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
4. Now go into site-packages and zip-archive all the files and empty site-packages.  
   When compressing, you can compress it with the extension [.zip] or [.z],
   Personally, I prefer [.z] because Windows systems recognize [.zip] as a zip folder and perform caching.
   If there are a lot of files inside [.zip], this may cause unnecessary overhead or system crashes on Windows systems.
```python
cd [python excutable path]/lib/site-packages
zip -r ../site-packages.torch.v2.3.1+cu118.win.zip *
rm -rf *
```
5. There are two ways to register sys.path for loading zip-archive.
The first way is to register in python3xx.pth. Add the content as follows.
```python
./lib/site-packages.torch.v2.3.1+cu118.win.zip
```
The second method is to add dynamically. Add it to sys.path in python colsole as shown below.
```python
import os, sys
sys.path.append(os.path.join(os.getcwd(), "lib/site-packages.torch.v2.3.1+cu118.win.zip"))
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
[7] : X:\python\portable.python.v3.11.09.x64.win\lib/site-packages.torch.v2.3.1+cu118.win.zip
```
6. The final step is to import the pytorch zip-archive module.
```
>>> import zimport, os, sys
[INF] zimport installed ...
[INF] zimport cache_dir ::: [X:/python/portable.python.v3.11.09.x64.win/.cache] from find('.cache')
>>> sys.path.append(os.path.join(os.getcwd(), "lib/site-packages.torch.v2.3.1+cu118.win.zip"))
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
zimport.install()                      # Since it is installed at the same time as import, there is no need to use it in general cases.
zimport.uninstall()                    # Used to uninstall zimport, and all variables will revert to before install.
zimport.debug(True/False)              # Used to perform debugging. The default is False.
zimport.zimport_set_cache_dir(PATH)    # You can customize the cache dir of zimport. By default, the cache dir is set automatically,  
                                       # and the [.cache] directory is searched in the order of ['.', '..', 'lib', 'lib/site-packages'] based on the python executable binary.
zimport.zimport_clear_cache()          # Deletes all files in the specified cache dir.
zimport.zimport_extract_to_cache(PATH) # This pre-caches the file. Normally you won't need to do this.
```

Save your Storage
------------
<p float="middle">
    <img src="resources\torch before after.png" alt="torch before after" width="100%"/>
</p>
