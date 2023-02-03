##  @package seal.cld.db.file
#   The main File class.

import os, sys
from os.path import dirname, abspath, expanduser, exists
from ..fs import ls
from ..object import import_class, class_name
from ..io import load_dict, save_dict, load_lines, BackingSave, pprint
from .disk import Disk, DiskWriter, writer
from .env import Environment
from .permissions import Permissions, InheritedPermissions, Everyone, GroupsFile
from .meta import PropListMixin, Index


def _BOM (name):
    return '##BOM' + name + '\n'

_EOM = '##EOM\n'


#--  MetadataInputStream  ------------------------------------------------------

##  Used to read the contents of a metadata item.  Pretends that it has
#   reached EOF when it reaches _EOM.

class MetadataInputStream (object):

    ##  Constructor.  Takes a regular input stream and a metadata item name.

    def __init__ (self, f, name):

        ##  The regular input stream.
        self.raw_stream = f

        line = next(f)
        if line != _BOM(name):
            raise Exception('Missing metadata section: %s' % name)

    ##  Returns self.

    def __iter__ (self):
        return self

    ##  The iterator method.

    def __next__ (self):
        for line in self.raw_stream:
            if line == _EOM:
                self.raw_stream = None
                raise StopIteration
            else:
                return line


#--  File  ---------------------------------------------------------------------

##  The class for persistent Files.
#   For general discussion, see <a href="../../../cld/database.html">Database</a>.</p>
#
#   Specializations should generally
#   override <tt>__read__()</tt>, and <tt>__write__()</tt>.
#   Specialization methods that access content members should
#   call <tt>require_load()</tt>, or <tt>with self.writer()</tt> if they may
#   potentially modify content members.  If they actually modify contents,
#   they should call <tt>modified()</tt> as well.
#
#   A database is just a root File (no parent).

