
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


class Dict:

    __keys__ = None

    def __init__ (self, fn=None, create=False):
        if fn:
            fn = Path(fn)

        self._filename = fn
        self._contents = {}

        if fn:
            self.load(fn, create)

    def load (self, fn, create=False):
        fn = Path(fn)
        if fn.exists():
            ctx = _LoadContext(self)
            with open(fn) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        ctx.process(line)
        elif not create:
            raise Exception('File not found')

    def save (self, fn=None):
        if fn is None:
            fn = self._filename
        with open(fn, 'w') as f:
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

    def __getitem__ (self, key):
        return self._contents[key]

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

