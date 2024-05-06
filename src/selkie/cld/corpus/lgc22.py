
import time, math, sys
from os import listdir
from os.path import join, exists, expanduser
from io import StringIO
from .com import Shift
from .webserver import Backend


#--  Utilities  ----------------------------------------------------------------

def counts (items):
    tab = {}
    for item in items:
        if item in tab:
            tab[item] += 1
        else:
            tab[item] = 1
    return tab


class Records (object):

    def __init__ (self, fn, strip_comments=False):
        self._filename = fn
        self._lno = None
        self._strip_comments = strip_comments

    def filename (self): return self._filename
    def lno (self): return self._lno

    def __iter__ (self):
        with open(self._filename) as f:
            for (self._lno, line) in enumerate(f, 1):
                line = line.rstrip('\r\n')
                if self._strip_comments and line.startswith('#'):
                    continue
                yield line.split('\t')
            
    def warn (self, *msgs):
        print('**', *msgs, '[{}:{}]'.format(self._filename, self._lno))

    def error (self, *msgs):
        raise Exception('** {} [{}:{}]'.format(' '.join(msgs), self._filename, self._lno))


class RecordGroups (Records):

    def __init__ (self, fn, start=None, strip_comments=False):
        self._records = Records(fn, strip_comments=strip_comments)
        self._filename = self._records.filename()
        self._lno = 0
        self._start = start
        self._group = []

    def _new_group (self):
        self._group = []
        self._lno = self._records.lno()

    def __iter__ (self):
        start = self._start
        if start is None:
            for rec in self._records:
                if rec == ['']:
                    if self._group:
                        yield self._group
                        self._new_group()
                else:
                    self._group.append(rec)
        else:
            for rec in self._records:
                if start(rec):
                    if self._group:
                        yield self._group
                        self._new_group()
                self._group.append(rec)
        if self._group:
            yield self._group


def read_toc_file (fn, cls, slots):
    fn = join(fn, 'toc')
    groups = RecordGroups(fn, strip_comments=True)
    for (i, group) in enumerate(groups):
        if group[0][0] != 'id':
            groups.error('TOC entry must start with id')
        kwargs = {}
        for (k,v) in group:
            if k in slots:
                kwargs[slots[k]] = v
            else:
                groups.error('Unrecognized key:', repr(k))
        yield cls(**kwargs)
    

#--  Corpus, Language  ---------------------------------------------------------

class Corpus (object):
    '''
    The top level object, representing a corpus directory.
    The constructor takes the directory's pathname.

    A corpus consists of a set of languages, represented by
    subdirectories whose names have the form langid.lg.
    '''

    def __init__ (self, dirname):
        self._dirname = dirname
        self._langs = list(read_toc_file(dirname, Language, {'id': 'langid', 'name': 'name'}))
        self._index = dict((lg.langid(), lg) for lg in self._langs)

        for lang in self._langs:
            lang._corpus = self

    def filename (self):
        '''
        Returns the pathname of the corpus directory.
        '''
        return self._dirname

    def languages (self):
        '''Iterates over languages.'''
        return iter(self._langs)

    def __repr__ (self):
        return '<Corpus {}>'.format(self._dirname)

    def language (self, name):
        '''
        Returns the language with the given langid, or None if it does
        not exist.
        '''
        return self._index.get(name)


