
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
        'text': ['ty', 'ti', 'de', 'au', 'ch', 'pdf', 'audio', 'video', 'sent'],
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

        self._filename = fn
        self._signature = signature
        self._format = self.__formats__[format](self._signature)
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

    def filename (self): return self._filename
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
        self.cob = self._format.decode(s)

    def save (self, fn=None):
        if fn is None:
            fn = self._filename
        with open(fn, 'w') as f:
            self.write(f)

    def write (self, f):
        f.write(self._format.encode(self.cob, pretty=False))

    def __str__ (self):
        return self._format.encode(self.cob, pretty=True)

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self._filename.name}>'

    def export_cld (self):
        return CLDFormat(self._signature).encode(self.cob)

    def export_json (self):
        return JSONFormat(self._signature).encode(self.cob)


class JSONFormat:

    def __init__ (self, signature):
        pass

    def encode (self, contents, pretty=False):
        return json.dumps(contents, indent=(2 if pretty else None))

    def decode (self, s):
        return json.loads(s)


class CLDFormat:

    def __init__ (self, signature):
        self._signature = signature
        
    def decode (self, s):
        stack = [{}]
        for (lno, k, v) in self._records(s):
            try:
                (ty, _) = split_at_period(k)
                lvl = self._signature.level(ty)
                if lvl == 0:
                    raise Exception(f'Invalid root key {k}')
                while len(stack) > lvl:
                    stack.pop()
                if len(stack) < lvl:
                    raise Exception(f'No parent for {k}')
                parent = stack[-1]
                if k in parent:
                    raise Exception(f'Duplicate key: {k}')
                if self._signature.children(ty):
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

class Location:

    def __init__ (self, item, **kwargs):
        self.item = item
        self.corpus = kwargs.get('corpus')
        self.language = kwargs.get('language')
        self.text = kwargs.get('text')
        self.sentence = kwargs.get('sentence')
        self.token = kwargs.get('token')
        self.word = kwargs.get('word')
        self.view = None


class Node:

    child_class = None
    child_prefix = None
    properties = None

    def __init__ (self, parent, key):
        self.file = None if parent is None else parent.file
        self.parent = parent
        self.key = key
        self.cob = None if parent is None else parent.cob[key]
        self.table = Table(self)
        self.props = Props(self)

    def __eq__ (self, other):
        return self.cob is other.cob and self.key == other.key

    def child_keys (self):
        if self.child_prefix is None:
            raise ValueError('No child keys')
        for key in self.cob.keys():
            if key.startswith(self.child_prefix):
                yield key

    def __iter__ (self):
        for key in self.child_keys():
            yield self.child_class(self, key)
        
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

    def location (self):
        raise NotImplementedError()

    def ancestors (self):
        if self.parent:
            yield from self.parent.ancestors()
        yield self

    def key_type (self):
        return split_at_period(self.key)[0]

    def full_name (self):
        return ' '.join([anc.key for anc in self.ancestors() if anc.key])

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self.key}>'


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


class Props:

    def __init__ (self, node):
        self.node = node

    def __len__ (self):
        return len(self.node.properties)

    def __iter__ (self):
        return iter(self.node.properties)

    def __getitem__ (self, key):
        if key in self.node.properties:
            return self.node.cob.get(key, '')
        else:
            raise KeyError('Unrecognized key')

    def keys (self):
        return self.node.properties

    def values (self):
        cob = self.node.cob
        for key in self.node.properties:
            yield cob.get(key, '')

    def items (self):
        cob = self.node.cob
        for key in self.node.properties:
            yield (key, cob.get(key, ''))


#--  Corpus  -------------------------------------------------------------------

class Corpus (Node):

    def __init__ (self, fn=None, **kwargs):
        Node.__init__(self, None, None)
        if fn is not None:
            fn = Path(fn)
            self.key = 'corp.' + fn.stem
        self.file = File(fn, **kwargs)
        self.cob = self.file.cob

    def filename (self):
        return self.cob.filename()

    def location (self):
        return Location(self, corpus=self)

    def __str__ (self):
        return str(self.file)

    def export_cld (self):
        return self.file.export_cld()

    def export_json (self):
        return self.file.export_json()

    def save (self, fn=None):
        self.file.save(fn=fn)


class Lang (Node):

    def location (self):
        return Location(self, language=self, corpus=self.parent)

    def lexicon (self):
        return Lexicon(self)


class Rom (Node):

    pass


class Text (Node):

    def location (self):
        return Location(self, text=self, language=self.parent, corpus=self.parent.parent)


class Lexicon (Node):

    def __init__ (self, parent):
        Node.__init__(self, parent, 'lexicon')


class Trans (Node):

    pass


class Sent (Node):

    def location (self):
        text = self.parent
        lang = text.parent
        corp = lang.parent
        return Location(self, sentence=self, text=text, language=lang, corpus=corp)

    def text (self):
        return self.parent

    def language (self):
        return self.text().language()

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


class TOC (Node):

    def __init__ (self, lang):
        Node.__init__(self, lang)
        self.language = lang
        self.parent_tab = self._build_parent_tab()
        
    def _build_parent_tab (self):
        texts = list(self.language)
        parent_tab = {}
        for parent in texts:
            if 'ch' in parent.cob:
                for n in parent.cob['ch'].split():
                    ck = 'text.' + n
                    parent_tab[ck] = parent
        return parent_tab


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
