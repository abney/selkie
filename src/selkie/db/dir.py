##  @package seal.cld.db.dir
#   Directories on disk.

import os
from os.path import abspath, expanduser, join
from collections import OrderedDict
from ..io import pprint
from .disk import Disk, writer
from .meta import Metadata
from .file import File, Integer, String, Strings, PropDict, Table
from .permissions import Permissions, GroupsFile


##  A special filename is one that starts with underscore, or contains a dot,
#   or ends with tilde or hash.

def is_special_filename (name):
    return (name.startswith('_') or
            '.' in name or
            name.endswith('~') or
            name.endswith('#'))


#--  Directory  ----------------------------------------------------------------

##  Each Directory has children, which are Files (which may be subdirectories).
#   The contents of a Directory is a dict mapping names to children.
#   The load() method reads the directory on disk.  If no disk directory exists,
#   an empty dict is returned.

class Directory (File):

    ##  A map from child name to class.
    signature = None

    ##  The child type, if all (creatable) children have a single type.
    childtype = None

    ##  Default for Directory is to have independent permissions.
    __has_permissions__ = True

    #--  override File methods  --------------------------------

    ##  Returns True.  Overrides the File method.
    def is_directory (self): return True

    ##  Returns my own filename.  Overrides the File method.
    def _directory_filename (self): return self._filename()

    ##  Contents filename.
    def _contents_filename (self):
        return join(self._filename(), '_dir')

    ##  Returns a child.

    def join (self, name):
        if isinstance(name, (tuple, list)):
            file = self
            names = name
            for name in name:
                file = file[name]
            return file
        else:
            return self[name]

    ##  Iterates over the children (File instances).

    def children (self):
        return self.values()


    #--  instantiate child  ------------------------------------

    def _suffix_to_class (self, suffix):
        cls = self.env.get_class(suffix)
        if cls is None:
            raise Exception('No class corresponding to suffix: %s' % suffix)
        return cls

    def _class_to_suffix (self, cls):
        suffix = self.env.get_suffix(cls)
        if suffix is None:
            raise Exception('No suffix corresponding to class: %s' % cls)
        return suffix

    def _instantiate_child (self, name, suffix, cls):
        if cls is None:

            # cls no, suffix no                
            if suffix is None:
                if self.signature and name in self.signature:
                    cls = self.signature[name]
                elif self.childtype:
                    cls = self.childtype
                else:
                    raise Exception('Cannot determine child class')
                suffix = self._class_to_suffix(cls)

            # cls no, suffix yes
            else:
                cls = self._suffix_to_class(suffix)
        else:
            # cls yes, suffix no
            if suffix is None:
                suffix = self._class_to_suffix(cls)

            # cls yes, suffix yes
            else:
                suffixclass = self._suffix_to_class(suffix)
                if suffixclass is not cls:
                    raise Exception('Suffix and class do not match')

        if name is None:
            name = self.allocate_name(suffix)
            if name is None:
                raise Exception('allocate_name returned None')

        return cls(parent=self, name=name, suffix=suffix)

    ##  Called when new_child is called without providing a name.
    #   seal.cld.glab.Library overrides this.

    def allocate_name (self, suffix):
        idx = self.env.index()
        if idx is None:
            raise Exception('No index')
        return idx[suffix].allocate_name(self)


    #--  Children  ---------------------------------------------

    ##  Read the contents from an open file.

    def __read__ (self, f):
        self._map = {}
        self._contents = []
        for line in f:
            (name, suffix) = line.rstrip('\r\n').split('\t')
            if name in self._map:
                raise Exception('Duplicate child: %s' % name)
            child = self._instantiate_child(name, suffix, None)
            self._map[name] = child
            self._contents.append(child)

    ##  Write the contents to an open file.

    def __write__ (self, f):
        for child in self._contents:
            f.write(child._name)
            f.write('\t')
            f.write(child._suffix or '')
            f.write('\n')

    ##  Fetch a child.  The key may be either a string (name) or an int.

    def __getitem__ (self, key):
        self.require_load()
        if isinstance(key, str):
            if key in self._map:
                return self._map[key]
            else:
                raise KeyError("No child with name '%s'" % key)
        elif isinstance(key, int):
            return self._contents[key]
        elif isinstance(key, tuple):
            obj = self
            for name in key:
                obj = obj[name]
            return obj

    ##  If name is in signature, it can be used as a member.

    def __getattr__ (self, name):
        if self.signature and name in self.signature:
            return self.get(name)

    ##  Fetch, but return None on failure.

    def get (self, name):
        self.require_load()
        return self._map.get(name)

    ##  Whether the name (a string) is present.

    def __contains__ (self, name):
        self.require_load()
        return self._map.__contains__(name)

    ##  The number of children.

    def __len__ (self):
        self.require_load()
        return len(self._map)

    ##  An iterator over the names of children.

    def __iter__ (self):
        self.require_load()
        return self._map.__iter__()

    ##  The index (in the list) of a given child.

    def index (self, child):
        self.require_load()
        return self._contents.index(child)

    ##  Returns the index of a given child.

    def child_index (self, child):
        return self.index(child)

    ##  Attach an existing File as my child.

    def attach_child (self, child, i=None):
        # this also does require_load()
        with writer(self):
            name = child.name()
            if name is None: raise Exception('Child has no name!')
            if name in self._map:
                raise Exception('Cannot attach child: duplicate name: %s' % name)
            t = self.childtype
            if not (t is None or isinstance(child, t)):
                raise Exception('Cannot attach child: wrong type')
            self.modified()
            self._map[name] = child
            if i is None:
                self._contents.append(child)
            else:
                self._contents[i:i] = [child]

    ##  Detach one of the children.

    def detach_child (self, child):
        with writer(self):
            name = child.name()
            if self._map.get(name) is not child:
                raise Exception('Cannot detach, not in child table')
            self.modified()
            del self._map[name]
            i = self._contents.index(child)
            del self._contents[i]

    ##  Iterate over the children, in linear order.

    def values (self):
        self.require_load()
        return iter(self._contents)

    ##  Iterates over a list of (name, child) pairs.

    def items (self):
        self.require_load()
        for child in self._contents:
            yield (child.name(), child)

    ##  Create a new child.  This counts as a protected updater: it modifies
    #   contents only via attach_child, which is protected.

    def new_child (self, name=None, suffix=None, cls=None, i=None):
        self.check_permission('write')
        child = self._instantiate_child(name, suffix, cls)
        if child.name() is None: raise Exception('new_child: Child has no name!')
        self.attach_child(child, i)
        child.__create__() # creates files that .created() requires
        child.created()
        return child

    ##  Fetch a child by name, creating a new one, if necessary.
    #   Does not work for all classes, only ones that are collections of children
    #   of a single type.

    def need_child (self, name, suffix=None, cls=None, i=None):
        if name is None:
            raise Exception('Need_child requires a name')
        self.require_load()
        if name in self._map:
            return self._map[name]
        else:
            return self.new_child(name, suffix, cls, i)

    ##  Rearrange the linear list of children.  Does not affect their pathnames.

    def reorder_children (self, indices, tgt_index):
        with writer(self):
            self.modified()
            n = sum((index < tgt_index) for index in indices)
            selected = [self._contents[i] for i in indices]

            # delete in order of largest to smallest index, so that deletions
            # do not invalidate subsequent i values
            for i in sorted(indices, reverse=True):
                del self._contents[i]

            # re-insert
            tgt_index -= n
            self._contents[tgt_index:tgt_index] = selected

    ##  This is called by reparent_children() and File.reparent().  This
    #   implementation just returns self, but it permits specializations to
    #   designate a proxy, so that attempts to use the directory as target
    #   for reparenting will cause the proxy to be used instead.

    def attachment_target (self):
        return self

    ##  Transfer some children to a different parent.

    def reparent_children (self, indices, tgt_index):
        with writer(self):
            newparent = self._contents[tgt_index].attachment_target()
            if newparent.attachment_target() is not newparent:
                raise Exception('Attachment target regression')
            index = self.env.index()
            with writer(newparent, index):
                self.modified()
                newparent.modified()
                # precompute as list, because the next loop will spoil indices
                selected = [(self._contents[i], i < tgt_index) for i in indices]
                head = 0
                for (child, prepend) in selected:
                    if prepend:
                        i = head
                        head += 1
                    else:
                        i = None
                    child.reparent(newparent, i=i)

    ##  Delete the child with the given name or at the given index.

    def delete_child (self, id):
        # will call back to detach
        self.__getitem__(id).delete()

    ##  Delete the children at the given indices.

    def delete_children (self, indices):
        if indices:
            with writer(self):
                for i in sorted(indices, reverse=True):
                    self._contents[i].delete()


    #--  misc, debugging  --------------------------------------

    ##  Iterates over the names in the directory on disk.
    #   Skips special names.  Even so, this is not guaranteed to
    #   match the child names.  Some children may not (yet) have
    #   on-disk representations, and some files on disk may not
    #   correspond to children.

    def listdir (self):
        fn = self._filename()
        if os.path.exists(fn):
            for name in os.listdir(fn):
                if not is_special_filename(name):
                    yield name

    ##  Print out the file hierarchy rooted here.

    def print_tree (self, verbose=False):
        if not self.permitted('read'):
            pprint(_ppname(self, verbose), '- not readable')
        else:
            pprint(_ppname(self, verbose))
            with pprint.indent():
                if verbose:
                    for f in self.metadata_items():
                        pprint(_ppname(f, verbose))
                children = self.children()
                for child in children:
                    if isinstance(child, Directory):
                        child.print_tree()
                    else:
                        pprint(_ppname(child, verbose))


def _ppname (file, verbose):
    if verbose:
        return '%s %s (%s %s)' % (file.name() or '-',
                                  file.suffix() or '-',
                                  file.__class__.__name__,
                                  file.logrelpath())
    else:
        return '<%s %s>' % (file.__class__.__name__, file.name() or '-')


#--  Structure  ----------------------------------------------------------------

##  A Structure is a Directory with a fixed list of children.
#   The attribute 'signature' contains the list; it specifies name and type
#   for each child.

class Structure (Directory):

    ##  Specializations should override 'signature'.  This should be a dict whose
    #   keys are names and whose values are types.

    signature = {}

    ##  Creates the children in the signature.

    def __init_contents__ (self):
        # the new_child calls are protected, but this consolidates all the writes
        with self.writer():
            for (name,cls) in self.signature.items():
                self.new_child(name=name, cls=cls)

    ##  Children whose names are in the signature can be accessed as members.
    #   This is similar to Directory.__getattr__, but stricter.

    def __getattr__ (self, att):
        if att in self.signature:
            return self.__getitem__(att)
        else:
            raise AttributeError("%s has no attribute '%s'" % (self, att))
