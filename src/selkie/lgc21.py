
import time, math, sys
from os.path import join, exists, expanduser
from os import listdir
from io import StringIO
from .com import Shift


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
        self.filename = fn
        self.lno = None
        self.strip_comments = strip_comments

    def __iter__ (self):
        with open(self.filename) as f:
            for (self.lno, line) in enumerate(f, 1):
                line = line.rstrip('\r\n')
                if self.strip_comments and line.startswith('#'):
                    continue
                yield line.split('\t')
            
    def warn (self, *msgs):
        print('**', *msgs, '[{}:{}]'.format(self.filename, self.lno))

    def error (self, *msgs):
        raise Exception('** {} [{}:{}]'.format(' '.join(msgs), self.filename, self.lno))


class RecordGroups (Records):

    def __init__ (self, fn, start=None, strip_comments=False):
        self.records = Records(fn, strip_comments=strip_comments)
        self.filename = self.records.filename
        self.lno = 0
        self.start = start
        self.group = []

    def _new_group (self):
        self.group = []
        self.lno = self.records.lno

    def __iter__ (self):
        start = self.start
        if start is None:
            for rec in self.records:
                if rec == ['']:
                    if self.group:
                        yield self.group
                        self._new_group()
                else:
                    self.group.append(rec)
        else:
            for rec in self.records:
                if start(rec):
                    if self.group:
                        yield self.group
                        self._new_group()
                self.group.append(rec)
        if self.group:
            yield self.group


#--  Corpus, Language  ---------------------------------------------------------

class Corpus (object):

    def __init__ (self, dirname):
        self.dirname = dirname
        self._langs = {}

    def __repr__ (self):
        return '<Corpus {}>'.format(self.dirname)

    def language (self, name):
        if name in self._langs:
            return self._langs[name]
        fn = join(self.dirname, name + '.lg')
        if not exists(fn):
            raise Exception('No such language: {}'.format(name))
        lang = Language(self, name)
        lang.lexicon = Lexicon(lang)
        lang.texts = TextList(lang, read_toc_file(join(fn, 'toc')))
        self._langs[name] = lang
        return lang


class Language (object):

    def __init__ (self, corpus, name):
        self.corpus = corpus
        self.name = name
        self.dirname = join(corpus.dirname, name + '.lg')
        self.lexicon = None
        self.texts = None

    def tokens (self):
        return self.texts.tokens()

    def get_location (self, loc):
        sent = self.texts[loc.t][loc.s]
        return (sent, loc.w)

    def drill (self):
        return Drill(self)

    def __repr__ (self):
        return '<Language {}>'.format(self.name)


def open_language (cname, lname):
    corpus = Corpus(cname + '.lgc')
    lang = corpus.language(lname)
    return lang
    

#--  Lexicon, Lexent, Loc  -----------------------------------------------------

class Lexent (object):

    def __init__ (self, key):
        self.key = key
        self.gloss = ''
        self.parts = []
        self.locations = []
        # automatically generated
        self.form = None
        self.sense = None
        self.variants = []
        self.part_of = []
        self.freq = None

        i = key.rfind('.')
        if i < 0:
            raise Exception('Bad key: {}'.format(key))
        self.form = key[:i]
        self.sense = int(key[i+1:])
        
    def __lt__ (self, other):
        return self.key < other.key

    def __eq__ (self, other):
        return self.key == other.key

    def __repr__ (self):
        return '<Lexent {}>'.format(self.key)

    def pprint (self):
        print(self.key)
        print('  gloss:    ', self.gloss or '')
        print('  parts:    ', self.parts or '')
        print('  part_of:  ', self.part_of)
        print('  variants: ', self.variants)
        print('  freq:     ', '' if self.freq is None else self.freq)
        print('  locations:', self.locations)

    def all_locations (self):
        for loc in self.locations:
            yield loc
        for w in self.part_of:
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
        self.t = t
        self.s = s
        self.w = w

    def __str__ (self):
        s = str(self.t) + '.' + str(self.s)
        if self.w is not None:
            s += '.' + str(self.w)
        return s

    def __repr__ (self):
        return '<Loc {}.{}.{}>'.format(self.t, self.s, '' if self.w is None else self.w)


