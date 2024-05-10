
import bz2, re, sys, pickle
from os import makedirs
from os.path import expanduser, exists, isdir, join, dirname
from urllib.request import urlopen
from io import StringIO
from bs4 import BeautifulSoup
from ..pyx.xml import lines_to_items
from ..pyx.com import Main, Progress
#from ..pyx.newio import Simples


#==  WiktDump  =================================================================

class WiktDump (object):

    # An estimate based on last time
    N_ARTICLES = 8073918

    def __init__ (self, dump_fn):
        if not dump_fn.endswith('-pages-articles.xml.bz2'):
            raise Exception("Expecting filename to end with '-pages-articles.xml.bz2'")

        self.dump_fn = expanduser(dump_fn)
        self.prefix = self.dump_fn[-23:]    # drop -pages-articles.xml.bz2
        self.parse = Parser()

    # The function lines_to_items takes an iteration over lines (i.e., a stream)
    # and returns an iteration over key-value pairs.  At each iteration step, it
    # reads as many lines as necessary to complete an XML element, and then it
    # converts the element into a key-value pair in which the key is the
    # element's category and the value is a dict formed from the key-value pairs
    # of the children.  An error is signalled if two children have the same
    # category.

    # articles() returns an iteration over dicts.

    def raw_articles (self):
        with bz2.open(self.dump_fn, mode='rt', encoding='utf8') as f:
            line1 = next(f)
            if not line1.startswith('<mediawiki xmlns='):
                raise Exception('Expecting the first line to be <mediawiki ...>')
            elt1 = read_element(f)
            if not (elt1 and elt1[0] == '<siteinfo>'):
                raise Exception('Expecting <siteinfo>')
            for (key, value) in lines_to_items(f):
                if key != 'page':
                    print("** Expecting 'page'", key, value)
                else:
                    yield value

    def articles (self):
        for art in self.raw_articles():
            yield WiktArticle(self, art)

    def find (self, title):
        for art in self.articles():
            if art.title == title:
                return art

    # Extract all language names and write them to enwiktionary-languages.txt

    def extract_language_names (self, tgtfn):
        print('Writing to', tgtfn)
        sys.stdout.flush()
        langs = set()
        with open(tgtfn, 'w') as f:
            with Progress() as prog:
                for art in self.articles():
                    if ':' not in art.title:
                        for entry in art.entries():
                            if entry.lang not in langs:
                                f.write(key)
                                f.write('\n')
                                langs.add(key)
                    prog += 1

    def extract_dicts (self, tgtlangs_fn, tgtdir):
        print('Writing to', tgtdir)
        sys.stdout.flush()
        with open(expanduser(tgtlangs_fn)) as f:
            tgtlangs = set(line.strip() for line in f)
        makedirs(tgtdir)
        with Progress(self.N_ARTICLES) as prog:
            for art in self.articles():
                for entry in art.entries():
                    if entry.lang in tgtlangs:
                        lf = LanguageFile(join(tgtdir, entry.lang))
                        lf.append(entry)
                prog += 1


class WiktArticle (object):
    
    # the wiktionary page text (in markdown) is a #CDATA leaf in the XML tree
    # It is (always?) at art['revision']['text']

    def __init__ (self, wikt, xmldict):
        self.wikt = wikt
        self.orig = xmldict
        self.title = xmldict.get('title', '')
        self.markdown = ''
        self._parsed = None

        if 'revision' in xmldict:
            self.markdown = xmldict['revision'].get('text', '')

    def parsed (self):
        if self._parsed is None:
            self._parsed = ParsedArticle(self)
        return self._parsed

    def entries (self):
        return self.parsed().entries()


class ParsedArticle (object):

    def __init__ (self, orig):
        self.orig = orig
        self.items = orig.wikt.parse(orig.markdown)
        
    def entries (self):
        if ':' not in self.orig.title:
            for (lang, items) in self.items:
                if not lang.startswith('__'):
                    yield Entry(self.orig.title, lang, items)
                    

