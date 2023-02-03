##  @package seal.cld.db.disk
#   The substrate that interacts with the disk.

try:
    from fcntl import flock, LOCK_EX
except:
    flock = LOCK_EX = None

import os, shutil
from os.path import exists
from ..fs import rmrf
from ..io import pprint
from .meta import Metadata


##  The input may be either a Metadata item or a File (more precisely,
#   something with a _writer member).  Returns the Metadata host, or the
#   File itself.  Signals an error on any other input.

def get_file (x):
    if isinstance(x, Metadata): return x.host
    elif hasattr(x, '_writer'): return x
    else: raise Exception('Not a file: %s' % x)


#--  Disk  ---------------------------------------------------------------------

##  An abstraction layer over disk access.

class Disk (object):

    ##  Constructor.

    def __init__ (self, log=pprint):

        ##  The log function.
        self.log = log

    ##  Create missing directories above this file.

    def makedirs (self, fn):
        if not exists(fn):
            self.log('disk', 'MakeDirs', fn)
            os.makedirs(fn)

    ##  Rename a file.

    def move (self, oldfn, newfn):
        self.log('disk', 'Move', oldfn, newfn)
        shutil.move(oldfn, newfn)

    ##  Open a file for writing.

    def open_write (self, fn, binary=False):
        if binary: mode = 'wb'
        else: mode = 'w'
        if exists(fn):
            self.log('disk', 'Modify', fn)
        else:
            self.log('disk', 'CreateFile', fn)
        return open(fn, mode)

    ##  Delete a file or directory and all its descendants.

    def nuke (self, fn):
        if exists(fn):
            self.log('disk', 'RecursiveDelete', fn)
            rmrf(fn)


#--  DiskWriter  ---------------------------------------------------------------

##  Handles locking and undo.
#   
#   Called by BaseFile.__save__ in the context of a Writer.
#
#   A substitute for <tt>open(fn, 'w')</tt> that does error trapping and
#   backup.  Should only be used in a with-statement:</p>
#
#       with DiskWriter(obj, binary=False, makedirs=False) as f:
#           f.write(...)
#           print(..., file=f)
#
#   The <tt>binary</tt> and <tt>makedirs</tt> keywords set members of the
#   same name; they default to False.
#   On entry, if <tt>makedirs</tt> is set, then any missing ancestor
#   directories are created.  All writes to the stream <tt>f</tt> go to a
#   temp file.  On exit without error, the temp file is closed, the target
#   file is moved to become a back-up, and the temp file is moved into its
#   place.  On exit with error, the temp file is deleted and the target
#   file is left unchanged.

class DiskWriter (object):

    ##  Constructor.  Accepts keyword arguments <tt>binary</tt> and <tt>makedirs</tt>.

    def __init__ (self, obj, binary=False, makedirs=False):

        ##  The object being written; an instance of File.
        self.obj = obj

        ##  An absolute pathname.
        self.filename = obj._contents_filename()

        ##  Whether or not to create ancestor directories.
        self.makedirs = makedirs

        ##  Whether or not to use <tt>'bw'</tt> mode.
        self.binary = binary

        ##  The name of the temp file.  It is the filename plus <tt>.tmp</tt>.
        self.tmp = self.filename + '.tmp'

        ##  A stream writing to the temp file, or None.
        self.file = None

    ##  Write a string.

    def write (self, s):
        self.file.write(s)

    ##  Enter.
    #   If the filename's directory does not exist, create it
    #   (if <tt>makedirs</tt> is true) or signal an error
    #   (if <tt>makedirs</tt> is false).  Then open the temp file and store
    #   the stream in <tt>file</tt>.

    def __enter__ (self):
        dir = os.path.dirname(self.filename)
        # if filename contains no slash, dir is ''
        if dir and not exists(dir):
            if self.makedirs:
                disk = self.obj.env['disk']
                disk.makedirs(dir)
            else:
                raise Exception('Directory does not exist: %s' % dir)
        if self.binary:
            self.file = open(self.tmp, 'wb')
        else:
            self.file = open(self.tmp, 'w', encoding=self.obj.encoding)
        return self

    ##  Exit.
    #   Close <tt>file</tt>.  If errors occurred, delete the temp file.
    #   Otherwise, do the following.  If the backup file exists (filename + <tt>'.bak'</tt>),
    #   delete it.  If the target file exists, rename it as the backup.
    #   Rename the temp file to the target file name.

    def __exit__ (self, type, value, traceback):
        self.file.close()
        if type is None:
            bak = self.filename + '.bak'
            if exists(bak):
                os.unlink(bak)
            if exists(self.filename):
                action = 'Modify'
                shutil.move(self.filename, bak)
            else:
                action = 'Create'
            disk = self.obj.env['disk']
            disk.log('disk', action, self.filename)
            shutil.move(self.tmp, self.filename)
        else:
            if exists(self.tmp):
                os.unlink(self.tmp)
        # No return value - any exception will be raised normally


#--  Lock  ---------------------------------------------------------------------

##  Uses <tt>flock()</tt> to create an exclusive lock on the file.

