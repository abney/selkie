
from pathlib import Path
from ..pyx import File, DCTFormat, Pathname, __formats__

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

class CLDFile (File):

    def __init__ (self, loc, name=None):
        File.__init__(self, loc, CLDFORMAT)
        if not self.contents:
            if name is None:
                name = str(self.name())
            self.contents['corp.' + name] = {}


def open_corpus (fn, name=None):
    return Registry().open(fn, name=name)


#--  Node  ---------------------------------------------------------------------

class Node:

    Page = None

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
        
    def get_displayable (self):
        return self
        

#     def view_name (self):
#         return self.__class__.__name__.lower()


#--  Item  ---------------------------------------------------------------------

class Item (Node):

    TypeString = None

    def __init__ (self, parent, name=None, record=None):
        assert self.TypeString is not None, f'Subclasses of Item must provide TypeString'

        # The discriminator. If this is an element of a list, the name is the key.
        self.name = name

        element_of = None
        if isinstance(parent, List):
            element_of = parent
            parent = element_of.parent
            assert parent is not None
            assert self.__class__ is element_of.ElementClass
            assert record is not None

        Node.__init__(self, parent)
        self.element_of = element_of
        self.views = None
        self.current_view = None
        self.state = {}
        self.itemid = self._compute_itemid()
        self.record = record

    def _compute_itemid (self):
        words = []
        if self.parent is not None:
            pfx = self.parent.child_itemid_prefix()
            if pfx:
                words.append(pfx)
        if self.name:
            words.append(self.name)
        return '.'.join(words)

    def child_itemid_prefix (self):
        return self.itemid

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
            view.set_view_of(self)
            self.views.append(view)
        if self.current_view is None:
            self.current_view = self.views[0]

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

    def save (self):
        self.corpus().save()

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

    def __init__ (self, eltclass, parent):
        assert isinstance(parent, Item)
        assert parent.record is not None

        Node.__init__(self, parent)
        self.ElementClass = eltclass
        self.elements = []
        self._index = {}
        self.selected = None

        # Populate it from the parent's record
        
        prefix = self.ElementClass.TypeString + '.'
        for (key, value) in parent.record.items():
            if key.startswith(prefix):
                self.add_element_from_record(key[len(prefix):], value)

    def new (self, name=None, constructor=None):
        if name is None:
            name = str(len(self.elements) + 1)
        return self.add_record(name, {}, constructor)

    def add_record (self, name, record, constructor=None):
        key = self.ElementClass.TypeString + '.' + name
        if key in self.parent.record:
            raise Exception('Name already in use')
        self.parent.record[key] = record
        return self.add_element_from_record(name, record, constructor)

    def add_element_from_record (self, name, record, constructor=None):
        if constructor is None:
            constructor = self.ElementClass
        elt = constructor(self, name, record)
        self.elements.append(elt)
        self.index_element(elt)
        return elt

    def index_element (self, elt):
        assert elt.name is not None
        assert elt.name not in self._index
        self._index[elt.name] = elt

    def __repr__ (self):
        return f'<{self.__class__.__name__} of {self.ElementClass.__name__}>'

    def __len__ (self): return len(self.elements)
    def __iter__ (self): return iter(self.elements)

    def __getitem__ (self, i):
        if isinstance(i, str):
            return self._index[i]
        else:
            return self.elements[i]

    def __contains__ (self, i):
        return i in self._index

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
    
    def __init__ (self, parent, displayable=None, view_type=None):
        if displayable is None:
            displayable = self
        if view_type is None:
            view_type = displayable.__class__.__name__.lower()
        Node.__init__(self, parent)
        self.view_of = None
        self.displayable = displayable
        self.view_type = view_type

    def set_view_of (self, item):
        if self.view_of is not None:
            raise Exception(f'Attempt to re-use a View: {repr(view)} -> {repr(view.view_of)}')
        self.view_of = item

    def get_displayable (self):
        return Node.get_displayable(self.displayable)

    def select (self):
        item = self.view_of
        assert item is not None
        item.current_view = self
        item.select()

    def __repr__ (self):
        s = '--' if self.view_of is None else repr(self.view_of)
        return f'<{self.__class__.__name__} {s}>'


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
        Item.__init__(self, None, None, None)
        # Corpora(self) relies on self.record existing
        self.record = {}
        self.corpora = List(Corpus, self)
        self.n_untitled = 0
        self.add_children(self.corpora)
        self.add_views(View(self, displayable=self))

    def __iter__ (self): return iter(self.corpora)
    def __len__ (self): return len(self.corpora)
    def __getitem__ (self, i): return self.corpora[i]
    def get (self, name): return self.corpora.get(name)

    def _compute_itemid (self):
        return None

    def open (self, loc, name=None):
        fi = CLDFile(loc, name=name)
        constructor = lambda parent, name, record: Corpus(parent, fi, name, record)
        assert len(fi.contents) == 1
        (key, record) = next(iter(fi.contents.items()))
        if name is None:
            assert key.startswith('corp.')
            name = key[5:]
        corpus = self.corpora.add_record(name, record, constructor)
        return corpus

    def new (self):
        self.n_untitled += 1
        return self.open(f'untitled-{self.n_untitled}')


