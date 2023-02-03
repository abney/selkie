
import time, math, os, sys, pathlib
from os import listdir
from os.path import join, exists, expanduser
from io import StringIO
from .io import load_kvi, tabular, pprint
from .object import ListProxy, MapProxy, LazyList
from .newio import File, BaseFile, Nested, NestedDict, Dicts, lines_to_records, records_to_lines
from .com import Main
from .webserver import Backend
from .disk import VDisk
from .user import User
from .drill import Drill


#--  Corpus, Language  ---------------------------------------------------------

class Corpus (object):

    def __init__ (self, root=None, user=None):
        if user is None:
            user = User()
        if root is None:
            root = user.props['corpus']
        root = expanduser(root)

        self.disk = VDisk(root)
        self._directory = self.disk['/']
        self._user = user
        self._langs = None
        self._roms = None
        self._index = None
        # dict((lg.langid(), lg) for lg in self._langs)

        # for lang in self._langs:
        #     lang._corpus = self

    def __getattr__ (self, name):
        if name == 'langs':
            if self._langs is None:
                self._langs = LanguageTable(self)
            return self._langs
        elif name == 'user':
            return self._user

    def __getitem__ (self, name):
        return self.langs[name]

    def __iter__ (self):
        return iter(self.langs)

    def __len__ (self):
        return len(self.langs)

    def languages (self):
        '''Iterates over languages.'''
        return iter(self._langs)

    def __repr__ (self):
        return '<Corpus {}>'.format(self.disk.root)

    def language (self, name):
        '''
        Returns the language with the given langid, or None if it does
        not exist.
        '''
        return self._index.get(name)


class LanguageTable (MapProxy):

    def __init__ (self, corpus):
        self._corpus = corpus
        self._file = Dicts(corpus._directory['langs'])
        self._langs = {}

        for d in self._file:
            langid = d.get('id')
            if not langid:
                print('** Missing id in langs')
                continue
            self._langs[langid] = Language(self, langid, d)

    def __map__ (self):
        return self._langs

    def __str__ (self):
        return tabular(((langid, lg.name) for (langid, lg) in self.__map__.items()),
                       hlines=False)


class Language (MapProxy):

    def __init__ (self, tab, langid, props):
        self._corpus = tab._corpus
        self._langid = langid
        self._directory = None
        self._name = props.get('name', '')
        self._lexicon = None
        self._toc = None

        root = tab._corpus._directory
        if langid in root:
            self._directory = root[langid]

    def directory (self):
        return self._directory

    def __map__ (self):
        return self.toc
    
    def __getattr__ (self, name):

        if name == 'name':
            return self._name

        elif name == 'langid':
            return self._langid

        elif name == 'toc':
            if self._toc is None:
                self._toc = TextTable(self)
            return self._toc

        elif name == 'lexicon':
            if self._lexicon is None:
                self._lexicon = Lexicon(self)
            return self._lexicon

        else:
            raise AttributeError(f'No such attribute: {name}')

    def filename (self):
        return '/' + self._langid

    def print_tree (self):
        for root in self.get_roots():
            root.pprint_tree()

    def get_roots (self):
        return [item for item in self.toc.values() if item.is_root()]

    def get_documents (self):
        return [item for item in self.toc.values() if item.is_document()]

    def get_texts (self):
        return [item for item in self.toc.values() if item.is_text()]

    def get_vocabularies (self):
        return [item for item in self.toc.values() if item.is_vocabulary()]

    def get_running_texts (self):
        return [item for item in self.toc.values() if item.is_running_text()]

    def words (self):
        return LazyList(self._iter_words)

    def sents (self):
        return LazyList(self._iter_sents)
    
    def _iter_sents (self):
        for text in self.toc.values():
            if text.is_running_text():
                for sent in text:
                    yield sent

    def _iter_words (self):
        for sent in self._iter_sents():
            for word in sent:
                yield word

    def __str__ (self):
        return str(self.toc)

    def __repr__ (self):
        return f'<Language {self._langid} {self._name}'


