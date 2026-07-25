
from pathlib import Path
from .file import File


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

    Choice = None

    def __init__ (self, parent, file=None):
        if file is None:
            file = parent.file
        self.parent = parent
        self.file = file

    def ancestors (self):
        yield self
        if self.parent:
            yield from self.parent.ancestors()

    def corpus (self):
        return self.parent.corpus()

    def language (self):
        return self.parent.language()

    def text (self):
        return self.parent.text()

    def sentence (self):
        return self.parent.sentence()

    def current_view (self):
        raise Exception(f'Not selectable: {self}')

    def select (self):
        view = self.current_view()
        state = {}
        selected = {}
        for anc in view.context_ancestors():
            if isinstance(anc, Selector):
                for (choice, selection) in anc.state.items():
                    if choice not in state:
                        state[choice] = selection
                        if choice in selected:
                            selection.selected = selected[choice]
            if anc.Choice is not None:
                selected[anc.Choice] = anc
        return state 


class Cob (Node):

    CobIndex = {}
    CobInfo = {'next_sn': 0}

    def __init__ (self, parent, sn=None, key=None, file=None):
        Node.__init__(self, parent, file)

        if sn is None:
            assert parent is not None
            k = self.__class__.__name__.lower()
            assert k in parent.cob
            sn = parent.cob[k]

        assert isinstance(sn, str) and sn.isdigit()
        cob = self.file.deref(str(sn))
        if 'key' in cob:
            if key is None:
                key = cob['key']
            else:
                assert key == cob['key']

        self.sn = sn
        self.cob = cob
        self.key = key
        
        assert self.cob is not None
        assert self.cob['sn'] == sn
        if self.cob['class'] != self.__class__.__name__:
            raise Exception(f"{self.__class__.__name__} sn={sn}: cob['class'] = {self.cob['class']}")
        assert sn not in self.CobIndex

        self.CobIndex[sn] = self
        nx = self.CobInfo['next_sn']
        sn = int(sn)
        if sn >= nx:
            self.CobInfo['next_sn'] = sn + 1

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self.key}>'


class View:

    Page = None

    def __init__ (self):
        self.view_of = None

    def current_view (self):
        return self

    def context_ancestors (self):
        yield self
        yield from self.view_of.ancestors()

    def __repr__ (self):
        if isinstance(self, Cob):
            return Cob.__repr__(self)
        else:
            return f'<{self.__class__.__name__} view of {repr(self.view_of)}>'


class Selection:

    def __init__ (self, options):
        self.selected = None
        self.options = options

    def __repr__ (self):
        return f'<Selection {self.selected} {self.options}>'


class Selector:

    Choices = None

    def __init__ (self):
        self.state = {chc: Selection(getattr(self, att)) for (chc,att) in self.Choices}


class Viewable (Selector):

    def __init__ (self, views):
        if self.Choices is None or not any(c=='view' for (c,_) in self.Choices):
            raise Exception(f"Viewable {self} does not have 'view' as a choice")
        self.views = views
        for view in self.views:
            if not isinstance(view, View):
                raise Exception(f'Not a view: {view}')
            if view.view_of is not None:
                raise Exception('Attempt to re-use a View')
            view.view_of = self
        Selector.__init__(self)
        selection = self.state['view']
        selection.selected = self.views[0]

    def current_view (self):
        return self.state['view'].selected


#-------------------------------------------------------------------------------

# View must come first - it overrides Node.current_view

class Props (View, Node):

    def __init__ (self, parent, keys=None, props=None):
        if props is None:
            props = parent.cob
        if keys is None:
            keys = list(props)

        Node.__init__(self, parent)
        View.__init__(self)
        self.keys = keys
        self.props = props

    def __len__ (self): return len(self.keys)
    def __iter__ (self): return iter(self.keys)
    def __getitem__ (self, key): return self.props[key]
    def keys (self): return self.keys
    def values (self): return (v for (k,v) in self.props.items() if k in self.keys)
    def items (self): return ((k,v) for (k,v) in self.props.items() if k in self.keys)


class List (Node):

    ChildType = None

    def __init__ (self, parent, key=None):
        assert isinstance(parent, Cob)
        assert self.ChildType is not None
        assert issubclass(self.ChildType, Cob)
        if key is None:
            key = self.__class__.__name__.lower()
        Node.__init__(self, parent)
        if key in parent.cob:
            sns = parent.cob[key].split()
        else:
            sns = []
        self.contents = [self.ChildType(self, sn) for sn in sns]

    def __len__ (self): return len(self.contents)
    def __iter__ (self): return iter(self.contents)
    def __getitem__ (self, i): return self.contents[i]

    def __repr__ (self):
        if isinstance(self, Cob):
            return Cob.__repr__(self)
        else:
            return f'<{self.__class__.__name__} of {repr(self.parent)}>'


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