class Language (object):
    '''
    Represents a language directory.  The language directory contains
    several subdirectories representing different aspects of texts, and
    two files representing the lexicon.
    '''

    def __init__ (self, langid, name):
        self._corpus = None
        self._langid = langid
        self._name = name
        self._lexicon = None
        self._texts = None

    def _load (self):
        dfn = self.filename()
        if not exists(dfn):
            raise Exception(f'File not found: {dfn}')
        self._lexicon = Lexicon(self)
        texts = read_toc_file(dfn, Text, {'id': 'textid',
                                          'ty': 'text_type',
                                          'au': 'author',
                                          'ti': 'title',
                                          'or': 'orthography',
                                          'ch': 'children',
                                          'fn': 'filename',
                                          'no': 'catalog_id'})
        self._texts = TextList(self, texts)

    def corpus (self):
        '''A backlink to the corpus.'''
        return self._corpus
    
    def langid (self):
        '''The language ID.'''
        return self._langid

    def name (self):
        '''Returns the language ID.'''
        return self._name

    def filename (self):
        '''Returns the pathname of the language directory.'''
        return join(self._corpus.filename(), self._langid + '.lg')

    def lexicon (self):
        '''Returns the lexicon.'''
        if self._lexicon is None:
            self._load()
        return self._lexicon

    def texts (self):
        '''Returns the list of texts (type TextList).'''
        if self._texts is None:
            self._load()
        return self._texts
    
    def text (self, i):
        '''Returns the text with the given ID (str) or at the given position (int).'''
        return self.texts()[i]
    
    def tokens (self):
        '''Returns the concatenation of the tokens of all texts.'''
        return self.texts().tokens()

    def get_location (self, loc):
        '''Converts a Loc to a pair (sentence, w) where *w* is a word position.'''
        (s,t,w) = loc
        sent = self.texts()[t][s]
        return (sent, w)

    def drill (self):
        '''Returns a Drill instance.'''
        return Drill(self)

    def metadata (self):
        '''Metadata in JSON form.'''
        return {'langid': self.langid(), 'name': self.name()}

    def __repr__ (self):
        return f'<Language {self._langid} {self._name}>'


def open_language (cname, lname):
    corpus = Corpus(cname + '.lgc')
    lang = corpus.language(lname)
    return lang
    

#--  Lexicon, Lexent, Loc  -----------------------------------------------------

class Lexent (object):

    def __init__ (self, key):
        self._key = key
        self._gloss = ''
        self._parts = []
        self._locations = []
        # automatically generated
        self._form = None
        self._sense = None
        self._variants = []
        self._wholes = []
        self._freq = None

        i = key.rfind('.')
        if i < 0:
            raise Exception('Bad key: {}'.format(key))
        self._form = key[:i]
        self._sense = int(key[i+1:])
        
    def key (self): return self._key
    def gloss (self): return self._gloss
    def parts (self): return iter(self._parts)
    def has_parts (self): return bool(self._parts)
    def locations (self): return iter(self._locations)
    def has_locations (self): return bool(self._locations)
    def form (self): return self._form
    def sense (self): return self._sense
    def variants (self): return iter(self._variants)
    def wholes (self): return iter(self._wholes)
    def freq (self): return self._freq

    def __lt__ (self, other):
        return self._key < other._key

    def __eq__ (self, other):
        return self._key == other._key

    def __repr__ (self):
        return '<Lexent {}>'.format(self._key)

    def pprint (self):
        print(self._key)
        print('  gloss:    ', self._gloss or '')
        print('  parts:    ', self._parts or '')
        print('  part_of:  ', self._part_of)
        print('  variants: ', self._variants)
        print('  freq:     ', '' if self._freq is None else self._freq)
        print('  locations:', self._locations)

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
        self._lang = lang
        self._filename = join(self._lang.filename(), 'lexicon')
        self._entdict = {}
        self._entries = []
        
        self.load()

    def language (self): return self._lang
    def filename (self): return self._filename
    def entdict (self): return self._entdict
    def entries (self): return self._entries

    def __repr__ (self):
        return '<Lexicon {}>'.format(self._lang.name())

    def intern (self, key):
        tab = self._entdict
        if key in tab:
            return tab[key]
        else:
            ent = Lexent(key)
            tab[key] = ent
            self._entries.append(ent)
            return ent

    def __len__ (self):
        return self._entdict.__len__()

    def __getitem__ (self, k):
        return self._entdict.__getitem__(k)

    def keys (self):
        return self._entdict.keys()

    def items (self):
        for (k, v) in self._entdict.items():
            if k == v.key():
                yield (k, v)
            else:
                yield (k, v.key())

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

