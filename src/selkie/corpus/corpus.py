
from pathlib import Path


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


#--  Node  ---------------------------------------------------------------------

class Node:

    # NodeIndex keys are serial numbers

    NodeIndex = {}
    NextSn = 0

    def __init__ (self, parent, key):
        self.nn = len(self.index)
        self.file = None if parent is None else parent.file
        self.parent = parent
        self.key = key

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

    def node (self):
        if isinstance(self, Node):
            return self
        else:
            return self.parent

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self.key}>'


class Cob (Node):

    def __init__ (self, cob):
        '''Assumes we have already done Node.__init__'''
        self.cob = cob
        self.sn = int(self.cob['sn'])
        
        if self.sn is not None:
            if sn >= self.NextSn:
                self.NextSn = sn + 1
            self.NodeIndex[sn] = self


class View (Node):

    Page = None
    view_of = None


class Selection:

    def __init__ (self, options):
        self.selected = None
        self.options = options


class Selector (Node):

    Choices = None

    def __init__ (self):
        self.state = {choice: Selection(getattr(self, choice)) for choice in choices}


class Viewable (Selector):

    def __init__ (self, views):
        if 'views' not in self.Choices:
            raise Exception("Viewable that does not have 'views' as a choice")
        self._views = views
        for view in self._views:
            if not isinstance(view, View):
                raise Exception('Not a view')
            if view.view_of is not None:
                raise Exception('Attempt to re-use a View')
            view.view_of = self
        Selector.__init__(self)
        selection = self.state['views']
        selection.selected = self._views[0]

    def views (self):
        return self._views

    def current_view (self):
        return self.state['views'].selected


#-------------------------------------------------------------------------------

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


#--  Directory  ----------------------------------------------------------------

# This is here to make life a little easier for the Editor. It pretends to be
# a node, though it is outside the genuine node sequence.


class Directory (Node):

    def __init__ (self):
        Node.__init__(self, None, 'directory')
        self.table = {}
        self.n_untitled = 0
        
    # the topmost genuine node is the corpus
    def ancestors (self): return []
    def node (self): return self
    def views (self): return [self]

    def __iter__ (self): return iter(self.table.values())
    def __bool__ (self): return bool(self.table)
    def children (self): return self.__iter__()
    def __len__ (self): return len(self.table)
    def __getitem__ (self, i): return nth(self.table.values(), i)

    def get (self, key):
        return self.table.get(key)

    def open (self, fn, **kwargs):
        fn = Path(fn)
        key = fn.stem
        if key in self.table:
            return self.table[key]
        else:
            corpus = Corpus(fn, key=key, **kwargs)
            self.table[key] = corpus
            return corpus

    def new_child (self):
        self.n_untitled += 1
        corpus = Corpus(f'untitled-{self.n_untitled}', create=True)
        self.table[corpus.key] = corpus
        return corpus

    def rename (self, corpus, filename):
        del self.table[corpus.full_name]
        corpus.rename(filename)
        self.table[corpus.full_name] = corpus


#--  Corpus  -------------------------------------------------------------------

class Corpus (Cob, Viewable):

    def __init__ (self, fn, key=None, **kwargs):
        fn = Path(fn)
        if key is None: key = fn.stem
        Cob.__init__(self, None, key)
        self.file = File(fn, **kwargs)
        self.cob = self.file.index['0']

    def filename (self):
        return self.file.filename

    def corpus (self):
        return self

    def views (self):
        return [CorpusProps(self), Roms(self)]

    def __str__ (self):
        return str(self.file)

    def export_cld (self):
        return self.file.export_cld()

    def export_json (self):
        return self.file.export_json()

    def save (self, fn=None):
        self.file.save(fn=fn)

    def rename (self, filename):
        self.file.filename = filename
        self.key = fn_to_key(filename)
        self.full_name = self.key


class Lang (Node):

    def views (self):
        return [Props(self), Toc(self)]

    def language (self):
        return self

    def lexicon (self):
        return Lexicon(self)

    def toc (self):
        return Toc(self)


class Roms (Item):

    def __init__ (self, parent):
        Item.__init__(self, parent, 'roms')

    def __getitem__ (self, name): return self.parent.cob[name]
    def get (self, name): return self.parent.cob.get(name)
    def keys (self): return (key for key in self.parent.cob if key.startswith('rom.'))
    def __iter__ (self): return self.keys()
    def __len__ (self): return sum(1 for _ in self.keys())
    def values (self): return (v for (k,v) in self.parent.cob.items() if k.startswith('rom.'))
    def items (self): return ((k,v) for (k,v) in self.parent.cob.items() if k.startswith('rom.'))


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
