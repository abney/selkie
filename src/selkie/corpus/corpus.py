
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
from itertools import islice


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

def nth (g, i):
    return next(islice(g, i, None))


#--  Dict  ---------------------------------------------------------------------

class Dict:

    __keys__ = None

    def __init__ (self, fn=None, contents=None, create=False):
        self._filename = fn
        self._contents = {}

        # In the browser, we create a Corpus that has a filename and contents,
        # but the contents came from the server, not a local file

        if contents is None:
            if fn:
                self.load(fn, create)
        else:
            self.read(contents.split('\n'))

    def filename (self): return self._filename
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
        return f'<{self.__class__.__name__} {self._filename}>'

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
# 
# class KeyPath:
# 
#     def __init__ (self, corpus):
#         self._corpus = corpus
#         self._menus = []
#         self._node = corpus
# 
#     def __len__ (self): return len(self._menus)
#     def __iter__ (self): return iter(self._menus)
#     def __getitem__ (self, i): return self._menus[i]
#     def corpus (self): return self._corpus
#     def menus (self): return self._menus
#     def node (self): return self._node
#     def string (self): return ' '.join(menu[0] for menu in self._menus)
# 
#     def join (self, key):
#         d = self._node
#         menu = [key] + sorted(k for (k,v) in d.items() if k != key and not isinstance(v, str))
#         path = KeyPath(self._corpus)
#         path._menus = self._menus + [menu]
#         path._node = d[key]
#         return path
# 
#     def __repr__ (self):
#         return f'<KeyPath {self.string()}>'
# 

#--  Node  ---------------------------------------------------------------------

class CorpusLocation:

    def __init__ (self, item=None, corpus=None, language=None, text=None,
                  sentence=None, token=None, word=None):
        self.item = item
        self.corpus = corpus
        self.language = language
        self.text = text
        self.sentence = sentence
        self.token = token
        self.word = word
        self.view = None


class Node:

    child_class = None
    child_prefix = None
    properties = None

    def __init__ (self, parent, key):
        self.parent = parent
        self.key = key
        self.meta = None if parent is None else parent.meta[key]
        self.table = Table(self)
        self.props = Props(self)

    def __eq__ (self, other):
        return self.meta is other.meta and self.key == other.key

    def _child_keys (self):
        if self.child_prefix is None:
            raise ValueError('No child keys')
        for key in self.meta.keys():
            if key.startswith(self.child_prefix):
                yield key

    def __iter__ (self):
        for key in self._child_keys():
            yield self.child_class(self, key)
        
    def __len__ (self):
        return sum(1 for _ in self._child_keys())

    def __getitem__ (self, i):
        childkey = None
        if i < 0:
            childkey = list(self._child_keys())[i]
        else:
            for (k, key) in enumerate(self._child_keys()):
                if k == i:
                    childkey = key
        if childkey is None:
            raise KeyError('Key not found')
        return self.child_class(self, childkey)

    def ancestors (self):
        if self.parent:
            yield from self.parent.ancestors()
        yield self

    def key_type (self):
        return self.key.split('.')[0]

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
        return self.node._child_keys()

    def __getitem__ (self, key):
        cls = self.node.child_class
        return cls(self.node, key)

    def keys (self):
        return self.node._child_keys()

    def values (self):
        return self.node

    def items (self):
        for child in self.node.__iter__():
            yield (child.key, child)


class Props:

    def __init__ (self, node):
        self.node = node

    def __len__ (self):
        return len(node.properties)

    def __iter__ (self):
        return iter(node.properties)

    def __getitem__ (self, key):
        if key in self.node.properties:
            return self.node.meta.get(key, '')
        else:
            raise KeyError('Unrecognized key')

    def keys (self):
        return self.node.properties

    def values (self):
        meta = self.node.meta
        for key in self.node.properties:
            yield meta.get(key, '')

    def items (self):
        meta = self.node.meta
        for key in self.node.properties:
            yield (key, meta.get(key, ''))


#--  Corpus  -------------------------------------------------------------------

class CorpusDict (Dict):

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


class Corpus (Node):

    def __init__ (self, fn=None, **kwargs):
        Node.__init__(self, None, None)
        self.meta = CorpusDict(fn=fn, **kwargs)
        self.parent = None
        self.key = 'corpus'

    def filename (self):
        return self.meta.filename()

    def location (self):
        return CorpusLocation(self, corpus=self)


class Language (Node):

    def location (self):
        return CorpusLocation(self, language=self, corpus=self.parent)


class Text (Node):

    def location (self):
        return CorpusLocation(self, text=self, language=self.parent, corpus=self.parent.parent)


class Sentence (Node):

    def location (self):
        text = self.parent
        lang = text.parent
        corp = lang.parent
        return CorpusLocation(self, sentence=self, text=text, language=lang, corpus=corp)

    def text (self):
        return self.parent

    def language (self):
        return self.text().language()

    def times (self):
        return Times(self)

    def tokens (self):
        return list(self)

    def string (self):
        return self.meta['w']

    def set_string (self, s):
        self.meta['w'] = s

    def __len__ (self):
        return len(self.meta['w'].split())

    def __iter__ (self):
        for (i, s) in enumerate(self.meta['w'].split()):
            yield Token(self, i, s)

    def __getitem__ (self, i):
        strs = self.meta['w'].split()
        return Token(self, i, strs[i])


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


class Lexicon (Node):

    pass


class Word (Node):

    pass


Corpus.child_class = Language
Corpus.child_prefix = 'lang.'
Corpus.properties = []

Language.child_class = Text
Language.child_prefix = 'text.'
Language.properties = ['name', 'glot', 'iso3', 'rom']

Text.child_class = Sentence
Text.child_prefix = 'sent.'
Text.properties = ['ty', 'ti', 'de', 'au', 'ch', 'pdf', 'audio', 'video']

Word.properties = ['ty', 'g', 'c', 'pp', 'cf', 'of']