class File (object):

    ##  All Files are text files.

    encoding = 'utf8'

    ##  Metadata information: (member, class) pairs.

    __metadata__ = tuple()

    ##  Adds an extra metadata item for Permissions.  It receives special treatment.

    __has_permissions__ = False

    ##  For the use of Environment.  Ignored unless the Environment's host is the root.

    types = None
    
    ##  What types, if any, are indexed.  A Directory is an index root just
    #   in case indexed is non-null.

    indexed = None

    ##  Used by the default create_env implementation.

    envclass = Environment


    #--  Initialization  ---------------------------------------

    ##  Constructor.
    #
    #   If env is None, it uses parent.env.
    #   Error if parent and env are both None.
    #   The parent, name, and filename are stored in private members.
    #   If there is no parent, name must be None.
    #
    #   If there is a parent, the filename is obtained by joining name to
    #   the parent's filename.  If there is no parent, 
    #   the filename is env.filename() and
    #   this file becomes
    #   env.root (which must not already exist).
    #
    #   There is a private member containing a Writer, initially None.
    #   There are private flags for whether the file has been loaded or modified
    #   (both initially False).

    def __init__ (self, parent=None, name=None, suffix=None):

        isroot = parent is None
        ownperm = self.__has_permissions__ or isroot
        if isroot:
            assert name is None and suffix is None

        ##  The Environment.
        self.env = None

        self._parent = parent
        self._name = name
        self._suffix = suffix
        self._perm = None
        self._writer = None
        self._loaded = False
        self._modified = False
        self._metaitems = []
        self._npermitems = 0

        # set up _metaitems
        if ownperm:
            self._metaitems.append(('_perm', Permissions))
            self._npermitems += 1
        if isroot:
            self._metaitems.append(('_groups', GroupsFile))
            self._npermitems += 1
        if self.indexed:
            self._metaitems.append(('_index', Index))
        if self.__metadata__:
            self._metaitems.extend(self.__metadata__)

        # create env
        self.env = self.create_env() or self._parent.env
        if isroot:
            self.env['root'] = self
            self.env['log'] = pprint
            self.env['disk'] = Disk(pprint)
        if self.indexed:
            assert isroot or self.env != parent.env
            self.env['index_root'] = self

        # create InheritedPermissions.  InheritedPermissions.__init__ requires env
        if not ownperm:
            self._perm = InheritedPermissions(self)

        # instantiate metadata.  Metadata.__init__ requires env
        for (name, cls) in self._metaitems:
            self._instantiate_metadata_item(name, cls)

    ##  Only for an existing item in _metaitems.

    def _instantiate_metadata_item (self, name, cls):
        if hasattr(self, name) and getattr(self, name) is not None:
            raise Exception('Metadata member is already set: %s' % name)
        f = cls(self)
        setattr(self, name, f)

    ##  Caution: when this is called, the metadata has not yet been set up.

    def create_env (self):
        if self.indexed or self._parent is None:
            return self.envclass(self)

    ##  The metadata items.

    def metadata_items (self):
        for (name, _) in self._metaitems:
            yield getattr(self, name)

    ##  String representation.

    def __repr__ (self):
        return '<%s %s>' % (self.__class__.__name__, self._name)


    #--  Location  ---------------------------------------------

    ##  Returns the parent.
    def parent (self): return self._parent

    ##  Returns the name.
    def name (self): return self._name

    ##  Returns the suffix.
    def suffix (self): return self._suffix

    ##  Returns False.  Overridden by Directory.
    def is_directory (self): return False

    ##  The children.
    def children (self): return [] # so that it's iterable

    ##  An iterator over the ancestors, bottom-up, including this file itself.

    def ancestors (self, root=None):
        x = self
        while x is not root:
            if x is None:
                raise Exception('Root not found')
            yield x
            x = x._parent

    ##  True if parent is None.

    def isroot (self):
        return self._parent is None

    ##  A string consisting of the names on the path from the root to this File,
    #   connected by slashes.

    def logrelpath (self):
        # root has no name
        ancnames = [a.name() for a in self.ancestors() if a.parent() is not None]
        ancnames.reverse()
        return '/'.join(ancnames)

    ##  A string consisting of the names on the path from this File to the given
    #   descendant File, connected by slashes.

    def logpathto (self, descendant):
        names = [f.name() for f in descendant.ancestors(root=self)]
        names.reverse()
        return '/'.join(names)

    ##  Follows a logical path consisting of names without suffixes.

    def join (self, *names):
        if names:
            raise Exception('Not a directory')
        else:
            return self

    ##  Synonym for join().

    def __truediv__ (self, name):
        return self.join(name)

    ##  Follow a pathname down to a descendant.

    def follow (self, pathname):
        if pathname.startswith('/'):
            pathname = pathname[1:]
        item = self
        if pathname:
            cpts = pathname.split('/')
            for cpt in cpts:
                item = item.join(cpt)
        return item

    ##  Return the index table for my class, if one exists.
    #   The environment may provide an index.  An index maps from a suffix
    #   to a table.  The File class determines a unique suffix.
    #   A table maps from an ID, which must be unique within the table,
    #   to an instance of the associated class.  This provides direct access
    #   to instances by ID.

    def index_table (self):
        suffix = self.env.get_suffix(self.__class__)
        if suffix:
            index = self.env.index()
            if index is not None and suffix in index:
                return index[suffix]


    #--  Implementation  ---------------------------------------

    ##  Has the form NAME.SUFFIX.

    def _typed_name (self):
        if self._suffix: return self._name + '.' + self._suffix
        else: return self._name

    ##  Returns the relative pathname of this
    #   file, relative to the database root.

    def _relpath (self):
        if self._parent is None:
            return ''
        else:
            ancs = list(self.ancestors())
            cpts = []
            i = len(ancs) - 1
            while i > 0:
                i -= 1
                cpts.append(ancs[i]._typed_name())
            return os.path.join(*cpts)

    ##  Returns the filename.  If there is a
    #   parent, this is the parent's filename joined with this file's
    #   name.  If there is no parent, this is env.filename().'''

    def _filename (self):
        root = self.env['filename']
        if root is None:
            raise Exception('No root filename: %s' % repr(self))
        # Don't call join with empty relpath, because it adds trailing slash
        if self._parent is None:
            return root
        else:
            return os.path.join(root, self._relpath())

    ##  Returns the contents filename.  Differs from filename only if this
    #   is a directory.

    def _contents_filename (self):
        return self._filename()

    ##  If this is a regular file, returns
    #   the parent's filename.  If this is a directory, returns the filename.

    def _directory_filename (self):
        return self._parent._filename()

    ##  If <tt>directory()</tt> does not exist,
    #   create it and any missing ancestors.