class TextTable (MapProxy):

    def __init__ (self, lang):
        self._lang = lang
        self._file = Dicts(lang._directory['toc'])
        self._props = {}

        for d in self._file:
            txtid = d['id']
            meta = Metadata(lang, d)
            if 'ch' in d:
                text = Aggregate(meta)
            else:
                text = Text(meta)
            self._props[txtid] = text

        for text in self._props.values():
            text._set_children(self)
        
    def __map__ (self):
        return self._props

    def __str__ (self):
        if self._props:
            return tabular((tx.toc_entry() for tx in self.values()), hlines=False)
        else:
            return '(empty text table)'


def open_language (cname, lname):
    corpus = Corpus(cname + '.lgc')
    lang = corpus.language(lname)
    return lang
    

class Rom (object):

    def __init__ (self, id=None, fn=None):
        self._romid = id
        self._filename = fn


class CorpusFormat (object):

    def load (self, fn):
        pass

    def save (self, x, fn):
        pass



def load_corpus (fn):
    corpus = Corpus.from_json(load_kvi(fn))
    corpus._dirname = pathlib.Path(fn).parent
    return corpus


#--  Lexicon, Lexent, Loc  -----------------------------------------------------

class Lexent (MapProxy):

    def __init__ (self, lexicon, props):
        self._lexicon = lexicon
        self._gloss = None
        self._parts = None
        self._locs = None
        # automatically generated
        self._form = None
        self._sense = None
        self._variants = tuple()
        self._part_of = tuple()
        self._freq = None

        lexid = props.get('id')
        if lexid is None:
            raise Exception('No lexid provided')
        i = lexid.rfind('.')
        if i < 0:
            self._form = lexid
            self._sense = 0
        else:
            self._form = lexid[:i]
            self._sense = int(lexid[i+1:])

        self._gloss = props.get('g', '')

        if 'pp' in props:
            self._parts = tuple(props['pp'].split())
        else:
            self._parts = tuple()
        
    def __getattr__ (self, name):
        if name == 'lexid':
            return (self._form, self._sense)
        elif name in {'gloss', 'parts', 'locs', 'form', 'sense', 'variants', 'part_of', 'freq'}:
            return getattr(self, '_' + name)
        else:
            raise AttributeError(f'No such attribute: {name}')

    def __lt__ (self, other):
        return self.lexid < other.lexid

    def __eq__ (self, other):
        return self.lexid == other.lexid

    def __repr__ (self):
        return f'<Lexent {self.lexid}>'

    def __str__ (self):
        with StringIO() as f:
            print(self._form, self._sense, file=f)
            print('  gloss:    ', self._gloss or '', file=f)
            print('  parts:    ', self._parts, file=f)
            print('  part_of:  ', self._part_of, file=f)
            print('  variants: ', self._variants, file=f)
            print('  freq:     ', '' if self._freq is None else self._freq, file=f)
            #print('  locations:', self._locs, file=f)
            return f.getvalue()

    def all_locations (self):
        for loc in self._locations:
            yield loc
        for w in self._part_of:
            for loc in w.all_locations():
                yield loc


class Loc (object):

    @staticmethod
    def from_string (s):
        fields = s.split('.')
        if len(fields) == 2:
            return Loc(int(fields[0]), int(fields[1]))
        else:
            return Loc(int(fields[0]), int(fields[1]), int(fields[2]))

    def __init__ (self, t, s, w=None):
        self._t = t
        self._s = s
        self._w = w

    def t (self): return self._t
    def s (self): return self._s
    def w (self): return self._w

    def __iter__ (self):
        yield self._t
        yield self._s
        yield self._w

    def __str__ (self):
        s = str(self._t) + '.' + str(self._s)
        if self._w is not None:
            s += '.' + str(self._w)
        return s

    def __repr__ (self):
        return '<Loc {}.{}.{}>'.format(self._t, self._s, '' if self._w is None else self._w)