class Entry (object):

    @staticmethod
    def to_simple (entry):
        if isinstance(entry, Entry):
            return {'lang': entry.lang,
                    'word': entry.word,
                    'items': Entry.to_simple(entry.items)}
        elif isinstance(entry, Markdown):
            return {'lines': entry.lines}
        elif isinstance(entry, list):
            return [Entry.to_simple(elt) for elt in entry]
        elif isinstance(entry, tuple) and len(entry) == 2 and isinstance(entry[0], str):
            return (entry[0], Entry.to_simple(entry[1]))
        else:
            raise Exception(f'Unexpected type of object: {repr(entry)}')

    @staticmethod
    def from_simple (x):
        if isinstance(x, dict):
            if 'word' in x:
                return Entry(x['word'],
                             x['lang'],
                             [(k, Entry.from_simple(v)) for (k,v) in x['items']])
            else:
                return Markdown(x['lines'])
        elif isinstance(x, list):
            return [Entry.from_simple(elt) for elt in x]
        elif isinstance(x, tuple):
            return (x[0], Entry.from_simple(x[1]))

    def __init__ (self, word, lang, items):
        self.word = word
        self.lang = lang
        self.items = items


class LanguageFile (object):

    def __init__ (self, fn):
        self.filename = fn

    def append (self, entry):
        Simples(self.filename).append([Entry.to_simple(entry)])

    def load (self):
        return [Entry.from_simple(s) for s in Simples(self.filename)]


#==  Parsing  ==================================================================

def strict_dict (items):
    d = {}
    for (key, value) in items:
        if key in d:
            raise Exception(f'Duplicate key: {key}')
        d[key] = value
    return d

def flexible_dict (items):
    d = {}
    for (key, value) in items:
        if key in d:
            old = d[key]
            if isinstance(old, list):
                old.append(value)
            else:
                d[key] = [old, value]
        else:
            d[key] = value
    return d


class Parser (object):

    TEXT = 9999

    def __init__ (self):
        self.lines = None

    # If this looks like a header, returns its level
    #  - Looks like a header if it begins and ends with the same non-zero
    #    number of '='s
    #  - Level is number of '='s
    # If it doesn't look like a header, return TEXT

    def parse_header (self, line):
        line = line.strip()
        i = 0
        while i < len(line) and line[i] == '=':
            i += 1
        j = 0
        while j < len(line) and line[-j-1] == '=':
            j += 1
        if i > 0 and i == j:
            return ('header', i, line[i:-j].strip())

    def parse_line (self, line):
        return self.parse_header(line) or ('data', line)

    # Split the text at headings of the given level.
    # Returns a list of pairs (header, lines).
    # First pair header is .

    def __call__ (self, raw):
        lines = [self.parse_line(line) for line in raw.split('\n')]
        return list(self.tops(lines))

    def tops (self, lines):
        for (header, items) in self.recursive_split(lines, 1):
            if header != '__pre__':
                yield ('__H1__', header)
            if isinstance(items, Markdown):
                yield ('__md__', items)
            else:
                for item in items:
                    if isinstance(item, Markdown):
                        yield ('__md__', item)
                    else:
                        yield item

    def recursive_split (self, lines, level):
        for (header, body) in self.split_at_level(lines, level):
            if any(line[0] == 'header' for line in body):
                body = list(self.recursive_split(body, level+1))
            else:
                body = Markdown([line[1] for line in body])
            yield (header, body)

    def split_at_level (self, lines, level):
        i = 0
        while i < len(lines):
            header = '__pre__'
            if lines[i][0] == 'header' and lines[i][1] <= level:
                header = lines[i][2]
                i += 1
            j = i
            while j < len(lines) and not (lines[j][0] == 'header' and lines[j][1] <= level):
                j += 1
            assert i <= j
            yield (header, lines[i:j])
            i = j


