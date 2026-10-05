
from pathlib import Path
from ..pyx.dct import File, DCTFormat

CLDFORMAT = 'cld29'

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


#--  Toplevel  -----------------------------------------------------------------

def open_cld_file (fn):
    fn = Path(fn)
    fi = File(fn, format=CLDFORMAT)
    if not fi.contents:
        name = fn.name
        fi.contents['corp.' + name] = {}
    return fi

def open_corpus (fn):
    return Registry().open(fn)


#--  Node  ---------------------------------------------------------------------

class Node:

    def __init__ (self, parent):
        self.parent = parent

    def root (self):
        if self.parent is None:
            return self
        else:
            return self.parent.root()

    def corpus (self):
        return self.parent.corpus()

    def language (self):
        return self.parent.language()

    def text (self):
        return self.parent.text()

    def sentence (self):
        return self.parent.sentence()

#     def print_selectable (self):
#         print('Selectable:', repr(self))
#         view = self.current_view
#         print('  current_view:', repr(view))
#         node = view.view_of
#         print('    view_of:', repr(node), repr(node.display_string()))
#         print('      views:')
#         if node.views:
#             for v in node.views:
#                 print('       ', repr(v), repr(v.view_name()), v is view)

    def choices (self):
        state = self.root().state
        return self._state_choices(state)

    def _state_choices (self, state):
        for lst in state.values():
            yield lst
            if lst.selected is not None and lst.selected.state:
                yield from self._state_choices(lst.selected.state)

    def print_state (self):
        state = self.root().state
        self._print_state_1(state, '')
        
    def _print_state_1 (self, state, indent):
        indent1 = indent + ' '
        indent4 = indent + '    '
        for (typ, lst) in state.items():
            print(f'{indent}{typ}:')
            for elt in lst:
                print(f'{indent1}', repr(elt), '== selected' if elt is lst.selected else '')
                if elt is lst.selected:
                    self._print_state_1(elt.state, indent4)
        
#     def view_name (self):
#         return self.__class__.__name__.lower()


#--  Item  ---------------------------------------------------------------------

class Item (Node):

    TypeString = None

    def __init__ (self, parent, name=None):
        assert self.TypeString is not None, f'Subclasses of Item must provide TypeString'

        # The discriminator. lst.index_element() relies on this
        self.name = name

        lst = None
        if isinstance(parent, List):
            lst = parent
            assert lst.parent is not None
            assert self.__class__ is lst.ElementClass
            parent = lst.parent
            lst.index_element(self)

        Node.__init__(self, parent)
        self.element_of = lst
        self.views = None
        self.current_view = None
        self.state = {}
        self.itemid = self._compute_itemid()
        self.record = self._find_record()

    def _compute_itemid (self):
        words = []
        if self.parent is not None and self.parent.itemid is not None:
            words.append(self.parent.itemid)
        if self.name:
            words.append(self.name)
        return '.'.join(words)

    def _find_record (self):
        if self.parent is None:
            return None
        else:
            key = self.TypeString
            if self.name:
                key = key + '.' + self.name
            return self.parent.record[key]

    def display_string (self):
        if self.itemid:
            return self.TypeString + ' ' + self.itemid
        else:
            return self.TypeString

    def add_children (self, children):
        assert isinstance(children, List)
        assert children.parent is self
        if children.ElementClass.TypeString is None:
            raise Exception(f'add_children: no children.ElementClass.TypeString: {repr(children)}')
        self.state[children.ElementClass.TypeString] = children
        #options.set_state_parent(self)

    def add_views (self, *views):
        if self.views is None:
            self.views = []
        for view in views:
            if not isinstance(view, View):
                raise Exception(f'Not a View: {repr(view)}')
            if view.Page is None:
                raise Exception(f'Cannot add an unviewable node as view: {repr(view)}')
            if view.view_of is not None:
                raise Exception(f'Attempt to re-use a View: {repr(view)} -> {repr(view.view_of)}')
            self.views.append(view)
            view.view_of = self
        if self.current_view is self:
            assert self.view_of is self
            self.current_view = self.views[0]
            self.view_of = None

    def select (self):
        if self.current_view is None:
            if self.views is None:
                raise Exception('Not selectable')
            self.current_view = self.views[0]
        view = self.current_view
        assert view.view_of is self
        node = self
        while node is not None and node.element_of is not None:
            lst = node.element_of
            lst.selected = node
            node = lst.parent

    def __repr__ (self):
        if self.itemid:
            s = ' ' + self.itemid
        else:
            s = ''
        return f'<{self.__class__.__name__}{s}>'


