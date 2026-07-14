
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

def split_at_period (key):
    i = key.find('.')
    if i < 0:
        ty = key
        val = None
    else:
        ty = key[:i]
        val = key[i+1:]
    return (ty, val)


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
        if not (fn.exists() or create):
            raise Exception(f'File not found: {fn}')
        with open(fn) as f:
            self.read(f)

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
                (ty, _) = split_at_period(k)
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


#--  Node  ---------------------------------------------------------------------

class Item:

    def __init__ (self, parent, key):
        self.file = None if parent is None else parent.file
        self.parent = parent
        self.key = key
        self.full_name = key if parent is None else parent.full_name + '/' + key

    def item_type (self):
        return split_at_period(self.key)[0]

    def ancestors (self):
        if self.parent:
            yield from self.parent.ancestors()
        yield self

    def corpus (self):
        return self.parent.corpus()

    def language (self):
        return self.parent.language()

    def text (self):
        return self.parent.text()

    def sentence (self):
        return self.parent.sentence()

    def __eq__ (self, other):
        return isinstance(other, Item) and self.key == other.key and self.parent == other.parent

    def node (self):
        if isinstance(self, Node):
            return self
        else:
            return self.parent

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self.key}>'


class Node (Item):

    child_class = None
    child_prefix = None
    properties = None

    def __init__ (self, parent, key):
        Item.__init__(self, parent, key)
        self.cob = None if parent is None else parent.cob[key]
        self.table = Table(self)
        self.props = Props(self)

    def level (self):
        return self.file.signature.level(self.item_type())

    def child_keys (self):
        if self.child_prefix is None:
            raise ValueError('No child keys')
        for key in self.cob.keys():
            if key.startswith(self.child_prefix):
                yield key

    def __iter__ (self):
        for key in self.child_keys():
            yield self.child_class(self, key)
        
    def __bool__ (self):
        for _ in self.child_keys():
            return True
        return False

    def children (self):
        return self.__iter__()

    def __len__ (self):
        return sum(1 for _ in self.child_keys())

    def __getitem__ (self, i):
        childkey = None
        if i < 0:
            childkey = list(self.child_keys())[i]
        else:
            for (k, key) in enumerate(self.child_keys()):
                if k == i:
                    childkey = key
        if childkey is None:
            raise KeyError('Key not found')
        return self.child_class(self, childkey)

    def views (self):
        return [self]


class Table:

    def __init__ (self, node):
        self.node = node

    def __len__ (self):
        return self.node.__len__()

    def __iter__ (self):
        return self.node.child_keys()

    def __getitem__ (self, key):
        cls = self.node.child_class
        return cls(self.node, key)

    def keys (self):
        return self.node.child_keys()

    def values (self):
        return self.node

    def items (self):
        for child in self.node.__iter__():
            yield (child.key, child)


class Props (Item):

    def __init__ (self, node):
        Item.__init__(self, node, 'props')

    def __len__ (self):
        return len(self.parent.properties)

    def __iter__ (self):
        return iter(self.parent.properties)

    def __getitem__ (self, key):
        if key in self.parent.properties:
            return self.parent.cob.get(key, '')
        else:
            raise KeyError('Unrecognized key')

    def keys (self):
        return self.parent.properties

    def values (self):
        cob = self.parent.cob
        for key in self.parent.properties:
            yield cob.get(key, '')

    def items (self):
        cob = self.parent.cob
        for key in self.parent.properties:
            yield (key, cob.get(key, ''))


#--  Corpus  -------------------------------------------------------------------

class Corpus (Node):

    def __init__ (self, fn=None, **kwargs):
        Node.__init__(self, None, 'corp')
        if fn is not None:
            fn = Path(fn)
            self.key = 'corp.' + fn.stem
        self.file = File(fn, **kwargs)
        self.cob = self.file.cob

    def filename (self):
        return self.file.filename

    def level (self):
        return 0

    def corpus (self):
        return self

    def __str__ (self):
        return str(self.file)

    def export_cld (self):
        return self.file.export_cld()

    def export_json (self):
        return self.file.export_json()

    def save (self, fn=None):
        self.file.save(fn=fn)


class Lang (Node):

    def views (self):
        return [Props(self), Toc(self)]

    def language (self):
        return self

    def lexicon (self):
        return Lexicon(self)

    def toc (self):
        return Toc(self)


class Rom (Node):

    pass


class Text (Node):

    def text (self):
        return self

    def children (self):
        return list(self.iter_children())
    
    def iter_children (self):
        if 'ch' in self.cob:
            lang = self.parent
            for n in self.cob['ch'].split():
                ck = 'text.' + n
                if ck in lang.cob:
                    yield Text(lang, ck)

    def title (self):
        return self.cob.get('ti', '(untitled)')


class Lexicon (Node):

    def __init__ (self, parent):
        Node.__init__(self, parent, 'lexicon')


class Trans (Node):

    pass


class Sent (Node):

    def sentence (self):
        return self

    def times (self):
        return Times(self)

    def tokens (self):
        return list(self)

    def string (self):
        return self.cob['w']

    def set_string (self, s):
        self.cob['w'] = s

    def __len__ (self):
        return len(self.cob['w'].split())

    def __iter__ (self):
        for (i, s) in enumerate(self.cob['w'].split()):
            yield Token(self, i, s)

    def __getitem__ (self, i):
        strs = self.cob['w'].split()
        return Token(self, i, strs[i])


class Form (Node):

    pass


class Xlexicon (Node):

    pass


class Xtext (Node):

    pass


class Times (Node):

    def sentence (self):
        return self.parent


class Token:

    def __init__ (self, sentence, idx, string):
        self.sentence = sentence
        self.idx = idx
        self.string = string

    def __repr__ (self):
        return f'<Token {self.idx} {self.string}>'


#--  Toc  ----------------------------------------------------------------------

class Toc (Item):

    def __init__ (self, lang):
        Item.__init__(self, lang, 'toc')
        self._backlinks = self._build_backlinks()
        self._roots = [text for text in self.parent if text.key not in self._backlinks]
        
    def _build_backlinks (self):
        texts = list(self.parent)
        backlinks = {}
        for parent in texts:
            if 'ch' in parent.cob:
                for n in parent.cob['ch'].split():
                    ck = 'text.' + n
                    # silently overwrites any older value
                    backlinks[ck] = parent
        return backlinks

    def roots (self):
        return self._roots

    def parent (self, text):
        return self._backlinks.get(text.key)


signature._update_node_classes()

# Corpus.child_class = Lang
# Corpus.child_prefix = 'lang.'
# Corpus.properties = []
# 
# Lang.child_class = Text
# Lang.child_prefix = 'text.'
# Lang.properties = ['name', 'glot', 'iso3', 'rom']
# 
# Text.child_class = Sent
# Text.child_prefix = 'sent.'
# Text.properties = ['ty', 'ti', 'de', 'au', 'ch', 'pdf', 'audio', 'video']
# 
# Form.properties = ['ty', 'g', 'c', 'pp', 'cf', 'of']
# 
