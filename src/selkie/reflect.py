

def load_module (name):
    '''
    Load a module, given a fully qualified name.
    The return value is the module.
    '''
    names = name.split('.')
    module = file = path = None
    try:
        for name in names:
            (file, path, desc) = imp.find_module(name, path)
            module = imp.load_module(name, file, path, desc)
            if file is not None: file.close()
            if hasattr(module, '__path__'): path = module.__path__
    finally:
        if file is not None: file.close()
    return module


def import_class (spec):
    '''
    Import a class, given a fully qualified name.
    '''
    i = spec.rfind('.')
    if i < 0: raise Exception('Need a fully qualified class name: %s' % spec)
    name = spec[i+1:]
    modname = spec[:i]
    module = importlib.import_module(modname)
    try:
        cls = module.__dict__[name]
    except KeyError:
        raise Exception('No class named %s in %s' % (name, modname))
    return cls


def class_name (cls):
    '''
    The fully qualified name for a given class object.
    '''
    return cls.__module__ + '.' + cls.__name__


def import_object (s):
    '''
    Takes a fully-qualified name and gets the object, importing the class if necessary.
    '''
    j = s.rfind('.')
    if j < 0:
        raise Exception('Require fully qualified name')
    m = load_module(s[:j])
    return m.__dict__[s[j+1:]]


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
    '''
    Instantiation: ``FunctionInfo(fnc)``. The argument is a function object
    (not a name). The FunctionInfo object has the attributes:

     * ``function`` — the function object
     * ``args`` — a list of parameter names (positional arguments)
     * ``kwargs`` — a list of (key, default) pairs
     * ``doc`` — the docstring
    
    '''
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
    '''
    Like FunctionInfo, but takes a method.
    '''
    return FunctionInfo(method, ismethod=True)