#     def makedirs (self):
#         p = self._parent
#         if p is None: d = None
#         else: d = p.filename()
#         self.env['disk'].makedirs(self._directory_filename())

    ##  Prints a directory listing, if this is a directory.

    def _ls (self):
        fn = self._filename()
        if os.path.isdir(fn):
            ls(fn)

    #--  Modifying directory hierarchy  ------------------------

    ##  Create the file on disk.
    #   Users should call directory's new_child() method.
    #   __create__ ONLY creates the disk-file or -directory for an existing File.

    def __create__ (self):
        if self._loaded:
            raise Exception('Already loaded')
        fn = self._contents_filename()
        if exists(fn):
            raise Exception('File already exists: %s' % fn)
        disk = self.env['disk']
        dir = dirname(fn)
        if not exists(dir):
            disk.makedirs(dir)
        # can't use __save__ here - it does require_load first
        with disk.open_write(fn) as f:
            for (name, _) in self._metaitems:
                f.write(_BOM(name))
                f.write(_EOM)
        self.__init_contents__()

    ##  Initialize content members.  The default implementation is a no-op.
    #   It is an update method, and should either be wrapped in 'with self.writer()' or
    #   call protected update methods.

    def __init_contents__ (self):
        pass

    ##  Called by my parent when I am created.  If I have an index table,
    #   this notifies the index table and causes me to be indexed.

    def created (self):
        table = self.index_table()
        if table is not None:
            table.created(self)

    ##  Change my parent.  Quite a few things need to be updated if a parent
    #   changes; this takes care of it.

    def reparent (self, newparent, i=None):
        if self._writer is not None:
            raise Exception('File is being saved')
        if self._parent is None:
            raise Exception('Cannot reparent a root node')
        if self._parent is newparent:
            raise Exception('New parent is same as old parent')

        newparent = newparent.attachment_target()
        if newparent.env is not self._parent.env:
            raise Exception('Cannot move outside the scope of env')
        oldlrp = self.logrelpath()

        oldparent = self._parent
        oldparent.check_permission('write')
        newparent.check_permission('write')
        oldfn = self._filename()
        newfn = os.path.join(newparent._filename(), self._typed_name())
        if newfn.startswith(oldfn):
            raise Exception('Attempt to create cycle')

        oldparent.detach_child(self)
        self.env['disk'].move(oldfn, newfn)
        self._parent = newparent
        newparent.attach_child(self, i=i)

        with writer(self.env.index()): # ignores it if index is None
            self._moved_recurse(oldlrp)
            
    def _moved_recurse (self, oldlrp):
        self.moved(oldlrp)
        for child in self.children():
            child._moved_recurse(oldlrp + '/' + child.name())

    ##  Notification that my parent has changed.  If I have an index table,
    #   this notifies it and causes the index information to be updated.

    def moved (self, oldlrp):
        table = self.index_table()
        if table is not None:
            table.moved(self)

    ##  Whether or not my file exists on disk.

    def exists (self):
        return os.path.exists(self._filename())

    ##  Delete me and any index information pointing to me.

    def delete (self):
        if self._parent is None:
            self.delete_file()
        else:
            idx = self.env.index()
            if idx is not None:
                with writer(idx):
                    self._deleted_recurse()
            self.delete_file()
            self._parent.detach_child(self)

    def _deleted_recurse (self):
        self.deleted()
        for child in self.children():
            child._deleted_recurse()

    ##  Notification that I have been deleted.  Causes my index information
    #   to be updated.

    def deleted (self):
        table = self.index_table()
        if table is not None:
            table.deleted(self)

    ##  Delete my file on disk.

    def delete_file (self):
        self.env['disk'].nuke(self._filename())

    #-----------------------------------------------------------
    #  loading

    ##  Anything that may get modified when I am modified.  The default
    #   implementation returns the empty list.

    def requires (self): return []

    ##  Does nothing if the load flag is True.
    #   Signals an error if the load flag is <tt>'loading'</tt> (load cycle
    #   detected).  Otherwise, it does the following.
    #   Temporarily sets the load flag to <tt>'loading'</tt>.
    #   Calls <tt>check_permission('read')</tt>, then <tt>__load__()</tt>.
    #   If <tt>__load__()</tt> returns without error, sets the load flag to True.

    def require_load (self):
        if self._loaded is False:
            self._loaded = 'loading'
            self.__load__()
        elif self._loaded == 'loading':
            raise Exception('Load cycle detected')

    ##  If the target file exists, open it for reading and pass it
    #   to <tt>__read__()</tt>.  Otherwise, do nothing.

    def __load__ (self):
        with open(self._contents_filename(), encoding=self.encoding) as f:
            for (name, _) in self._metaitems[:self._npermitems]:
                self._read_metaitem(name, f)
            self.check_permission('read')
            for (name, _) in self._metaitems[self._npermitems:]:
                self._read_metaitem(name, f)
            self.__read__(f)

        self._loaded = True
        self._modified = False

    ##  This is solely for the use of PermItem.require_load.  It only loads the
    #   permission items.

    def _load_permissions (self):
        with open(self._contents_filename(), encoding=self.encoding) as f:
            for (name, _) in self._metaitems[:self._npermitems]:
                mf = self._read_metaitem(name, f)
                mf._loaded = True

    def _read_metaitem (self, name, f):
        mf = getattr(self, name)
        mf.__read__(MetadataInputStream(f, name))
        return mf

    ##  To be implemented by specializations.  A specialization should
    #   initialize content members appropriately in the constructor,
    #   because <tt>__read__()</tt> is only called if the file exists.

    def __read__ (self, f):
        raise Exception('Specializations must implement')

    ##  This is ONLY called by Writer.__exit__, when a save fails and
    #   the old state needs to be restored.

    def _reload (self):
        self._loaded = 'loading'
        self.__load__()

    #-----------------------------------------------------------
    #  saving

    ##  Just calls the function writer().

    def writer (self):
        return writer(self)

    # called by Writer.__exit__()

    ##  Only for use by the exit method of <a href="#Writer">Writer</a>.
    #   Calls <a href="#FileWithBackup">FileWithBackup</a> in
    #   a with-statement, and calls <tt>__write__()</tt> in that context.
    #   Then turns off the modified flag.

    def __save__ (self):
        with DiskWriter(self) as f:
            for (name, _) in self._metaitems:
                f.write(_BOM(name))
                mf = getattr(self, name)
                mf.__write__(f)
                f.write(_EOM)
            self.__write__(f)
        self._modified = False

    ##  To be overridden by specializations.  The default implementation
    #   signals an error.

    def __write__ (self, f):
        raise Exception('Specializations must override')

    ##  Must be called within the body of <code>with writer(file)</code>
    #   or <code>with Loading(file)</code>.

    def modified (self):
        if self._writer is None:
            raise Exception("Unprotected call to 'modified'")
        self._modified = True

    ##  Whether I have been modified since the last save.

    def is_modified (self):
        return self._modified

    #-----------------------------------------------------------
    #  Permissions

    ##  Returns the permissions.

    def permissions (self):
        return self._perm

    ##  Dispatches to the Permissions object.

    def permitted (self, action, user=None):
        return self.permissions().permitted(action, user)

    ##  Dispatches to the Permissions object's <tt>check()</tt> method.

    def check_permission (self, action, user=None):
        return self.permissions().check(action, user)

    #--  Root file  --------------------------------------------

    ##  Create the database on disk.

    def create (self, force=False):
        if self._parent is not None:
            raise Exception('Method create is only available for the root File')
        fn = self._filename()
        if os.path.exists(fn):
            if force:
                self.delete_file()
            else:
                raise Exception('Database already exists: %s' % fn)
        self.__create__()

    ##  Set the username.  Error unless this is the root file.

    def set_username (self, username):
        if self.parent() is not None:
            raise Exception('The method set_username is only available for the root File')
        self.env['username'] = username


