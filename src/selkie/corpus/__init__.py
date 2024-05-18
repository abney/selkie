
import time, math, os, sys, pathlib
from os import listdir
from os.path import join, exists, expanduser
from io import StringIO
from .. import config
#from ..pyx.io import load_kvi
from ..pyx.io import tabular, pprint
from ..pyx.seq import LazyList
from ..pyx.object import ListProxy, MapProxy
from ..pyx.formats import File, BaseFile, Dicts, PLists, Records
#from ..pyx.formats import Nested, NestedDict,
from ..pyx.com import Main
from ..pyx.disk import VDisk
from ..editor.webserver import Backend
from .drill import Drill

# corpus          Corpus
#   langs         LanguageTable
#   roms          RomRepository
#     *romname*   Rom
#   *lgid*        Language
#     lexicon     Lexicon
#     index       TokenIndex
#     txt         TextTable
#       *txtid*   SimpleText


#--  Corpus, Language  ---------------------------------------------------------

class Corpus (object):

    def __init__ (self, root):
        root = expanduser(root)

        self._disk = VDisk(root)
        self._langs = None
        self._roms = None

    def disk (self):
        return self._disk

    def getfile (self, name):
        return self._disk[name]

    # 'langs' and 'roms' are created on demand

    def __getattr__ (self, name):
        if name == 'langs':
            if self._langs is None:
                self._langs = LanguageTable(self)
            return self._langs
        elif name == 'roms':
            if self._roms is None:
                self._roms = RomRepository(self)
            return self._roms

    def filename (self):
        return self.disk().root

    def __getitem__ (self, name):
        return self.langs[name]

    def __iter__ (self):
        return iter(self.langs)

    def __len__ (self):
        return len(self.langs)

    def languages (self):
        return iter(self.langs)

    def __repr__ (self):
        return '<Corpus {}>'.format(self.filename())

    def language (self, name):
        return self.langs.get(name)


class LanguageTable (MapProxy):

    def __init__ (self, corpus):
        self._corpus = corpus
        self._file = Dicts(corpus.getfile('/langs'))
        self._table = {}
        self.__proxyfor__ = self._table

        for entry in self._file:
            langid = entry.get('id')
            if not langid:
                print('** Missing id in langs')
                continue
            self._table[langid] = Language(self, langid, entry)

    def corpus (self):
        return self._corpus

    def item_name (self):
        return '/langs'

    def __str__ (self):
        if self._table:
            return tabular(((langid, lg.full_name()) for (langid, lg) in self._table.items()),
                           hlines=False)
        else:
            return '(no languages)'


class Language (object):

    def __init__ (self, tab, langid, props):
        self._corpus = tab._corpus
        self._langid = langid
        self._props = props
        self._lexicon = None
        self._index = None
        self._txt = None

    def __getattr__ (self, name):
        if name == 'lexicon':
            if self._lexicon is None:
                self._lexicon = Lexicon(self)
            return self._lexicon
        elif name == 'index':
            if self._index is None:
                self._index = TokenIndex(self)
            return self._index
        elif name == 'txt':
            if self._txt is None:
                self._txt = TextTable(self)
            return self._txt
        elif name == 'toc':
            return self.txt.metadata()

    def corpus (self):
        return self._corpus

    def item_name (self):
        return '/' + self._langid

    def langid (self):
        return self._langid

    def full_name (self):
        return self._props.get('name', '(no name given)')

    def print_tree (self):
        for root in self.get_roots():
            root.pprint_tree()

    def get_roots (self):
        return [item for item in self.txt.values() if item.is_root()]

    def get_collections (self):
        return [item for item in self.txt.values() if item.is_collection()]

    def get_documents (self):
        return [item for item in self.txt.values() if item.is_document()]

    def get_simple_texts (self):
        return [item for item in self.txt.values() if item.is_simple_text()]

    def get_vocabularies (self):
        return [item for item in self.txt.values() if item.is_vocabulary()]

    def get_running_texts (self):
        return [item for item in self.txt.values() if item.is_running_text()]

    def words (self):
        return LazyList(self._iter_words)

    def sents (self):
        return LazyList(self._iter_sents)
    
    def _iter_sents (self):
        for text in self._toc.values():
            if text.is_running_text():
                for sent in text:
                    yield sent

    def _iter_words (self):
        for sent in self._iter_sents():
            for word in sent:
                yield word

    def __str__ (self):
        return str(self._toc)

    def __repr__ (self):
        return f'<Language {self._langid} {self.full_name()}>'


# The difference between a TextTable and a Toc is that the values
# in a TextTable are Texts, whereas the values in a Toc are Metadata
# instances.

