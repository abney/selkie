
from os import unlink, makedirs, listdir, walk
from os.path import join, normpath, dirname, exists, isdir, expanduser
from collections.abc import MutableMapping
from .object import MapProxy
from .formats import File, blocks_to_lines, lines_to_blocks

# def coerce_to (x, cls):
#     return x if isinstance(x, cls) else cls(x)


class BaseDisk (MutableMapping):
    '''
    An abstract class that specifies the methods that all "virtual disks" share.
    A **disk** behaves like a dict whose keys
    are (functionally) pathnames with the root at the disk itself, and whose
    values are representations of files.

    An implementation must provide the usual map methods (``__iter__()``, ``__contains__()``,
    ``__getitem__()``, ``__setitem__()``, ``__delitem__()``) and the method ``iterdirectory()``.
    It may optionally provide the method ``physical_pathname()``. The remaining methods are
    implemented by BaseDisk itself.

    BaseDisk also provides the HTTP methods ``HEAD()``, ``GET()``, ``PUT()``, and ``DELETE()``.
    '''

    def __iter__ (self):
        '''
        Returns an iteratation over the keys of the disk.
        Must be implemented.
        '''
        raise NotImplementedError()

    def __contains__ (self, name):
        '''
        Returns boolean true just in case the given key has a value.
        Must be implemented.
        '''
        raise NotImplementedError()

    def __getitem__ (self, name):
        '''
        Returns the value for the given key. **Nota bene:** it is not guaranteed that two calls
        to getitem using the same key (with no intervening modifying operations)
        return identical values, in the sense of ``is``. It is only guaranteed that the values
        are functionally equal, and that changes to the contents of one modify the contents of
        the other.

        Must be implemented.
        '''
        raise NotImplementedError()

    def __setitem__ (self, name, value):
        '''
        Sets the value for the given key. The value is stored as-is, not copied.
        Must be implemented.
        '''
        raise NotImplementedError()

    def __delitem__ (self, name):
        '''
        Removes any key-value association for the given key.
        Must be implemented.
        '''
        raise NotImplementedError()

    def iterdirectory (self, name):
        '''
        The input *name* is a key for a directory,
        and the return value is an iterator over the keys of files belonging
        to the directory. The iteration only includes children; it does not recurse.
        '''
        raise NotImplementedError()

    def physical_pathname (self, name):
        '''
        The input *name* is a key (that is, a disk-specific file identifier), and the return value
        is a disk-independent identifier. This method is optional.
        '''
        raise NotImplementedError()

    def __len__ (self):
        '''
        The number of keys.
        '''
        return sum(1 for _ in self.__iter__())

    def keys (self):
        '''
        A synonym for ``__iter__().``
        '''
        return self.__iter__()

    def items (self):
        '''
        Returns an iteration over (key, value) pairs.
        '''
        for key in self.keys():
            yield (key, self.__getitem__(key))

    def values (self):
        '''
        Returns an iteration over values (files).
        '''
        for key in self.keys():
            yield self.__getitem__(key)

    def HEAD (self, fn):
        '''
        A synonym for ``__contains__()``.
        '''
        return self.__contains__(fn)

    def GET (self, fn):
        '''
        A synonym for ``__getitem__()``.
        '''
        return self.__getitem__(fn)
    
    def PUT (self, fn, value):
        '''
        A synonym for ``__setitem__()``.
        '''
        self.__setitem__(fn, value)

    def DELETE (self, fn):
        '''
        A synonym for ``__delitem__()``.
        '''
        self.__delitem__(fn)


class VDisk (BaseDisk, MapProxy):
    '''
    An implementation of BaseDisk that contains a dict that serves as the mapping.
    '''
    def __init__ (self):
        self.__dict = {}

    def __map__ (self):
        return self.__dict
        

class Directory (object):
    '''
    A representation of a directory on a virtual disk.
    Can be used by any implementation.
    '''

    def __init__ (self, disk, name):
        '''
        Initializer. Name should be a valid key for the VDisk.
        '''
        assert isinstance(disk, BaseDisk), f'Not a BaseDisk: {str(disk)}'
        self._disk = disk
        self._name = name

    def physical_pathname (self, name=None):
        '''
        The physical pathname. If *name* is not provided, the
        physical pathname of the directory itself is returned; otherwise,
        the *name* is joined to the physical pathname of the directory.
        Raises an exception if the disk does
        not provide an implementation for physical pathnames.
        '''
        dfn = self._disk.physical_pathname(self._name)
        if name:
            return join(dfn, name)
        else:
            return dfn

    def __iter__ (self):
        '''
        Dispatches to ``BaseDisk.iterdirectory()``.
        '''
        return self._disk.iterdirectory(self._name)

    def __getitem__ (self, name):
        '''
        Uses join to combine the directory's name with *name*, and then dispatches
        to ``BaseDisk.__getitem__()``.
        '''
        return self._disk.__getitem__(join(self._name, name))


class VDisk (BaseDisk):

    def __init__ (self, root):
        BaseDisk.__init__(self)
        self.root = expanduser(root)
        self.ignore = self._ignore

    def physical_pathname (self, name):
        if name.startswith('/'):
            name = name[1:]
        return join(self.root, *name.split('/'))

    def iterdirectory (self, name):
        fn = self.physical_pathname(name)
        return iter(listdir(fn))

    def __iter__ (self):
        for (dirpath, dirnames, filenames) in walk(self.root):
            assert dirpath.startswith(self.root)
            for name in filenames:
                reldirpath = dirpath[len(self.root):]
                # join() does not add a leading '/' if reldirpath is empty
                fn = reldirpath + '/' + name
                if not self.ignore(fn):
                    yield fn

    def _ignore (self, fn):
        return (fn.endswith('~') or
                fn.endswith('.safe') or
                '/tmp' in fn or
                '.safe/' in fn)

    def __contains__ (self, fn):
        fn = self.physical_pathname(fn)
        return exists(fn)

    def mkdir (self, fn):
        fullfn = self.physical_pathname(fn)
        if exists(fullfn):
            if not isdir(fullfn):
                raise Exception(f'Existing file is not a directory: {fullfn}')
        else:
            makedirs(fullfn)

    def __getitem__ (self, fn):
        fullfn = self.physical_pathname(fn)
        if isdir(fullfn):
            return Directory(self, fn)
        else:
            return File(fullfn)

#         with open(fn) as f:
#             for line in f:
#                 yield line.rstrip('\r\n')

    def __setitem__ (self, fn, lines):
        fn = self.physical_pathname(fn)
        dn = dirname(fn)
        if not exists(dn):
            makedirs(dn)
        File(fn).store(lines)

#         with open(fn, 'w') as f:
#             for line in lines:
#                 f.write(line)
#                 f.write('\n')

    def __delitem__ (self, fn):
        fn = self.physical_pathname(fn)
        if not exists(fn):
            raise KeyError(f'Key does not exist: {fn}')
        unlink(fn)

