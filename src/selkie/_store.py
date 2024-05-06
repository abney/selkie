
import pathlib
from .io import ispathlike
from .disk import JSONDisk


# A backing without an object is useful for passing the disk down and
# keeping track of the current pathname

class Store (object):

    def __init__ (self, disk, fn='', obj=None):
        if ispathlike(disk):
            disk = JSONDisk(disk)
        self._disk = disk
        self._filename = fn
        self._object = obj

    def join (self, name, obj=None):
        return Store(self._disk, self._filename + '/' + name, obj)

    def save (self, contents):
        if self._object is None:
            raise Exception('Not saveable')
        self._disk[self._filename] = self._object._contents

    def load (self):
        if self._object is None:
            raise Exception('Not loadable')
        self._object._contents = self._disk[self._filename]


class Object (object):
    
    def __init__ (self, backing=None, contents=None):
        self.__backing__ = backing
        if contents is not None:
            self.__setitems__(contents)

    def __load__ (self):
        if self.__backing__ is None:
            raise Exception('Not loadable')
        self.__backing__.load()

    def __save__ (self):
        if self.__backing__ is None:
            raise Exception('Not saveable')
        self.__backing__.save()


# A metaobject

class File (object):

    def __init__ (self, rootcls):
        if not hasattr(rootcls, '__setitems__'):
            raise Exception(f'Not a legal File class: {rootcls}')
        self.rootclass = rootcls

    def __call__ (self, backing):
        return self.rootclass(backing)


class List (object):

    def __init__ (self, elttype):
        self.elttype = elttype

    # to make it list-like
    __setitems__ = None

    def __call__ (self, backing, contents=None):
        return _List(self.elttype, backing, contents)


class _List (Object):

    def __init__ (self, elttype, backing, contents=None):
        self.__elttype__ = elttype
        Object.__init__(self, backing, contents)

    def __setitems__ (self, contents):
        if not islistlike(contents):
            raise Exception(f'Expecting a list: {self._filename}')
        for elt in contents:
            if not isinstance(elt, self.__elttype__):
                raise Exception(f'Bad element {elt} in contents')
        self._contents = contents
        
    def __getitem__ (self, i):
        if self._contents is None:
            self.__load__()
        return self._contents[i]

    def __setitem__ (self, i, value):
        if self._contents is None:
            raise KeyError(f'Illegal index {i}')
        if not isinstance(value, self.__elttype__):
            raise ValueError(f'Not a legal value: {value}')
        self._contents[i] = value
        self.__save__()


class Dict (Object):

    __schema__ = NotImplemented

    def __setitems__ (self, json):
        if not isdictlike(json):
            raise Exception(f'Expecting a dict: {self._filename}')
        for k in json.keys():
            if k not in self.__schema__:
                raise Exception(f'Bad key {k} in {self._filename}')
        for (k, cls) in self.__schema__.keys():
            if k not in json:
                json[k] = cls()
        self._contents = json
        
    def __getitem__ (self, name):
        if self._contents is None:
            self.__load__()
        return self._contents[name]
        
    def __setitem__ (self, key, value):
        if key not in self.__schema__:
            raise NameError(f'Not a valid key: {key}')
        cls = self.__schema__[key]
        if not isinstance(value, cls):
            raise ValueError(f'Not a legal value for {key}: {value}')
        self._contents[key] = value


class Directory (Object):

    def __init__ (self, backing):
        Object.__init__(self, backing)
        self._contents = {}
        for (name, cls) in self.__schema__.items():
            self._contents[name] = cls(backing.join(name))


#--  Intra-file objects  -------------------------------------------------------

def Str (x):
    if not isinstance(x, str):
        raise Exception(f'Expecting a string: {repr(x)}')
    return x

def Path (x):
    if not isinstance(x, pathlib.Path):
        raise Exception(f'Expecting a path: {repr(x)}')
    return x

def Int (x):
    if not isinstance(x, int):
        raise Exception(f'Expecting an int: {repr(x)}')
    return x

def Float (x):
    if not isinstance(x, float):
        raise Exception(f'Expecting a float: {repr(x)}')
    return x

def Bool (x):
    if not isinstance(x, bool):
        raise Exception(f'Expecting a bool: {repr(x)}')
    return x


#--  Store  --------------------------------------------------------------------

# class Store (object):
# 
#     def __init__ (self, dirname):
#         disk = self.__disk__ = JSONDisk(dirname)
#         schema = self.__load__.__annotations__
#         kwargs = {}
#         for (name, childcls) in schema.items():
#             child = kwargs[name] = childcls(disk[name])
#             child.__address__ = (self, name)
#         self.__load__(**kwargs)
# 
#     def normalize (self, fn):
#         if isinstance(fn, (lst, tuple)):
#             return fn
#         else:
#             if not fn.startswith('/'):
#                 fn = '/' + fn
#             fn = normpath(fn)
#             return fn[1:].split('/')
# 
#     def create (self):
#         return NotImplemented
# 
#     def __getitem__ (self, cpts):
#         cpts = self.normalize(cpts)
#         name = cpts[0]
#         annos = self.create.__annotations__
#         if name not in annos:
#             raise NameError(f'Not in schema: {name}')
#         cls = annos[name]
#         json = self._disk[name]
#         item = cls(json)
#         if len(cpts) > 1:
#             return item[cpts[1:]]
#         else:
#             return item