class MetadataTable (object):

    def __init__ (self, table):
        self._table = table

    def __getitem__ (self, textid):
        return self._table[textid].metadata()

    def __iter__ (self):
        return self._table.__iter__()

    def __len__ (self):
        return self._table.__len__()

    def items (self):
        for (textid, txt) in self._table.items():
            yield (textid, txt.metadata())
    
    def keys (self):
        return self._table.keys()

    def values (self):
        for txt in self._table.values():
            yield txt.metadata()

    def item_name (self):
        return self._table.item_name()

    def __repr__ (self):
        return f'<MetadataTable {self._table.langid()}>'

    def __str__ (self):
        if self._table:
            return tabular((tx.toc_entry() for tx in self._table.values()), hlines=False)
        else:
            return '(empty text table)'

class TextTable (MapProxy):

    def __init__ (self, lang):
        self._lang = lang
        self._file = Dicts(lang.corpus().getfile(self.item_name()))
        self._metadata = MetadataTable(self)
        self._dict = {}
        self.__proxyfor__ = self._dict

        for d in self._file:
            txtid = d['id']
            metadata = Metadata(lang, d)
            if 'ch' in d:
                text = Aggregate(lang, metadata)
            else:
                text = SimpleText(lang, metadata)
            self._dict[txtid] = text

        # after all the toc file has been loaded and all texts have metadata,
        # set parent and children values

        for text in self._dict.values():
            text._set_children(self)

    def langid (self):
        return self._lang.langid()

    def language (self):
        return self._lang

    # 'txt' is not actually an item
    
    def item_name (self):
        return self._lang.item_name() + '/toc'

    def metadata (self):
        return self._metadata

    def __repr__ (self):
        return f'<TextTable {self._lang.langid()}>'


def open_language (cname, lname):
    corpus = Corpus(cname + '.lgc')
    lang = corpus.language(lname)
    return lang
    

class RomRepository (object):

    def __init__ (self, corpus):
        self._corpus = corpus

    def __getitem__ (self, name):
        return Rom(self._corpus, name)


class Rom (object):

    def __init__ (self, corpus, name):
        self._corpus = corpus
        self.name = name


class CorpusFormat (object):

    def load (self, fn):
        pass

    def save (self, x, fn):
        pass



def load_corpus (fn):
    corpus = Corpus.from_json(load_kvi(fn))
    corpus._dirname = pathlib.Path(fn).parent
    return corpus


#--  read_toc_file, SimpleText  ------------------------------------------------------

##  The constructor is called while building the language's TextList.  Thus the __init__
##  method should not seek to access lang.toc.

class Metadata (MapProxy):
    
    FileKeys = {'id', 'ty', 'de', 'au', 'ti', 'or', 'ch', 'no', 'audio'}

    def __init__ (self, lang, props):
        self._lang = lang
        self.__proxyfor__ = props

        if 'ch' in props:
            props['ch'] = tuple(props['ch'].split())

    def language (self):
        return self._lang

    def corpus (self):
        return self._lang.corpus()

    def __map__ (self):
        return self.__proxyfor__

    def __str__ (self):
        return tabular((item for item in self.__proxyfor__.items()),
                       hlines=False)

    def __repr__ (self):
        return repr(self.__proxyfor__)


class Text (object):

    def __init__ (self, lang, metadata):
        self._lang = lang
        self._metadata = metadata
        self._parent = None
        self._children = None

    def language (self):
        return self._lang

    def corpus (self):
        return self._lang.corpus()

    def metadata (self):
        return self._metadata

    def parent (self):
        return self._parent

    def children (self):
        return self._children

    # Called by TextTable after all texts have been created.
    # Overridden by Aggregate.

    def _set_children (self, table):
        pass

    def walk (self):
        yield self
        for child in self.children():
            for item in child.walk():
                yield item

    def textid (self):
        return self._metadata['id']

    def item_name (self):
        return self.language().item_name() + '/txt/' + self.textid()

    def text_type (self):
        return self._metadata.get('ty', '')

    def title (self):
        return self._metadata.get('ti', '')

    def author (self):
        return self._metadata.get('au', '')

    def is_root (self):
        return self._parent is None

    def is_collection (self):
        return self._metadata.get('ty') == 'collection'

    def is_document_part (self):
        return not self.is_collection()

    def is_document (self):
        return self.is_document_part() and (self._parent is None or self._parent.is_collection())

    def is_simple_text (self):
        return isinstance(self, SimpleText)

    def is_vocabulary (self):
        return self._metadata.get('ty') == 'vocab'

    def is_running_text (self):
        return self.is_simple_text() and not self.is_vocabulary()

    def get_simple_texts (self):
        for txt in self.walk():
            if txt.is_simple_text():
                yield txt

    def toc_entry (self):
        return (self.textid(), self._metadata.get('ty'), self._metadata.get('ti'))

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self.textid()}>'


class SimpleText (Text):

    def __init__ (self, *args):
        Text.__init__(self, *args)
        self._sents = None

    def sentences (self):
        if self._sents is None:
            self._sents = Sentences(self)
        return self._sents

    def __iter__ (self):
        return self.sentences().__iter__()

    def __getitem__ (self, i):
        return self.sentences().__getitem__(i)

    def __len__ (self):
        return self.sentences().__len__()

    def pprint_tree (self):
        pprint(*self.toc_entry())

    def __str__ (self):
        return ''.join(self.sentences().to_lines())


