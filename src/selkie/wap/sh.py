
import os, stat, shutil, subprocess, tempfile
from tempfile import TemporaryDirectory as tmpdir, NamedTemporaryFile
from os.path import expanduser, join
from glob import glob
from urllib.request import urlretrieve
from io import StringIO
from time import ctime


def norm_filename (fn, default='pwd'):
    if not fn:
        if default == '~':
            return expanduser('~')
        elif default == 'pwd':
            return pwd()
        elif default:
            raise Exception(f'Bad default value: {default}')
        else:
            raise Exception('No filename provided')
    elif fn.startswith('~'):
        return expanduser(fn)
    else:
        return fn

def norm_filenames (fns, default='pwd'):
    for ptn in fns:
        ptn = norm_filename(ptn, default)
        if '*' in ptn:
            yield from glob(ptn)
        else:
            yield ptn


#--  Testing filenames  --------------------------------------------------------

def exists (fn):
    return os.path.exists(norm_filename(fn))

def isfile (fn):
    return os.path.isfile(norm_filename(fn))

def isdir (fn):
    return os.path.isdir(norm_filename(fn))

def islink (fn):
    return os.path.islink(norm_filename(fn))

from os.path import isabs

class Time (object):

    def __init__ (self, value):
        self.value = value

    def __eq__ (self, other):
        if isinstance(other, Time):
            other = other.value
        return self.value == other
        
    def __lt__ (self, other):
        if isinstance(other, Time):
            other = other.value
        return self.value < other

    def __le__ (self, other):
        if isinstance(other, Time):
            other = other.value
        return self.value <= other

    def __gt__ (self, other):
        if isinstance(other, Time):
            other = other.value
        return self.value > other

    def __ge__ (self, other):
        if isinstance(other, Time):
            other = other.value
        return self.value >= other

    def __repr__ (self):
        return ctime(self.value)

def modtime (fn):
    return Time(os.stat(norm_filename(fn)).st_mtime)

def filesize (fn):
    return os.stat(norm_filename(fn)).st_size


#--  Modifying filenames  ------------------------------------------------------

def basename (fn):
    return os.path.basename(norm_filename(fn))

def dirname (fn):
    return os.path.dirname(norm_filename(fn))

def suffix (fn):
    (_, sfx) = os.path.splitext(fn)
    return sfx

from os.path import expanduser


#--  System  -------------------------------------------------------------------

from os import environ as ENV, system as sh, getpid as pid
from sys import stdin, stdout, stderr, argv

def error (*msg, code=1):
    print(*msg, file=stderr)
    exit(code)

# text=True - stdout and stderr are opened in text format, not binary format

def backtick (comline):
    if isinstance(comline, (list, tuple)):
        args = comline
    else:
        args = comline.split()
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout

# with tmpfile() as tmp

def tmpfile ():
    f = NamedTemporaryFile(delete_on_close=False)
    fn = TmpFile(f.name)
    fn.f = f
    return fn

class TmpFile (str):
    
    def __enter__ (self):
        self.f.__enter__()
        self.f.close()
        return self
    
    def __exit__ (self, t, v, tb):
        self.f.__exit__(t,v,tb)


#--  Distinguished files  ------------------------------------------------------

from os import getcwd as pwd

def home ():
    return ENV['HOME']


#--  Navigation  ---------------------------------------------------------------

class CurrentDirectory (object):

    def __init__ (self, fn):
        self.filename = norm_filename(fn)
        self.saved_filename = None

    def __enter__ (self):
        assert self.saved_filename is None, 'Attempt to enter CurrentDirectory twice'
        self.saved_filename = pwd()
        cd(self.filename)

    def __exit__ (self, t, v, tb):
        cd(self.saved_filename)


def cd (fn=None):
    fn = norm_filename(fn, default='~')
    os.chdir(fn)

def ls (fn='', flags=''):
    fn = norm_filename(fn)
    # follow a symlink unless long mode
    if 'l' not in flags and 'H' not in flags:
        flags += 'H'
    if flags:
        flags = ' -' + flags
    sh(f"ls{flags} {fn}")

from os import listdir

def walk (fn):
    for (relpath, subdirnames, filenames) in os.walk(fn, followlinks=True):
        for name in filenames:
            yield join(relpath, name)


#--  Viewing files  ------------------------------------------------------------

def cat (*fns, to=None, ato=None):
    if to or ato:
        mode = 'a' if ato else 'w'
        with open(to or ato, mode) as of:
            for fn in norm_filenames(fns):
                with open(fn) as f:
                    print(f.read(), end='', file=of)
    else:
        for fn in norm_filenames(fns):
            with open(fn) as f:
                print(f.read(), end='')