class Markdown (object):

    def __init__ (self, lines):
        self.lines = lines
        
    def __str__ (self):
        return '\n'.join(self.lines)


#==  Extraction  ===============================================================

#--  Functions  ----------------------------------------------------------------

def indentation (line):
    '''Returns the number of leading whitespace characters'''
    for (i, c) in enumerate(line):
        if not c.isspace():
            return i
    return len(line)

# Not used

def skip_to_end (tag, f):
    '''Reads and discards lines up to and including </TAG>'''
    endtag = '</' + tag
    for line in f:
        line = line.strip()
        if line.startswith(endtag):
            break

def _read_element (f):
    '''The next line must be a start tag.  Yields lines up to and including the matching end tag.'''
    line = next(f)
    line = line.strip()
    if not (line.startswith('<') and line.endswith('>')):
        raise Exception('Not the beginning of an element')
    tag = line[1:-1]
    endtag = '</' + tag + '>'
    yield line
    for line in f:
        line = line.strip()
        yield line
        if line.startswith(endtag):
            break

def read_element (f):
    '''The next line must be a start tag.  Returns list of lines up to and including the matching end tag.'''
    return list(_read_element(f))

def print_keys (dump_fn, n=None):
    '''Print the keys encountered in the articles and in their 'revision' subdicts.'''
    topkeys = set()
    revkeys = set()
    for (i, art) in enumerate(articles(dump_fn)):
        if n and i >= n:
            break
        for key in art:
            if key not in topkeys:
                print('top', repr(key))
                topkeys.add(key)
        if 'revision' in art:
            for revkey in art['revision']:
                if revkey not in revkeys:
                    print('revision', repr(revkey))
                    revkeys.add(revkey)
        else:
            print('Warning: article without revision')

# Called by Unpacker.entry_texts

def texts (dump_fn):
    '''Iteration over (title, text) pairs.'''
    for art in articles(dump_fn):
        yield extract_text(art)

# Articles have the keys:  __type__, title, ns, id, revision, redirect
# Revisions have the keys: id, parentid, timestamp, contributor, minor, comment, model, format, sha1, text

def articles (dump_fn):
    '''Returns an iteration over dicts (from XML elements).  Key __type__ is added, value is toplevel tag.'''
    with bz2.open(expanduser(dump_fn), mode='rt', encoding='utf8') as f:
        line1 = next(f)
        if not line1.startswith('<mediawiki xmlns='):
            raise Exception('Expecting the first line to be <mediawiki ...>')
        elt1 = read_element(f)
        if not (elt1 and elt1[0] == '<siteinfo>'):
            raise Exception('Expecting <siteinfo>')
        try:
            for (typ, table) in lines_to_items(f):
                if '__type__' in table:
                    raise Exception("Not expecting '__type__' in page")
                table['__type__'] = typ
                yield table
        except Exception as e:
            print('Warning: lines_to_items terminated with exception', e)

def extract_text (tab):
    '''Take the title from the toplevel dict and the text from the 'revision' subdict.  Return (title, text).'''
    title = tab.get('title', '')
    text = ''
    if 'revision' in tab:
        text = tab['revision'].get('text', '')
    return (title, text)

def entry_texts (dump_fn):
    '''Iteration over (title, text) pairs, omitting articles whose title contains a colon.'''
    for (title, text) in texts(dump_fn):
        if ':' in title:
            print('Skipping', title)
        else:
            yield (title, text)

def header_level (line):
    '''The number of '='s at beginning and end of the line.  9999 if none or unequal.'''
    i = 0
    while i < len(line) and line[i] == '=':
        i += 1
    j = 0
    while j < len(line) and line[-j-1] == '=':
        j += 1
    if i > 0 and i == j:
        return i
    else:
        return 9999

# Called by Unpacker.unpack_text

