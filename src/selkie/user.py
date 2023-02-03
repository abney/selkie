
from .newio import NestedDict
from .object import MapProxy
from .disk import VDisk


class User (object):

    def __init__ (self):
        self._disk = VDisk('~/.cld')
        self._props = Props(self._disk['props'])

    def __getattr__ (self, name):
        if name == 'disk':
            return self._disk
        elif name == 'props':
            return self._props


class Props (MapProxy):

    def __init__ (self, f):
        self._file = NestedDict(f)
        self.__map__ = self._file.load()
