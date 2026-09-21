
import json, os
from io import StringIO
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
        return key[:i]


#--  Location  -----------------------------------------------------------------

class TestLocation:

    def __init__ (self, contents):
        assert isinstance(contents, str)
        self.contents = contents

    def read (self):
        return self.contents

    def write (self, s):
        assert isinstance(s, str)
        self.contents = s

    def __str__ (self):
        return '(string)'


class PathLocation:

    def __init__ (self, fn):
        if not isinstance(fn, Path):
            fn = Path(fn)
        self.fn = fn

    def read (self):
        if self.fn.exists():
            with open(self.fn) as f:
                return f.read()
        else:
            return ''

    def write (self, s):
        with open(self.fn, 'w') as f:
            f.write(s)

    def __str__ (self):
        return str(self.fn)


#--  File  ---------------------------------------------------------------------

class File:

    __formats__ = None

    def __init__ (self, fn=None, format=None):
        if fn is None:
            self.filename = TestLocation('')
        else:
            self.filename = PathLocation(fn)

        content_string = self.filename.read()

        if format is None:
            if not content_string.startswith('#!selkie file '):
                raise Exception('No format provided, cannot determine format from file')
            i = j = 14
            while j < len(content_string) and not content_string[j].isspace():
                j += 1
            format = content_string[i:j]

        if isinstance(format, str):
            if format not in self.__formats__:
                raise Exception(f'Unrecognized format: {format}')            
            format = self.__formats__[format]
            
        assert hasattr(format, 'decode')
        assert hasattr(format, 'encode')

        self.format = format
        self.contents = format.decode(content_string)

    def save (self):
        self.filename.write(self.format.encode(self.contents))

    def __str__ (self):
        return self.format.encode(self.contents, pretty=True)

    def __repr__ (self):
        return f'<{self.__class__.__name__} {str(self.filename)}>'

    def export (self, format):
        if isinstance(format, str):
            format = self.__formats__[format]
        return format.encode(self.contents)


class JSONFormat:

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

    def __init__ (self, name, roots, **kwargs):
        self.name = name
        self.signature = {}
        self.signature[''] = set(roots)
        for (k,v) in kwargs.items():
            self.signature[k] = set(v)
        
    def decode (self, s):
        keys = self.signature['']
        stack = [(keys,{})]
        for (lno, key, value) in self._records(s):
            t = key_prefix(key)
            while t not in stack[-1][0]:
                if len(stack) <= 1:
                    raise Exception(f'No parent found for {repr(key)} [lno {lno}] t={repr(t)} stack={repr(stack)}')
                stack.pop()
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
            print(f'#!selkie file {self.name}', file=f)
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


__formats__ = File.__formats__ = {'json': JSONFormat()}
