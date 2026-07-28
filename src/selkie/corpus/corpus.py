
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
    '''
    The "state graph" consists of nodes that either have Choices (state parents)
    or provide a Choice (state children). A nonterminal's children are the
    options in the Selections of its state; each is associated with a choice.
    The child's Choice must match the Selection's choice. The state parent is
    recorded as the child's state_parent. Children are added using
    add_selectables(choice, options).

    A node is "viewable" just in case it has a Page. It must either be a
    state-graph node, or declared to be a view of a given state-graph node,
    using add_view(view). A viewable state-graph node is not permitted to have
    views.

    A node is "selectable" just in case it is a viewable state-graph node or
    a view.
    '''

    IsCob = False
    Choice = None
    Choices = None
    Page = None

    def __init__ (self, parent, arg=None):
        assert arg is None or isinstance(arg, str)
        self.views = None
        self.current_view = self
        self.view_of = self
        self.state_parent = None
        self.state = None

        self._init_parent(parent)
        if self.IsCob:
            self._init_cob(arg)
        else:
            self.nid = arg

    def _init_parent (self, parent):
        if parent is None:
            corpus = None
        else:
            corpus = parent.corpus
            if corpus is None:
                raise Exception('No corpus')

        self.parent = parent
        self.corpus = corpus

    def _init_cob (self, sn):
        parent = self.parent
        if sn is None:
            if parent is None:
                raise Exception('No parent')
            k = self.__class__.__name__.lower()
            assert k in parent.cob
            sn = parent.cob[k]
        else:
            assert isinstance(sn, str) and sn.isdigit()
                
        cob = self.corpus.require_cob(sn)
        assert cob['sn'] == sn
        cn = self.__class__.__name__
        if cob['class'] != cn:
            raise Exception(f"{cn} sn={sn}: cob['class'] = {cob['class']}")
        
        if 'key' in cob:
            nid = cob['key']
        elif parent is None:
            nid = None
        else:
            nid = parent.nid

        self.sn = sn
        self.cob = cob
        self.nid = nid

        self.corpus.index_cob(self)

    def add_choice (self, options):
        assert isinstance(options, List)
        if options.ElementType.Choice is None:
            raise Exception(f'add_choice: no options.ElementType.Choice: {repr(options)}')
        if self.state is None:
            self.state = {}
        self.state[options.ElementType.Choice] = options
        options.set_state_parent(self)

    def add_views (self, *views):
        if self.views is None:
            self.views = []
        for view in views:
            if view is self:
                raise Exception(f'Cannot be your own view: {repr(view)}')
            if view.Page is None:
                raise Exception(f'Cannot add an unviewable node as view: {repr(view)}')
            if view.current_view is not view:
                raise Exception(f'View cannot have a view: {repr(view)} -> {repr(view.current_view)}')
            if view.view_of is not view and view.view_of is not None:
                raise Exception(f'Attempt to re-use a View: {repr(view)} -> {repr(view.view_of)}')
            self.views.append(view)
            view.view_of = self
            view.current_view = None
            if self.current_view is self:
                self.current_view = view
                assert self.view_of is self
                self.view_of = None

    def ancestors (self):
        yield self
        if self.parent:
            yield from self.parent.ancestors()

    def language (self):
        return self.parent.language()

    def text (self):
        return self.parent.text()

    def sentence (self):
        return self.parent.sentence()

    def select (self):
        view = self.current_view
        assert view is not None
        node = view.view_of
        assert node is not None
        while node.state_parent is not None:
            if node.Choice is not None:
                node.state_parent.state[node.Choice].selected = node
            node = node.state_parent

    def print_selectable (self):
        print('Selectable:', repr(self))
        view = self.current_view
        print('  current_view:', repr(view))
        print('    view_of:', repr(view.view_of))

    def current (self):
        state = self.corpus.state_graph_root.state
        return self._state_options(state)

    def _state_options (self, state):
        for options in state.values():
            yield options
            if options.selected is not None and options.selected.state:
                yield from self._state_options(options.selected.state)

    def print_state (self):
        state = self.corpus.state_graph_root.state
        self._print_state_1(state, '')
        
    def _print_state_1 (self, state, indent):
        indent2 = indent + '  '
        indent4 = indent + '    '
        for (choice, options) in state.items():
            print(f'{indent}{choice}:')
            print(f'{indent2}selected:', options.selected)
            for opt in options:
                print(f'{indent2}option:', repr(opt), '<==' if opt is options.selected else '')
                if opt.state:
                    self._print_state_1(opt.state, indent4)

    def display_string (self):
        s = ' ' + self.nid if self.nid else ''
        return f'{self.__class__.__name__}{s}'
        
    def view_name (self):
        return self.__class__.__name__.lower()

    def __repr__ (self):
        return '<' + self.display_string + '>'