#--  List  ---------------------------------------------------------------------

class List (Node):
    '''
    A List represents a space-separated list of sns that appears as
    a value in a record. The key is the List's class name.
    '''

    ElementClass = None

    def __init__ (self, parent):
        assert self.ElementClass is not None
        assert isinstance(parent, Item)
        assert parent.record is not None
        
        Node.__init__(self, parent)

#         parent = self.parent
#         key = self.__class__.__name__.lower()
#         if key in parent.record:
#             discrims = parent.record[key].split()
#             elements = [self.ElementClass(self, sn) for sn in sns]
#             else:
#                 elements = []

        self.elements = []
        self._index = {}
        self.selected = None

        # Populate it from the parent's record
        
        prefix = self.ElementClass.TypeString + '.'
        for (key, value) in parent.record.items():
            if key.startswith(prefix):
                name = key[len(prefix):]
                self.ElementClass(self, name)

    def __repr__ (self):
        return f'<List of {self.ElementClass.__name__}>'

    def index_element (self, elt):
        self.elements.append(elt)
        assert elt.name is not None
        assert elt.name not in self._index
        self._index[elt.name] = elt

    def __len__ (self): return len(self.elements)
    def __iter__ (self): return iter(self.elements)

    def __getitem__ (self, i):
        if isinstance(i, str):
            return self._index[i]
        else:
            return self.elements[i]

    def get (self, name):
        return self._index.get(name)

#     def set_state_parent (self, state_parent):
#         choice = self.ElementClass.TypeString
#         assert choice is not None
#         assert state_parent is not None
#         if self.state_parent is None:
#             self.state_parent = state_parent
#             for elt in self.elements:
#                 assert elt.__class__ is self.ElementClass
#                 assert elt.state_parent is None
#                 elt.state_parent = state_parent


#--  View  ---------------------------------------------------------------------

class View (Node):
    
    Page = True

    def __init__ (self, parent):
        Node.__init__(self, parent)
        self.view_of = None

    def select (self):
        item = self.view_of
        assert item is not None
        item.current_view = self
        item.select()

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self.view_of.itemid}>'


#-------------------------------------------------------------------------------

class Props (View):

    def __init__ (self, parent, arg=None):
        View.__init__(self, parent)
        if isinstance(arg, list):
            keys = arg
            props = parent.record
        elif isinstance(arg, dict):
            props = arg
            keys = list(props)
        else:
            props = parent.record
            keys = list(props)

        Node.__init__(self, parent)
        self._keys = keys
        self._props = props

    def __len__ (self): return len(self._keys)
    def __iter__ (self): return iter(self._keys)
    def __getitem__ (self, key): return self._props[key]
    def keys (self): return self._keys
    def values (self): return (v for (k,v) in self._props.items() if k in self._keys)
    def items (self): return ((k,v) for (k,v) in self._props.items() if k in self._keys)


#--  Corpora, Corpus  ----------------------------------------------------------
#
#  View must be first - if there is no view_of, Viewable init will signal an error
#

class Registry (Item):

    TypeString = 'registry'

    def __init__ (self):
        Item.__init__(self, None)
        # Corpora(self) relies on self.record existing
        self.record = {}
        self.corpora = Corpora(self)
        self.n_untitled = 0
        self.add_children(self.corpora)

    def __iter__ (self): return iter(self.corpora)
    def __len__ (self): return len(self.corpora)
    def __getitem__ (self, i): return self.corpora[i]
    def get (self, name): return self.corpora.get(name)

    def _compute_itemid (self):
        return None

    def open (self, fn):
        fi = open_cld_file(Path(fn))
        for (key, value) in fi.contents.items():
            self.record[key] = value
            (_, discrim) = key.split('.')
            corpus = Corpus(self.corpora, fi, discrim)
        return corpus

    def new (self):
        self.n_untitled += 1
        return self.open(f'untitled-{self.n_untitled}')


class Corpus (Item):

    TypeString = 'corp'

    def __init__ (self, registry, fi, name):
        Item.__init__(self, registry, name)

        self.file = fi
        self.props = Props(self, {'filename': str(fi.filename)})
        self.langs = Langs(self)
        self.roms = Roms(self)

        self.add_children(self.langs)
        self.add_children(self.roms)
        self.add_views(self.props, View(self.roms))

    def _compute_itemid (self):
        return None

    def export_cld (self):
        return self.file.export(CLDFORMAT)

    def export_json (self):
        return self.file.export('json')

    def save (self, fn=None):
        self.file.save(fn=fn)

    def rename (self, filename):
        self.file.rename(filename)
        self.props['filename'] = str(self.file.filename)

    def corpus (self):
        return self

    def __str__ (self):
        return str(self.file)

    def __repr__ (self):
        return f'<Corpus {self.name}>'