#--  Integer  ------------------------------------------------------------------

##  A file containing a single integer.

class Integer (File):

    ##  Read it from an open file.

    def __read__ (self, f):
        try:
            line = next(f)
            self._value = int(line.rstrip('\r\n'))
        except StopIteration:
            self._value = 0

    ##  Write it to an open file.

    def __write__ (self, f):
        f.write(str(self._value))
        f.write('\n')

    ##  Return the value (an int).

    def value (self):
        self.require_load()
        return self._value

    ##  Set the value.

    def set (self, value):
        with writer(self):
            self.modified()
            self._value = value

    ##  Increment the value.

    def incr (self):
        with writer(self):
            self.modified()
            self._value += 1


#--  String  -------------------------------------------------------------------

##  A File that contains a single string.

class String (File):

    ##  Read one from a stream.

    def __read__ (self, f):
        try:
            self._value = next(f).rstrip('\r\n')
        except StopIteration:
            self._value = ''

    ##  Write one to a stream.

    def __write__ (self, f):
        f.write(self._value)
        f.write('\n')

    ##  Get the value (a string).

    def value (self):
        self.require_load()
        return self._value

    ##  Set the value.

    def set (self, value):
        if not isinstance(value, str):
            raise ValueError('Not a string: %s' % repr(value))
        with writer(self):
            self.modified()
            self._value = value


