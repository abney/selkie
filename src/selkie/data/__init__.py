
# Temporary solution until Python 3.9 becomes standard

from os import PathLike
from os.path import join, dirname

class _Path (PathLike):

    def __init__ (self, fn):
        self._filename = fn
        
    def __enter__ (self):
        return self

    def __exit__ (self, t, v, tb):
        return

    def __add__ (self, suffix):
        return _Path(self._filename + suffix)

    def __str__ (self):
        return self._filename

    def __repr__ (self):
        return f'<_Path {self._filename}>'

    def __fspath__ (self):
        return self._filename
    

def path (*names):
    return _Path(join(dirname(__file__), *names))

def ex (*names):
    return path('examples', *names)