class Lexicon (MapProxy):

    def __init__ (self, lang):
        self._lang = lang
        self._file = Dicts(lang.directory()['/lexicon'])
        self._table = {}

        tab = self._table
        for props in self._file:
            lexent = Lexent(self, props)
            form = lexent.form
            i = lexent.sense
            if form in tab:
                lst = tab[form]
            else:
                lst = tab[form] = []
            while i >= len(lst):
                lst.append(None)
            lst[i] = lexent

    def __map__ (self):
        return self._table

    def __repr__ (self):
        return '<Lexicon {}>'.format(self._lang.langid)

    def intern (self, key):
        tab = self._entdict
        if key in tab:
            return tab[key]
        else:
            ent = Lexent(key)
            tab[key] = ent
            self._entries.append(ent)
            return ent

    ##  Load  --------------------------

    def load (self):
        redirects = []
        for rec in Records(self._filename + '.lx'):
            if len(rec) == 2:
                redirects.append(rec)
            else:
                self._intern_canonical(rec[0], rec[1], rec[2].split())
        for (key, canonical) in redirects:
            self._process_redirect(key, canonical)
        self._intern_parts()
        self._load_index()
        self.compute_frequencies()

    def _intern_canonical (self, key, gloss, parts):
        ent = self.intern(key)
        if ent._gloss or ent._parts:
            raise Exception('Duplicate key: {}'.format(key))
        ent._gloss = gloss
        ent._parts = parts

    def _process_redirect (self, key, canonical):
        ent = self.intern(canonical)
        tab = self._entdict
        if key in tab:
            raise Exception('Duplicate key: {}'.format(key))
        ent._variants.append(key)
        tab[key] = ent
        
    def _intern_parts (self):
        # the list of entries may grow as we go
        entries = self._entries
        n = len(self._entries)
        for i in range(n):
            ent = entries[i]
            ent._parts = [self.intern(p) for p in ent._parts]
            for part in ent._parts:
                part._wholes.append(ent)

    def _load_index (self):
        records = Records(self._filename + '.idx')
        for (key, locs) in records:
            e = self.intern(key)
            e._locations.extend(Loc.from_string(s) for s in locs.split(','))
    
    ##  Save  --------------------------

    def save_main (self):
        with open(self._filename + '.lx', 'w') as f:
            for (k, v) in sorted(self.items()):
                f.write(k)
                f.write('\t')
                if isinstance(v, Lexent):
                    f.write(v.gloss())
                    f.write('\t')
                    f.write(' '.join(p.key() for p in v.parts()))
                else:
                    f.write(v)
                f.write('\n')

    def save_index (self):
        with open(self.filename + '.idx', 'w') as f:
            for ent in self._entries:
                if ent.has_locations():
                    f.write(ent.key())
                    f.write('\t')
                    first = True
                    for loc in ent.locations():
                        if first: first = False
                        else: f.write(',')
                        f.write(str(loc))
                    f.write('\n')

    ##  index  -------------------------

    def generate_index (self):

        # Clear
        for ent in self._entdict.values():
            ent._locations = []
            ent._freq = None

        # Regenerate
        for (loc, ent) in self._lang.tokens():
            ent._locations.append(loc)
        self.compute_frequencies()

        # Save
        self.save_index()

    def update (self):
        self.generate_index()
        self.save_main()

    def compute_frequencies (self):
        for e in self._entries:
            self._compute_freq(e, [])

    def _compute_freq (self, ent, callers):
        if ent.freq() is None:
            if ent in callers:
                raise Exception('Cycle detected: {} -> {}'.format(callers, self))
            if ent._locations:
                ent._freq = len(ent._locations)
            else:
                ent._freq = 0
            callers.append(ent)
            if ent._wholes:
                for w in ent._wholes:
                    ent._freq += self._compute_freq(w, callers)
            callers.pop()
        return ent._freq

    #  concordance  --------------------

    def concordance (self, ent):
        return Concordance(self, ent)


#--  read_toc_file, Text  ------------------------------------------------------

##  The constructor is called while building the language's TextList.  Thus the __init__
##  method should not seek to access lang.toc.

class Metadata (MapProxy):
    
    FileKeys = {'id', 'ty', 'de', 'au', 'ti', 'or', 'ch', 'no', 'audio'}

    def __init__ (self, lang, props):
        self._lang = lang
        self._props = props

        if 'ch' in props:
            props['ch'] = tuple(props['ch'].split())

    def __map__ (self):
        return self._props

    def __str__ (self):
        return tabular((item for item in self._props.items()),
                       hlines=False)

    def __repr__ (self):
        return repr(self._props)


