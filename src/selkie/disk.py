
from os import unlink, makedirs, listdir, walk
from os.path import join, normpath, dirname, exists, isdir, expanduser
from .newio import File, blocks_to_lines, lines_to_blocks


def coerce_to (x, cls):
    return x if isinstance(x, cls) else cls(x)


class BaseDisk (object):

    def physical_pathname (self, name): raise NotImplementedError()
    def iterdirectory (self, name): raise NotImplementedError()

    def __iter__ (self): raise NotImplementedError()
    def __contains__ (self): raise NotImplementedError()
    def __getitem__ (self, name): raise NotImplementedError()
    def __setitem__ (self, name, value): raise NotImplementedError()
    def __delitem__ (self, name): raise NotImplementedError()

    def __len__ (self):
        return sum(1 for _ in self.__iter__())

    def keys (self):
        return self.__iter__()

    def items (self):
        for key in self.keys():
            yield (key, self.__getitem__(key))

    def values (self):
        for key in self.keys():
            yield self.__getitem__(key)

    def HEAD (self, fn): return self.__contains__(fn)
    def GET (self, fn): return self.__getitem__(fn)
    def PUT (self, fn, value): self.__setitem__(fn, value)
    def DELETE (self, fn): self.__delitem__(fn)


class Directory (object):

    def __init__ (self, disk, name=''):
        self._disk = disk
        self._name = name

    def physical_pathname (self, name=None):
        dfn = self._disk.physical_pathname(self._name)
        if name:
            return join(dfn, name)
        else:
            return dfn

    def __iter__ (self):
        return self._disk.iterdirectory(self._name)

    def __getitem__ (self, name):
        return self._disk[self._name + '/' + name]


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
