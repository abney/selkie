
from os import unlink, makedirs, listdir, walk
from os.path import join, normpath, dirname, exists, isdir, expanduser
from collections.abc import MutableMapping
#from .object import MapProxy
from .formats import RegularFile

# def coerce_to (x, cls):
#     return x if isinstance(x, cls) else cls(x)


class VDisk (MutableMapping):

    def __init__ (self, root):
        self.root = expanduser(root)

    def physical_pathname (self, name):
        if name.startswith('/'):
            name = name[1:]
        return join(self.root, *name.split('/'))

    def iterdirectory (self, dname):
        return iter(listdir(self.physical_pathname(dname)))

    def __iter__ (self):
        for (dirpath, dirnames, filenames) in walk(self.root):
            assert dirpath.startswith(self.root)
            for name in filenames:
                reldirpath = dirpath[len(self.root):]
                # join() does not add a leading '/' if reldirpath is empty
                yield reldirpath + '/' + name

#     def _ignore (self, fn):
#         return (fn.endswith('~') or
#                 fn.endswith('.safe') or
#                 '/tmp' in fn or
#                 '.safe/' in fn)

    def __contains__ (self, name):
        return exists(self.physical_pathname(name))

    def mkdir (self, name):
        fullfn = self.physical_pathname(name)
        if exists(fullfn):
            if not isdir(fullfn):
                raise Exception(f'Existing file is not a directory: {fullfn}')
        else:
            makedirs(fullfn)

    def __getitem__ (self, name):
        fullfn = self.physical_pathname(name)
        if isdir(fullfn):
            return Directory(self, name)
        else:
            return RegularFile(fullfn, mkdirs=True)

    def __setitem__ (self, fn, lines):
        fullfn = self.physical_pathname(fn)
        RegularFile(fullfn, mkdirs=True).store(lines)

    def __delitem__ (self, fn):
        fn = self.physical_pathname(fn)
        if not exists(fn):
            raise KeyError(f'Key does not exist: {fn}')
        unlink(fn)

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


# class VDisk (BaseDisk, MapProxy):
#     '''
#     An implementation of BaseDisk that contains a dict that serves as the mapping.
#     '''
#     def __init__ (self):
#         self.__dict = {}
# 
#     def __map__ (self):
#         return self.__dict
        

class Directory (object):
    '''
    A representation of a directory on a virtual disk.
    Can be used by any implementation.
    '''

    def __init__ (self, disk, name):
        '''
        Initializer. Name should be a valid key for the VDisk.
        '''
        assert isinstance(disk, VDisk), f'Not a VDisk: {str(disk)}'
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
