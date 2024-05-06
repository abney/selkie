
import os, sys, stat, shutil, subprocess
from io import StringIO
from .io import iter_lines
from glob import glob


#--  open and close  -----------------------------------------------------------

_builtin_open = open

##  Accepts redirects.

def open (fn, mode='r'):
    if fn is None: return sys.stdout
    if not isinstance(fn, str): raise Exception('Bad filename')
    fn = fn.strip()
    if not fn: return sys.stdout
    if fn.startswith('>'):
        if fn.startswith('>>'):
            mode = 'a'
            fn = fn[2:]
        else:
            mode = 'w'
            fn = fn[1:]
        if len(fn) == 0: raise Exception('Illegal redirect')
        elif fn == '1':
            return sys.stdout
        elif fn == '2':
            return sys.stderr
        elif fn[0].isdigit() or fn[0] in '<|>':
            raise Exception('Illegal redirect')
        fn = fn.strip()
        if (not fn): raise Exception('Illegal redirect')
        return _builtin_open(fn, mode)
    elif fn.startswith('<'):
        fn = fn[1:]
        if fn == '0': return sys.stdin
        elif fn[0].isdigit() or fn[0] in '<|>':
            raise Exception('Illegal redirect')
        fn = fn.strip()
        if (not fn): raise Exception('Illegal redirect')
        return _builtin_open(fn, 'r')
    else:
        return _builtin_open(fn, mode)

##  Close.

def close (f):
    if f is sys.stdin or f is sys.stdout or f is sys.stderr:
        pass
    else:
        f.close()


#--  Environment variables  ----------------------------------------------------

##  Set an environment variable.

def setenv (var, val):
    os.environ[var] = val

##  Expand $ENVVAR references and print.

def echo (s, fn=None):
    s = expand_envvars(s)
    f = open(fn, 'a')
    print(s, file=f)
    close(f)


#--  Creating directories  -----------------------------------------------------

from os import mkdir

##  Create a directory and all missing ancestors.

def mkdirp (fn):
    if not fn: raise Exception('Empty filename')
    if os.path.exists(fn):
        if not os.path.isdir(fn):
            raise Exception('Exists, but not a directory: ' + fn)
    else:
        os.makedirs(fn)

##  Same as mkdirp.

def need_dir (dir):
    mkdirp(dir)

##  Call mkdirp on the directory portion.

def need_parent (fn):
    dir = os.path.dirname(fn)
    # if fn is 'foo', dir is ''
    if dir:
        mkdirp(dir)


#--  Creating files  -----------------------------------------------------------

##  Touch a file.

def touch (file):
    os.system('touch ' + file)

##  Concatenate multiple files.

def cat (*filenames):
    if len(filenames) == 1:
        outfile = sys.stdout
    else:
        outfile = open(filenames[-1], 'w')
        filenames = filenames[:-1]
    for fn in filenames:
        for line in iter_lines(fn):
            print(line, file=outfile)
    close(outfile)


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

##  Readable version of permissions value.

def mod_string (mode):
    with StringIO() as out:
        if mode & stat.S_ISUID: out.write('U')
        if mode & stat.S_ISGID: out.write('G')
        if mode & stat.S_ISVTX: out.write('T')
        if mode & stat.S_IRUSR: out.write('r')
        else: out.write('-')
        if mode & stat.S_IWUSR: out.write('w')
        else: out.write('-')
        if mode & stat.S_IXUSR: out.write('x')
        else: out.write('-')
        if mode & stat.S_IRGRP: out.write('r')
        else: out.write('-')
        if mode & stat.S_IWGRP: out.write('w')
        else: out.write('-')
        if mode & stat.S_IXGRP: out.write('x')
        else: out.write('-')
        if mode & stat.S_IROTH: out.write('r')
        else: out.write('-')
        if mode & stat.S_IWOTH: out.write('w')
        else: out.write('-')
        if mode & stat.S_IXOTH: out.write('x')
        else: out.write('-')
        return out.getvalue()

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


#--  Examining files  ----------------------------------------------------------

##  Word count.

def wc (fn):
    os.system('wc ' + fn)

##  Octal dump.

def od (fn, type='c'):
    os.system("od -t %s '%s'" % (type, fn))

##  Paging.

def more (fn):
    os.system("more '%s'" % fn)


#--  Testing  ------------------------------------------------------------------

from os.path import isfile, isdir, islink, isabs, exists, basename, dirname


#--  Navigation  ---------------------------------------------------------------

##  Returns the current working directory.

def pwd ():
    return os.getcwd()

##  Change directory.

def cd (dir=None):
    if dir == None: dir = os.environ.get('HOME')
    dir = os.path.expanduser(dir)
    os.chdir(dir)

##  List files or directories.

def ls (*fns):
    os.system('ls ' + ' '.join(fns))

##  Long-form listing.

def lsl (*fns):
    os.system('ls -l ' + ' '.join(fns))

##  Display directories themselves, not their contents.

def lsd (*fns):
    os.system('ls -d ' + ' '.join(fns))

##  Long form.

def lsld (*fns):
    os.system('ls -ld ' + ' '.join(fns))

##  Sort newest to oldest.

def lslt (*fns):
    os.system('ls -lt ' + ' '.join(fns))

##  Return a list of file names.

def listdir (dir='.'):
    return os.listdir(dir)


#--  Cwd  ----------------------------------------------------------------------

##  To change the current directory temporarily.
#
#       with Cwd():
#           ...
#
#  On exit, undoes any chdir() in the body.

class Cwd (object):

    ##  @var wd
    #   The original working directory.

    ##  Enter.

    def __enter__ (self):
        self.wd = os.getcwd()

    ##  Exit.

    def __exit__ (self, t, v, tb):
        os.chdir(self.wd)


#--  Copying  ------------------------------------------------------------------

##  Copy.  If more than two filenames are provided, the last must name a directory
#   and the copies are created in that directory.  If there are two and the second
#   names an existing directory, the first is copied into the directory.

def cp (*filenames):
    if len(filenames) == 1:
        raise Exception('Need at least two arguments to cp')
    filenames = [os.path.expanduser(fn) for fn in filenames]
    dest = filenames[-1]
    filenames = filenames[:-1]
    if isdir(dest):
        for fn in filenames:
            name = basename(fn)
            fn2 = os.path.join(dest, name)
            print('Copy', fn, fn2)
            shutil.copy(fn, fn2)
    else:
        if len(filenames) != 1:
            raise Exception('Cannot copy multiple files to a regular file')
        shutil.copy(filenames[0], os.path.join(dest))

##  Copy an entire directory hierarchy.

def cpr (src, tgt):
    shutil.copytree(src, tgt, symlinks=True)

##  Rename.

def mv (src, dst):
    shutil.move(src, dst)

from os import symlink as ln
from os import link


#--  Deletion  -----------------------------------------------------------------

from os import rmdir

##  Delete files.

def rm (*gfns):
    for gfn in gfns:
        for fn in glob(gfn):
            if exists(fn):
                os.unlink(fn)
            else:
                print('File not found:', fn, file=sys.stderr)

##  Recursively delete a directory hierarchy.

def rmrf (dir):
    if (not isinstance(dir, str)) or (not dir) or (dir == '/'):
        raise Exception('Invalid directory: %s' % repr(dir))
    if exists(dir):
        if isdir(dir):
            shutil.rmtree(dir)
        else:
            os.unlink(dir)


#--  Misc  ---------------------------------------------------------------------

from os import system as sh
from os import getpid as pid


##  Launch an application.

def launch (fn):
    os.system("open " + fn)
