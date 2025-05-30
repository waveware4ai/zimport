#-------------------------------------------------------------------------------
# zimport v0.1.4 20250531
# by 14mhz@hanmail.net, zookim@waveware.co.kr
#
# This code is in the public domain
#-------------------------------------------------------------------------------
import os, sys, time, timeit
import io, _io
import zlib, zipfile
import typing # typing added in version 3.5, https://docs.python.org/3/library/typing.html

from importlib import abc
from importlib import _bootstrap
from importlib import _bootstrap_external

class ZipException(ImportError):
    def __init__(self, *args, **kwargs):
        if False : print(f"[EXP] {args[0]}:::{kwargs}", file=sys.stderr)
        pass

class ZipReader(abc.TraversableResources):
    def __init__(self, loader, module):
        _, _, name = module.rpartition('.')
        self.prefix = loader.virt.replace('\\', '/') + name + '/'
        self.archive = loader.real

    def open_resource(self, resource):
        try:
            return super().open_resource(resource)
        except KeyError as exc:
            raise FileNotFoundError(exc.args[0])

    def is_resource(self, path):
        target = self.files().joinpath(path)
        return target.is_file() and target.exists()

    def files(self):
        path = zipfile.Path(self.archive, self.prefix)
        return path

########################################

SIG_STT_ARCHIVE = b'\x50\x4B\x03\x04'
SIG_END_ARCHIVE = b'\x50\x4B\x05\x06'
CENTRAL_DIR_SZE = 22
MAX_COMMENT_LEN = (1 << 16) - 1

def is_ziparchive(p) -> bool :
    return p.endswith(".z") or p.endswith(".zip")

def is_ziparchive_deep(p) -> bool :
    try:
        with io.open(p, "rb") as z:
            byte = z.read(4)
            return True if byte == SIG_STT_ARCHIVE else False
    except : # is directory
        return False

########################################

USEFUCKFILE = False
FUCKINGFILE = dict()

def open(fle) :
    if fle in FUCKINGFILE:
        if False : print(f"[INF] reuse fd {fle}")
        zio = FUCKINGFILE[fle]
    else:
        # zio = _io.open_code(fle)
        zio = io.open(fle, 'rb', buffering = 16384) # io.DEFAULT_BUFFER_SIZE : 8192
        FUCKINGFILE[fle] = zio
    return zio

def zipentries(fle) :
    val = zipentriesbycase(fle, True, False, False, False)
    return val

def zipstaties(fle) :
    val = zipentriesbycase(fle, False, False, True, False)
    return val