class Text (object):

    def __init__ (self,
                  textid=None,
                  text_type=None,
                  author=None,
                  title=None,
                  orthography=None,
                  children=None,
                  filename=None,
                  catalog_id=None):
        
        if isinstance(children, str):
            children = children.split(',')
            
        self._textid = textid
        self._catalog_id = catalog_id
        self._lang = None
        self._text_type = text_type
        self._author = author
        self._title = title
        self._orthography = orthography
        self._filename = filename
        self._children = children
        self._parent = None
        self._sents = None

    def name (self): return self._textid
    def catalog_id (self): return self._catalog_id
    def language (self): return self._lang
    def text_type (self): return self._text_type
    def author (self): return self._author
    def title (self): return self._title
    def orthography (self): return self._orthography
    def filename (self): return self._filename
    def children (self): return iter(self._children)
    def has_children (self): return bool(self._children)
    def parent (self): return self._parent
    def sentences (self): return self._sents

    # For use by TextList
    # Replace child names with child Texts
    
    def _intern_children (self, texts):
        if self._children is None:
            self._children = []
        elif self._children and not isinstance(self._children[0], Text):
            self._children = [texts[int(s)] for s in self._children]
            for child in self._children:
                if child._parent:
                    raise Exception('Text with multiple parents: {}'.format(repr(text)))
                child._parent = self

    # For use by TextList
    
    def _set_sentences (self, lang):
        self._lang = lang
        fn = join(lang.filename(), 'txt', str(self._textid) + '.txt')
        if exists(fn):
            self._sents = list(read_txt_file(fn))
            for (i, sent) in enumerate(self._sents):
                sent._text = self
                sent._i = i
                sent.intern_words(lang.lexicon())
        else:
            self._sents = []

    def __str__ (self):
        with StringIO() as s:
            print('Text', self._textid, file=s)
            print('  lang:       ', self._lang or '', file=s)
            print('  text_type:  ', self._text_type or '', file=s)
            print('  author:     ', self._author or '', file=s)
            print('  title:      ', self._title or '', file=s)
            print('  orthography:', self._orthography or '', file=s)
            print('  filename:   ', self._filename or '', file=s)
            print('  children:   ', self._children or '', file=s)
            print('  #sentences: ', 0 if self._sents is None else len(self._sents), file=s, end='')
            return s.getvalue()

    def metadata (self):
        return {'textid': self._textid,
                'text_type': self._text_type,
                'author': self._author,
                'title': self._title,
                'orthography': self._orthography,
                'filename': self._filename,
                'children': [text.name() for text in self._children] if self._children else []}

    def __repr__ (self):
        return '<Text {}>'.format(self._textid)

    def __len__ (self):
        lst = self._sents if self._sents else self._children
        return lst.__len__()

    def __getitem__ (self, i):
        lst = self._sents if self._sents else self._children
        return lst.__getitem__(i)
                    
    def __iter__ (self):
        lst = self._sents if self._sents else self._children
        return lst.__iter__()


class TextList (object):

    def __init__ (self, lang, texts):
        texts = list(texts)

        self._contents = texts
        self._index = dict((t.name(), t) for t in texts)

        for text in texts:
            text._intern_children(texts)
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

class Sentence (object):

    def __init__ (self, text=None, i=None, words=None, trans=None):
        self._text = text
        self._i = i
        self._words = words
        self._trans = trans

    def text (self): return self._text
    def i (self): return self._i
    def words (self): return self._words
    def translation (self): return self._trans

    def intern_words (self, lex):
        words = self._words
        for i in range(len(words)):
            w = words[i]
            if isinstance(w, str):
                words[i] = lex.intern(w)

    def __repr__ (self):
        words = ['<S']
        for w in self._words:
            words.append(' ')
            words.append(w.key() if isinstance(w, Lexent) else repr(w))
        words.append('>')
        return ''.join(words)

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


def standardize_token (s):
    j = len(s)
    i = j-1
    while i > 0 and s[i].isdigit():
        i -= 1
    if 0 < i < j and s[i] == '.':
        return s
    else:
        return s + '.0'

def parse_tokens (s):
    for token in s.split():
        yield standardize_token(token)

def read_txt_file (fn):
    records = Records(fn)
    for rec in records:
        if len(rec) == 1:
            trans = ''
        elif len(rec) == 2:
            trans = rec[1]
        else:
            records.error('Bad record')
        words = list(parse_tokens(rec[0]))
        yield Sentence(words=words, trans=trans)


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


#--  Drill  --------------------------------------------------------------------