def parse_text (text):
    '''Split the text at headings of the given level.  Returns list of pairs (header, lines).  First pair header is ''.'''
    lines = text.split('\n')
    return _parse_text(lines, 0, len(lines), 2)

def _parse_text (lines, i, j, level):
    key = '__top__'
    items = []
    recurse = False
    for k in range(i, j):
        line = lines[k].strip()
        n = header_level(line)
        if n <= level:
            if recurse:
                value = _parse_text(lines, i, k-1, level+1)
            else:
                value = lines[i:k-1]
            items.append((key, value))
            key = line[n:-n]
            i = k+1
            recurse = False
        elif n < 9999:
            recurse = True
    if recurse:
        value = _parse_text(lines, i, j, level+1)
    else:
        value = lines[i:j]
    items.append((key, value))
    if len(items) == 1:
        return items[0][1]
    else:
        return dict(items)

def write_object (x, f):
    if isinstance(x, str):
        f.write('|')
        f.write(x)
        f.write('\n')
    elif isinstance(x, list):
        f.write('[\n')
        for elt in x:
            write_object(elt, f)
        f.write(']\n')
    elif isinstance(x, dict):
        f.write('{\n')
        for (key, value) in x.items():
            f.write('k')
            f.write(key)
            f.write('\n')
            write_object(value, f)
        f.write('}\n')
    else:
        raise Exception(f'Not writable: {repr(x)}')

eol = object()

def read_object (f):
    line = next(f).rstrip('\r\n')
    if line[0] == '|':
        return line[1:]
    elif line[0] == '[':
        lst = []
        while True:
            elt = read_object(f)
            if elt is eol:
                break
            lst.append(elt)
        return lst
    elif line[0] == '{':
        dct = {}
        while True:
            line = next(f).rstrip('\r\n')
            if line[0] == '}':
                break
            elif line[0] != 'k':
                raise Exception(f"Expecting 'k': {repr(line)}")
            key = line[1:]
            value = read_object(f)
            if value is eol:
                raise Exception('Unexpected end of list')
            dct[key] = value
        return dct
    elif line[0] == ']':
        return eol
    else:
        raise Exception(f'Syntax error: {repr(line)}')

# Called by Unpacker.unpack_text

def save_lemma (lemma, entry, fn):
    with open(fn, 'a') as f:
        f.write('+')
        f.write(lemma)
        f.write('\n')
        write_object(entry, f)

def load (fn):
    lex = {}
    with open(fn) as f:
        for line in f:
            line = line.rstrip('\r\n')
            if line[0] != '+':
                raise Exception(f'Syntax error, expecting +: {repr(line)}')
            lemma = line[1:]
            text = read_object(f)
            if lemma in lex:
                print('Duplicate entry, skipping: {lemma}')
            else:
                lex[lemma] = text
    return lex

# Called by Unpacker.unpack_text

def make_filename (lang):
    out = bytearray()
    for c in lang:
        c = ord(c)
        if 65 <= c <= 90 or 97 <= c <= 122 or c == 45 or c == 46 or c == 95:
            out.append(c)
        else:
            out.append(61) # ord('=')
            for c1 in str(c):
                out.append(ord(c1))
    return out.decode('ascii')


#--  Unpacker  -----------------------------------------------------------------