# class Cob (Node):
# 
#     def __init__ (self, parent, sn=None, key=None):
#         Node.__init__(self, parent)
#         parent = self.parent # Node.__init__ may change it
# 
#         if sn is None:
#             if parent is None:
#                 raise Exception('No parent')
#             k = self.__class__.__name__.lower()
#             assert k in parent.cob
#             sn = parent.cob[k]
#         else:
#             assert isinstance(sn, str) and sn.isdigit()
#                 
#         cob = self.corpus.require_cob(sn)
#         if 'key' in cob:
#             if key is None:
#                 key = cob['key']
#             else:
#                 assert key == cob['key']
#         assert cob['sn'] == sn
#         cn = self.__class__.__name__
#         if cob['class'] != cn:
#             raise Exception(f"{cn} sn={sn}: cob['class'] = {cob['class']}")
# 
#         self.sn = sn
#         self.cob = cob
#         self.key = key
#         self.nid = key
# 
#         self.corpus.index_cob(self)


# #--  Selectables  --------------------------------------------------------------
# 
# class Selection:
# 
#     def __init__ (self, options):
#         '''Options must be iterable'''
#         self.selected = None
#         self.options = options
# 
#     def __repr__ (self):
#         return f'<Selection {self.selected} {list(self.options)}>'


class List (Node):
    '''
    A List represents a space-separated list of sns that appears as
    a value in a cob. The key is the List's class name.
    '''

    ElementType = None

    def __init__ (self, parent, elements=None):
        assert not self.IsCob
        assert self.ElementType is not None
        Node.__init__(self, parent)

        if elements is None:
            parent = self.parent
            assert parent.IsCob
            key = self.__class__.__name__.lower()
            if key in parent.cob:
                sns = parent.cob[key].split()
                elements = [self.ElementType(self, sn) for sn in sns]
            else:
                elements = []

        self.elements = elements
        self.selected = None

    def __len__ (self): return len(self.elements)
    def __iter__ (self): return iter(self.elements)
    def __getitem__ (self, i): return self.elements[i]

    def set_state_parent (self, state_parent):
        choice = self.ElementType.Choice
        assert choice is not None
        assert state_parent is not None
        if self.state_parent is None:
            self.state_parent = state_parent
            for elt in self.elements:
                assert elt.__class__ is self.ElementType
                assert elt.state_parent is None
                elt.state_parent = state_parent

    def append (self, elt):
        assert elt.__class__ is self.ElementType
        assert elt.state_parent is None
        assert self.state_parent is not None
        self.elements.append(elt)
        elt.state_parent = self.state_parent


#--  Corpora, Corpus  ----------------------------------------------------------
#
#  View must be first - if there is no view_of, Viewable init will signal an error
#

class Registry (Node):
    '''
    Behaves like a list. The method get() permits access by corpus key. It
    searches through the list and returns the first corpus with the given key.
    Not all corpora have keys, and there is no guarantee that a key identifies
    a unique corpus.
    '''

    def __init__ (self):
        Node.__init__(self, None)
        self.corpus = self
        self.state_graph_root = self
        self.corpora = Corpora(self, elements=[])
        self.n_untitled = 0
        self.add_choice(self.corpora)
        
    # the topmost genuine node is the corpus
    def ancestors (self): return []

    def __iter__ (self): return iter(self.corpora)
    def __bool__ (self): return bool(self.corpora)
    def __len__ (self): return len(self.corpora)
    def __getitem__ (self, i): return self.corpora[i]

    def get (self, nid):
        for corpus in self.corpora:
            if corpus.nid == nid:
                return corpus

    def _add_corpus (self, corpus):
        corpus.parent = self
        corpus.state_graph_root = self
        corpus.idx = len(self.corpora)
        self.corpora.append(corpus)

    def open (self, fn, **kwargs):
        fn = Path(fn)
        nid = fn.stem
        corpus = self.get(nid)
        if corpus is not None:
            return corpus
        else:
            corpus = Corpus(fn, nid=nid, **kwargs)
            self._add_corpus(corpus)
            return corpus

    def new (self):
        self.n_untitled += 1
        corpus = Corpus(f'untitled-{self.n_untitled}', create=True)
        self._add_corpus(corpus)
        return corpus


