
#
#  Lines are either NODE NAMES (no space) or DATA (space separates key and value)
#  Each node name has a LEVEL (of indentation)
#
#  Reading the file
#  ----------------
#  Keep a stack of dicts
#  

from io import StringIO
from pathlib import Path


def _split_at_ws (line):
    i = 0
    while i < len(line) and not line[i].isspace():
        i += 1
    if i >= len(line):
        return (line, None)
    else:
        return (line[:i], line[i+1:])

def _nested_dict_push (d, key):
    if key in d:
        d1 = d[key]
        assert isinstance(d1, dict)
    else:
        d1 = {}
        d[key] = d1
    return d1


#--  Dict  ---------------------------------------------------------------------

class Dict:

    __keys__ = None

    def __init__ (self, fn=None, create=False):
        if fn:
            fn = Path(fn)

        self._filename = fn
        self._contents = {}

        if fn:
            self.load(fn, create)

    def __len__ (self): return len(self._contents)
    def __getitem__ (self, key): return self._contents[key]
    def __iter__ (self): return iter(self._contents)
    def keys (self): return self._contents.keys()
    def values (self): return self._contents.values()
    def items (self): return self._contents.items()

    def load (self, fn, create=False):
        fn = Path(fn)
        if fn.exists():
            with open(fn) as f:
                self.read(f)
        elif not create:
            raise Exception('File not found')

    def read (self, f):
        ctx = _LoadContext(self)
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                ctx.process(line)

    def save (self, fn=None):
        if fn is None:
            fn = self._filename
        with open(fn, 'w') as f:
            self.write(f)

    def write (self, f):
        self._write_dict(self._contents, f, False, 0)

    def _write_dict (self, d, f, pretty, level):
        assert isinstance(d, dict)
        for (k,v) in d.items():
            if isinstance(v, str):
                if pretty: self._write_indent(level+1, f)
                print(k, v, file=f)
            else:
                chlevel = self._node_level(k)
                if pretty: self._write_indent(chlevel, f)
                print(k, file=f)
                self._write_dict(v, f, pretty, chlevel)

    def _node_level (self, name):
        typ = name.split('.')[0]
        if typ not in self.__keys__:
            raise Exception(f'Unrecognized node type {typ}')
        return self.__keys__[typ]

    def _write_indent (self, level, f):
        for _ in range(2 * level):
            f.write(' ')

    def __repr__ (self):
        return repr(self._contents)

    def __str__ (self):
        with StringIO() as f:
            self._write_dict(self._contents, f, True, 0)
            return f.getvalue()


class _LoadContext:

    def __init__ (self, corpus):
        self.corpus = corpus
        self.path = [corpus._contents]

    def process (self, line):
        (key, value) = _split_at_ws(line)
        if value is None:
            self.process_node(key)
        else:
            self.process_datum(key, value)

    def process_node (self, name):
        level = self.corpus._node_level(name)
        idx = level + 1
        assert idx > 0
        path = self.path
        while len(path) > idx:
            path.pop()
        d = path[-1]
        while len(path) < idx:
            path.append(d)
        d = _nested_dict_push(d, name)
        path.append(d)
                
    def process_datum (self, key, value):
        self.path[-1][key] = value


#--  KeyPath  ------------------------------------------------------------------

class KeyPath:

    def __init__ (self, corpus):
        self._corpus = corpus
        self._menus = []
        self._node = corpus

    def __len__ (self): return len(self._menus)
    def __iter__ (self): return iter(self._menus)
    def __getitem__ (self, i): return self._menus[i]
    def corpus (self): return self._corpus
    def menus (self): return self._menus
    def node (self): return self._node

    def join (self, key):
        d = self._node
        menu = [key] + sorted(k for (k,v) in d.items() if k != key and not isinstance(v, str))
        path = KeyPath(self._corpus)
        path._menus = self._menus + [menu]
        path._node = d[key]
        return path

    def __repr__ (self):
        return f'<KeyPath {' '.join(menu[0] for menu in self._menus)}>'


#--  Node  ---------------------------------------------------------------------

class Node:

    __nodetype__ = None
    __keys__ = {}

    def __init__ (self, parent, name=None):
        key = self.__nodetype__
        if name:
            key = key + '.' + name
        self._path = parent.path().join(key)

    def path (self): return self._path
    def corpus (self): return self._path.corpus()
    def node (self): return self._path.node()
    def is_legal_key (self, key): return key in self.__keys__
    
    def __getitem__ (self, key):
        if not self.is_legal_key(key):
            raise KeyError('Unrecognized key')
        return self._path._node[str(key)]

    def __setitem__ (self, key, value):
        if not self.is_legal_key(key):
            raise KeyError('Unrecognized key')
        self._path._node[str(key)] = value


#--  Corpus  -------------------------------------------------------------------

class Corpus (Dict):

    __keys__ = {
        'lang': 0,
        'rom': 0,
        'text': 1,
        'lexicon': 1,
        'trans': 1,
    	'sent': 2,
        'form': 2,
        'xlexicon': 2,
        'xtext': 2,
    	'times': 3
    }

    def path (self):
        return KeyPath(self)

    def language (self, name):
        return Language(self, name)


class Language (Node):

    __nodetype__ = 'lang'
    __keys__ = {'name', 'glot', 'iso3', 'rom'}

    def text (self, name):
        return Text(self, name)


class Text (Node):

    __nodetype__ = 'text'
    __keys__ = {'ty', 'ti', 'de', 'au', 'ch', 'pdf', 'audio', 'video'}

    def sentence (self, name):
        return Sentence(self, name)


class Sentence (Node):

    __nodetype__ = 'sent'
    __keys__ = {'w', 'g'}

    def times (self):
        return Times(self)


class Times (Node):

    __nodetype__ = 'times'

    def is_legal_key (self, key):
        return isinstance(key, int)