#--  Strings  ------------------------------------------------------------------

##  A File that contains a list of strings.

class Strings (File):

    ##  Read one from a stream.

    def __read__ (self, f):
        self._value = []
        for line in f:
            self._value.append(line.rstrip('\r\n'))

    ##  Write one to a stream.

    def __write__ (self, f):
        for s in self._value:
            f.write(s)
            f.write('\n')

    ##  The number of strings.

    def __len__ (self):
        self.require_load()
        return len(self._value)

    ##  Iterate over the strings.

    def __iter__ (self):
        self.require_load()
        return self._value.__iter__()

    ##  Get the i-th string.

    def __getitem__ (self, i):
        self.require_load()
        return self._value.__getitem__(i)

    ##  Set the i-th string.

    def __setitem__ (self, i, s):
        with writer(self):
            lst = self._value
            if i < len(lst) and lst[i] == s: return
            self.modified()
            while len(lst) <= i: lst.append('')
            lst[i] = s

    ##  Append a new string.

    def append (self, s):
        with writer(self):
            self.modified()
            self._value.append(s)

    ##  Insert a string at position i.

    def insert (self, i, s):
        with writer(self):
            lst = self._value
            self.modified()
            while len(lst) <= i: lst.append('')
            lst[i:i] = [s]

    ##  Delete the string at position i.

    def __delitem__ (self, i):
        with writer(self):
            lst = self._value
            if i < 0:
                i += len(lst)
            if 0 <= i < len(lst):
                self.modified()
                del lst[i]
            else:
                raise IndexError('Index out of range')


#--  Table  --------------------------------------------------------------------

##  A File that contains tabular data.

class Table (File):

    ##  Read the contents from a stream.

    def __read__ (self, f):
        self._value = []
        for line in f:
            rec = tuple(line.rstrip('\r\n').split('\t'))
            self._value.append(rec)

    ##  Write the contents to a stream.

    def __write__ (self, f):
        for record in self._value:
            first = True
            for field in record:
                if first: first = False
                else: f.write('\t')
                f.write(field)
            f.write('\n')

    ##  Append a new record.

    def append (self, rec):
        with writer(self):
            self.modified()
            self._value.append(tuple(rec))

    ##  Get the i-th record.

    def __getitem__ (self, i):
        self.require_load()
        return self._value.__getitem__(i)

    ##  The number of records.

    def __len__ (self):
        self.require_load()
        return self._value.__len__()

    ##  Iterate over the records.

    def __iter__ (self):
        self.require_load()
        return self._value.__iter__()


#--  PropDict  -----------------------------------------------------------------

##  A File that contains a dict mapping property names to values.

class PropDict (PropListMixin, File):
    pass