class Unpacker (object):
    
    def __init__ (self):
        self.dump_fn = None
        self.tgt_dir = None
        self.skipf = None
    
    def entry_texts (self):
        '''Iteration over (title, text) pairs, omitting articles whose title contains a colon.'''
        for (title, text) in texts(self.dump_fn):
            if ':' in title:
                self.skipf.write(title)
                self.skipf.write('\n')
            else:
                yield (title, text)

    def unpack_text (self, lemma, text):
        text = parse_text(text)
        if isinstance(text, dict):
            for (lang, entry) in text.items():
                fn = join(self.tgt_dir, make_filename(lang))
                save_lemma(lemma, entry, fn)

    def __call__ (self, dump_fn, tgt_dir):
        '''Unpack into the tgt_dir.  Level-2 headers in entry texts are assumed to be language names = tgt filenames.'''
        tgt_dir = expanduser(tgt_dir)
        if exists(tgt_dir) and not isdir(tgt_dir):
            raise Exception(f'Exists but is not directory: {tgt_dir}')
        self.dump_fn = expanduser(dump_fn)
        self.tgt_dir = tgt_dir
        makedirs(tgt_dir)
        prog = Progress()
        with open(join(tgt_dir, '__skipped__'), 'w') as self.skipf:
            for (i, (title, text)) in enumerate(self.entry_texts()):
                if i > 0 and i % 500 == 0:
                    prog += 500
                self.unpack_text(title, text)
        prog.done()


#==  UDT-Wikt map file  ========================================================

class UDTWiktMap (object):

    def __init__ (self, mapfn):
        self.mapfn = expanduser(mapfn)
        self.entries = self._load()

    def _read (self):
        with open(self.mapfn) as f:
            for line in f:
                entry = line.strip('\r\n').split('\t')
                if len(entry) == 1:
                    entry.append('')
                if entry[1]:
                    entry[1] = entry[1].split(',')
                else:
                    entry[1] = []
                yield entry
    
    def _load (self):
        return list(self._read())
    
    def save (self):
        with open(self.mapfn, 'w') as f:
            for entry in self.entries:
                f.write(entry[0])
                f.write('\t')
                f.write(','.join(entry[1]))
                f.write('\n')

    def wikt_filenames (self):
        return (wname for (_, wnames) in self.entries for wname in wnames)

    def normalize (self, name):
        with StringIO() as f:
            i = 0
            while i < len(name):
                if name[i] == '=':
                    i += 1
                    j = i
                    while j < len(name) and name[j].isdigit():
                        j += 1
                    f.write(chr(int(name[i:j])))
                    i = j
                else:
                    f.write(name[i])
                    i += 1
            return f.getvalue().strip()

    def udt_langs (self):
        return set(uname for (uname, _) in self.entries)

    def wikt_langs (self):
        return set(self.normalize(name) for name in self.wikt_filenames())


#==  Kaikki dictionaries  ======================================================

class Kaikki (object):

    url = 'https://kaikki.org/dictionary/'

    def __init__ (self):
        self._table = None

    def table (self):
        if self._table is None:
            self._table = dict(self._fetch_langs())
        return self._table

    def languages (self):
        return sorted(self.table())
        
    def __getitem__ (self, lang):
        return self.table()[lang]

    def __iter__ (self):
        if self._languages is None:
            self._languages = set(self.fetch_languages())
        
    def _fetch_langs (self):
        for (text, tgt) in self._fetch_links():
            if not len(text) == 1:
                raise Exception(f'Unexpected anchor contents: {text}')
            text = text[0]
            if not text.startswith('All languages combined'):
                m = re.match(r'(.*) \(\d* senses\)$', text)
                if not m:
                    raise Exception(f'Unexpected anchor contents: {text}')
                yield (m[1], tgt)

    def _fetch_links (self):
        with urlopen(self.url) as f:
            doc = BeautifulSoup(f, features='lxml')
            for link in doc.select('h2 ~ ul li a'):
                yield (link.contents, link['href'])


#==  Main  =====================================================================

class WiktionaryMain (Main):

    def com_xlangs (self, dump_fn, tgtfn):
        WiktDump(dump_fn).extract_language_names(tgtfn)

    def com_xdicts (self, dump_fn, tgtlangs_fn, tgtdir):
        WiktDump(dump_fn).extract_dicts(tgtlangs_fn, tgtdir)

    def com_dict (self, fn):
        print(LanguageFile(fn))


if __name__ == '__main__':
    WiktionaryMain()()
