
#
#  Lines are either NODE NAMES (no space) or DATA (space separates key and value)
#  Each node name has a LEVEL (of indentation)
#
#  Reading the file
#  ----------------
#  Keep a stack of dicts
#  

import json
from io import StringIO
from pathlib import Path
from itertools import islice


def split_at_ws (line):
    i = 0
    while i < len(line) and not line[i].isspace():
        i += 1
    if i >= len(line):
        return (line, None)
    else:
        return (line[:i], line[i+1:].strip())

def split_key (key):
    i = key.find('.')
    if i < 0:
        ty = key
        val = ''
    else:
        ty = key[:i]
        val = key[i+1:]
    return (ty, val)

def nth (iter, n):
    for (i, elt) in enumerate(iter):
        if i == n:
            return elt


class Signature:
    
    default_spec = {
        'corpus': ['lang', 'rom'],
        'lang': ['name', 'glot', 'iso3', 'userom', 'text', 'lexicon', 'trans'],
        'rom': ['u'],
        'text': ['sent', 'ty', 'ti', 'de', 'au', 'ch', 'pdf', 'audio', 'video', 'xid'],
        'lexicon': ['form'],
        'trans': ['xlexicon', 'xtext'],
        'sent': ['w', 'tr', 'times'],
        'form': ['fy', 'g', 'c', 'pp', 'cf', 'of'],
        'xlexicon': ['fg'],
        'xtext': ['sg'],
        'times': ['t']
    }

    def __init__ (self, spec=None):
        self._children = spec or self.default_spec
        self._levels = {}
        self._parents = {}

        self._set_level_recurse('corpus', 0)

    def _set_level_recurse (self, ty, lvl):
        if ty in self._levels:
            raise Exception(f'Recursion in signature: {ty}')
        self._levels[ty] = lvl
        if ty in self._children:
            for child in self._children[ty]:
                if child in self._parents:
                    raise Exception(f'Type with multiple parents: {child}')
                self._parents[child] = ty
                self._set_level_recurse(child, lvl+1)

    def level (self, ty):
        return self._levels[ty]

    def children (self, ty):
        return self._children.get(ty)

    def parent (self, ty):
        return self._parents[ty]

    def child_type (self, ty):
        for ct in self._children[ty]:
            if ct in self._children:
                return ct

    def properties (self, ty):
        for ct in self._children[ty]:
            if ct not in self._children:
                yield ct

    def __str__ (self):
        return str(self._children)

    def _update_node_classes (self):
        tab = globals()
        for pt in self._children:
            ct = self.child_type(pt)
            pcls = tab[pt.capitalize()]
            pcls.properties = list(self.properties(pt))
            if ct:
                ccls = tab[ct.capitalize()]
                pcls.child_class = ccls
                pcls.child_prefix = ct + '.'


signature = Signature()


#--  File  ---------------------------------------------------------------------

class File:

    __formats__ = None

    def __init__ (self, fn, signature=signature, contents=None, format='cld', create=False):
        if format not in self.__formats__:
            raise Exception(f'Unrecognized format: {format}')            
        if fn and not isinstance(fn, Path):
            fn = Path(fn)

        self.filename = fn
        self.signature = signature
        self.format = self.__formats__[format](signature)
        self.cob = None

        # In the browser, we create a Corpus that has a filename and contents,
        # but the contents came from the server, not a local file

        if contents is None:
            if fn:
                self.load(fn, create)
            else:
                self.cob = {}
        else:
            self.parse(contents)

    def __len__ (self): return len(self.cob)
    def __getitem__ (self, key): return self.cob[key]
    def __iter__ (self): return iter(self.cob)
    def keys (self): return self.cob.keys()
    def values (self): return self.cob.values()
    def items (self): return self.cob.items()

    def load (self, fn, create=False):
        fn = Path(fn)
        if fn.exists():
            with open(fn) as f:
                self.read(f)
        elif create:
            self.cob = {}
        else:
            raise Exception(f'File not found: {fn}')

    def read (self, f):
        self.parse(f.read())

    def parse (self, s):
        self.cob = self.format.decode(s)

    def save (self, fn=None):
        if fn is None:
            fn = self.filename
        with open(fn, 'w') as f:
            self.write(f)

    def write (self, f):
        f.write(self.format.encode(self.cob, pretty=False))

    def __str__ (self):
        return self.format.encode(self.cob, pretty=True)

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self.filename.name}>'

    def export_cld (self):
        return CLDFormat(self.signature).encode(self.cob)

    def export_json (self):
        return JSONFormat(self.signature).encode(self.cob)

    def rename (self, filename):
        self.filename = filename


class JSONFormat:

    def __init__ (self, signature):
        pass

    def encode (self, contents, pretty=False):
        return json.dumps(contents, indent=(2 if pretty else None))

    def decode (self, s):
        return json.loads(s)


class CLDFormat:

    def __init__ (self, signature):
        self.signature = signature
        
    def decode (self, s):
        stack = [{}]
        for (lno, k, v) in self._records(s):
            try:
                (ty, _) = split_key(k)
                lvl = self.signature.level(ty)
                if lvl == 0:
                    raise Exception(f'Invalid root key {k}')
                while len(stack) > lvl:
                    stack.pop()
                if len(stack) < lvl:
                    raise Exception(f'No parent for {k}')
                parent = stack[-1]
                if k in parent:
                    raise Exception(f'Duplicate key: {k}')
                if self.signature.children(ty):
                    v = {}
                    parent[k] = v
                    stack.append(v)
                else:
                    parent[k] = v
            except Exception as e:
                print(f'** [line {lno}]', str(e))
        return stack[0]

    def _records (self, text):
        for (lno, line) in enumerate(text.split('\n')):
            line = line.strip().replace('\t', ' ')
            if line and not line.startswith('#'):
                (k,v) = split_at_ws(line)
                yield (lno, k, v)

    def encode (self, contents, pretty=False):
        with StringIO() as f:
            self._write_dict(contents, f, pretty, -1)
            return f.getvalue()

    def _write_dict (self, d, f, pretty, level):
        assert isinstance(d, dict)
        for (k,v) in d.items():
            if pretty: self._write_indent(level+1, f)
            if isinstance(v, str):
                print(k, v, file=f)
            else:
                print(k, file=f)
                self._write_dict(v, f, pretty, level+1)

    def _write_indent (self, level, f):
        for _ in range(2 * level):
            f.write(' ')


File.__formats__ = {'cld': CLDFormat,
                    'json': JSONFormat}


