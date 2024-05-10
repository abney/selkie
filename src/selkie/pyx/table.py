
from .object import ListProxy, MapProxy
#from .newio import Format


#--  Table  --------------------------------------------------------------------

class Record (object):

    __keys__ = None

    def __init__ (self):
        if self.__keys__ is None:
            raise Exception('Subtype must specify keys')
        for key in self.__keys__:
            setattr(self, key, '')


class Table (ListProxy):

    def __init__ (self, objtype, source):
        ListProxy.__init__(self)

        self._source = source
        self._fmt = Format(lambda lines: lines_to_objects(objtype, lines), objects_to_lines)
        self._contents = list(self._fmt(self._source))

    def __list__ (self): return self._contents

    def __repr__ (self):
        return object.__repr__(self)


def lines_to_objects (typ, lines):
    obj = None
    for line in lines:
        line = line.rstrip('\r\n')
        if line:
            if obj is None:
                obj = typ()
            i = _first_space(line)
            if i is None:
                raise Exception(f'No space in line: {repr(line)}')
            key = line[:i]
            value = line[i+1:]
            setattr(obj, key, value)
        else:
            yield obj
            obj = None
    if obj is not None:
        yield obj

def _first_space (line):
    for i in range(len(line)):
        if line[i].isspace():
            return i

def objects_to_lines (objects):
    first = True
    for obj in objects:
        if first: first = False
        else: yield '\n'
    for key in obj.__keys__:
        value = str(getattr(obj, key))
        if '\n' in value:
            raise Exception(f'Value of {repr(key)} contains a newline: {repr(obj)}')
        yield key + ' ' + value + '\n'


#--  Index  --------------------------------------------------------------------

class Index (MapProxy):

    def __init__ (self, table, key, multi=False):
        if isinstance(key, str):
            keyf = lambda obj: getattr(obj, key)
        else:
            keyf = key

        self._index = {}
        if multi: add = self._add2
        else: add = self._add1
        for obj in table:
            add(keyf(obj), obj)

    def _add1 (self, key, value):
        if key in self._index:
            raise Exception(f'Multiple records for key {repr(key)}')
        self._index[key] = value

    def _add2 (self, key, value):
        if key in self._index:
            self._index[key].append(value)
        else:
            self._index[key] = [value]

    def __map__ (self):
        return self._index