def zipentriesbycase(fle : str, gen_entries_by_partname : bool, gen_entries_by_fullname : bool, gen_st_data_by_partname : bool, gen_st_data_by_fullname : bool) :
    try :
        stf = _bootstrap_external._path_stat(fle) # get file stat struct
        std = _bootstrap_external._path_stat(os.path.dirname(fle)) # get directory stat struct
    except :
        raise ZipException(f"can't open Zip file: {fle!r}")

    entries_by_partname = {} # by partname as d/e.txt
    entries_by_fullname = {} # by fullname as a/b/c.z/d/e.txt
    st_data_by_partname = {} # by partname as d/e.txt
    st_data_by_fullname = {} # by fullname as a/b/c.z/d/e.txt

    try:
        fle = fle.replace('\\', '/') # all path must use separator '/'
        zio = open(fle) if USEFUCKFILE else _io.open_code(fle)

        try:
            zio.seek(-CENTRAL_DIR_SZE, 2)
            header_position = zio.tell()
            buffer = zio.read(CENTRAL_DIR_SZE)
        except OSError:
            raise ZipException(f"can't read Zip file: {fle!r}", path=fle)
        if len(buffer) != CENTRAL_DIR_SZE:
            raise ZipException(f"can't read Zip file: {fle!r}", path=fle)
        if buffer[:4] != SIG_END_ARCHIVE:
            try:
                zio.seek(0, 2)
                file_size = zio.tell()
            except OSError:
                raise ZipException(f"can't read Zip file: {fle!r}", path=fle)
            max_comment_start = max(file_size - MAX_COMMENT_LEN - CENTRAL_DIR_SZE, 0)
            try:
                zio.seek(max_comment_start)
                data = zio.read()
            except OSError:
                raise ZipException(f"can't read Zip file: {fle!r}", path=fle)
            pos = data.rfind(SIG_END_ARCHIVE)
            if pos < 0:
                raise ZipException(f'not a Zip file: {fle!r}', path=fle)
            buffer = data[pos:pos + CENTRAL_DIR_SZE]
            if len(buffer) != CENTRAL_DIR_SZE:
                raise ZipException(f"corrupt Zip file: {fle!r}", path=fle)
            header_position = file_size - len(data) + pos

        header_size = _unpack_uint32(buffer[12:16])
        header_offset = _unpack_uint32(buffer[16:20])
        if header_position < header_size:
            raise ZipException(f'bad central directory size: {fle!r}', path=fle)
        if header_position < header_offset:
            raise ZipException(f'bad central directory offset: {fle!r}', path=fle)
        header_position -= header_size
        arc_offset = header_position - header_offset
        if arc_offset < 0:
            raise ZipException(f'bad central directory size or offset: {fle!r}', path=fle)

        try: # start of CD (central directory)
            zio.seek(header_position)
        except OSError:
            raise ZipException(f"can't read Zip file: {fle!r}", path=fle)
        while True:
            buffer = zio.read(46)
            if len(buffer) < 4:
                raise EOFError('EOF read where not expected')
            # Start of file header
            if buffer[:4] != b'PK\x01\x02':
                break                                # Bad: Central Dir File Header
            if len(buffer) != 46:
                raise EOFError('EOF read where not expected')

            ''''''
            flags        = _unpack_uint16(buffer[8:10])
            compress     = _unpack_uint16(buffer[10:12])
            time         = _unpack_uint16(buffer[12:14])
            date         = _unpack_uint16(buffer[14:16])
            crc          = _unpack_uint32(buffer[16:20])
            data_size    = _unpack_uint32(buffer[20:24])
            file_size    = _unpack_uint32(buffer[24:28])
            name_size    = _unpack_uint16(buffer[28:30])
            extra_size   = _unpack_uint16(buffer[30:32])
            comment_size = _unpack_uint16(buffer[32:34])
            file_offset  = _unpack_uint32(buffer[42:46])
            header_size  = name_size + extra_size + comment_size
            timestamp    = int(datetime(date, time))
            ''''''

            if file_offset > header_offset:
                raise ZipException(f'bad local header offset: {fle!r}', path=fle)
            file_offset += arc_offset

            try:
                name = zio.read(name_size)
            except OSError:
                raise ZipException(f"can't read Zip file: {fle!r}", path=fle)

            if len(name) != name_size:
                raise ZipException(f"can't read Zip file: {fle!r}", path=fle)

            try:# on windows, calling fseek to skip over the fields we don't use is slower than reading the data
                # because fseek flushes stdio's internal buffers.    See issue #8745.
                if len(zio.read(header_size - name_size)) != header_size - name_size:
                    raise ZipException(f"can't read Zip file: {fle!r}", path=fle)
            except OSError:
                raise ZipException(f"can't read Zip file: {fle!r}", path=fle)

            if flags & 0x800:
                name = name.decode()
            else:
                try:
                    name = name.decode('ascii')
                except UnicodeDecodeError:
                    raise ZipException(f"unicode decode error: {fle!r}", path=fle)

            is_d = name.endswith('/')    # is dir
            path = '/'.join([fle, name]) # dir is always endswith '/'
            _nme = [p for p in name.split('/') if 0 < len(p)][-1] # file/dir name only ::: low performance
            if False : print(name + " ::: " + _nme)

            if gen_entries_by_partname or gen_entries_by_fullname :
                nt = \
                { # entry data
                    "isd" : is_d       , # is dir
                    "pth" : path       , # simple file/dir name only
                    "nme" : _nme       , # simple file/dir name only
                    "met" : compress   , # compression method refer to https://en.wikipedia.org/wiki/ZIP_(file_format)
                    "esz" : data_size  , # encrypt data size
                    "dsz" : file_size  , # decrypt data size
                    "pos" : file_offset, # data position
                    "tme" : timestamp  , # datetime
                    "crc" : crc        , # crc-code
                }
                if gen_entries_by_partname : entries_by_partname[name] = nt # by partname as d/e.txt
                if gen_entries_by_fullname : entries_by_fullname[path] = nt # by fullname as a/b/c.z/d/e.txt

            if gen_st_data_by_partname or gen_st_data_by_fullname :
                #st = copy.deepcopy(std) if is_d else copy.deepcopy(stf)
                s_ = std if is_d else stf
                st = os.stat_result((s_.st_mode,
                                     s_.st_ino,
                                     s_.st_dev,
                                     s_.st_nlink,
                                     s_.st_uid,
                                     s_.st_gid,
                                     file_size,
                                     timestamp,
                                     timestamp,
                                     timestamp,
                                     0, # ? s_.st_blocks,
                                     0, # ? s_.st_blksize,
                                     0, # ? s_.st_rdev,
                                     0, 0, 0, 0, 0))
                if gen_st_data_by_partname : st_data_by_partname[name] = st # by partname as d/e.txt
                if gen_st_data_by_fullname : st_data_by_fullname[path] = st # by fullname as a/b/c.z/d/e.txt
    except OSError:
        raise ZipException(f"can't open Zip file: {fle!r}")
    finally:
        if USEFUCKFILE == False : zio.close()

    ret = []
    cnt = 0
    if gen_entries_by_partname: ret.append(entries_by_partname); cnt+=1
    if gen_entries_by_fullname: ret.append(entries_by_fullname); cnt+=1
    if gen_st_data_by_partname: ret.append(st_data_by_partname); cnt+=1
    if gen_st_data_by_fullname: ret.append(st_data_by_fullname); cnt+=1
    return None if cnt == 0 else ret[0] if cnt == 1 else tuple(ret)

