
from pathlib import Path


def split_at_ws (line):
    i = 0
    while i < len(line) and not line[i].isspace():
        i += 1
    if i >= len(line):
        return (line, None)
    else:
        return (line[:i], line[i+1:].strip())

def key_prefix (key):
    i = key.find('.')
    if i < 0:
        return key
    else:
        return key[:i+1]


#--  File  ---------------------------------------------------------------------

class File:

    __formats__ = None

    def __init__ (self, fn, signature, contents=None, format='dct', create=False):
        '''
        The signature is passed to the format.
        '''

        if format not in self.__formats__:
            raise Exception(f'Unrecognized format: {format}')            
        if fn and not isinstance(fn, Path):
            fn = Path(fn)

        self.filename = fn
        self.signature = signature
        self.format = self.__formats__[format](signature)
        self.contents = None

        if contents is None:
            if fn:
                self.load(fn, create)
            else:
                self.contents = {}
        else:
            self.parse(contents)

    def __len__ (self): return len(self.contents)
    def __getitem__ (self, key): return self.contents[key]
    def __iter__ (self): return iter(self.contents)
    def keys (self): return self.contents.keys()
    def values (self): return self.contents.values()
    def items (self): return self.contents.items()

    def load (self, fn, create=False):
        fn = Path(fn)
        if not (fn.exists() or create):
            raise Exception(f'File not found: {fn}')
        with open(fn) as f:
            self.read(f)

    def read (self, f):
        self.parse(f.read())

    def parse (self, s):
        self.contents = self.format.decode(s)

    def save (self, fn=None):
        if fn is None:
            fn = self.filename
        with open(fn, 'w') as f:
            self.write(f)

    def write (self, f):
        f.write(self.format.encode(self.contents, pretty=False))

    def __str__ (self):
        return self.format.encode(self.contents, pretty=True)

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self.filename.name}>'

    def export_cld (self):
        return CLDFormat(self.signature).encode(self.contents)

    def export_json (self):
        return JSONFormat(self.signature).encode(self.contents)


class JSONFormat:

    def __init__ (self, signature):
        pass

    def encode (self, contents, pretty=False):
        return json.dumps(contents, indent=(2 if pretty else None))

    def decode (self, s):
        return json.loads(s)


class DCTFormat:
    '''
    Each subdict is the value of a key, and the subdict's TYPE is the prefix
    of that key.

    The value for a key standing alone is obtained by reading a subdict at
    that point.

    A stack is maintained, in which the entries are pairs (attrs, parent).
    The current key-value pair can be attached to the parent iff the key's
    prefix is one of the attrs.

    The signature is a dict whose keys are subdict types and whose values
    are ATTRS lists.

    The root object type is the empty string.
    '''

    def __init__ (self, signature):
        self.signature = signature
        
    def decode (self, s):
        keys = self.signature['']
        stack = [(keys,{})]
        for (lno, key, value) in self._records(s):
            t = key_prefix(key)
            while stack and t not in stack[-1][0]:
                stack.pop()
            if not stack:
                raise Exception(f'No parent for {t} [lno {lno}]')
            parent = stack[-1][1]
            if key in parent:
                raise Exception(f'Duplicate key: {repr(key)} [lno {lno}]')
            if value is None:
                value = {}
                parent[key] = value
                if t not in self.signature:
                    raise Exception(f'Illegal key {key} [lno {lno}]')
                keys = self.signature[t]
                stack.append((keys, value))
            else:
                parent[key] = value
        return stack[0][1]

    def _records (self, text):
        for (lno, line) in enumerate(text.split('\n'), 1):
            line = line.strip().replace('\t', ' ')
            if line and not line.startswith('#'):
                (k,v) = split_at_ws(line)
                yield (lno, k, v)

    def encode (self, contents, pretty=False):
        with StringIO() as f:
            self._write_dict(contents, f, pretty, -1)
            return f.getvalue()

    def _write_dict (self, d, f, level):
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


File.__formats__ = {'dct': DCTFormat,
                    'json': JSONFormat}
