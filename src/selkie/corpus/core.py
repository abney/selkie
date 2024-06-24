
import time, math, os, sys, pathlib
from os import listdir, walk
from os.path import join, exists, expanduser
from io import StringIO
from collections import OrderedDict
from collections.abc import Sequence
from .. import config
#from ..pyx.io import load_kvi
from ..pyx.io import tabular, pprint
from ..pyx.seq import LazyList
from ..pyx.object import ListProxy, MapProxy
from ..pyx.formats import File, BaseFile, Dicts, PLists, Records, ObjectTables
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
#       *txtid*   Text


def pget (plist, key):
    for (k, value) in plist:
        if k == key:
            return value


#--  Items  --------------------------------------------------------------------
#
# Modifications to items are saved up and written to disk all at once.
# Deleting an entire item can happen immediately.
# A deleted item should be removed from the 'tosave' set.

class ItemDisk (object):

    def __init__ (self, corpus, filename):
        self._corpus = corpus
        self._root = expanduser(filename)
        self._disk = VDisk(self._root)
        self._nholds = 0
        self._aborted = False
        self._tosave = set()
        self._items = {'/': self}

    def corpus (self):
        return self._corpus
    
    # for use by Item only
    
    def _File (self, name):
        return self._disk[name]

    def __delitem__ (self, name):
        self._disk.__delitem__(name)
        # there should be at most one
        tosave = [item for item in self._tosave if item.item_name() == name]
        for item in tosave:
            self._tosave.remove(item)
            
    # for use by _Hold only

    def _release (self, abort):
        if self._nholds <= 0:
            raise Exception('Hold count is off')
        self._nholds -= 1
        if abort: self._aborted = True
        if self._nholds == 0:
            if not self._aborted:
                for item in self._tosave:
                    item._save()
            self._tosave.clear()
            self._aborted = False

    def hold (self):
        self._nholds += 1
        return _Hold(self)

    # for use by Item only

    def _modified (self, item):
        if self._nholds > 0:
            self._tosave.add(item)
        else:
            item._save()

    def intern (self, name, *moreargs):
        item = self._items.get(name)
        if item is None:
            if not moreargs:
                raise Exception('Must provide cls if the item does not already exist')
            cls = moreargs[0]
            moreargs = moreargs[1:]
            item = self._items[name] = cls(self, name, *moreargs)
        return item

#     def __getitem__ (self, name):
#         return self._items[name]
# 
#     def get (self, name, default=None):
#         return self._items.get(name, default)
# 
#     def __iter__ (self):
#         return self._items.__iter__()
# 
#     def __len__ (self):
#         return self._items.__len__()

    def __delitem__ (self, name):
        del self._items[name]
        del self._disk[name]

    def rmtree (self, pfx):
        todo = [name for name in self._items if name.startswith(pfx)]
        for name in todo:
            self.__delitem__(name)

    def filename (self):
        return self._disk.root

#     def disk (self):
#         return self._disk


class _Hold (object):

    def __init__ (self, disk):
        self._disk = disk

    def __enter__ (self):
        return self

    def __exit__ (self, error_type, v, tb):
        self._disk._release(abort=error_type)


class Item (object):

    debug = False

    # Must be overridden by specializations
    format = None

    # May be overridden by specializations
    backlinks_class = None

    def __init__ (self, disk, name):
        assert isinstance(disk, ItemDisk), 'Not an ItemDisk'
        self._disk = disk
        self._item_name = name
        self._file = None
        self._contents = None
        self._backlinks = None

    def disk (self): return self._disk
    def corpus (self): return self._disk.corpus()
    def item_name (self): return self._item_name
    def filename (self): return self._disk.filename() + self.item_name()

    def contents (self):
        if self._contents is None:
            self._file = self.format(self._disk._File(self._item_name))
            self._contents = list(self._file)
            if self.debug: print('[READ]', self._item_name, self._contents)
        return self._contents
    
    def backlinks (self):
        if self._backlinks is None:
            if self.backlinks_class is None:
                raise Exception('This class has no backlinks')
            self._backlinks = self.backlinks_class(self)
        return self._backlinks

    # So that we can put Items in a set

    def __hash__ (self):
        return hash(self._item_name)

    def __cmp__ (self, other):
        return cmp(self._item_name, other._item_name)
        
    def modified (self):
        if self.debug: print('[MODIFIED]', self._item_name)
        self._backlinks = None
        self._disk._modified(self)

    def modifying (self):
        return self._disk.hold()

    # for the use of ItemDisk only

    def _save (self):
        if self._contents is None:
            raise Exception('Contents not set')
        if self.debug: print('[WRITE]', self._item_name, self._contents)
        self._file.store(self._contents)

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self.item_name()}>'


#--  Corpus, Language  ---------------------------------------------------------

