
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

class Location:

    __formats__ = None

    def __init__ (self, name=None):
        self._name = name

    def name (self):
        return self._name

    def rename (self, name):
        self._name = name

    def open (self, fmt):
        return File(self, fmt)

    def read (self):
        raise NotImplementedError()

    def write (self, contents):
        raise NotImplementedError()

    def save (self):
        raise NotImplementedError()


class TestLocation (Location):

    def __init__ (self, contents):
        Location.__init__(self)
        assert isinstance(contents, str)
        self._contents = contents

    def read (self):
        return self._contents

    def write (self, s):
        assert isinstance(s, str)
        self._contents = s

    def __str__ (self):
        return '(string)'


class UploadedFile (Location):

    def __init__ (self, name, contents):
        Location.__init__(self, name)
        self._contents = contents

    def read (self):
        return self._contents
    
    def __repr__ (self):
        return f'<UploadedFile {self.name()}>'


class Pathname (Location):

    def __init__ (self, fn):
        if not isinstance(fn, Path):
            fn = Path(fn)
        Location.__init__(self, fn)

    def read (self):
        fn = self.name()
        if fn.exists():
            with open(fn) as f:
                return f.read()
        else:
            return ''

    def write (self, s):
        with open(self.name(), 'w') as f:
            f.write(s)

    def __str__ (self):
        return str(self.name())


#--  Formats  ------------------------------------------------------------------

class JSONFormat:

    name = 'json'

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

    def __init__ (self, name, **kwargs):
        self.name = name
        self.root = next(iter(kwargs))
        self.signature = {}
        for (k,v) in kwargs.items():
            self.signature[k] = set(v)
        
    def _stack_repr (self, stack):
        return ' '.join(f"{t}{' '.join(sorted(keys))}" for (t,keys,_) in stack)

    def decode (self, s):
        stack = [(self.signature[self.root], {})]
        for (lno, key, value) in self._records(s):
            t = key_prefix(key)
            while t not in stack[-1][0]:
                if len(stack) <= 1:
                    raise Exception(f'[lno {lno}] No parent found: key={repr(key)} t={repr(t)}')
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



#--  File  ---------------------------------------------------------------------

class File (Location):

    __formats__ = {'json': JSONFormat()}

    def __init__ (self, loc=None, format=None):
        if loc is None:
            loc = TestLocation('')
        elif isinstance(loc, str):
            loc = Pathname(loc)
        elif not isinstance(loc, Location):
            raise Exception(f'Invalid location argument: {repr(loc)}')

        Location.__init__(self, loc)
        content_string = loc.read()

        file_format = None
        if content_string.startswith('#!selkie file '):
            i = j = 14
            while j < len(content_string) and not content_string[j].isspace():
                j += 1
            file_format = content_string[i:j]

        if format is None:
            if file_format is None:
                raise Exception('No format provided, cannot determine format from file')
            format = file_format

        if isinstance(format, str):
            if format not in self.__formats__:
                raise Exception(f'Unrecognized format: {format}')            
            format = self.__formats__[format]
            
        if file_format is not None:
            if format.name != file_format:
                raise Exception(f'File format {file_format} does not match format parameter {format.name}')

        assert hasattr(format, 'decode')
        assert hasattr(format, 'encode')

        self.format = format
        self.contents = format.decode(content_string)

    def location (self):
        return self._name

    def name (self):
        return self.location().name()

    def rename (self, name):
        self.location().rename(name)

    def read (self):
        return self.contents

    def write (self, newcontents):
        self.contents = newcontents
        self.save()

    def save (self):
        self.location().write(self.format.encode(self.contents))

    def __str__ (self):
        return self.format.encode(self.contents, pretty=True)

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self.name()}>'

    def export (self, format):
        if isinstance(format, str):
            format = self.__formats__[format]
        return format.encode(self.contents)


#-------------------------------------------------------------------------------

__formats__ = File.__formats__