class Lexicon (object):

    def __init__ (self, lang):
        self.lang = lang
        self.filename = join(self.lang.dirname, 'lexicon')
        self.entdict = {}
        self.entries = []
        
        self.load()

    def __repr__ (self):
        return '<Lexicon {}>'.format(self.lang.name)

    def intern (self, key):
        tab = self.entdict
        if key in tab:
            return tab[key]
        else:
            ent = Lexent(key)
            tab[key] = ent
            self.entries.append(ent)
            return ent

    def __len__ (self):
        return self.entdict.__len__()

    def __getitem__ (self, k):
        return self.entdict.__getitem__(k)

    def keys (self):
        return self.entdict.keys()

    def items (self):
        for (k, v) in self.entdict.items():
            if k == v.key:
                yield (k, v)
            else:
                yield (k, v.key)

    ##  Load  --------------------------

    def load (self):
        redirects = []
        for rec in Records(self.filename + '.lx'):
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
        if ent.gloss or ent.parts:
            raise Exception('Duplicate key: {}'.format(key))
        ent.gloss = gloss
        ent.parts = parts

    def _process_redirect (self, key, canonical):
        ent = self.intern(canonical)
        tab = self.entdict
        if key in tab:
            raise Exception('Duplicate key: {}'.format(key))
        ent.variants.append(key)
        tab[key] = ent
        
    def _intern_parts (self):
        # the list of entries may grow as we go
        entries = self.entries
        n = len(self.entries)
        for i in range(n):
            ent = entries[i]
            ent.parts = [self.intern(p) for p in ent.parts]
            for part in ent.parts:
                part.part_of.append(ent)

    def _load_index (self):
        records = Records(self.filename + '.idx')
        for (key, locs) in records:
            e = self.intern(key)
            e.locations.extend(Loc.from_string(s) for s in locs.split(','))
    
    ##  Save  --------------------------

    def save_main (self):
        with open(self.filename + '.lx', 'w') as f:
            for (k, v) in sorted(self.items()):
                f.write(k)
                f.write('\t')
                if isinstance(v, Lexent):
                    f.write(v.gloss)
                    f.write('\t')
                    f.write(' '.join(p.key for p in v.parts))
                else:
                    f.write(v)
                f.write('\n')

    def save_index (self):
        with open(self.filename + '.idx', 'w') as f:
            for ent in self.entries:
                if ent.locations:
                    f.write(ent.key)
                    f.write('\t')
                    first = True
                    for loc in ent.locations:
                        if first: first = False
                        else: f.write(',')
                        f.write(str(loc))
                    f.write('\n')

    ##  index  -------------------------

    def generate_index (self):

        # Clear
        for ent in self.entdict.values():
            ent.locations = []
            ent.freq = None

        # Regenerate
        for (loc, ent) in self.lang.tokens():
            ent.locations.append(loc)
        self.compute_frequencies()

        # Save
        self.save_index()

    def update (self):
        self.generate_index()
        self.save_main()

    def compute_frequencies (self):
        for e in self.entries:
            self._compute_freq(e, [])

    def _compute_freq (self, ent, callers):
        if ent.freq is None:
            if ent in callers:
                raise Exception('Cycle detected: {} -> {}'.format(callers, self))
            if ent.locations:
                ent.freq = len(ent.locations)
            else:
                ent.freq = 0
            callers.append(ent)
            if ent.part_of:
                for w in ent.part_of:
                    ent.freq += self._compute_freq(w, callers)
            callers.pop()
        return ent.freq

    #  concordance  --------------------

    def concordance (self, ent):
        return Concordance(self, ent)


#--  read_toc_file, Text  ------------------------------------------------------

