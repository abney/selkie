
from .formats import Containers


#--  Single  -------------------------------------------------------------------

class Single (object):

    def __init__ (self, f):
        self._file = f

    def load (self):
        for elt in self._file:
            return elt

    def save (self, obj):
        self._file.store([obj])


def Simple (f):
    return Single(Simples(f))


#--  Container  ----------------------------------------------------------------

class Container (object):

    def __init__ (self, f):
        self._file = Containers(f)
        self._editing = False
        self._contents = None
        self.load()
        if self._contents is None:
            raise Exception('Implementation error: loading failed to set _contents')

    # Returns the first element without checking whether there are more

    def load (self):
        isempty = True
        for elt in self._file:
            self._contents = elt
            isempty = False
            break
        if isempty:
            self._contents = {}

    def save (self):
        if not self._editing:
            self._file.store([self._contents])

    def edit (self):
        return BatchEdit(self)

    def __setitem__ (self, key, value):
        self._contents[key] = value
        self.save()

    def __delitem__ (self, key):
        del self._contents[key]
        self.save()

    def __getitem__ (self, att):
        return self._contents[att]

    def append (self, value):
        self._contents.append(value)
        self.save()

    def __repr__ (self):
        return repr(self._contents)


class BatchEdit (object):

    def __init__ (self, tgt):
        self._tgt = tgt

    def __enter__ (self):
        self._tgt._editing = True
        return self

    def __exit__ (self, t, v, tb):
        self._tgt._editing = False
        if not t:
            self._tgt.save()