def echo (*strings, to=None, ato=None):
    if to or ato:
        mode = 'a' if ato else 'w'
        with open(to or ato, mode) as of:
            for string in strings:
                print(string, end='', file=of)
            print(file=of)
    else:
        for string in strings:
            print(string, end='')
        print()

def more (fn):
    fn = norm_filename(fn)
    sh(f"more '{fn}'")

def wc (fn):
    fn = norm_filename(fn)
    sh(f"wc '{fn}'")

def od (fn, type='c'):
    fn = norm_filename(fn)
    sh(f"od -t {type} '{fn}'")


#--  Creating and modifying files  ---------------------------------------------

def touch (fn):
    fn = norm_filename(fn)
    if not exists(fn):
        with open(fn, 'w'):
            pass

def cp (src, dst, flags=''):
    (src, dst) = (norm_filename(src), norm_filename(dst))
    if flags == 'r':
        shutil.copytree(src, dst)
    elif flags == '':
        shutil.copyfile(src, dst)
    else:
        raise Exception(f'Unrecognized flags: {flags}')

def ln (src, dst, mode=''):
    (src, dst) = (norm_filename(src), norm_filename(dst))
    if mode == 's':
        os.symlink(src, dst)
    else:
        os.link(src, dst)

def mv (src, dst):
    (src, dst) = (norm_filename(src), norm_filename(dst))    
    shutil.move(src, dst)

def rm (fn, flags=''):
    fn = norm_filename(fn)
    if flags == 'rf':
        shutil.rmtree(fn)
    else:
        os.unlink(fn)


#--  Chmod  --------------------------------------------------------------------

##  Change permissions.

def chmod (fn, perm):
    if isinstance(perm, str):
        _chmodstr(fn, perm)
    elif isinstance(perm, int):
        os.chmod(fn, perm)
    else:
        raise Exception('Bad perm: %s' % repr(perm))


_masks = {'u': stat.S_IRWXU,
          'g': stat.S_IRWXG,
          'o': stat.S_IRWXO,
          'a': stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO}

_perms = {('u','r'): stat.S_IRUSR,
          ('u','w'): stat.S_IWUSR,
          ('u','x'): stat.S_IXUSR,
          ('g','r'): stat.S_IRGRP,
          ('g','w'): stat.S_IWGRP,
          ('g','x'): stat.S_IXGRP,
          ('o','r'): stat.S_IROTH,
          ('o','w'): stat.S_IWOTH,
          ('o','x'): stat.S_IXOTH,
          ('a','r'): stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH,
          ('a','w'): stat.S_IWUSR|stat.S_IWGRP|stat.S_IWOTH,
          ('a','x'): stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH}

def _chmodstr (fn, permstr):

    perm = 0
    mask = 0

    i = 0
    while i < len(permstr):
        c = permstr[i]
        if c in _masks:
            mask |= _masks[c]
            i += 1
        else:
            break
    if i == 0:
        who = 'u'
        nwho = 1
        mask = _masks['u']
    else:
        who = permstr
        nwho = i

    if permstr[i] == '+': unset = False
    elif permstr[i] == '-': unset = True
    else: raise Exception('Expected + or -')
    i += 1

    while i < len(permstr):
        c = permstr[i]
        i += 1
        for j in range(nwho):
            key = (who[j], c)
            if key in _perms:
                perm |= _perms[key]
            else:
                raise Exception('Unexpected char: %s' % c)

    old = os.stat(fn).st_mode

    if unset:
        new = old & ~perm
    else:
        new = old | perm

    os.chmod(fn, new)


#--  Creating and modifying directories  ---------------------------------------

def mkdir (fn):
    fn = norm_filename(fn)
    if exists(fn):
        if isdir(fn):
            print('Directory already exists:', fn)
        else:
            print('** File already exists, is not a directory:', fn)
    else:
        dfn = dirname(fn) or pwd()
        if not exists(dfn):
            print('Creating intermediate directories')
        os.makedirs(fn)

def rmdir (fn):
    os.rmdir(norm_filename(fn))


#--  Wget, tar  ----------------------------------------------------------------

def wget (url, fn=None):
    if fn is None:
        fn = basename(url)
    urlretrieve(url, fn)
    return fn

def tar (flags='x', fn=None, *targets):
    assert fn, 'Must provide tarfile name'
    flags += 'f'
    if fn.endswith('.bz2'):
        flags += 'y'
    elif fn.endswith('.tgz') or fn.endswith('.gz'):
        flags += 'z'
    sh(f'tar {flags} {fn} {" ".join(targets)}')