class Lock (object):

    ##  Constructor.

    def __init__ (self, obj):

        ##  The object being written.
        self.obj = obj

        fn = obj._contents_filename()
        disk = obj.env['disk']
        disk.makedirs(os.path.dirname(fn))
        disk.log('locks', 'Lock', fn)

        ##  The lock's filename.
        self.filename = fn + '.lock'

        ##  The lock file.
        self.file = open(self.filename, 'w')

        flock(self.file, LOCK_EX)

    ##  Close.  Release the lock.

    def close (self):
        disk = self.obj.env['disk']
        disk.log('locks', 'Release', self.obj._contents_filename())
        self.file.close()
        os.unlink(self.filename)
        self.obj = None


#--  Writer  -------------------------------------------------------------------

##  The Writer manages one or more files (instances of BaseFile).  One
#   must be passed to the constructor; more may be added by
#   calling <tt>add_all()</tt>.
#
#   The Writer should be created in a with-statement.  It
#   is <b>active</b> between entry and exit.  On entry, it locks each
#   file, and on successful exit, it saves each file that has been
#   modified.  On unsuccessful exit, it reloads each file that has been
#   modified.  In either case, it releases all locks.
#
#   If files are added while the Writer is active, they are immediately
#   locked.

class Writer (object):

    # file._writer is set immediately
    # we are inside body if file.locks is not None
    # file is locked if in body and file's index in self.files < self.nlocked

    ##  Constructor.
    #   Initialize <tt>files</tt> to contain this file.  Locks is
    #   initially None.

    def __init__ (self, files):

        ##  Files that are being managed by this Writer.
        self.files = []

        ##  One for each file, while the Writer is active.
        self.locks = None

        ##  Number of locked files.
        self.nlocked = 0

        for file in files:
            self.add(file)

    ##  Add <i>file</i> to the file list.  If active, also lock it and
    #   add the lock to the lock list.

    def add (self, file):
        file = get_file(file)
        if file._writer is None:
            self.files.append(file)
            file._writer = self
            if self.locks is not None:
                self.lock_all()
            for r in file.requires():
                self.add(r)

    ##  Create the lock list and lock each file.

    def __enter__ (self):
        self.locks = []
        self.lock_all()
        return self

    ##  Lock all files.

    def lock_all (self):
        while self.nlocked < len(self.files):
            f = self.files[self.nlocked]
            self.nlocked += 1
            f.check_permission('write')
            f.require_load()
            self.locks.append(Lock(f))

    ##  True if we are in the process of locking this file.  To detect cycles.

    def is_locking (self, file):
        if file._writer is not self:
            return False
        for lock in self.locks:
            if lock.obj is file:
                return True
        return False

    ##  Exit.
    #   For each modified file, call its <tt>__save__()</tt> method (if
    #   this is a successful exit) or its <tt>__load__()</tt> method (if
    #   this is an exit on error).  Then release each lock.

    def __exit__ (self, exception_type, v, tb):
        try:
            for file in self.files:
                if file._writer is not None:
                    if file._writer is not self:
                        raise Exception('Writer protocol violation')
                    file._writer = None
                    if file.is_modified():
                        if exception_type is None:
                            file.__save__()
                        else:
                            file._reload()
        finally:
            for lock in self.locks:
                lock.close()
            self.locks = None


##  A dummy writer.  Does nothing.

class DummyWriter (object):

    ##  Enter.

    def __enter__ (self):
        return self

    ##  Exit.

    def __exit__ (self, t, v, tb):
        pass

_dummy_writer = DummyWriter()


##  Create a writer for any of the given files that do not already have
#   active writers.  If none remain, returns a dummy writer.

def writer (*files):
    to_manage = []
    for f in files:
        f = get_file(f)
        if f._writer is None and f not in to_manage:
            to_manage.append(f)
    if to_manage:
        return Writer(to_manage)
    else:
        return _dummy_writer


##  A harness for loading a file.

class Loading (object):

    ##  Constructor.

    def __init__ (self, file):

        ##  The file, but only if it does not already have a writer.
        self.file = None

        if file._writer is None:
            self.file = file

    ##  Enter.

    def __enter__ (self):
        if self.file is not None:
            self.file._writer = self
        return self

    ##  Exit.

    def __exit__ (self, t, v, tb):
        if self.file is not None:
            self.file._writer = None


#--  Undo/redo  ----------------------------------------------------------------

##  Whether a backup file exists.

def is_undoable (file):
    bak = file._contents_filename() + '.bak'
    return exists(bak)

##  Restore the file from backup.

def undo (file):
    with writer(file):
        fn = file._contents_filename()
        bak = fn + '.bak'
        if not exists(bak):
            raise Exception('File is not undoable')
        disk = file.env['disk']
        redofn = fn + '.redo'
        if exists(redofn):
            unlink(redofn)
        disk.move(fn, redofn)
        disk.move(bak, fn)

##  Whether a 'redo' file exists.  It is created when a backup
#   is restored.

def is_redoable (file):
    redofn = file._contents_filename() + '.redo'
    return exists(redofn)

##  Replace the file with its redo.

def redo (file):
    with writer(file):
        fn = file._contents_filename()
        redofn = fn + '.redo'
        if not exists(redofn):
            raise Exception('File is not redoable')
        disk = file.env['disk']
        bak = fn + '.bak'
        if exists(bak):
            unlink(bak)
        disk.move(fn, bak)
        disk.move(redofn, fn)
