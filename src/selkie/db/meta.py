##  \package seal.cld.db.meta
#   Provides the class Metadata.


##  Metadata.

class Metadata (object):

    ##  Constructor.  The host is the file that this is metadata for.

    def __init__ (self, host):

        ##  The host.
        self.host = host

        ##  Same as host.env.
        self.env = host.env

    ##  Calls host.require_load().

    def require_load (self):
        self.host.require_load()

    ##  Calls host.writer().

    def writer (self):
        return self.host.writer()

    ##  Calls host.modified().

    def modified (self):
        self.host.modified()

    ##  Must be implemented by specializations.

    def __read__ (self, f):
        raise Exception('Must be implemented by specialization')

    ##  Must be implemented by specializations.

    def __write__ (self, f):
        raise Exception('Must be implemented by specialization')

    ##  Calls host.permitted().

    def meta_permitted (self, action, user=None):
        return self.host.permitted(action, user)

    ##  String representation.

    def __repr__ (self):
        return '<%s %s>' % (self.__class__.__name__, repr(self.host.logrelpath()))


##  A "virtual object" is backed by a file.  The accessor methods of a virtual
#   object are protected by calls to require_load, and its update methods are
#   protected by calls to 'with writer'.

class VirtualObject (object):

    ##  Constructor.  The host is a File.

    def __init__ (self, host):
        self._host = host

    ##  Generic intern method.  Does a deep copy.  The input is only allowed to
    #   contain strings, ints, floats, lists, and dicts whose keys are strings.
    #   The list elements and dict values must have one of those types as well.
    #   Lists and dicts are converted to VirtualLists and VirtualDicts.

    def intern (self, obj):
        if obj is None:
            return None
        elif isinstance(obj, str):
            if '\n' in obj:
                raise Exception('Strings may not contain embedded newlines')
            return obj
        elif isinstance(obj, (int, float)):
            return obj
        elif isinstance(obj, list):
            out = VirtualList(self._host)
            for x in obj:
                out.append(self.intern(x))
            return out
        elif isinstance(obj, dict):
            out = VirtualDict(self._host)
            for (k,v) in obj.items():            
                out[self._check_key(k)] = self.intern(v)
            return out
        else:
            raise Exception('Not virtualizable: %s' % repr(obj))

    def _check_key (self, k):
        if isinstance(k, str):
            return k
        else:
            raise Exception('Keys must be strings: %s' % repr(k))


##  A virtual list.

class VirtualList (VirtualObject):

    ##  Constructor.

    def __init__ (self, host):
        VirtualObject.__init__(self, host)
        self._contents = []
        
    ##  Get an element.

    def __getitem__ (self, i):
        self.host.require_load()
        return self._contents.__getitem__(i)

    ##  Set an element.

    def __setitem__ (self, i, v):
        with self.host.writer():
            self._contents.__setitem__(i, self.intern(v))

    ##  Iterate over elements.

    def __iter__ (self):
        self.host.require_load()
        return self._contents.__iter__()

    ##  Append a new element.

    def append (self, x):
        with self.host.writer():
            self._contents.append(self.intern(x))


##  A virtual dict.

class VirtualDict (VirtualObject):

    ##  Constructor.

    def __init__ (self, host):
        VirtualObject.__init__(self, host)
        self._contents = {}

    ##  Get an element.

    def __getitem__ (self, k):
        self.host.require_load()
        return self._contents.__getitem__(k)

    ##  Set an element.  The key must be a string.

    def __setitem__ (self, k, v):
        assert isinstance(k, str)
        with self.host.writer():
            self._contents.__setitem__(k, self.intern(v))

    ##  Iterate over elements.

    def __iter__ (self):
        self.host.require_load()
        return self._contents.__iter__()

    ##  Iteration over keys.

    def keys (self):
        self.host.require_load()
        return self._contents.keys()

    ##  Iteration over values.

    def values (self):
        self.host.require_load()
        return self._contents.values()

    ##  Iteration over (key, value) pairs.

    def items (self):
        self.host.require_load()
        return self._contents.items()


##  This class provides a metadata item with generic JSON-like read and
#   write methods.  (Currently incomplete; needs methods that dispatch to
#   the contents.)

