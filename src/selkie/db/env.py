##  @package seal.cld.db.env
#   The database environment.

from io import StringIO


##  Gets set in __init__.py

default_types = None


#--  TypeTable  ----------------------------------------------------------------

##  Turn a dict around.  Values become keys and keys become values.
#   If a given value is associated with multiple keys, an error is signalled.

def reverse_dict (d):
    if d is None:
        return {}
    else:
        table = {}
        for (suffix, cls) in d.items():
            if cls in table:
                raise Exception('Class with multiple suffixes: %s' % cls)
            table[cls] = suffix
        return table


#--  Environment  --------------------------------------------------------------

##  An Environment behaves like a dict.  Environments are always created by the
#   method File.create_env.
#
#   The following keys are defined by the initializer:
#
#    - 'filename' - the filename for the database directory.
#    - 'username' - the username of the current user.
#    - 'disk' - a Disk object.
#    - 'log' - a logging function.
#    - 'root' - the database object.
#    - 'index_root' - the directory containing the index, or None.

class Environment (object):

    ##  Constructor.  The parent, if provided, is an Environment to copy.

    def __init__ (self, host):
        self._table = {}
        self._types_table = None
        self._suffixes_table = None
        self._frozen = False  # freezes when becomes parent.env

        parent = host.parent()
        if parent is None:
            # My own table, because it may get added to
            self._types_table = {}
            self._types_table.update(default_types)
            if host.types:
                self._types_table.update(host.types)
            self._suffixes_table = reverse_dict(self._types_table)
            self._table['types'] = self._types_table
            self._table['suffixes'] = self._suffixes_table
        else:
            self.update(parent.env)
            parent.env._frozen = True

    ##  Get an item from the table.
    def __getitem__ (self, key): return self._table.__getitem__(key)

    ##  Get an item from the table, returning None on failure.
    def get (self, key): return self._table.get(key)

    ##  Whether an item is present.
    def __contains__ (self, key): return self._table.__contains__(key)

    ##  Set an item in the table.
    def __setitem__ (self, key, value): return self._table.__setitem__(key, value)

    ##  Copy items from a dict.
    def update (self, tab):
        for (k,v) in tab.items():
            self.__setitem__(k,v)

    ##  The number of entries in the table.
    def __len__ (self): return self._table.__len__()

    ##  Iterate over the keys of the table.
    def __iter__ (self): return self._table.__iter__()

    ##  Iterate over the keys of the table.
    def keys (self): return self._table.keys()

    ##  Iterate over the values in the table.
    def values (self): return self._table.values()

    ##  Iterate over (key, value) pairs.
    def items (self): return self._table.items()

    ##  Returns the <tt>_groups</tt> child of the root.

    def groups (self):
        return self._table['root']._groups

    ##  Get the class corresponding to the given suffix.
    def get_class (self, suffix):
        types = self._table.get('types')
        if types: return types.get(suffix)

    ##  Get the suffix corresponding to the given class.
    def get_suffix (self, cls):
        suffixes = self._table.get('suffixes')
        if suffixes:
            return suffixes.get(cls)

    ##  Return the list of types that are indexed.

    def indexed_types (self):
        ir = self._table.get('index_root')
        if ir is not None: return ir.indexed

    ##  Return the index, or None.

    def index (self):
        ir = self._table.get('index_root')
        if ir is not None: return ir._index

    ##  Add more types.  Signals an (obscure) error if this is not the root
    #   environment.

    def update_types (self, types):
        for (typename,cls) in types.items():
            self.add_type(typename, cls)

    ##  Add another type.  Signals an (obscure) error if this is not the root
    #   environment.

    def add_type (self, typename, cls):
        assert typename not in self._types_table
        assert cls not in self._suffixes_table
        self._types_table[typename] = cls
        self._suffixes_table[cls] = typename

    ##  String representation.

    def __str__ (self):
        with StringIO() as f:
            print('%s:' % self.__class__.__name__, file=f)
            for (k,v) in self._table.items():
                print('    %s:' % k, repr(v), file=f)
            return f.getvalue()