class Corpus (Node):

    Choice = 'corp'

    def __init__ (self, fn, nid=None, contents=None, create=False):
        fn = Path(fn)
        file = File(fn, contents=contents, create=create)
        if nid is None: nid = fn.stem

        Node.__init__(self, None, nid)
        self.corpus = self
        self.file = file
        self.cob_index = {}
        self.next_sn = 0
        self.state_graph_root = self
        self.root = Root(self)
        self.props = Props(self, {'filename': str(self.corpus.filename())})
        self.langs = self.root.langs
        self.roms = self.root.roms

        self.add_choice(self.langs)
        self.add_choice(self.roms)
        self.add_views(self.props, self.roms)

    def filename (self):
        return self.file.filename

    def require_cob (self, sn):
        return self.file.deref(sn)

    def index_cob (self, cob):
        sn = cob.sn
        assert sn is not None
        assert sn not in self.cob_index
        self.cob_index[sn] = cob
        sni = int(sn)
        if sni >= self.next_sn:
            self.next_sn = sni + 1

    def __str__ (self):
        return str(self.file)


class Corpora (List):

    ElementType = Corpus


#-------------------------------------------------------------------------------

class Props (Node):

    Page = True

    def __init__ (self, parent, arg=None):
        if isinstance(arg, list):
            keys = arg
            props = parent.cob
        elif isinstance(arg, dict):
            props = arg
            keys = list(props)
        else:
            props = parent.cob
            keys = list(props)

        Node.__init__(self, parent)
        self.keys = keys
        self.props = props

    def __len__ (self): return len(self.keys)
    def __iter__ (self): return iter(self.keys)
    def __getitem__ (self, key): return self.props[key]
    def keys (self): return self.keys
    def values (self): return (v for (k,v) in self.props.items() if k in self.keys)
    def items (self): return ((k,v) for (k,v) in self.props.items() if k in self.keys)


#--  Corpus  -------------------------------------------------------------------

class Root (Node):

    IsCob = True

    def __init__ (self, parent):
        assert parent is not None
        Node.__init__(self, parent, '0')
        self.langs = Langs(self)
        self.roms = Roms(self)

    def filename (self):
        return self.corpus.filename()

    def views (self):
        return [Props(self), Roms(self)]

    def __str__ (self):
        return str(self.corpus.file)

    def export_cld (self):
        return self.corpus.file.export_cld()

    def export_json (self):
        return self.corpus.file.export_json()

    def save (self, fn=None):
        self.corpus.file.save(fn=fn)

    def rename (self, filename):
        self.corpus.file.filename = filename
        self.key = fn_to_key(filename)
        self.full_name = self.key


class Language (Node):

    IsCob = True
    Choice = 'lang'

    def __init__ (self, parent, sn):
        Node.__init__(self, parent, sn)
        self.props = Props(self, ['name', 'glot', 'iso3', 'rom'])
        self.texts = Texts(self)
        self.toc = Toc(self)

        self.add_choice(self.texts)
        self.add_views(self.props, self.toc)

    def language (self):
        return self

    def lexicon (self):
        return Lexicon(self)

    def toc (self):
        return Toc(self)


class Langs (List):

    ElementType = Language


class Rom (Node):

    Choice = 'rom'

    def __init__ (self, parent, **kwargs):
        Node.__init__(self, parent, state=True, **kwargs)


class Roms (List):

    Page = True
    ElementType = Rom


class Text (Node):

    IsCob = True
    Choice = 'text'

    def __init__ (self, parent, sn):
        Node.__init__(self, parent, sn)
        self.props = Props(self)
        self.sents = Sents(self)

        self.add_choice(self.sents)
        self.add_views(self.props, self.sents)

    def key (self):
        return self.cob['key']

    def text (self):
        return self

    def title (self):
        return self.cob.get('ti', '(untitled)')


class Texts (List):

    ElementType = Text


class Lexicon (Node):

    IsCob = True


class Trans (Node):

    pass


class Sentence (Node):

    IsCob = True
    Choice = 'sent'

    def __init__ (self, parent, sn):
        Node.__init__(self, parent, sn)
        self.tokens = Tokens(self)

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


class Tokens (Node):

    def __init__ (self, parent):
        assert isinstance(parent, Sentence)
        Node.__init__(self, parent)
        self.rebuild()

    def rebuild (self):
        self.tokens = [Token(self, i, s) for (i, s) in enumerate(self.parent.cob['w'].split())]

    def __len__ (self): return len(self.tokens)
    def __iter__ (self): return iter(self.tokens)
    def __getitem__ (self, i): return self.tokens[i]


class Sents (List):

    Page = True
    ElementType = Sentence


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

class Toc (Node):

    Page = True

    def __init__ (self, lang):
        Node.__init__(self, lang)
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