class Corpus (object):

    def __init__ (self, filename):
        self._items = ItemDisk(self, filename)

    def disk (self):
        return self._items.disk()

    def filename (self):
        return self._items.filename()

    def list_files (self):
        dirname = self.filename()
        n = len(dirname)
        for (relpath, subdirnames, filenames) in walk(dirname):
            for name in filenames:
                print(join(relpath, name)[n:])

    def item (self, name):
        return self._items[name]

    def intern (self, name, *moreargs):
        return self._items.intern(name, *moreargs)
        
    def __getattr__ (self, name):
        if name == 'langs':
            return self.intern('/langs', LanguageTable)
        elif name == 'roms':
            # This is a directory, not an Item
            return RomTable(self)
        else:
            raise AttributeError(f'No such attribute: {name}')

    def __getitem__ (self, name):
        return self.langs[name]

    def get (self, name):
        return self.langs.get(name)

    def __iter__ (self):
        return iter(self.langs)

    def __len__ (self):
        return len(self.langs)

    def language (self, name):
        return self.langs.get(name)

    def new (self, langid, fullname):
        return self.langs.new(langid, fullname)

    def __delitem__ (self, langid):
        self.langs.__delitem__(langid)

    def languages (self):
        return iter(self.langs)

    def __repr__ (self):
        return '<Corpus {}>'.format(self.filename())


class LanguageTable (Item):

    format = ObjectTables

    def _table (self):
        return self.contents()[0]

    def __getitem__ (self, langid):
        lang = self._table().get(langid)
        if lang is None:
            raise Exception(f'No such language in corpus: {langid}')
        return Language(self, lang)

    def get (self, langid):
        return self._table().get(langid)

    def __iter__ (self):
        return self._table().__iter__()

    def __len__ (self):
        return self._table().__len__()

    def items (self):
        for (key, value) in self._table().items():
            yield (key, Language(self, value))

    def keys (self):
        return self._table().keys()

    def values (self):
        for value in self._table().values():
            yield Language(self, value)

    def __bool__ (self):
        return bool(self._table())

    def __delitem__ (self, langid):
        self._table().__delitem__(langid)
        self.modified()
        self.disk().rmtree('/' + langid)

    def new (self, langid, fullname):
        table = self.contents()[0]
        if langid in table:
            raise Exception(f'Language already exists: {langid}')
        table[langid] = obj = OrderedDict([('id', langid), ('name', fullname)])
        self.modified()
        return Language(self, obj)

    def __str__ (self):
        if self:
            return tabular(((langid, lg.fullname()) for (langid, lg) in self.items()),
                           hlines=False)
        else:
            return '(no languages)'


class Language (object):

    def __init__ (self, langs, props):
        assert isinstance(langs, LanguageTable), 'Not a LanguageTable'
        self._langs = langs
        self._props = props

    def disk (self):
        return self._langs.disk()

    def corpus (self):
        return self._langs.corpus()

    def __getitem__ (self, prop):
        return self._props.__getitem__(prop)

    def __iter__ (self):
        return self._props.__iter__()

    def __len__ (self):
        return self._props.__len__()

    def __setitem__ (self, key, value):
        assert isinstance(value, str), 'Value must be a string'
        if key == 'id': raise KeyError("The key 'id' is not mutable")
        self._props[key] = value
        self._langs.modified()

    def __getattr__ (self, name):
        if name == 'lexicon':
            return self.disk().intern(self.item_name() + '/lexicon', Lexicon, self)
        elif name == 'index':
            return self.disk().intern(self.item_name() + '/index', TokenIndex, self)
        elif name == 'toc':
            return self.disk().intern(self.item_name() + '/toc', Toc, self)
        elif name == 'txt':
            return TextTable(self.toc, self)
        else:
            raise AttributeError(f'No such attribute: {name}')

    def langid (self):
        return self._props['id']

    def fullname (self):
        return self._props.get('name', '(no name given)')

    def item_name (self):
        return '/' + self.langid()

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

    def deref (self, locs):
        if isinstance(locs, Loc):
            return self.deref_loc(locs)
        else:
            return self.deref_locs(locs)

    def deref_loc (self, loc):
        text = self.txt[loc.t()]
        sents = text.sentences()
        sent = sents[loc.s()-1]
        w = loc.w()
        return sent[w-1]

    def deref_locs (self, locs):
        for loc in locs:
            yield self.deref_loc(loc)

    def clear_index (self):
        self.index.clear()

    def __str__ (self):
        return str(self._toc)

    def __repr__ (self):
        return f'<Language {self.langid()} {self.fullname()}>'


class TocBacklinks (object):

    def __init__ (self, toc):
        self._toc = toc
        self._parent_table = {}
        
        for (parid, obj) in self._toc._table().items():
            if 'ch' in obj:
                for childid in obj['ch'].split():
                    if childid not in self._parent_table:
                        self._parent_table[childid] = parid

    def parent (self, textid):
        return self._parent_table.get(textid)


# The difference between a TextTable and a Toc is that the values
# in a TextTable are Texts, whereas the values in a Toc are TextMetadata
# instances.