class Aggregate (Text):

    def __init__ (self, *args):
        Text.__init__(self, *args)
        self._children = None

    # Called by TextTable after all texts have been created (with metadata).

    def _set_children (self, table):
        if self._children is None:
            self._children = tuple(table[textid] for textid in self._metadata.get('ch'))
            for child in self._children:
                # note: if multiple documents "claim" the same child, the first one wins
                if child._parent is None:
                    child._parent = self

    def pprint_tree (self):
        pprint(*self.toc_entry())
        if self.__proxyfor__:
            with pprint.indent():
                for child in self.__proxyfor__:
                    child.pprint_tree()


class TextList (object):

    def __init__ (self, lang, texts):
        texts = list(texts)

        self._contents = texts
        self._index = dict((t.name(), t) for t in texts)

        SimpleText._set_children_and_parents(texts)
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
        self._text = text
        self._file = PLists(text.corpus().getfile(text.item_name()))
        self._sents = [Sentence(text, i, plist) for (i, plist) in enumerate(self._file, 1)]
        self.__proxyfor__ = self._sents

    def __repr__ (self):
        return repr(self._sents)


class Sentence (ListProxy):

    def __init__ (self, text, sno, plist):
        self._text = text
        self._sno = sno
        self._words = []
        self._timestamps = []
        self._trans = None
        self.__proxyfor__ = self._words

        for (key, value) in plist:
            if key == 'w':
                self._words.extend(value.split())
            elif key == 't':
                self._timestamps.append((len(self._words), value))
            elif key == 'g':
                self._trans = value

    def text (self): return self._text
    def sno (self): return self._sno
    def words (self): return self._words
    def timestamps (self): return self._timestamps
    def translation (self): return self._trans

    def intern_words (self, lex):
        words = self.__proxyfor__
        for i in range(len(words)):
            w = words[i]
            if isinstance(w, str):
                words[i] = lex.intern(w)

#     def __repr__ (self):
#         words = ['<Sentence']
#         for (i, w) in enumerate(self.__proxyfor__):
#             if i >= 3:
#                 words.append(' ...')
#                 break
#             else:
#                 words.append(' ')
#                 words.append(w.key() if isinstance(w, Lexent) else w)
#         words.append('>')
#         return ''.join(words)

    def __repr__ (self):
        if len(self._words) > 5:
            suffix = ' ...'
        else:
            suffix = ''
        return f"<Sentence {self._sno} {' '.join(self._words[:5])}{suffix}>"

    def pprint (self):
        print('Sentence', self._text.textid() if self._text else '(no text)', self._i)
        for (i, word) in enumerate(self.__proxyfor__):
            print(' ', i, word)

    def __str__ (self):
        return ' '.join(self._words)


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


#--  Lexicon, Lexent, Loc  -----------------------------------------------------

class Lexent (object):

    def __init__ (self, lexicon, obj):
        self._lexicon = lexicon
        self._obj = obj

        if 'id' not in obj:
            raise Exception(f'No lexid provided: {obj}')
        
    def form (self): return self._obj['id']
    def gloss (self): return self._obj.get('g', '')
    def parts (self): return self._obj.get('pp', '').split()

    def __lt__ (self, other):
        return self._form < other._form

    def __eq__ (self, other):
        return self._form == other._form

    def __repr__ (self):
        return f'<Lexent {self.form()}>'

    def __str__ (self):
        with StringIO() as f:
            first = True
            for (key, value) in self._obj.items():
                if first: first = False
                else: f.write('\n')
                f.write(f'{key:5s}')
                f.write(value)
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


class Lexicon (object):

    def __init__ (self, lang):
        self._corpus = lang.corpus()
        self._lang = lang
        self._file = Dicts(self._corpus.getfile(self.item_name()))
        self._entries = None

    def item_name (self):
        return self._lang.item_name() + '/lexicon'

    def entries (self):
        if self._entries is None:
            self._entries = tab = {}
            for obj in self._file:
                lexent = Lexent(self, obj)
                form = lexent.form()
                if form in tab:
                    print(f"** Duplicate entries in lexicon for form '{form}'; keeping the last one only")
                else:
                    tab[form] = lexent
        return self._entries

    def __repr__ (self):
        return '<Lexicon {}>'.format(self._lang.langid())

    def __iter__ (self): return self.entries().__iter__()
    def __getitem__ (self, form): return self.entries().__getitem__(form)
    def __len__ (self): return self.entries().__len__()

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


class TokenIndex (object):

    def __init__ (self, lang):
        self._lang = lang

    def __repr__ (self):
        return f'<TokenIndex {self._lang.langid()}>'


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
