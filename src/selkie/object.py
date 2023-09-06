##  @package seal.core.misc
#   Miscellaneous useful Python extensions.

import datetime, os, pty, unicodedata, sys, imp, threading, traceback, importlib
import signal
from itertools import islice, chain
from importlib import import_module
from io import StringIO
from time import time
from math import inf
import collections


#--  General  ------------------------------------------------------------------

##  Checks whether the object has the given type.

def check_type (x, t):
    xnames = [c.__name__ for c in x.__class__.__mro__]
    if isinstance(t, (tuple, list)):
        types = t
    else:
        types = [t]
    for ty in types:
        if isinstance(ty, str):
            name = ty
        else:
            name = ty.__name__
        if name in xnames:
            return
    raise Exception('Object does not have required type: %s, %s' % (x, t))


#--  Matching  -----------------------------------------------------------------

##  Indicates whether the object matches the description.

def matches (x, descr):
    for (k, v) in descr.items():
        if v is None: continue
        if not hasattr(x, k): return False
        val = getattr(x, k)
        if isinstance(val, collections.Callable): val = val()
        if isinstance(v, list):
            if val not in v: return False
        else:
            if val != v: return False
    return True


##  Returns a module given its name.
#   May raise ModuleNotFoundError

def string_to_module (s):
    if not s:
        raise Exception('Require nonempty name')
    return import_module(s)

##  Takes a fully-qualified name and gets the object.

def string_to_object (s):
    j = s.rfind('.')
    if j < 0:
        raise Exception('Require fully qualified name')
    m = string_to_module(s[:j])
    return m.__dict__[s[j+1:]]


#--  Object  -------------------------------------------------------------------

class Object (object):

    def __init__ (self, *args, **kwargs):
        d = dict(kwargs)
        object.__setattr__(self, '_dict', d)
        if d:
            object.__setattr__(self, '_listlen', None)
            for (i, arg) in enumerate(args):
                d[i] = arg
        else:
            object.__setattr__(self, '_listlen', len(args))
            self.extend(args)

    def _setlistlen (self, n):
        object.__setattr__(self, '_listlen', n)

    def __getitem__ (self, key):
        return self._dict[key]

    def __getattr__ (self, name):
        return self._dict[name]
            
    def __setitem__ (self, name, value):
        self._dict[name] = value
        n = self._listlen
        if not (isinstance(name, int) and n is not None and 0 <= name < n):
            self._setlistlen(None)

    def __setattr__ (self, name, value):
        self.__setitem__(name, value)

    def append (self, value):
        if self._listlen is None:
            raise Exception('Not a list-like Object')
        else:
            n = self._listlen
            self._setlistlen(n + 1)
            self._dict[n] = value

    def extend (self, values):
        for val in values:
            self.append(val)

    def __iter__ (self):
        if self._listlen is None:
            for k in self._dict.keys():
                yield k
        else:
            for i in range(self._listlen):
                yield self._dict[i]

    def __len__ (self): return len(self._dict)
    def items (self): return self._dict.items()
    def keys (self): return self._dict.keys()
    def values (self): return self._dict.values()

    def __repr__ (self):
        if self._listlen is None:
            return repr(self._dict)
        else:
            return repr(list(self))


#--  Reflexion  ----------------------------------------------------------------

def _docstring_lines (x):
    doc = x.__doc__
    if doc:
        if doc.startswith('\n'):
            i = 1
            while i < len(doc) and doc[i].isspace() and doc[i] not in '\r\n':
                i += 1
            prefix = doc[1:i]
            doc = doc[i:]
        else:
            prefix = ''
        n = len(prefix)
        for line in doc.split('\n'):
            if line.startswith(prefix):
                line = line[n:]
            yield line


class FunctionInfo (object):

    def __init__ (self, fnc, ismethod=False):
        dflts = fnc.__defaults__ or []
        nkws = len(dflts)
        varnames = fnc.__code__.co_varnames
        nselfargs = 1 if ismethod else 0
        nargs = fnc.__code__.co_argcount - (nselfargs + nkws)
        i = nselfargs
        j = 1 + nargs
        k = j + nkws   # after kws are local variables
        args = varnames[i:j]
        kws = varnames[j:k]
        doc = list(_docstring_lines(fnc)) if fnc.__doc__ else []

        self.function = fnc
        self.args = args
        self.kwargs = list((kws[i], dflts[i]) for i in range(len(kws)))
        self.doc = doc


def MethodInfo (method):
    return FunctionInfo(method, ismethod=True)


#--  ListProxy, MapProxy  ------------------------------------------------------

class ListProxy (object):

    def __iter__ (self):
        return self.__list__().__iter__()
        
    def __contains__ (self, k):
        return self.__list__().__contains__(k)

    def __getitem__ (self, k):
        return self.__list__().__getitem__(k)

    def __len__ (self):
        return self.__list__().__len__()

    def __repr__ (self):
        return self.__list__().__repr__()


class MapProxy (object):

    def __iter__ (self):
        return iter(self.__map__())
        
    def __len__ (self):
        return len(self.__map__())

    def __contains__ (self, k):
        return k in self.__map__()

    def __getitem__ (self, k):
        return self.__map__()[k]

    def get (self, k, dflt=None):
        return self.__map__().get(k, dflt)

    def keys (self):
        return self.__map__().keys()

    def values (self):
        return self.__map__().values()
    
    def items (self):
        return self.__map__().items()

    def __repr__ (self):
        return self.__map__().__repr__()


class LazyList (ListProxy):

    # The iterf should be repeatedly callable, returning an iteration
    # over the underlying data structure each time

    def __init__ (self, iterf):
        self._expanded = None
        self._iterf = iterf

    def __list__ (self):
        if self._expanded is None:
            self._expanded = list(self._iterf())
        return self._expanded

    def __iter__ (self):
        if self._expanded is None:
            return self._iterf()
        else:
            return iter(self._expanded)

    def __repr__ (self):
        if self._expanded is None:
            return '[...]'
        else:
            return repr(self._expanded)