########################################

def getbytes(fle : str, ent : dict):
    try:
        isd = ent["isd"]  # is dir
        nme = ent["nme"]  # simple name
        esz = ent["esz"]  # encrypt data size
        pos = ent["pos"]  # data position
        met = ent["met"]  # compression method
    except OSError:
        raise ZipException(f"invalid entry: {ent!r}", path=fle)

    if isd:
        if False : print(f"cannot decompress dir entry: {nme!r}", file=sys.stderr)
        return

    try:
        fle = fle.replace('\\', '/') # all path must use separator '/'
        zio = open(fle) if USEFUCKFILE else _io.open_code(fle)

        try:
            zio.seek(pos)
        except OSError :
            raise ZipException(f"can't read zip file: {fle!r}", path=fle)

        buf = zio.read(30)
        if len(buf) != 30 :
            raise ZipException(f"eof read where not expected: {fle!r}", path=fle)
        if buf[:4] != SIG_STT_ARCHIVE : # bad: local file header
            raise ZipException(f"bad local file header: {fle!r}", path=fle)

        name_size = _unpack_uint16(buf[26:28])
        extr_size = _unpack_uint16(buf[28:30])
        head_size = 30 + name_size + extr_size
        pos += head_size  # Start of file data

        try:
            zio.seek(pos)
        except OSError :
            raise ZipException(f"can't read Zip file: {fle!r}", path=fle)

        raw = zio.read(esz)
        if len(raw) != esz:
            raise ZipException(f"data size mismatch : {fle!r}", path=fle)
    except OSError:
        raise ZipException(f"can't open Zip file: {fle!r}")
    finally:
        if USEFUCKFILE == False : zio.close()

    if esz < 0 :
        raise ZipException(f"invalid data size: {esz!r}", path=fle)

    bin = raw if met == 0 else zlib.decompress(raw, -15)
    return bin # refer to https://en.wikipedia.org/wiki/ZIP_(file_format)