class Item (ListProxy):

    def __init__ (self, meta):
        self._meta = meta
        self._lang = meta._lang
        self._parent = None

    def __getattr__ (self, name):
        if name == 'meta':
            return self._meta
        elif name == 'parent':
            return self._parent
        elif name == 'lang':
            return self._lang
        elif name == 'textid':
            return self._meta['id']
        else:
            raise AttributeError(f'No such attribute: {name}')

    def is_root (self):
        return self.parent is None

    def is_collection (self):
        return self._meta.get('ty') == 'collection'

    def is_document_part (self):
        return not self.is_collection()

    def is_document (self):
        return self.is_document_part() and (self.parent is None or self.parent.is_collection())

    def is_text (self):
        return isinstance(self, Text)

    def is_vocabulary (self):
        return self._meta.get('ty') == 'vocab'

    def is_running_text (self):
        return self.is_text() and not self.is_vocabulary()

    def get_texts (self):
        for txt in self.walk():
            if txt.is_text():
                yield txt

    def toc_entry (self):
        return (self.textid, self.meta.get('ty'), self.meta.get('ti'))

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self.textid}>'


class Text (Item):

    def __init__ (self, meta):
        Item.__init__(self, meta)
        self._sents = None

    def __list__ (self):
        return self.sents

    def walk (self):
        yield self

    def is_text (self):
        return True

    def __getattr__ (self, name):
        if name == 'sents':
            if self._sents is None:
                self._sents = Sentences(self)
            return self._sents
        else:
            return Item.__getattr__(self, name)

    # For use by TextTable

    def _set_children (self, texts):
        pass

    def pprint_tree (self):
        pprint(*self.toc_entry())

    def __str__ (self):
        return ''.join(self.sents.to_lines())


class Aggregate (Item):

    def __init__ (self, meta):
        Item.__init__(self, meta)
        self._children = None

    def __getattr__ (self, name):
        if name == 'children':
            return self._children
        else:
            return Item.__getattr__(self, name)

    def __list__ (self):
        return self._children

    def is_text (self):
        return False

    def _set_children (self, texts):
        ch_names = self.meta.get('ch')
        if not ch_names:
            self._children = tuple()
        else:
            self._children = tuple(texts[name] for name in ch_names)
            for child in self._children:
                # note: if multiple documents "claim" the same child, the first one wins
                if child._parent is None:
                    child._parent = self

    def walk (self):
        yield self
        if self._children:
            for child in self._children:
                for item in child.walk():
                    yield item

    def pprint_tree (self):
        pprint(*self.toc_entry())
        if self._children:
            with pprint.indent():
                for child in self._children:
                    child.pprint_tree()


class TextList (object):

    def __init__ (self, lang, texts):
        texts = list(texts)

        self._contents = texts
        self._index = dict((t.name(), t) for t in texts)

        Text._set_children_and_parents(texts)
        for text in texts:
            text._set_sentences(lang)

    def __len__ (self):
        return self._contents.__len__()

    def __getitem__ (self, i):
        if isinstance(i, str):
            return self._index[i]
        else:
            return self._contents[i]

    def __iter__ (self):
        return self._contents.__iter__()
    
    def roots (self):
        for text in self._contents:
            if text.parent() is None:
                yield text

    def tokens (self):
        for text in self._contents:
            for sent in text.sentences():
                for (j, word) in enumerate(sent):
                    yield (Loc(text.textid(), sent.i(), j), word)

    @staticmethod
    def write_tree (f, text, indent):
        if indent: f.write(' ' * indent)
        f.write('[')
        f.write(str(text.textid()))
        f.write('] ')
        f.write(text.title() or '(no title)')
        indent += 2
        if text.has_children():
            for child in text.children():
                f.write('\n')
                TextList.write_tree(f, child, indent)
        
    def print_tree (self):
        roots = self.roots()
        for root in roots:
            self.write_tree(sys.stdout, root, 0)
            print()


# join(self.lang.dirname, 'toc')
# set text.lang

#--  Sentence, read_txt_file  --------------------------------------------------

#     def _make_sentence (self, words, i):
#         words = [self.lex.intern(w) for w in words]
#         return Sentence(self.text, i, words)
# 
# join(text.lang.dirname, 'tok', str(text.textid) + '.tok')
#     
# list(Tokfile(self))