class Toc (Item):

    format = ObjectTables
    backlinks_class = TocBacklinks

    def __init__ (self, corpus, name, lang):
        Item.__init__(self, corpus, name)
        self._lang = lang

    def langid (self):
        return self._lang.langid()

    def language (self):
        return self._lang

    def text_table (self):
        return self._lang.txt

    def _table (self):
        return self.contents()[0]

    def __getitem__ (self, textid):
        obj = self._table()[textid]
        return TextMetadata(self, obj)

    def get (self, textid):
        obj = self._table().get(textid)
        if obj is not None:
            return TextMetadata(self, obj)

    def __iter__ (self):
        return self._table().__iter__()

    def __len__ (self):
        return self._table().__len__()

    def __bool__ (self):
        return self._table().__bool__()

    def items (self):
        for (textid, obj) in self._table().items():
            yield (textid, TextMetadata(self, obj))
    
    def keys (self):
        return self._table().keys()

    def values (self):
        for obj in self._table().values():
            yield TextMetadata(self, obj)

    def intern (self, textid, **kwargs):
        val = self.get(textid)
        if val is None:
            val = self.new(textid, **kwargs)
        return val

    def new (self, textid, **kwargs):
        obj = OrderedDict([('id', textid)] + list(kwargs.items()))
        self._table()[textid] = obj
        self.modified()
        return TextMetadata(self, obj)

    def __delitem__ (self, textid):
        table = self._table()
        del table[textid]
        self.modified()
        del self.text_table()[textid]

    def _toc_entry (self, obj):
        return (obj.get('id'), obj.get('ty'), obj.get('ti'))

    # for use by Text only
    
    def _parent (self, textid):
        return self.backlinks().parent(textid)

    def __str__ (self):
        table = self._table()
        if table:
            return tabular((self._toc_entry(obj) for obj in table.values()), hlines=False)
        else:
            return '(empty text table)'


class TextTable (object):

    def __init__ (self, toc, lang):
        self._toc = toc
        self._lang = lang

    def toc (self):
        return self._toc
    
    def langid (self):
        return self._lang.langid()

    def language (self):
        return self._lang

    def corpus (self):
        return self._lang.corpus()

    def toc (self):
        return self._lang.toc

    # although 'txt' is not actually an item
    
    def item_name (self):
        return self._lang.item_name() + '/txt'

    def __getitem__ (self, textid):
        return Text(self._lang, self._toc[textid])

    def __iter__ (self):
        return self._toc.__iter__()

    def __len__ (self):
        return self._toc.__len__()

    def keys (self):
        return self._toc.keys()

    def items (self):
        for (textid, metadata) in self._toc.items():
            yield (textid, Text(self._lang, metadata))

    def values (self):
        for (textid, text) in self.items():
            yield text

    def new (self, textid, **kwargs):
        metadata = self.toc().new(textid, **kwargs)
        return Text(self._lang, metadata)

    def intern (self, textid, **kwargs):
        metadata = self.toc().intern(textid, **kwargs)
        return Text(self._lang, metadata)

    def __delitem__ (self, textid):
        self.toc().__delitem__(textid)

    def __repr__ (self):
        return f'<TextTable {self._lang.langid()}>'


#--  read_toc_file, SimpleText  ------------------------------------------------------

##  The constructor is called while building the language's TextList.  Thus the __init__
##  method should not seek to access lang.toc.

class TextMetadata (object):
    
#    FileKeys = {'id', 'ty', 'de', 'au', 'ti', 'or', 'ch', 'no', 'audio'}

    def __init__ (self, toc, props):
        assert isinstance(toc, Toc), 'Not a Toc'
        self._toc = toc
        self._props = props

    def language (self):
        return self._toc.language()

    def corpus (self):
        return self._toc.corpus()

    def textid (self):
        return self._props['id']

    def text (self):
        return self.language().txt[self.textid()]

    def __getitem__ (self, key):
        return self._props[key]

    def get (self, key, default=None):
        return self._props.get(key, default)

    def __iter__ (self):
        return self._props.__iter__()

    def __len__ (self):
        return self._props.__len__()

    def __setitem__ (self, key, value):
        self._props[key] = value
        self._toc.modified()

    def __delitem__ (self, key):
        if key == 'id':
            raise KeyError("The property 'id' is immutable")
        del self._props[key]
        self._toc.modified()

    def __str__ (self):
        return tabular((item for item in self._props.items()),
                       hlines=False)

    def __repr__ (self):
        return f"<TextMetadata {self._toc.langid()} {self.textid()}>"


