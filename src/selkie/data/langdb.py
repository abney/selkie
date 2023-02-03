##  @package seal.data.langdb
#   Ethnologue database of the world's languages.

import codecs, os, re
from seal.core.misc import chain, deaccent, run
from seal.core.io import tabular, Data
from seal.data.panlex import PanLex


##  The Seal data directoryn.
data = str(Data)
##  The ethnologue data directory.
dir = str(Data/'iso'/'639-3')
##  The file names, sorted alphabetically.
names = sorted(os.listdir(dir))

##  Iterate over the records of the given data file.  A record is a list of strings.

def iter_data_file (fn):
    first = True
    for line in codecs.open(fn, encoding='utf8'):
        if first:
            first = False
        else:
            yield line.rstrip('\r\n').split('\t')


#--  Languages File  -----------------------------------------------------------
#
#  data/iso/639-3/iso-639-3_
#  Contains the ISO 639-3 codes.
#

##  Load the file containing languages.

def load_languages_file (db):
    fn = os.path.join(dir, names[1])
    for entry in iter_data_file(fn):
        db.add_language(Language(*entry))


#--  Names File  ---------------------------------------------------------------
#
#  data/iso/639-3/iso-639-3_Name_Index_20140320.tab
#  Contains alternate names for languages.
#

##  Load the file containing alternate names.

def load_names_file (db):
    fn = os.path.join(dir, names[2])
    for (code, name, inv_name) in iter_data_file(fn):
        lg = db.bycode[code]
        lg.names.append(name)
        lg.inv_names.append(inv_name)


#--  Macrolanguages File  ------------------------------------------------------
#
#  data/iso/639-3/iso-639-3-macrolanguages.tab
#  Contains macrolanguage names and codes.
#

##  Load the file containing macrolanguages.

def load_macrolanguages_file (db):
    fn = os.path.join(dir, names[0])
    for (mcode, lcode, status) in iter_data_file(fn):
        db.add_macrolanguage_member(mcode, lcode)


#--  Retirements File  ---------------------------------------------------------
#
#  data/iso/639-3/iso-639-3_Retirements_20140320.tab
#  Contains information about retired codes.
#

##  Load the file containing retirement information.

def load_retirements_file (db):
    fn = os.path.join(dir, names[3])
    for entry in iter_data_file(fn):
        db.add_retirement(Retirement(*entry))


#--  Groups File  --------------------------------------------------------------
#
#  data/iso/639-5.txt
#  Contains information about language families
#

##  Load the file containing language-family information.

def load_groups_file (db):
    fn = os.path.join(data, 'iso', '639-5.txt')
    with open(fn, 'r', encoding='utf8') as f:
        for line in f:
            (url, code, name, fr_name) = line.rstrip('\r\n').split('\t')
            db.add_group(code, name)


#--  Orthographies  ------------------------------------------------------------
#
#  data/seal/*.rom
#  Loads information about orthographies.
#

##  Load the list of orthographies.

def load_orthographies (db):
    fn = os.path.join(data, 'seal')
    for name in os.listdir(fn):
        if name.endswith('.rom'):
            name = name[:-4]
            i = name.find('-')
            if i > 0: code = name[:i]
            else: code = name
            lang = db.add_orthography(code, name)


#--  Language  -----------------------------------------------------------------

_scopes = {
    'I': 'Language',
    'G': 'Group',
    'M': 'Macrolanguage',
    'R': 'Retired Code',
    'S': 'Special Code'}

_types = {
    'A': 'Ancient',
    'C': 'Constructed',
    'E': 'Extinct',
    'H': 'Historical',
    'L': 'Living',
    'R': 'Retired Code',
    'S': 'Special Code'}


##  Information about a particular language.