class Sentences (ListProxy):
    
    def __init__ (self, text):
        lang = text.lang
        txtdir = lang._directory['txt']

        self._text = text
        self._file = Dicts(txtdir[text.textid])
        self._sents = [Sentence(text, i, d) for (i, d) in enumerate(self._file)]

    def to_dicts (self):
        for sent in self._sents:
            yield sent.to_dict()

    def to_lines (self):
        return Dicts.render(self.to_dicts())

    def __list__ (self):
        return self._sents

    def __repr__ (self):
        return repr(self._sents)


class Sentence (ListProxy):

    def __init__ (self, text, i, props):
        self._text = text
        self._i = i
        self._words = props.get('w').split()
        self._trans = props.get('g')

    def to_dict (self):
        return {'w': ' '.join(self._words),
                'g': self._trans}

    def text (self): return self._text
    def i (self): return self._i
    def words (self): return self._words
    def translation (self): return self._trans
    def __list__ (self): return self._words

    def intern_words (self, lex):
        words = self._words
        for i in range(len(words)):
            w = words[i]
            if isinstance(w, str):
                words[i] = lex.intern(w)

#     def __repr__ (self):
#         words = ['<Sentence']
#         for (i, w) in enumerate(self._words):
#             if i >= 3:
#                 words.append(' ...')
#                 break
#             else:
#                 words.append(' ')
#                 words.append(w.key() if isinstance(w, Lexent) else w)
#         words.append('>')
#         return ''.join(words)

    def __repr__ (self):
        return repr(self._words)

    def pprint (self):
        print('Sentence', self._text.textid() if self._text else '(no text)', self._i)
        for (i, word) in enumerate(self._words):
            print(' ', i, word)

    def __len__ (self):
        return self._words.__len__()
    
    def __getitem__ (self, i):
        return self._words.__getitem__(i)

    def __iter__ (self):
        return self._words.__iter__()

    def __str__ (self):
        return ' '.join(self)


# def standardize_token (s):
#     j = len(s)
#     i = j-1
#     while i > 0 and s[i].isdigit():
#         i -= 1
#     if 0 < i < j and s[i] == '.':
#         return s
#     else:
#         return s + '.0'
# 
# def parse_tokens (s):
#     for token in s.split():
#         yield standardize_token(token)

# def read_txt_file (fn):
#     records = Records(fn)
#     for rec in records:
#         if len(rec) == 1:
#             trans = ''
#         elif len(rec) == 2:
#             trans = rec[1]
#         else:
#             records.error('Bad record')
#         words = list(parse_tokens(rec[0]))
#         yield Sentence(words=words, trans=trans)


#--  Concordance  --------------------------------------------------------------

class Concordance (object):

    def __init__ (self, lex, ent):
        if isinstance(ent, str): ent = lex[ent]

        self._lexicon = lex
        self._ent = ent

    def __repr__ (self):
        lang = self._lexicon.lang
        with StringIO() as f:
            for loc in self._ent.all_locations():
                (sent, i) = lang.get_location(loc)
                s = ' '.join(w.form for w in sent[:i])
                t = ' '.join(w.form for w in sent[i:])
                print('{:>40}  {:40}'.format(s[-40:], t[:40]), file=f)
            return f.getvalue()

    def _display_lexent (self, key):
        print(key)

    def _get_rows (self):
        for loc in self._ent.all_locations():
            (sent, i) = self._lexicon.language().get_location(loc)
            yield (sent[i].key,
                   loc,
                   ' '.join(w.form for w in sent[:i]),
                   ' '.join(w.form for w in sent[i+1:]))


#--  User Config  --------------------------------------------------------------

class PersistentDict (object):

    def __init__ (self, f, items=[]):
        self._file = f
        self._table = dict(items)

    def __iter__ (self): return self._table.__iter__()
    def __len__ (self): return self._table.__len__()
    def keys (self): return self._table.keys()
    def values (self): return self._table.values()
    def items (self): return self._table.items()
    def __getitem__ (self, key): return self._table.__getitem__(key)
    def __contains__ (self, key): return self._table.__contains__(key)

    def __nested__ (self):
        for (key, value) in self.items():
            if isinstance(value, str):
                yield key + '\t' + value
            else:
                yield key
                yield list(value.__nested__())

    def __setitem__ (self, key, value):
        self._table.__setitem__(key, value)
        self._file.save()

    def __repr__ (self):
        return '<PersistentDict ' + repr(self._table) + '>'