class Text (Sequence):

    def __init__ (self, lang, metadata):
        self._lang = lang
        self._metadata = metadata

    def language (self):
        return self._lang

    def langid (self):
        return self._lang.langid()

    def toc (self):
        return self._lang.toc

    def text_table (self):
        return self._lang.txt

    def corpus (self):
        return self._lang.corpus()

    def metadata (self):
        return self._metadata

    def parent (self):
        # Value None if there is no parent
        parentid = self._lang.toc._parent(self.textid())
        if parentid is not None:
            return self._lang.txt[parentid]

    def has_children (self):
        return 'ch' in self._metadata

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
        return self.parent() is None

    def is_collection (self):
        return self._metadata.get('ty') == 'collection'

    def is_document_part (self):
        return not self.is_collection()

    def is_document (self):
        if self.is_document_part():
            parent = self.parent()
            return parent is None or parent.is_collection()

    def is_simple_text (self):
        return not (self.is_collection() or self.has_children())

    def is_vocabulary (self):
        return self._metadata.get('ty') == 'vocab'

    def is_running_text (self):
        return self.is_simple_text() and not self.is_vocabulary()

    def get_simple_texts (self):
        for txt in self.walk():
            if txt.is_simple_text():
                yield txt

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self.textid()}>'

    def _list (self):
        return self.children() if self.has_children() else self.sentences()

    def __iter__ (self):
        return self._list().__iter__()

    def __getitem__ (self, i):
        return self._list().__getitem__(i)

    def __len__ (self):
        return self._list().__len__()

    def append (self, *args, **kwargs):
        if self.has_children():
            self._append_child(*args, **kwargs)
        else:
            self.sentences().append(*args, **kwargs)

    def pprint_tree (self):
        meta = self.metadata()
        pprint(meta.get('id'), meta.get('ty'), meta.get('ti'))
        with pprint.indent():
            for child in self.children():
                child.pprint_tree()

#     def __str__ (self):
#         if self.has_children():
#             return repr(self)
#         else:
#             return ''.join(self.sentences().to_lines())

    ## Simple Texts

    def sentences (self):
        return self.corpus().intern(self.item_name(), SentenceList, self)

    def tokens (self):
        for sent in self.sentences():
            for token in sent:
                yield token

    ## Aggregate Texts
    
    def children (self):
        if self.has_children():
            chids = self._metadata['ch'].split()
            txt = self.text_table()
            return [txt.intern(chid) for chid in chids]
        else:
            return []

    def _append_child (self, child):
        raise Exception('Not implemented yet')

#     def _set_children (self, table):
#         if self._children is None:
#             self._children = tuple(table[textid] for textid in self._metadata.get('ch'))
#             for child in self._children:
#                 # note: if multiple documents "claim" the same child, the first one wins
#                 if child._parent is None:
#                     child._parent = self


# class TextList (object):
# 
#     def __init__ (self, lang, texts):
#         texts = list(texts)
# 
#         self._contents = texts
#         self._index = dict((t.name(), t) for t in texts)
# 
#     def __len__ (self):
#         return self._contents.__len__()
# 
#     def __getitem__ (self, i):
#         if isinstance(i, str):
#             return self._index[i]
#         else:
#             return self._contents[i]
# 
#     def __iter__ (self):
#         return self._contents.__iter__()
#     
#     def roots (self):
#         for text in self._contents:
#             if text.parent() is None:
#                 yield text
# 
#     def tokens (self):
#         for text in self._contents:
#             for sent in text.sentences():
#                 for (j, word) in enumerate(sent):
#                     yield (Loc(text.textid(), sent.i(), j), word)
# 
#     @staticmethod
#     def write_tree (f, text, indent):
#         if indent: f.write(' ' * indent)
#         f.write('[')
#         f.write(str(text.textid()))
#         f.write('] ')
#         f.write(text.title() or '(no title)')
#         indent += 2
#         if text.has_children():
#             for child in text.children():
#                 f.write('\n')
#                 TextList.write_tree(f, child, indent)
#         
#     def print_tree (self):
#         roots = self.roots()
#         for root in roots:
#             self.write_tree(sys.stdout, root, 0)
#             print()


# join(self.lang.dirname, 'toc')
# set text.lang


#--  Tokens  -------------------------------------------------------------------

def Token_ (form, sent, lex, loc):
    token = Token(form)
    token._bind(sent, lex, loc)
    return token


class Token (str):

    def _bind (self, sent, lex, loc):
        self._sentence = sent
        self._lexicon = lex
        self._loc = loc

    def sentence (self): return self._sentence
    def sentence_index (self): return self._loc.w() - 1
    def lexicon (self): return self._lexicon
    def loc (self): return self._loc
    def entry (self): return self._lexicon[self]

    ##  Indirect
        
    def form (self): return self
    def formtype (self): return self.entry().formtype()
    def cat (self): return self.entry().cat()
    def gloss (self): return self.entry().gloss()
    def canonical (self): return self.entry().canonical()
    def orthographic (self): return self.entry().orthographic()
    def parts (self): return self.entry().parts()
    def partof (self): return self.entry().partof()
    def variants (self): return self.entry().variants()
    def set (self, **kwargs): self.entry().set(**kwargs)
    def sentences (self, *args, **kwargs): return self.entry().sentences(*args, **kwargs)
    def locations (self, *args, **kwargs): return self.entry().locations(*args, **kwargs)
    def table (self): return self.entry().table()