class Corpus (Item):

    TypeString = 'corp'

    def __init__ (self, registry, cldfile, name, record):
        Item.__init__(self, registry, name, record)

        self.file = cldfile
        self.props = Props(self, {'filename': self.filename()})
        self.langs = List(Language, self)
        self.roms = List(Rom, self)

        self.add_children(self.langs)
        self.add_children(self.roms)
        self.add_views(self.props, View(self, displayable=self.roms))

    def filename (self):
        # str() because it may be a Pathname
        return str(self.file.name())

    def child_itemid_prefix (self):
        return None

    def export_cld (self):
        return self.file.export(CLDFORMAT)

    def export_json (self):
        return self.file.export('json')

    def save (self, fn=None):
        self.file.save(fn=fn)

    def rename (self, filename):
        self.file.rename(filename)
        self.props['filename'] = str(self.file.name())

    def corpus (self):
        return self

    def __str__ (self):
        return str(self.file)

    def __repr__ (self):
        return f'<Corpus {self.name}>'


#--  Corpus  -------------------------------------------------------------------

class Language (Item):

    TypeString = 'lang'

    def __init__ (self, parent, name, record):
        Item.__init__(self, parent, name, record)
        self.props = Props(self, ['name', 'glot', 'iso3', 'rom'])
        self.texts = List(Text, self)
        self.toc = Toc(self)
        self.lexicon = Lexicon(self)

        self.add_children(self.texts)
        self.add_views(self.props, self.toc)

    def language (self):
        return self


class Roms (View):
    pass


class Rom (Node):

    TypeString = 'rom'

    def __init__ (self, parent, **kwargs):
        Node.__init__(self, parent, state=True, **kwargs)


class Text (Item):

    TypeString = 'text'

    def __init__ (self, parent, name, record):
        Item.__init__(self, parent, name, record)
        self.props = Props(self, ['au', 'ti', 'ty', 'ch'])
        self.sents = List(Sentence, self)

        self.add_children(self.sents)
        self.add_views(self.props, Plaintext(self))

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

    def __init__ (self, parent, name, record):
        Item.__init__(self, parent, name, record)
        self.tokens = Tokens(self)
        self.times = Times(self)
        self.add_views(self.tokens)

    def sentence (self):
        return self

    def string (self):
        return self.record.get('w', '')

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
        self._tokens = [Token(self, i, s) for (i, s) in enumerate(self.parent.record.get('w','').split())]

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
        # _parents maps child name -> parent item
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
                    for child_name in parent_text.record['ch'].split():
                        # silently overwrites any older value
                        parent_table[child_name] = parent_text
        return self._parents

    def parent (self, text):
        return self._need_parents().get(text.name)

    def roots (self):
        if self._roots is None:
            parent_table = self._need_parents()
            lang = self.parent
            assert isinstance(lang, Language)
            # print('parent_table=', parent_table)
            self._roots = [text for text in lang.texts if not parent_table.get(text.name)]
        return self._roots


class Plaintext (View):

    def __init__ (self, text):
        View.__init__(self, text)
        self.sents = text.sents


#--  CLD file format  ----------------------------------------------------------

__formats__[CLDFORMAT] = DCTFormat(
    CLDFORMAT,
    root={'corp'},
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