class PersistentList (object):

    def __init__ (self, f, lst=[]):
        self._file = f
        self._list = lst

    def __iter__ (self): return self._list.__iter__()
    def __len__ (self): return self._list.__len__()
    def __getitem__ (self, i): return self._list.__getitem__(i)

    def __setitem__ (self, i, value):
        self._list.__setitem__(i, value)
        self._file.save()

    def __repr__ (self):
        return '<PersistentList ' + repr(self._list) + '>'
        

#--  IGT  ----------------------------------------------------------------------

def print_igt (sent):
    for w in sent:
        print('{:20} {}'.format(w.key(), w.gloss()))
        if w.has_parts():
            for p in w.parts():
                print('    {:20} {}'.format(p.key(), p.gloss()))
    print()
    print(sent.trans)


#--  CorpusDisk  ---------------------------------------------------------------

class JsonCorpus (Backend):

    def __init__ (self, dirname):
        Backend.__init__(self)
        self._corpus = Corpus(dirname)
        
    def get_lang (self, langid):
        return self._corpus.language(langid).metadata()

    def get_langs (self):
        return {'langs': [lg.metadata() for lg in self._corpus.languages()]}

    def get_toc (self, lgid, textid=None):
        lang = self._corpus.language(lgid)
        if textid is None:
            return {'toc': [text.metadata() for text in lang.texts()]}
        else:
            return lang.text(textid).metadata()


#--  main  ---------------------------------------------------------------------

def _flag_to_kv (flag):
    assert flag[0] == '-'
    i = flag.rfind('=')
    if i > 1:
        value = flag[i+1:]
        key = flag[1:i]
    else:
        key = flag[1:]
        value = True
    return (key, value)

def get_corpus (user=None):
    if user is None:
        user = User()
    corpfn = user.props.get('corpus')
    if not corpfn:
        raise Exception('No specification for corpus in ~/.cld/props')
    return Corpus(corpfn)

def get_defaults (lg=None, textid=None, user=None):
    if user is None:
        user = User()
    if lg is None and textid and '.' in textid:
        (lg, textid) = textid.split('.')
    if lg is None:
        lg = user.props.get('lang')
        if not lg:
            raise Exception('No specification for lang in ~/.cld/props')
    return (user, get_corpus(user), lg, textid)


class CorpusMain (Main):
    
    def com_info (self):
        user = User()
        print('default corpus:  ', user.props.get('corpus'))
        print('default language:', user.props.get('lang'))

    def com_texts (self, lg=None):
        (_, corpus, lg, _) = get_defaults(lg)
        print(corpus.langs[lg].toc)

    def com_docs (self, lg=None):
        (_, corpus, lg, _) = get_defaults(lg)
        print(tabular((doc.toc_entry() for doc in corpus.langs[lg].get_documents()), hlines=False))

    def com_tree (self, textid=None):
        (_, corpus, lg, textid) = get_defaults(textid=textid)
        if textid is None:
            for text in corpus[lg].get_roots():
                text.pprint_tree()
        else:
            corpus[lg][textid].pprint_tree()

    def com_drill (self, lg=None):
        (user, corpus, lg, _) = get_defaults(lg)
        drill = Drill(user, corpus, lg)
        drill()

    def com_text (self, textid):
        (_, corpus, lg, textid) = get_defaults(textid=textid)
        print(corpus[lg][textid])

    def com_sents (self, textid):
        (_, corpus, lg, textid) = get_defaults(textid=textid)
        text = corpus[lg][textid]
        for sent in text.sents:
            print(sent)

    def com_tsents (self, textid):
        (_, corpus, lg, textid) = get_defaults(textid=textid)
        text = corpus[lg][textid]
        first = True
        for sent in text.sents:
            if first:
                first = False
            else:
                print()
            print(sent)
            print(sent.translation())

    def com_get (self, fn, path):
        print(JsonCorpus(fn)[path])

    def com_open (self, fn, nw=False):
        JsonCorpus(fn).run(nw)
    

if __name__ == '__main__':
    CorpusMain()()