class Corpus (Viewable, Cob):

    Choice = 'corp'
    Choices = [('view', 'views'), ('lang', 'langs'), ('rom', 'roms')]

    def __init__ (self, fn, key=None, **kwargs):
        fn = Path(fn)
        file = File(fn, **kwargs)
        if key is None: key = fn.stem
        Cob.__init__(self, None, '0', key=key, file=file)
        self.props = Props(self, {'filename': str(file.filename)})
        self.langs = Langs(self)
        self.roms = Roms(self)
        Viewable.__init__(self, [self.props, self.roms])

    def filename (self):
        return self.file.filename

    def corpus (self):
        return self

    

    def views (self):
        return [Props(self), Roms(self)]

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


class Language (Viewable, Cob):

    Choice = 'lang'
    Choices = [('view', 'views'), ('text', 'texts')]

    def __init__ (self, parent, key):
        Cob.__init__(self, parent, key)
        self.props = Props(self, ['name', 'glot', 'iso3', 'rom'])
        self.texts = Texts(self)
        self.toc = Toc(self)
        Viewable.__init__(self, [self.props, self.toc])

    def language (self):
        return self

    def lexicon (self):
        return Lexicon(self)

    def toc (self):
        return Toc(self)


class Langs (List):

    ChildType = Language


class Rom (Cob):

    pass


class Roms (View, List):

    ChildType = Rom

    def __init__ (self, parent):
        List.__init__(self, parent)
        View.__init__(self)


class Text (Viewable, Cob):

    Choice = 'text'
    Choices = [('view', 'views'), ('sent', 'sents')]

    def __init__ (self, parent, sn):
        Cob.__init__(self, parent, sn)
        self.sents = Sents(self)
        Viewable.__init__(self, [self.sents])

    def key (self):
        return self.cob['key']

    def text (self):
        return self

    def title (self):
        return self.cob.get('ti', '(untitled)')


class Texts (List):

    ChildType = Text


class Lexicon (Cob):

    pass


class Trans (Node):

    pass


class Sentence (Viewable, Cob):

    Choice = 'sent'
    Choices = [('view', 'views')]

    def __init__ (self, parent, key):
        Cob.__init__(self, parent, key)
        self.tokens = Tokens(self)
        Viewable.__init__(self, [self.tokens])

    def sentence (self):
        return self

    def times (self):
        return Times(self)

    def string (self):
        return self.cob['w']

    def set_string (self, s):
        self.cob['w'] = s
        self.tokens.rebuild()

    def __len__ (self): return len(self.tokens)
    def __iter__ (self): iter(self.tokens)
    def __getitem__ (self, i): return self.tokens[i]


class Tokens (View, Node):

    Choice = 'view'

    def __init__ (self, parent):
        assert isinstance(parent, Sentence)
        Node.__init__(self, parent)
        View.__init__(self)
        self.rebuild()

    def rebuild (self):
        self.tokens = [Token(self, i, s) for (i, s) in enumerate(self.parent.cob['w'].split())]

    def __len__ (self): return len(self.tokens)
    def __iter__ (self): return iter(self.tokens)
    def __getitem__ (self, i): return self.tokens[i]


class Sents (View, List):

    ChildType = Sentence

    def __init__ (self, parent):
        List.__init__(self, parent)
        View.__init__(self)


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
#
#  If a 'ch' value gets changed, be sure to clear the Toc
#

class Toc (View, Node):

    def __init__ (self, lang):
        Node.__init__(self, lang, 'toc')
        View.__init__(self)
        self._parents = None
        self._roots = None

    def clear (self):
        self._parents = None
        self._roots = None
        
    def _compute_parents (self):
        texts = self.parent.texts
        parent_table = {}
        for parent in texts:
            if 'ch' in parent.cob:
                for ck in parent.cob['ch'].split():
                    # silently overwrites any older value
                    parent_table[ck] = parent
        return parent_table

    def roots (self):
        if self._roots is None:
            self._compute_parents()
        return self._roots

    def parent (self, text):
        if self._parents is None:
            self._compute_parents()
        return self._parents.get(text.key())