class Loc (object):

    @staticmethod
    def from_string (s):
        fields = s.split('.')
        assert len(fields) == 3, 'Bad loc'
        return Loc(fields[0], int(fields[1]), int(fields[2]))

    def __init__ (self, t, s, w):
        self._t = t
        self._s = s
        self._w = w

    def t (self): return self._t
    def s (self): return self._s
    def w (self): return self._w

    # for the sake of destructuring bind

    def __iter__ (self):
        yield self._t
        yield self._s
        yield self._w

    # so that we can put them in a set

    def __hash__ (self): return hash((self._t, self._s, self._w))
    def __eq__ (self, other): return (self._t, self._s, self._w) == (other._t, other._s, other._w)

    def __str__ (self):
        return self._t + '.' + str(self._s) + '.' + str(self._w)

    def __repr__ (self):
        return f'<Loc {self.__str__()}>'


#--  Sentence, read_txt_file  --------------------------------------------------

#     def _make_sentence (self, words, i):
#         words = [self.lex.intern(w) for w in words]
#         return Sentence(self.text, i, words)
# 
# join(text.lang.dirname, 'tok', str(text.textid) + '.tok')
#     
# list(Tokfile(self))


# This is the actual contents of a simple text

class SentenceList (Item, Sequence):
    
    format = PLists

    def __init__ (self, disk, name, text):
        Item.__init__(self, disk, name)
        self._text = text

    def text (self): return self._text
    def language (self): return self._text.language()

    def __iter__ (self):
        for (i, obj) in enumerate(self.contents(), 1):
            yield Sentence(self, i, obj)
            
    def __getitem__ (self, i):
        sents = self.contents()
        if i < 0:
            i = len(sents) + i
            if i < 0:
                raise IndexError()
        return Sentence(self, i+1, sents[i])

    def __len__ (self):
        return len(self.contents())

    def _parse_rawsent (self, rawsent, gloss):
        out = []
        if isinstance(rawsent, str):
            out.append(('w', rawsent))
        else:
            for elt in rawsent:
                if isinstance(elt, str):
                    out.append(('w', elt))
                elif isinstance(elt, (float, int)):
                    out.append(('t', str(elt)))
                else:
                    raise Exception(f'Bad element in sentence: {repr(elt)}')
        if gloss is not None:
            assert isinstance(gloss, str), 'Gloss is not a string'
            out.append(('g', gloss))
        return out

    def append (self, rawsent, gloss=None):
        '''rawsent is a string or an iterable containing strings and floats.'''
        sents = self.contents()
        i = len(sents)
        obj = self._parse_rawsent(rawsent, gloss)
        sents.append(obj)
        self.modified()
        
    def modified (self):
        Item.modified(self)
        self.language().clear_index()


class Sentence (ListProxy):

    def __init__ (self, sentences, sno, plist, gloss=None):
        self._sentences = sentences
        self._sno = sno
        self._words = None
        self._timestamps = None
        self._gloss = gloss
        self.__proxyfor__ = None

        self._parse_contents(plist)

    def _loc (self):
        return (self.language().langid(), self.text().textid(), self._sno)

    def __hash__ (self): return hash(self._loc())
    def __eq__ (self, other): return self._loc() == other._loc()

    def _parse_contents (self, plist):
        self._words = []
        self._timestamps = []
        self._gloss = None
        self.__proxyfor__ = self._words

        lex = self.language().lexicon
        textid = self.text().textid()
        sno = self._sno
        i = 0
        for (key, value) in plist:
            if key == 'w':
                for form in value.split():
                    i += 1
                    token = Token_(form, self, lex, Loc(textid, sno, i))
                    self._words.append(token)
            elif key == 't':
                self._timestamps.append((len(self._words), value))
            elif key == 'g':
                self._gloss = value

    def text (self): return self._sentences.text()
    def language (self): return self._sentences.language()
    def sno (self): return self._sno
    def words (self): return self._words
    def timestamps (self): return self._timestamps
    def gloss (self): return self._gloss

    def spans (self, allwords=False):
        if not self._timestamps:
            yield (None, self._words)
        else:
            if allwords:
                i = 0
                (j, end) = self._timestamps[0]
                if i < j:
                    yield (None, end, self._words[i:j])
            for t in range(len(self._timestamps)-1):
                (i, start) = self._timestamps[t]
                (j, end) = self._timestamps[t+1]
                yield (start, end, self._words[i:j])
            if allwords:
                (i, start) = self._timestamps[-1]
                j = len(self._words)
                if i < j:
                    yield (start, None, self._words[i:j])

#     def intern_words (self, lex):
#         words = self.__proxyfor__
#         for i in range(len(words)):
#             w = words[i]
#             if isinstance(w, str):
#                 words[i] = lex.intern(w)

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
        return f"<Sentence {self.text().textid()}.{self._sno} {' '.join(self._words[:5])}{suffix}>"

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

def Lexent_ (lexicon, obj):
    form = obj['id']
    entry = Lexent(form)
    entry._bind(lexicon, obj)
    return entry