class Language (object):

    ##  Constructor.

    def __init__ (self, code, code2b='', code2t='', code1='', scope='', type='', name='', cmt=''):

        ##  The 3-letter code.
        self.code = code

        ##  An alternate code.
        self.code2b = code2b

        ##  An alternate code.
        self.code2t = code2t

        ##  An alternate code.
        self.code1 = code1

        ##  The scope of the language.
        self.scope = scope

        ##  The type of item.
        self.type = type

        ##  The name of the language.
        self.name = name

        ##  All names.
        self.names = []

        ##  Inverted names.
        self.inv_names = []

        ##  Comment.
        self.comment = cmt

        ##  The parent.
        self.parent = None

        ##  The members, if this is a macrolanguage.
        self.members = []

        ##  Retirement status.
        self.retirement = None

        ##  List of varieties.
        self.varieties = []

        ##  List of orthographies.
        self.orthographies = []

    ##  Hashed by code.
    def __hash__ (self): return self.code.__hash__()

    ##  Equal if the code is equal.
    def __eq__ (self, other): return self.code.__eq__(other.code)

    ##  The first orthography listed, or 'default', if there are none listed.

    def default_orthography (self):
        if self.code in self.orthographies: return self.code
        elif self.orthographies: return self.orthographies[0]
        else: return 'default'

    ##  The dictionaries for this language (from panlex).

    def dictionaries (self):
        visited = set()
        for v in self.varieties:
            for d in v.dicts:
                if d.id not in visited:
                    visited.add(d.id)
                    yield d

    ##  String representation with lots of detail.

    def __str__ (self):
        rows = [['Code:', self.code]]
        if self.code2b: rows.append(['Code2B:', self.code2b])
        if self.code2t: rows.append(['Code2T:', self.code2t])
        if self.code1: rows.append(['Code1:', self.code1])
        if self.type: rows.append(['Type:', _types[self.type]])
        if self.scope: rows.append(['Scope:', _scopes[self.scope]])
        rows.append(['RefName:', self.name])
        for name in self.names:
            if name != self.name:
                rows.append(['Name:', self.name])
        if self.comment: rows.append(['Comment:', self.comment])
        if self.retirement:
            r = self.retirement
            if r.name != self.name: rows.append(['Ret.Name:', r.name])
            if r.reason: rows.append(['Ret.Reason:', r.reason])
            if r.replacement: rows.append(['Ret.Repl:', r.replacement])
            if r.split: rows.append(['Ret.Split:', r.split])
            if r.date: rows.append(['Ret.Date:', r.date])
        if self.parent: rows.append(['Parent:', repr(self.parent)])
        for member in self.members:
            rows.append(['Member:', repr(member)])
        rows.append(['Varieties:', ','.join(v.uid for v in self.varieties)])
        rows.append(['Dicts:', ','.join(d.id for d in self.dictionaries())])
        return tabular(rows)

    ##  String representation.

    def __repr__ (self):
        return '<%s %s %s %s>' % (_types[self.type], _scopes[self.scope], self.code, repr(self.name))


##  Retirement information.

class Retirement (object):

    ##  Constructor.

    def __init__ (self, code, name, reason, replac, split, date):

        ##  The code.
        self.code = code

        ##  The language name.
        self.name = name

        ##  The reason for retirement.
        self.reason = reason

        ##  The replacement code, if any.
        self.replacement = replac

        ##  If it was split, all replacement codes.
        self.split = split

        ##  The date of retirement.
        self.date = date


##  Turn a word into ASCII.  Essentially just deletes diacritics.

def romanize_word (word):
    return ''.join([deaccent(c.lower()) for c in word if c.isalpha()])

##  Turn a language name into ASCII.
#   Discard anything in parentheses.
#   Split at spaces and hyphens.
#   Discard remaining non-letters, remove accents, downcase.
#   Return value is a tuple of pure-alphabetic, lowercase words.

def romanize_name (name):
    i = name.find('(')
    if i >= 0:
        if not name.endswith(')'):
            raise Exception('Bad assumption')
        name = name[:i].strip()
    return tuple(romanize_word(w) for w in re.split('\s|-', name))


#--  LanguageTables  -----------------------------------------------------------

##  Instantiating LanguageTables loads all the language database files.