#--  Corpus  -------------------------------------------------------------------

class Language (Item):

    TypeString = 'lang'

    def __init__ (self, parent, name):
        Item.__init__(self, parent, name)
        self.props = Props(self, ['name', 'glot', 'iso3', 'rom'])
        self.texts = Texts(self)
        self.toc = Toc(self)
        self.lexicon = Lexicon(self)

        self.add_children(self.texts)
        self.add_views(self.props, self.toc)

    def language (self):
        return self


class Rom (Node):

    TypeString = 'rom'

    def __init__ (self, parent, **kwargs):
        Node.__init__(self, parent, state=True, **kwargs)


class Text (Item):

    TypeString = 'text'

    def __init__ (self, parent, name):
        Item.__init__(self, parent, name)
        self.props = Props(self, ['au', 'ti', 'ty', 'ch'])
        self.sents = Sents(self)

        self.add_children(self.sents)
        self.add_views(self.props, View(self.sents))

    def text (self):
        return self

    def title (self):
        return self.record.get('ti', '(untitled)')

    def children (self):
        ch = self.record.get('ch')
        if ch:
            texts = self.language().texts
            return [texts[name] for name in ch.split() if name in texts]


class Lexicon (Item):

    TypeString = 'lexicon'


class Trans (Node):

    pass


class Sentence (Item):

    TypeString = 'sent'

    def __init__ (self, parent, sn):
        Item.__init__(self, parent, sn)
        self.tokens = Tokens(self)
        self.times = Times(self)
        self.add_views(self.tokens)

    def sentence (self):
        return self

    def string (self):
        return self.record['w']

    def set_string (self, s):
        self.record['w'] = s
        self.tokens.rebuild()

    def __len__ (self): return len(self.tokens)
    def __iter__ (self): iter(self.tokens)
    def __getitem__ (self, i): return self.tokens[i]


class Tokens (View):

    def __init__ (self, parent):
        assert isinstance(parent, Sentence)
        View.__init__(self, parent)
        self.rebuild()

    def rebuild (self):
        self._tokens = [Token(self, i, s) for (i, s) in enumerate(self.parent.record['w'].split())]

    def __len__ (self): return len(self._tokens)
    def __iter__ (self): return iter(self._tokens)
    def __getitem__ (self, i): return self._tokens[i]


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

class Toc (View):

    def __init__ (self, lang):
        View.__init__(self, lang)
        # _parents maps sn -> node
        self._parents = None
        self._roots = None

    def clear (self):
        self._parents = None
        self._roots = None
        
    def _need_parents (self):
        if self._parents is None:
            lang = self.parent
            assert isinstance(lang, Language)
            self._parents = parent_table = {}
            for parent_text in lang.texts:
                if 'ch' in parent_text.record:
                    for child_nid in parent_text.record['ch'].split():
                        # silently overwrites any older value
                        parent_table[child_nid] = parent_text
        return self._parents

    def parent (self, text):
        return self._need_parents().get(text.sn)

    def roots (self):
        if self._roots is None:
            parent_table = self._need_parents()
            lang = self.parent
            assert isinstance(lang, Language)
            print('parent_table=', parent_table)
            self._roots = [text for text in lang.texts if not parent_table.get(text.nid)]
        return self._roots


#--  Lists  --------------------------------------------------------------------

class Corpora (List):
    ElementClass = Corpus

class Langs (List):
    ElementClass = Language

class Roms (List):
    ElementClass = Rom

class Texts (List):
    ElementClass = Text

class Sents (List):
    ElementClass = Sentence


#--  CLD file format  ----------------------------------------------------------

File.__formats__[CLDFORMAT] = DCTFormat(
    CLDFORMAT,
    {'corp'},
    corp={'lang', 'rom'},
    lang={'name', 'glot', 'iso3', 'rom', 'text', 'lexicon', 'trans'},
    text={'ty', 'ti', 'au', 'de', 'ch', 'pdf', 'audio', 'video', 'xid', 'sent'},
    lexicon={'form'},
    sent={'w', 'tr', 'times'},
    form={'ty', 'g', 'c', 'pp', 'cf', 'of'},
    rom={'u'},
    trans={'xlexicon', 'xtext'},
    xlexicon={'xform'},
    xtext={'xsent'},
    times={'t'}
)