class Lexent (str):

    def _bind (self, lexicon, obj):
        self._lexicon = lexicon
        self._obj = obj

        if 'id' not in obj:
            raise Exception(f'No lexid provided: {obj}')
        
    # To make Lexents and Tokens behave alike
    def entry (self): return self

    def form (self): return self
    def formtype (self): return self._obj.get('ty', '')
    def cat (self): return self._obj.get('c', '')
    def gloss (self): return self._obj.get('g', '')
    def canonical (self): return self._obj.get('cf', '')
    def orthographic (self): return self._obj.get('of', '')

    def parts (self):
        lex = self._lexicon
        with lex.modifying():
            return [lex.intern(form) for form in self._obj.get('pp', '').split()]

    def partof (self, closure=True):
        if not closure:
            return set(self._lexicon.backlinks().partof(self))
        else:
            out = set()
            self._partof_recurse(out)
            return out

    def _partof_recurse (self, out):
        out.add(self)
        for parent in self._lexicon.backlinks().partof(self):
            parent._partof_recurse(out)

    def variants (self):
        return self._lexicon.backlinks().variants(self.form())

    def set (self, formtype=None, cat=None, parts=None, gloss=None, canonical=None, orthographic=None):
        obj = self._obj
        mod = False
        if formtype is not None:
            obj['ty'] = formtype
            mod = True
        if cat is not None:
            obj['c'] = cat
            mod = True
        if parts is not None:
            obj['pp'] = ' '.join(part.form() for part in parts)
            mod = True
        if gloss is not None:
            obj['g'] = gloss
            mod = True
        if canonical is not None:
            obj['cf'] = canonical
            mod = True
        if orthographic is not None:
            obj['of'] = orthographic
            mod = True
        if mod:
            self._lexicon.modified()

    def table (self):
        with StringIO() as f:
            first = True
            for (key, value) in self._obj.items():
                if first: first = False
                else: f.write('\n')
                f.write(f'{key:5s}')
                f.write(value)
            return f.getvalue()

    def tokens (self, lang=None, recurse=True):
        if lang is None:
            lang = self._lexicon.language()
        return lang.deref_locs(self.locations(lang, recurse))

    def sentences (self, lang=None, recurse=True):
        return set(token.sentence() for token in self.tokens(lang, recurse))

    def locations (self, lang=None, recurse=True):
        if lang is None:
            lang = self._lexicon.language()
        out = set()
        if recurse:
            for form in self.partof(closure=True):
                out |= lang.index.get(form)
        else:
            out |= lang.index.get(self)
        return out


class LexiconBacklinks (object):

    def __init__ (self, lexicon):
        self._lexicon = lexicon
        self._table = {}
        
        table = self._table
        for (form, obj) in self._lexicon._table().items():

            if 'pp' in obj:
                for part in obj['pp'].split():
                    self._add_backlink(part, 'po', form)

            if 'cf' in obj:
                self._add_backlink(obj['cf'], 'vv', form)

    def _add_backlink (self, form, key, value):
        table = self._table
        if form in table:
            obj = table[form]
        else:
            obj = table[form] = {}
        if key in obj:
            obj[key].append(value)
        else:
            obj[key] = [value]

    def _get_backlinks (self, form, key):
        lex = self._lexicon
        if form in self._table:
            values = self._table[form].get(key)
            if values:
                return [lex[value] for value in values]
        return []

    def partof (self, form):
        return self._get_backlinks(form, 'po')

    def variants (self, textid):
        return self._get_backlinks(form, 'vv')


class Lexicon (Item):

    format = ObjectTables
    backlinks_class = LexiconBacklinks

    def __init__ (self, corpus, name, lang):
        Item.__init__(self, corpus, name)
        self._lang = lang

    def _table (self):
        return self.contents()[0]

    def language (self): return self._lang
    def corpus (self): return self._lang.corpus()

    def __iter__ (self):
        for obj in self._table().values():
            yield Lexent_(self, obj)

    def __len__ (self): return self._table().__len__()

    def __getitem__ (self, form):
        return Lexent_(self, self._table().__getitem__(form))

    def intern (self, form):
        tab = self._table()
        if form in tab:
            obj = tab[form]
        else:
            obj = OrderedDict([('id', form)])
            tab[form] = obj
            self.modified()
        return Lexent_(self, obj)