class LanguageTables (object):

    ##  Constructor.

    def __init__ (self):

        ##  List of languages.
        self.languages = []

        ##  Dict mapping code to language.
        self.bycode = {}

        ##  Dict mapping name to languages.
        self.byname = None

        ##  Dict mapping word in a name to languages.
        self.byword = None

        load_languages_file(self)
        load_names_file(self)
        load_retirements_file(self)
        load_macrolanguages_file(self)
        load_groups_file(self)
        load_orthographies(self)
        self.repair_entries()
        self.index()
        self.import_panlex()

    ##  Callback for load_languages_file.

    def add_language (self, lg):
        if lg.code in self.bycode:
            raise Exception('Language already present: %s' % lg.code)
        self.languages.append(lg)
        for code in [lg.code, lg.code2b, lg.code2t, lg.code1]:
            if code:
                if code in self.bycode:
                    other = self.bycode[code]
                    if lg != other:
                        raise Exception('Duplicate entry for %s' % code)
                else:
                    self.bycode[code] = lg

    ##  Callback for load_macrolanguages_file.

    def add_macrolanguage_member (self, mcode, lcode):
        if mcode not in self.bycode:
            raise Exception('Macrolanguage code not found: %s' % mcode)
        macro = self.bycode[mcode]
        if not macro.scope == 'M':
            raise Exception('Not a macrolanguage: %s' % mcode)
        lg = self.bycode[lcode]
        if not isinstance(lg, Language):
            raise Exception('Macrolanguage member is not a language: %s' % lcode)
        if lg.parent:
            raise Exception('Multiple parents for %s' % lcode)
        macro.members.append(lg)
        lg.parent = macro

    ##  Callback for load_retirements_file.

    def add_retirement (self, r):
        if r.code in self.bycode:
            lg = self.bycode[r.code]
        else:
            lg = Language(r.code, name=r.name)
            self.add_language(lg)
        if lg.retirement:
            raise Exception('Duplicate retirement: %s' % r.code)
        lg.retirement = r

    ##  Callback for load_groups_file.

    def add_group (self, code, name):
        if code in self.bycode:
            print('Warning: group code already in use: %s' % code)
        else:
            self.add_language(Language(code, scope='G', name=name))

    ##  Callback for load_orthographies.

    def add_orthography (self, code, name):
        if code in self.bycode:
            lang = self.bycode[code]
            lang.orthographies.append(name)

    ##  Called by the constructor.
    #   Add lg.names if missing.
    #   Set lg.scope and lg.type to 'R' if retired.

    def repair_entries (self):
        for lang in self.languages:
            if not lang.names: lang.names = [lang.name]
            if not lang.inv_names: lang.inv_names = [lang.name]
            if lang.retirement:
                lang.scope = lang.type = 'R'

    ##  Called by the constructor.  Constructs the indices.

    def index (self):
        byname = {}
        byword = {}
        for lg in self.languages:
            for name in chain(iter(lg.names), iter(lg.inv_names)):
                name = romanize_name(name)
                if name in byname:
                    ent = byname[name]
                    if lg not in ent:
                        ent.append(lg)
                else:
                    byname[name] = [lg]
                for word in name:
                    if word in byword:
                        ent = byword[word]
                        if lg not in ent:
                            ent.append(lg)
                    else: byword[word] = [lg]
        self.byname = byname
        self.byword = byword
    
    ##  Called by the constructor.  Imports information from panlex.

    def import_panlex (self):
        panlex = PanLex()
        if panlex.is_installed():
            cat = PanLex().catalog()
            for v in cat.varieties:
                if v.langid not in self.bycode:
                    print('Warning: panlex lang code not found: %s' % repr(v.langid))
                else:
                    lang = self.bycode[v.langid]
                    lang.varieties.append(v)
                    v.language = lang


#--  Database  -----------------------------------------------------------------

##  It is a stub when first created.  Loading is triggered when one calls a
#   method that calls tables().  The tables() method instantiates LanguageTables.

class Database (object):

    ##  Constructor.

    def __init__ (self):
        self._tables = None

    ##  Returns a LanguageTables instance.  Computed the first time and cached.

    def tables (self):
        if self._tables is None:
            self._tables = LanguageTables()
        return self._tables

    ##  Whether the given key is in the table.

    def __contains__ (self, key):
        tab = self.tables()
        return tab.bycode.__contains__(key) or tab.byname.__contains__(key)

    ##  Fetch the value for the given key.  It is tried as a code first,
    #   and if that fails, as a name.

    def __getitem__ (self, key):
        tab = self.tables()
        if key in tab.bycode:
            return tab.bycode[key]
        elif key in tab.byname:
            return tab.byname[key]
        else:
            raise Exception('Not found: %s' % key)

    ##  Fetch a language by name.  Romanizes the name before searching.

    def named (self, name):
        tab = self.tables()
        name = romanize_name(name)
        if name in tab.byname:
            return tab.byname[name]

    ##  Fetch a language by a word in the name.

    def find (self, word):
        tab = self.tables()
        word = romanize_word(word)
        if word in tab.byword:
            return tab.byword[word]

    ##  Search for a language.  Returns a list.

    def search (self, word):
        return list(self.iter_search(word))

    ##  Iterator.  Looks for a language whose name contains the word.

    def iter_search (self, word):
        tab = self.tables()
        returned = set()
        word = romanize_word(word)
        for key in tab.byword:
            if word in key:
                for lg in tab.byword[key]:
                    if lg not in returned:
                        returned.add(lg)
                        yield lg

    ##  The number of languages.

    def __len__ (self):
        tab = self.tables()
        return tab.languages.__len__()

    ##  Iterate over the language codes.

    def __iter__ (self):
        tab = self.tables()
        return tab.languages.__iter__()


##  A Database instance.
languages = Database()


if __name__ == '__main__':

    def _com_search (name):
        for lg in languages.search(name):
            print()
            print(repr(lg))
            print(lg)

    run({'search': _com_search})