class GeneralMetadata (Metadata):

    ##  Constructor.

    def __init__ (self, host):
        Metadata.__init__(self, host)
        self._contents = None

    ##  Read contents from file.

    def __read__ (self, f):
        self._contents = self._read_obj(f)

    def _read_obj (self, f):
        line = next(f).rstrip('\r\n')
        if line[0] == 'N': return None
        elif line[0] == 'S': return line[1:]
        elif line[0] == 'I': return int(line[1:])
        elif line[0] == 'F': return float(line[1:])
        elif line[0] == 'L': return self._read_list(f)
        elif line[0] == 'D': return self._read_dict(f)
        elif line[0] == 'E': return StopIteration()

    def _read_list (self, f):
        out = VirtualList(self.host)
        while True:
            elt = self._read_obj()
            if isinstance(elt, StopIteration):
                break
            out.append(elt)
        return out

    def _read_dict (self, f):
        out = VirtualDict(self.host)
        while True:
            key = self._read_obj()
            if isinstance(key, StopIteration):
                break
            value = self._read_obj()
            if isinstance(value, StopIteration):
                raise Exception('Expecting a value')
            out[key] = value
        return out

    ##  Write contents to file.

    def __write__ (self, f):
        self._write_obj(self._contents, f)

    def _write_obj (self, obj, f):
        if obj is None:
            f.write('N\n')
        elif isinstance(obj, str):
            f.write('S')
            f.write(obj)
            f.write('\n')
        elif isinstance(obj, int):
            f.write('I')
            f.write(str(obj))
            f.write('\n')
        elif isinstance(obj, float):
            f.write('F')
            f.write(str(obj))
            f.write('\n')
        elif isinstance(obj, VirtualList):
            f.write('L\n')
            for elt in obj:
                self._write_obj(elt)
            f.write('E\n')
        elif isinstance(obj, VirtualDict):
            f.write('D\n')
            for (k,v) in obj.items():
                self._write_obj(k)
                self._write_obj(v)
            f.write('E\n')
        else:
            raise Exception('Unexpected object type encountered')


#--  PropListMixin  ------------------------------------------------------------

##  A file-like object that contains a dict mapping property names to values.

class PropListMixin (object):

    ##  Should be a list or tuple - encodes the order of the properties.
    property_names = None

    ##  Read the contents from a stream.

    def __read__ (self, f):
        self._dict = {}
        if self.property_names:
            assert isinstance(self.property_names, (list, tuple))
            tab = self._dict
            for spec in self.property_names:
                if isinstance(spec, (tuple, list)):
                    if len(spec) != 2:
                        raise Exception('Bad property name spec: %s' % spec)
                    tab[spec[0]] = spec[1]
                else:
                    tab[spec] = ''
        for line in f:
            (k,v) = line.rstrip('\r\n').split('\t')
            if self.property_names and k not in self._dict:
                raise KeyError('Illegal key: %s, %s, %s' % (k, self, self.property_names))
            self._dict[k] = v

    ##  Write the contents to a stream.

    def __write__ (self, f):
        for (k,v) in self._dict.items():
            f.write(k)
            f.write('\t')
            f.write(v)
            f.write('\n')

    ##  The number of properties.

    def __len__ (self):
        self.require_load()
        return len(self._dict)

    ##  Whether the given property is present.

    def __contains__ (self, k):
        self.require_load()
        return self._dict.__contains__(k)

    ##  Iterate over the properties (strings).

    def __iter__ (self):
        self.require_load()
        return self._dict.__iter__()

    ##  Get the value for the given property.

    def __getitem__ (self, k):
        self.require_load()
        return self._dict[k]

    ##  Get the value ofr the given property, returning None on failure.

    def get (self, k):
        self.require_load()
        return self._dict.get(k)

    ##  Iterate over the properties.

    def keys (self):
        if self.property_names:
            return self.property_names
        else:
            self.require_load()
            return list(self._dict.keys())

    ##  Iterate over the values.

    def values (self):
        self.require_load()
        return self._dict.values()

    ##  Iterate over (property, value) pairs.

    def items (self):
        self.require_load()
        return self._dict.items()

    ##  Set the value for a property.

    def __setitem__ (self, key, value):
        with self.writer():
            if self.property_names and key not in self._dict:
                raise KeyError('Bad key: %s' % key)
            self.modified()
            self._dict[key] = value


class MetaPropList (PropListMixin, Metadata):
    pass


#--  Index  --------------------------------------------------------------------