#     ##  Load  --------------------------
# 
#     def load (self):
#         redirects = []
#         for rec in Records(self._filename + '.lx'):
#             if len(rec) == 2:
#                 redirects.append(rec)
#             else:
#                 self._intern_canonical(rec[0], rec[1], rec[2].split())
#         for (key, canonical) in redirects:
#             self._process_redirect(key, canonical)
#         self._intern_parts()
#         self._load_index()
#         self.compute_frequencies()
# 
#     def _intern_canonical (self, key, gloss, parts):
#         ent = self.intern(key)
#         if ent._gloss or ent._parts:
#             raise Exception('Duplicate key: {}'.format(key))
#         ent._gloss = gloss
#         ent._parts = parts
# 
#     def _process_redirect (self, key, canonical):
#         ent = self.intern(canonical)
#         tab = self._entdict
#         if key in tab:
#             raise Exception('Duplicate key: {}'.format(key))
#         ent._variants.append(key)
#         tab[key] = ent
#         
#     def _intern_parts (self):
#         # the list of entries may grow as we go
#         entries = self._entries
#         n = len(self._entries)
#         for i in range(n):
#             ent = entries[i]
#             ent._parts = [self.intern(p) for p in ent._parts]
#             for part in ent._parts:
#                 part._wholes.append(ent)
# 
#     def _load_index (self):
#         records = Records(self._filename + '.idx')
#         for (key, locs) in records:
#             e = self.intern(key)
#             e._locations.extend(Loc.from_string(s) for s in locs.split(','))
#     
#     ##  Save  --------------------------
# 
#     def save_main (self):
#         with open(self._filename + '.lx', 'w') as f:
#             for (k, v) in sorted(self.items()):
#                 f.write(k)
#                 f.write('\t')
#                 if isinstance(v, Lexent):
#                     f.write(v.gloss())
#                     f.write('\t')
#                     f.write(' '.join(p.key() for p in v.parts()))
#                 else:
#                     f.write(v)
#                 f.write('\n')
# 
#     def save_index (self):
#         with open(self.filename + '.idx', 'w') as f:
#             for ent in self._entries:
#                 if ent.has_locations():
#                     f.write(ent.key())
#                     f.write('\t')
#                     first = True
#                     for loc in ent.locations():
#                         if first: first = False
#                         else: f.write(',')
#                         f.write(str(loc))
#                     f.write('\n')
# 
#     ##  index  -------------------------
# 
#     def generate_index (self):
# 
#         # Clear
#         for ent in self._entdict.values():
#             ent._locations = []
#             ent._freq = None
# 
#         # Regenerate
#         for (loc, ent) in self._lang.tokens():
#             ent._locations.append(loc)
#         self.compute_frequencies()
# 
#         # Save
#         self.save_index()
# 
#     def update (self):
#         self.generate_index()
#         self.save_main()
# 
#     def compute_frequencies (self):
#         for e in self._entries:
#             self._compute_freq(e, [])
# 
#     def _compute_freq (self, ent, callers):
#         if ent.freq() is None:
#             if ent in callers:
#                 raise Exception('Cycle detected: {} -> {}'.format(callers, self))
#             if ent._locations:
#                 ent._freq = len(ent._locations)
#             else:
#                 ent._freq = 0
#             callers.append(ent)
#             if ent._wholes:
#                 for w in ent._wholes:
#                     ent._freq += self._compute_freq(w, callers)
#             callers.pop()
#         return ent._freq


##  The reason for storing Locs instead of Tokens is that we do not
##  want to be forced to load all texts in order to load the index.

class TokenIndex (Item):

    class TokenDicts (Dicts):
        @classmethod
        def parse_value (self, value):
            return set(Loc.from_string(loc) for loc in value.split())
        @classmethod
        def unparse_value (self, value):
            return ' '.join(str(loc) for loc in value)

    format = TokenDicts

    def __init__ (self, corpus, name, lang):
        Item.__init__(self, corpus, name)
        self._lang = lang

    def clear (self):
        lst = self.contents()
        if lst:
            lst.clear()
            self.modified()

    def _rebuild (self):
        if self.debug: print('[REBUILD-INDEX]')
        table = {}
        for txt in self._lang.get_simple_texts():
            for token in txt.tokens():
                if token in table:
                    table[token].add(token.loc())
                else:
                    table[token] = set([token.loc()])
        lst = self.contents()
        if lst: lst.clear()
        lst.append(table)
        self.modified()

    def _table (self):
        lst = self.contents()
        if not lst: self._rebuild()
        return lst[0]

    def __getitem__ (self, form):
        table = self._table()
        return table[form]

    def get (self, form):
        table = self._table()
        if form in table:
            return table[form]
        else:
            return set()

# 
# #--  Concordance  --------------------------------------------------------------
# 
# class Concordance (object):
# 
#     def __init__ (self, lex, ent):
#         if isinstance(ent, str): ent = lex[ent]
# 
#         self._lexicon = lex
#         self._ent = ent
# 
#     def __repr__ (self):
#         lang = self._lexicon.lang
#         with StringIO() as f:
#             for loc in self._ent.all_locations():
#                 (sent, i) = lang.get_location(loc)
#                 s = ' '.join(w.form for w in sent[:i])
#                 t = ' '.join(w.form for w in sent[i:])
#                 print('{:>40}  {:40}'.format(s[-40:], t[:40]), file=f)
#             return f.getvalue()
# 
#     def _display_lexent (self, key):
#         print(key)
# 
#     def _get_rows (self):
#         for loc in self._ent.all_locations():
#             (sent, i) = self._lexicon.language().get_location(loc)
#             yield (sent[i].key,
#                    loc,
#                    ' '.join(w.form for w in sent[:i]),
#                    ' '.join(w.form for w in sent[i+1:]))
# 