class Text (object):

    def __init__ (self, textid):
        self.textid = textid
        self.lang = None
        self.text_type = None
        self.author = None
        self.title = None
        self.orthography = None
        self.filename = None
        self.children = None
        self.parent = None
        self.sents = None

    def intern_children (self, texts):
        if self.children is None:
            self.children = []
        elif self.children and not isinstance(self.children[0], Text):
            self.children = [texts[int(s)] for s in self.children]
            for child in self.children:
                if child.parent:
                    raise Exception('Text with multiple parents: {}'.format(repr(text)))
                child.parent = self

    def set_sents (self, lang):
        self.lang = lang
        fn = join(lang.dirname, 'txt', str(self.textid) + '.txt')
        if exists(fn):
            self.sents = list(read_txt_file(fn))
            for (i, sent) in enumerate(self.sents):
                sent.text = self
                sent.i = i
                sent.intern_words(lang.lexicon)
        else:
            self.sents = []

    def pprint (self):
        print('Text', self.textid)
        print('  lang:       ', self.lang or '')
        print('  text_type:  ', self.text_type or '')
        print('  author:     ', self.author or '')
        print('  title:      ', self.title or '')
        print('  orthography:', self.orthography or '')
        print('  filename:   ', self.filename or '')
        print('  children:   ', self.children or '')

    def __repr__ (self):
        return '<Text {}>'.format(self.textid)

    def __len__ (self):
        lst = self.sents if self.sents else self.children
        return lst.__len__()

    def __getitem__ (self, i):
        lst = self.sents if self.sents else self.children
        return lst.__getitem__(i)
                    
    def __iter__ (self):
        lst = self.sents if self.sents else self.children
        return lst.__iter__()


def read_toc_file (fn):
    groups = RecordGroups(fn, strip_comments=True)
    for (i, group) in enumerate(groups):
        if group[0][0] != 'id':
            groups.error('TOC entry must start with id')
        textid = int(group[0][1])
        if textid != i:
            groups.error('Bad text ID', textid, 'expected', i)
        text = Text(textid)
        for (k,v) in group[1:]:
            if k == 'ty': text.text_type = v
            elif k == 'au': text.author = v
            elif k == 'ti': text.title = v
            elif k == 'or': text.orthography = v
            elif k == 'ch': text.children = v.split(',')
            elif k == 'fn': text.filename = v
            elif k == 'no': text.catalog_id = v
            else:
                groups.error('Unrecognized key:', repr(k))
        yield text
    

class TextList (object):

    def __init__ (self, lang, texts):
        texts = list(texts)

        self._contents = texts

        for text in texts:
            text.intern_children(texts)
            text.set_sents(lang)

    def __len__ (self):
        return self._contents.__len__()

    def __getitem__ (self, i):
        return self._contents[i]

    def __iter__ (self):
        return self._contents.__iter__()
    
    def roots (self):
        for text in self._contents:
            if text.parent is None:
                yield text

    def tokens (self):
        for text in self._contents:
            for sent in text.sents:
                for (j, word) in enumerate(sent):
                    yield (Loc(text.textid, sent.i, j), word)

    @staticmethod
    def write_tree (f, text, indent):
        if indent: f.write(' ' * indent)
        f.write('[')
        f.write(str(text.textid))
        f.write('] ')
        f.write(text.title or '(no title)')
        indent += 2
        if text.children:
            for child in text.children:
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
        self.text = text
        self.i = i
        self._words = words
        self.trans = trans

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
            words.append(w.key if isinstance(w, Lexent) else repr(w))
        words.append('>')
        return ''.join(words)

    def pprint (self):
        print('Sentence', self.text.textid if self.text else '(no text)', self.i)
        for (i, word) in enumerate(self._words):
            print(' ', i, word)

    def __len__ (self):
        return self._words.__len__()
    
    def __getitem__ (self, i):
        return self._words.__getitem__(i)

    def __iter__ (self):
        return self._words.__iter__()


def parse_tokens (s):
    for token in s.split():
        fields = token.split('\x1f') # unit separator
        if len(fields) == 1:
            yield fields[0] + '.0'
        elif len(fields) == 2:
            yield fields[0] + '.' + fields[1]
        else:
            raise Exception('Bad token: {}'.format(token))

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

        self.lexicon = lex
        self.ent = ent

    def __repr__ (self):
        lang = self.lexicon.lang
        with StringIO() as f:
            for loc in self.ent.all_locations():
                (sent, i) = lang.get_location(loc)
                s = ' '.join(w.form for w in sent[:i])
                t = ' '.join(w.form for w in sent[i:])
                print('{:>40}  {:40}'.format(s[-40:], t[:40]), file=f)
            return f.getvalue()

    def _display_lexent (self, key):
        print(key)

    def _get_rows (self):
        for loc in self.ent.all_locations():
            (sent, i) = self.lexicon.lang.get_location(loc)
            yield (sent[i].key,
                   loc,
                   ' '.join(w.form for w in sent[:i]),
                   ' '.join(w.form for w in sent[i+1:]))