##  An Index maps types to IndexTables.
#   An IndexTable maps names to logical relpaths.

class IndexTable (object):

    ##  Constructor.

    def __init__ (self, index):

        ##  The index this table belongs to.
        self.index = index

        ##  The maximum ID assigned so far.
        self.maxvalue = 0

        ##  The contents (a dict).  Keys are IDs and values are logical relpaths.
        self.contents = {}

    ##  Iterate over the keys.

    def keys (self):
        return self.contents.keys()

    ##  Iterate over the values.

    def values (self):
        return self.contents.values()

    ##  Iterate over (ID, relpath) pairs.

    def items (self):
        return self.contents.items()

    ##  Get the relpath for the given ID.

    def __getitem__ (self, name):
        return self.contents[name]

    ##  Like __getitem__(), but returns None on failure.

    def get (self, name):
        return self.contents.get(name)

    ##  The number of entries.

    def __len__ (self):
        return self.contents.__len__()

    ##  Fetch the relpath and follow it to fetch the actual File instance.

    def file (self, name):
        if name not in self.contents:
            raise Exception('No indexed file with name: %s' % name)
        root = self.index.env['root']
        names = self.contents[name].split('/')
        return root.join(names)

    ##  Iterates over all indexed files.

    def files (self):
        root = self.index.env['root']
        for rp in self.contents.values():
            names = rp.split('/')
            yield root.join(names)

    # this is called without a writer by Index.__read__

    def _set (self, name, relpath):
        self.contents[name] = relpath
        if name.isdigit():
            n = int(name)
            if n > self.maxvalue:
                self.maxvalue = n

    ##  Add a new entry.

    def __setitem__ (self, name, relpath):
        with writer(self.index):
            if name not in self.contents or self.contents[name] != relpath:
                self.index.modified()
                self._set(name, relpath)

    ##  Delete an entry.

    def __delitem__ (self, name):
        with writer(self.index):
            if name in self.contents:
                self.index.modified()
                del self.contents[name]

    ##  Allocate a new ID.

    def allocate_name (self, dir):
        return str(self.maxvalue + 1)

    ##  Callback notifying us that a new file has been created and should be indexed.

    def created (self, file):
        with self.index.writer():
            name = file.name()
            if name in self.contents:
                raise Exception('Name already in use: %s' % name)
            self.index.modified()
            self._set(name, file.logrelpath())

    ##  Callback notifying us that an indexed file has moved.

    def moved (self, file):
        self.index.modified()
        self._set(file.name(), file.logrelpath())

    ##  Callback notifying us that an indexed file has been deleted.

    def deleted (self, file):
        self.index.modified()
        del self.contents[file.name()]


##  An index mapping suffixes to tables.

class Index (Metadata):

    ##  Read the contents from a stream.

    def __read__ (self, f):
        self._tables = {}
        types = self.env.indexed_types()
        if types:
            for type in types:
                if isinstance(type, str): suffix = type
                else: suffix = self.env.get_suffix(type)
                self._tables[suffix] = IndexTable(self)
        for line in f:
            (type, name, relpath) = line.rstrip('\r\n').split('\t')
            table = self._need_table(type)
            table._set(name, relpath)

    ##  Write the contents to a stream.

    def __write__ (self, f):
        for (type, table) in self._tables.items():
            for (name, relpath) in table.items():
                f.write('%s\t%s\t%s\n' % (type, name, relpath))

    def _need_table (self, type):
        if type in self._tables:
            return self._tables[type]
        elif self.env.indexed_types():
            raise Exception('Illegal type for Index: %s' % type)
        else:
            table = IndexTable(self)
            self._tables[type] = table
            return table

    ##  Get the table for the given type, returning None on failure.

    def get (self, type):
        self.require_load()
        return self._tables.get(type)

    ##  Get the table for the given type, signalling an error on failure.

    def __getitem__ (self, type):
        self.require_load()
        return self._tables[type]

    ##  Get the indexed file with the given type and name.

    def file (self, type, name):
        return self[type].file(name)

    ##  Get all indexed files with the given type.

    def files (self, type):
        return self[type].files()

    ##  Whether a type is in the index.

    def __contains__ (self, type):
        self.require_load()
        return self._tables.__contains__(type)

    ##  Iterates over (type, table) pairs.

    def items (self):
        self.require_load()
        return self._tables.items()