# #--  User Config  --------------------------------------------------------------
# 
# class PersistentDict (object):
# 
#     def __init__ (self, f, items=[]):
#         self._file = f
#         self._table = dict(items)
# 
#     def __iter__ (self): return self._table.__iter__()
#     def __len__ (self): return self._table.__len__()
#     def keys (self): return self._table.keys()
#     def values (self): return self._table.values()
#     def items (self): return self._table.items()
#     def __getitem__ (self, key): return self._table.__getitem__(key)
#     def __contains__ (self, key): return self._table.__contains__(key)
# 
#     def __nested__ (self):
#         for (key, value) in self.items():
#             if isinstance(value, str):
#                 yield key + '\t' + value
#             else:
#                 yield key
#                 yield list(value.__nested__())
# 
#     def __setitem__ (self, key, value):
#         self._table.__setitem__(key, value)
#         self._file.save()
# 
#     def __repr__ (self):
#         return '<PersistentDict ' + repr(self._table) + '>'
# 
# 
# class PersistentList (object):
# 
#     def __init__ (self, f, lst=[]):
#         self._file = f
#         self._list = lst
# 
#     def __iter__ (self): return self._list.__iter__()
#     def __len__ (self): return self._list.__len__()
#     def __getitem__ (self, i): return self._list.__getitem__(i)
# 
#     def __setitem__ (self, i, value):
#         self._list.__setitem__(i, value)
#         self._file.save()
# 
#     def __repr__ (self):
#         return '<PersistentList ' + repr(self._list) + '>'
#         
# 
# #--  IGT  ----------------------------------------------------------------------
# 
# def print_igt (sent):
#     for w in sent:
#         print('{:20} {}'.format(w.key(), w.gloss()))
#         if w.has_parts():
#             for p in w.parts():
#                 print('    {:20} {}'.format(p.key(), p.gloss()))
#     print()
#     print(sent.trans)
# 
# 
# #--  CorpusDisk  ---------------------------------------------------------------
# 
# class JsonCorpus (Backend):
# 
#     def __init__ (self, dirname):
#         Backend.__init__(self)
#         self._corpus = Corpus(dirname)
#         
#     def get_lang (self, langid):
#         return self._corpus.language(langid).metadata()
# 
#     def get_langs (self):
#         return {'langs': [lg.metadata() for lg in self._corpus.languages()]}
# 
#     def get_toc (self, lgid, textid=None):
#         lang = self._corpus.language(lgid)
#         if textid is None:
#             return {'toc': [text.metadata() for text in lang.texts()]}
#         else:
#             return lang.text(textid).metadata()


#--  main  ---------------------------------------------------------------------

# def _flag_to_kv (flag):
#     assert flag[0] == '-'
#     i = flag.rfind('=')
#     if i > 1:
#         value = flag[i+1:]
#         key = flag[1:i]
#     else:
#         key = flag[1:]
#         value = True
#     return (key, value)
# 
# def get_corpus (user=None):
#     if user is None:
#         user = User()
#     corpfn = user.props.get('corpus')
#     if not corpfn:
#         raise Exception('No specification for corpus in ~/.cld/props')
#     return Corpus(corpfn)
# 
# def get_defaults (lg=None, textid=None, user=None):
#     if user is None:
#         user = User()
#     if lg is None and textid and '.' in textid:
#         (lg, textid) = textid.split('.')
#     if lg is None:
#         lg = user.props.get('lang')
#         if not lg:
#             raise Exception('No specification for lang in ~/.cld/props')
#     return (user, get_corpus(user), lg, textid)
# 
# 
# class CorpusMain (Main):
#     
#     def com_info (self):
#         user = User()
#         print('default corpus:  ', user.props.get('corpus'))
#         print('default language:', user.props.get('lang'))
# 
#     def com_texts (self, lg=None):
#         (_, corpus, lg, _) = get_defaults(lg)
#         print(corpus.langs[lg].toc)
# 
#     def com_docs (self, lg=None):
#         (_, corpus, lg, _) = get_defaults(lg)
#         print(tabular((doc.toc_entry() for doc in corpus.langs[lg].get_documents()), hlines=False))
# 
#     def com_tree (self, textid=None):
#         (_, corpus, lg, textid) = get_defaults(textid=textid)
#         if textid is None:
#             for text in corpus[lg].get_roots():
#                 text.pprint_tree()
#         else:
#             corpus[lg][textid].pprint_tree()
# 
#     def com_drill (self, lg=None):
#         (user, corpus, lg, _) = get_defaults(lg)
#         drill = Drill(user, corpus, lg)
#         drill()
# 
#     def com_text (self, textid):
#         (_, corpus, lg, textid) = get_defaults(textid=textid)
#         print(corpus[lg][textid])
# 
#     def com_sents (self, textid):
#         (_, corpus, lg, textid) = get_defaults(textid=textid)
#         text = corpus[lg][textid]
#         for sent in text.sents:
#             print(sent)
# 
#     def com_tsents (self, textid):
#         (_, corpus, lg, textid) = get_defaults(textid=textid)
#         text = corpus[lg][textid]
#         first = True
#         for sent in text.sents:
#             if first:
#                 first = False
#             else:
#                 print()
#             print(sent)
#             print(sent.translation())
# 
#     def com_get (self, fn, path):
#         print(JsonCorpus(fn)[path])
# 
#     def com_open (self, fn, nw=False):
#         JsonCorpus(fn).run(nw)
#     
# 
# if __name__ == '__main__':
#     CorpusMain()()