########################################

def _pack_uint32(x):
    return (int(x) & 0xFFFFFFFF).to_bytes(4, 'little')

def _unpack_uint32(data):
    assert len(data) == 4
    return int.from_bytes(data, 'little')

def _unpack_uint16(data):
    assert len(data) == 2
    return int.from_bytes(data, 'little')

def datetime(d, t):
    return time.mktime((
        (d >> 9) + 1980,    # bits 9..15: year
        (d >> 5) & 0xF,     # bits 5..8: month
        d & 0x1F,           # bits 0..4: day
        t >> 11,            # bits 11..15: hours
        (t >> 5) & 0x3F,    # bits 8..10: minutes
        (t & 0x1F) * 2,     # bits 0..7: seconds / 2
        -1, -1, -1))

########################################

def testcase1() :
    SETUP_CODE = '''
import os, sys    
from zimport.util.zip import zipentries
'''
    TEST_CODE = '''
list = []
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.additional.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.g2p-en.v2.1.0.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.g2p-ko.v0.9.4.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.mecab.ko.v1.3.7.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.librosa.v0.10.2.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.scipy.v1.14.1.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.numba.v0.60.0.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.tensorboard.v2.17.1.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.torch.v2.0.1+cu118.z")
for p in list :
    zipentries(p)
print('.', end='')
'''
    # timeit.repeat statement
    val = timeit.repeat(setup=SETUP_CODE, stmt=TEST_CODE, repeat=10, number=1)
    print()
    print(f"[INF] min({min(val)}) ~ max({max(val)})")
    # [INF] min(0.13779499999873224) ~ max(0.140073399998073)

def testcase2() :
    path = os.path.dirname(sys.executable) + "/lib/site-packages.additional.z"
    dict = zipentriesbycase(path, True, False, False, False)
    ntry = dict['pydub/audio_segment.py']
    byte = getbytes(path, ntry)
    name = ntry["nme"]
    with open(f"w:/{name}", "wb") as b:
        # Write bytes to file
        b.write(byte)
    print("end of job")

def testcase3() :
    SETUP_CODE = '''
import os, sys
import marshal
from zimport.util.zip import zipentries, zipentriesbycase, getbytes
'''
    TEST_CODE = '''
list = []
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.additional.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.g2p-en.v2.1.0.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.g2p-ko.v0.9.4.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.mecab.ko.v1.3.7.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.librosa.v0.10.2.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.scipy.v1.14.1.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.numba.v0.60.0.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.tensorboard.v2.17.1.z")
list.append(os.path.dirname(sys.executable) + "/lib/site-packages.torch.v2.0.1+cu118.z")
for p in list:
    e1, e2, e3, e4 = zipentriesbycase(p, True, True, True, True)
    for n in e1:
        if not (n.endswith(".py") or n.endswith(".pyc")) : continue
        b = getbytes(p, e1[n])
        # if n.endswith(".py")  : c = compile(b, n, 'exec', dont_inherit=True)
        if n.endswith(".pyc") : m = marshal.loads(b[16:])
    if False : print(f"[INF] completed {p} test ...") 
print('.', end='')
'''
    # timeit.repeat statement
    val = timeit.repeat(setup=SETUP_CODE, stmt=TEST_CODE, repeat=10, number=1)
    print()
    print(f"[INF] min({min(val)}) ~ max({max(val)})")
    # no reuse fd               : [INF] min(1.575370700000348) ~ max(1.646620899999106)
    # ok reuse fd               : [INF] min(0.980815700000675) ~ max(1.028009200002998)
    # ok reuse fd and unmarshal : [INF] min(1.310854899998958) ~ max(1.372702799999388)
    # ok reuse fd and compile   : [INF] min(12.60920729999998) ~ max(13.583235800000693)
if __name__ == "__main__":
    # testcase1()
    # testcase2()
    # testcase3()
    pass