#--  Drill  --------------------------------------------------------------------

class DrillHistory (object):

    def __init__ (self):
        self.filename = expanduser('~/.cld_drill')
        self.results = {}
        self.today = round(time.time() / (24 * 60 * 60))
        
        self._load()

    def _load (self):
        tab = self.results
        if exists(self.filename):
            for (form, d, result) in Records(self.filename):
                d = int(d)
                result = int(result)
                if form in tab:
                    tab[form].append((d, result))
                else:
                    tab[form] = [(d, result)]

    def __getitem__ (self, form):
        return self.results.get(form, [])

    def store (self, form, result):
        tab = self.results
        if form in tab:
            tab[form].append((self.today, result))
        else:
            tab[form] = [(self.today, result)]
        with open(self.filename, 'a') as f:
            f.write(form)
            f.write('\t')
            f.write(str(self.today))
            f.write('\t')
            f.write(str(result))
            f.write('\n')


def logistic (x):
    return 1/(1 + math.exp(-x))


class Drill (object):

    def __init__ (self, lang):
        self.lang = lang
        self.history = DrillHistory()
        self.items = self._sorted_items()
        self.i = -1

    def __repr__ (self):
        return '<Drill {}>'.format(self.lang.name)

    def __iter__ (self):
        return self
    
    def __next__ (self):
        self.i += 1
        if self.i >= len(self.items):
            self.items = self._sorted_items()
            self.i = 0
        return self.items[self.i]

    # priority at 0 should mean 50/50 chance of getting it right
    # base priority: prop to freq, inv prop to len
    # decay rate decreases when you get it right, increases when wrong
    # priority is prop to log number of days since last tested times decay rate
    #
    # (freq/len) * 1-logistic(days-since-got-it-right/total-right)

    def age (self, ent):
        h = self.history[ent.form]
        right = [d for (d,r) in h if r == 1]
        if right:
            dpp = 2 ** len(right)                     # days per period
            d = (self.history.today - right[-1])
            p = d/dpp  # periods
            z = (-1 + p) * 3
            mult = logistic(z)
        else:
            d = None
            mult = 1
        return (d, mult)
        
    def priority (self, ent):
        (_, mult) = self.age(ent)
        return (ent.freq / len(ent.form)) * mult

    def _sorted_items (self):
        lex = self.lang.lexicon
        items = [e for e in lex.entries if e.gloss]
        items.sort(key=self.priority, reverse=True)
        return items

    def ans (self, gloss):
        ent = self.items[self.i]
        tgts = [s.strip() for s in ent.gloss.replace(';', ',').split(',')]
        result = int(gloss in tgts)
        self.history.store(ent.form, result)
        return (result, ent.gloss)

    def pprint (self):
        print('{:20} {:20} {:3} {:4} {:5} {:}'.format('form', 'gloss', 'fr', 'age', 'm', 'pri'))
        for ent in self.items:
            (age, mult) = self.age(ent)
            if age is None:
                age = '-'
            print('{:20} {:20} {:3} {:>4} {:5.3f} {:.3f}'.format(
                ent.form[:20], ent.gloss[:20], ent.freq, age, mult,
                (ent.freq / len(ent.form)) * mult))

import readline

def com_drill (lg):
    corp = Corpus('.')
    lang = corp.get_language(lg)
    drill = Drill(lang)
    for ent in drill:
        reply = input(ent.form + ': ')
        (result, gloss) = drill.ans(reply)
        print('Yes' if result == 1 else 'No ', gloss)


#--  IGT  ----------------------------------------------------------------------

def print_igt (sent):
    for w in sent:
        print('{:20} {}'.format(w.key, w.gloss))
        if w.parts:
            for p in w.parts:
                print('    {:20} {}'.format(p.key, p.gloss))
    print()
    print(sent.trans)


#--  Save as  ------------------------------------------------------------------

def save_as_json (corpus, outfn):
    langs = [name[:-3] for name in listdir(corpus.dirname) if name.endswith('.lg')]
    for lang in langs:
        lang = corpus.language(lang)
        

#--  main  ---------------------------------------------------------------------

def main ():
    with Shift() as shift:
        com = shift()
        if com == 'drill':
            lg = shift()
            shift.done()
            com_drill(lg)
        else:
            shift.error('Unrecognized command')


if __name__ == '__main__':
    main()
