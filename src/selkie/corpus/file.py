
import json
from io import StringIO
from pathlib import Path


class File:

    __formats__ = None

    def __init__ (self, fn, contents=None, format='cld', create=False):
        if format not in self.__formats__:
            raise Exception(f'Unrecognized format: {format}')            
        if fn and not isinstance(fn, Path):
            fn = Path(fn)

        self.filename = fn
        self.format = self.__formats__[format]()
        self.table = None

        # In the browser, we create a Corpus that has a filename and contents,
        # but the contents came from the server, not a local file

        if contents is None:
            if fn:
                self.load(fn, create)
            else:
                self.table = {}
        else:
            self.parse(contents)

    def deref (self, sn):
        return self.table[sn]

    def load (self, fn, create=False):
        fn = Path(fn)
        if fn.exists():
            with open(fn) as f:
                self.read(f)
        elif create:
            self.table = {}
        else:
            raise Exception(f'File not found: {fn}')

    def read (self, f):
        self.parse(f.read())

    def parse (self, s):
        self.table = self.format.decode(s)

    def save (self, fn=None):
        if fn is None:
            fn = self.filename
        with open(fn, 'w') as f:
            self.write(f)

    def write (self, f):
        f.write(self.format.encode(self.table))

    def __str__ (self):
        return self.format.encode(self.table)

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self.filename.name}>'

    def export_cld (self):
        return CLDFormat().encode(self.table)

    def export_json (self):
        return JSONFormat().encode(self.table)

    def rename (self, filename):
        self.filename = filename


class JSONFormat:

    def encode (self, contents, pretty=False):
        return json.dumps(contents, indent=(2 if pretty else None))

    def decode (self, s):
        return json.loads(s)


class CLDFormat:
        
    def decode (self, s):
        idx = {}
        parent = None
        records = self._records(s)
        for (lno, k, v) in records:
            if v is None:
                if k in idx:
                    print(f'** [{lno}] Duplicate sn, overwriting: {k}')
                parent = {'sn': k}
                idx[k] = parent
            else:
                if parent is None:
                    print(f'** [{lno}] Stray key-value pair')
                else:
                    if k in parent:
                        print(f'** [{lno}] Duplicate key, overwriting: {k}')
                    parent[k] = v
        return idx

    def _records (self, text):
        for (lno, line) in enumerate(text.split('\n')):
            line = line.strip().replace('\t', ' ')
            if (not line) or line.startswith('#'):
                if lno == 0 and line != '#!selkie file cld 28':
                    print('** Wrong file format')
            else:
                (k,v) = self._split(line)
                yield (lno, k, v)
    
    def _split (self, line):
        i = 0
        while i < len(line) and not line[i].isspace():
            i += 1
        if i >= len(line):
            return (line, None)
        else:
            return (line[:i], line[i+1:].strip())

    def encode (self, idx):
        with StringIO() as f:
            f.write('#!selkie file cld 28\n')
            for (k,v) in idx.items():
                if isinstance(v, dict):
                    self._write_cob(k,v,f)
                else:
                    self._write_record(k,v,f)
            return f.getvalue()

    def _write_cob (self, sn, cob, f):
        f.write(sn)
        f.write('\n')
        for (k,v) in cob.items():
            if k == 'sn':
                pass
            elif isinstance(v, dict):
                print(k, v['sn'], file=f)
            else:
                print(k, v, file=f)
                
    def _write_record (self, k, v, f):
        f.write(k)
        f.write(' ')
        f.write(v)
        f.write('\n')


File.__formats__ = {'cld': CLDFormat,
                    'json': JSONFormat}