class DrillHistory (object):

    def __init__ (self):
        self._filename = expanduser('~/.cld_drill')
        self._results = {}
        self._today = round(time.time() / (24 * 60 * 60))
        
        self._load()

    def _load (self):
        tab = self._results
        if exists(self._filename):
            for (form, d, result) in Records(self._filename):
                d = int(d)
                result = int(result)
                if form in tab:
                    tab[form].append((d, result))
                else:
                    tab[form] = [(d, result)]

    def __getitem__ (self, form):
        return self._results.get(form, [])

    def store (self, form, result):
        tab = self._results
        if form in tab:
            tab[form].append((self._today, result))
        else:
            tab[form] = [(self._today, result)]
        with open(self._filename, 'a') as f:
            f.write(form)
            f.write('\t')
            f.write(str(self._today))
            f.write('\t')
            f.write(str(result))
            f.write('\n')


def logistic (x):
    return 1/(1 + math.exp(-x))


class Drill (object):

    def __init__ (self, lang):
        self._lang = lang
        self._history = DrillHistory()
        self._items = self._sorted_items()
        self._i = -1

    def __repr__ (self):
        return '<Drill {}>'.format(self._lang.name())

    def __iter__ (self):
        return self
    
    def __next__ (self):
        self._i += 1
        if self._i >= len(self._items):
            self._items = self._sorted_items()
            self._i = 0
        return self._items[self._i]

    # priority at 0 should mean 50/50 chance of getting it right
    # base priority: prop to freq, inv prop to len
    # decay rate decreases when you get it right, increases when wrong
    # priority is prop to log number of days since last tested times decay rate
    #
    # (freq/len) * 1-logistic(days-since-got-it-right/total-right)

    def age (self, ent):
        h = self._history[ent.form()]
        right = [d for (d,r) in h if r == 1]
        if right:
            dpp = 2 ** len(right)                     # days per period
            d = (self._history._today - right[-1])
            p = d/dpp  # periods
            z = (-1 + p) * 3
            mult = logistic(z)
        else:
            d = None
            mult = 1
        return (d, mult)
        
    def priority (self, ent):
        (_, mult) = self.age(ent)
        return (ent.freq() / len(ent.form())) * mult

    def _sorted_items (self):
        lex = self._lang.lexicon()
        items = [e for e in lex.entries() if e.gloss()]
        items.sort(key=self.priority, reverse=True)
        return items

    def ans (self, gloss):
        ent = self._items[self._i]
        tgts = [s.strip() for s in ent.gloss().replace(';', ',').split(',')]
        result = int(gloss in tgts)
        self._history.store(ent.form(), result)
        return (result, ent.gloss())

    def pprint (self):
        print('{:20} {:20} {:3} {:4} {:5} {:}'.format('form', 'gloss', 'fr', 'age', 'm', 'pri'))
        for ent in self._items:
            (age, mult) = self.age(ent)
            if age is None:
                age = '-'
            print('{:20} {:20} {:3} {:>4} {:5.3f} {:.3f}'.format(
                ent.form()[:20], ent.gloss()[:20], ent.freq(), age, mult,
                (ent.freq() / len(ent.form())) * mult))

import readline

def com_drill (lg):
    corp = Corpus('.')
    lang = corp.get_language(lg)
    drill = Drill(lang)
    for ent in drill:
        reply = input(ent.form() + ': ')
        (result, gloss) = drill.ans(reply)
        print('Yes' if result == 1 else 'No ', gloss)


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


def com_get (fn, path):
    print(JsonCorpus(fn)[path])

def com_open (fn, nw=False):
    JsonCorpus(fn).run(nw)
    

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

def main ():

    coms = {'drill': (com_drill, 2),
            'open': (com_open, 1),
            'get': (com_get, 2)}

    with Shift() as shift:
        com = shift()
        if com not in coms:
            print('** Unrecognized command', com)
            sys.exit(1)
        (fnc, nargs) = coms[com]
        flags = []
        while shift.isflag():
            flags.append(shift())
        kwargs = dict(_flag_to_kv(f) for f in flags)
        args = [shift() for _ in range(nargs)]
        shift.done()
        fnc(*args, **kwargs)


if __name__ == '__main__':
    main()
