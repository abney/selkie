##  @package seal.data.panlex
#   The class PanLex provides an interface to the panlex data.

import os, sys, csv, optparse, zipfile
from io import StringIO
from seal.core.io import Data, pprint
from seal.core.misc import run


##  Represents the database as a whole.

class PanLex (object):

    ##  Constructor.

    def __init__ (self):

        ##  The panlex directory.
        self.dest = str(Data/'panlex')
        self._pkg = None

        ##  The zip file name.
        self.zfname = 'panlex-20140501-csv'
        self._zipfile = None
        self._catalog = None

    ##  Whether it has been installed.

    def is_installed (self):
        return os.path.exists(os.path.join(self.dest, 'varieties'))

    ##  Compile.

    def compile (self, what=None):
        if not what:
            compile_varieties(self)
            compile_catalog(self)
        elif what == 'varieties':
            compile_varieties(self)
        elif what == 'catalog':
            compile_catalog(self)
        else:
            compile_dict(self, what)

    ##  Open.

    def open (self, name, mode='r'):
        dir = self.dest
        fn = os.path.join(dir, name)
        if mode.startswith('r'):
            return open(fn, 'r', encoding='utf8')
        elif mode.startswith('w'):
            if not os.path.exists(dir):
                pprint('Creating', dir)
                os.makedirs(dir)
            pprint('Writing', fn)
            return open(fn, 'w', encoding='utf8')
        else:
            raise Exception('Bad mode: %s' % mode)

    ##  The panlex package.

    def package (self):
        if self._pkg is None:
            table = seal.pkg.load()
            self._pkg = table['panlex']
        return self._pkg

    ##  The pathname of the zip file.

    def zip_filename (self):
        pkg = self.package()
        return str(pkg.sourcedir/(self.zfname + '.zip'))

    ##  Returns a ZipFile.  It is created and cached the first time this is called.

    def zipfile (self):
        if self._zipfile is None:
            self._zipfile = ZipFile(self)
        return self._zipfile

    ##  Create and cache a Catalog.

    def catalog (self):
        if self._catalog is None:
            self._catalog = Catalog(self)
        return self._catalog

    # This only loads the 'varieties' file.
    # The table is not cached, and varieties have empty 'dicts' lists

    def _varieties (self):
        return Varieties(self)


##  A list of languages, varieties, dicts.

class Catalog (object):

    ##  Constructor.

    def __init__ (self, config):

        ##  Configuration.
        self.config = config

        ##  Varieties.
        self.varieties = config._varieties()

        ##  A LanguageTable.  These need self.varieties to exist.
        self.languages = LanguageTable(self)

        ##  A DictTable.
        self.dicts = DictTable(self)


#--  ZipFile  ------------------------------------------------------------------

##  In-memory representation for zip files.

class ZipFile (object):

    ##  Constructor.

    def __init__ (self, config):

        ##  Configuration.
        self.config = config

        ##  A ZipFile.
        self.zipfile = zipfile.ZipFile(config.zip_filename())

    ##  Print the filenames in the zip file.

    def ls (self):
        self.zipfile.printdir()

    ##  Iterate over the filenames.

    def filenames (self):
        i = len(self.config.zfname) + 1
        for name in self.zipfile.namelist():
            if len(name) > i:
                yield name[i:-4]


    #--  Reading a file  -------------------

    #  s = zf.raw_contents('fm')
    #
    #  Fetches the contents of the file 'fm' out of the zip file.
    #  Return value is one large string.

    def _raw_contents (self, fn):
        txt = self.zipfile.read('%s/%s.csv' % (self.config.zfname, fn))
        return txt.decode('utf8')
    

    #  for line in self.lines('fm'):

    def _lines (self, fn):
        s = self._raw_contents(fn)
        n = len(s)
        i = 0
        while i < n:
            j = s.find('\n', i)
            if j < 0:
                yield s[i:]
                break
            else:
                yield s[i:j]
                i = j + 1


    #  for record in reader('fm'):
    #
    #  each record is a list of strings
    #  the first record is the list of field names

    def _reader (self, fn):
        return csv.reader(self._lines(fn))

    #  (hdr, recs) = zf.file('fm')

    def _file (self, fn):
        records = self._reader(fn)
        header = next(records)
        return (header, records)

    #  recs = zf.records('fm')

    def _records (self, fn):
        (hdr, recs) = self._file(fn)
        return recs

    ##  Print the headers of the files.
    #   zf.print_headers().

    def print_headers (self):
        for name in self.filenames():
            (hdr, recs) = self._file(name)
            print(name + ':', ' '.join(hdr))

    ##  Print the first records of a given table.
    #   zf.print_head('lv').

    def head (self, fn, n=50):
        try:
            records = self._reader(fn)
            while n > 0:
                record = next(records)
                print(' | '.join(record))
                n -= 1
        except StopIteration:
            pass

    ##  Print out a table.
    #   zf.cat('fm').
    #   zf.cat('fm', format='html').

    def cat (self, fn, format=None):
        if format == 'html':
            table = self._reader(fn)
            print('<table class="display">')
            h = next(table)
            print('<tr><th>%s</th></tr>' % ('</th> <th>'.join(h)))
            for row in table:
                print('<tr><td>%s</td></tr>' % ('</td> <td>'.join(row)))
            print('</table>')

        else:
            for record in self._reader(fn):
                print(' | '.join(record))


    def _table (self, fn):
        (hdr, recs) = self._file(fn)
        return Table(self, hdr, recs)

    ##  Adds two new columns: ex.tt, ex.lv
    #   Takes a pass through the expression file, pulling out just those
    #   entries that occur in table[j], where j is the index of 'ex' in header.

    def table (self, fn):
        (hdr, recs) = self._file(fn)
        if 'ex' in hdr:
            j = hdr.index('ex')
            recs = list(recs)
            expan = dict()
            for rec in recs:
                expan[rec[j]] = None
            (exhdr, exrecs) = self._file('ex')
            for (ex, lv, tt, td) in exrecs:
                if ex in expan:
                    expan[ex] = [tt, lv]

            hdr += ['ex.tt', 'ex.lv']
            recs = (r + expan[r[j]] for r in recs)

        return Table(self, hdr, recs)


#-------------------------------------------------------------------------------
#  Utilities
#

##  Convert to a set.  The input may be a set, a dict, a string, or an iterable.

def as_set (ids):
    if isinstance(ids, set): return ids
    elif isinstance(ids, dict): return ids
    elif isinstance(ids, str): return set([ids])
    else: return set(ids)


#--  Table  --------------------------------------------------------------------

##  A database table.

class Table (object):

    ##  Constructor.

    def __init__ (self, zipfile, header, records):
        if not isinstance(records, list):
            records = list(records)

        ##  The zip file.
        self.zipfile = zipfile

        ##  The header row.
        self.header = header

        ##  The records.
        self.records = records

    ##  Iterate over the records.

    def __iter__ (self): return self.records.__iter__()

    ##  Print out in HTML format.

    def dump_html (self):
        print('<table class="display">')
        if self.header:
            print('<tr><th>%s</th></tr>' % ('</th> <th>'.join(self.header)))
        for row in self.records:
            print('<tr><td>%s</td></tr>' % ('</td> <td>'.join(row)))
        print('</table>', file=f)

    ##  Print out in ASCII format.

    def dump (self):
        if self.header:
            print(' | '.join(self.header))
        for row in self.records:
            print(' | '.join(row))


    #--  Where  ----------------------------

    def _where (self, field, value):
        value = as_set(value)
        i = self.header.index(field)
        for record in self.records:
            if record[i] in value:
                yield record

    ##  Select a subtable.  The return value is a Table.
    #
    #       for record in tab.where('lc', 'deu'):
    #           print(' | '.join(record))
    #

    def where (self, field, value):
        return Table(self.zipfile, self.header, self._where(field, value))

    ##  Call where(), then print it out.
    #
    #       tab.grep('ex', ['274','18586881','18586883','12660638'])

    def grep (self, field, value):
        self.where(field, value).dump()


#-------------------------------------------------------------------------------
#  Variety
#

##  A dialect.

class Variety (object):

    ##  Constructor.  The VARID is panlex variety number.

    def __init__ (self, varid, uid, name, name_lv):

        ##  The variety number.
        self.id = varid

        ##  Variety code + language code.
        self.uid = uid

        ##  The language code.
        self.langid = self.uid[:3]

        ##  The language.
        self.language = None

        ##  The name.
        self.name = name

        ##  Variety name.
        self.name_lv = name_lv

        ##  Tables.
        self.dicts = []

    ##  Pretty-print.

    def __pprint__ (self):
        pprint('Variety', self.uid)
        with pprint.indent():
            pprint('id:', self.id)
            pprint('uid:', self.uid)
            pprint('langid:', self.langid)
            pprint('language:', self.language)
            pprint('name:', self.name)
            pprint('name_lv:', self.name_lv)
            if self.dicts:
                pprint('dicts:')
                with pprint.indent():
                    for d in sorted(self.dicts, key=lambda d:int(d.id)):
                        pprint(d.id, d.name)
            else:
                pprint('dicts: -')

    ##  String representation.

    def __repr__ (self):
        return '<Variety %s %s %s>' % (self.id, self.uid, self.name)


#--  Compile dict  -------------------------------------------------------------

##  A 'meaning' is an alignment bead belonging to a particular dictionary ('source').
#
#   Paraphrasing the documentation:
#   when a source indicates that two or more expressions are translations
#   or synonyms for each other, the user creates a meaning associated with
#   the source, and creates one denotation for each expression
#
#       table 'mn': (mn, ap)
#       table 'dn': (dn, mn, ex)
#
#   In addition, a meaning may have:
#    - domain specifications - table dm (dm, mn, ex)
#    - definitions           - table df (df, mn, lv, tt)
#  
#   Denotations may have:
#    - parts of speech       - table wc (wc, dn, ex)
#                            - table wcex (ex, tt)
#    - metadata              - table md (md, dn, vb, vl)
#
#   For each variety, write a file dict-variety.txt
#
#       dn.ex dn.mn wcex.tt|ex=wc.ex md.vb=md.vl*
#
#   Also write dict-defns.txt
#
#       mn dm.ex df.lv df.tt
#

def compile_dict (config, target_ap):
    mntab = {}
    dntab = {}
    extab = {}
    wctab = {}
    varieties = set()
    prog = Progress()
    zf = config.zipfile()

    # get list of meaning IDs

    print("Processing table 'mn'")
    for (mn,ap) in zf.table('mn'):
        prog.incr()
        if ap == target_ap:
            mntab[mn] = Meaning(mn)
    print('Meanings:', len(mntab))

    print("Processing table 'dn'")
    prog.reset()
    for (dn,mn,ex) in zf.table('dn'):
        prog.incr()
        if mn in mntab:
            meaning = mntab[mn]
            ent = Entry(meaning, ex)
            dntab[dn] = ent
            meaning.entries.append(ent)
            if ex in extab: print('Warning: ex associated with multiple dn: %s' % ex)
            extab[ex] = ent
    print('Denotations:', len(dntab))
    print('Expressions:', len(extab))

    print("Processing table 'wcex'")
    for (ex,tt) in zf.table('wcex'):
        wctab[ex] = tt

    print("Processing table 'wc'")
    for (wc,dn,ex) in zf.table('wc'):
        if dn in dntab:
            ent = dntab[dn]
            ent.pos = wctab[ex]

    print("Processing table 'md'")
    for (md,dn,vb,vl) in zf.table('md'):
        if dn in dntab:
            ent = dntab[dn]
            if '=' in vb: print('Warning: property contains=: %s' % vb)
            ent.properties.append((vb,vl))

    print("Processing table 'ex'")
    for (ex,lv,tt,td) in zf.table('ex'):
        if ex in extab:
            ent = extab[ex]
            ent.lemma = tt
            ent.variety = lv
            ent.search_key = td
            varieties.add(lv)

    meanings = list(mntab.values())

    for lv in varieties:
        with config.open('%s-%s' % (target_ap, lv), 'w') as f:
            for meaning in meanings:
                for ent in meaning.entries:
                    if ent.variety == lv:
                        f.write(ent.record())
    with config.open('%s-defs' % target_ap, 'w') as f:
        for meaning in meanings:
            f.write(meaning.record())
            f.write('\n')


#--  Dictionary  ---------------------------------------------------------------

##  A PanLex dictionary.

class Dictionary (object):

    ##  Constructor.

    def __init__ (self):
        ##  The dictionary ID.
        self.id = None
        ##  The data of publication.
        self.date = None
        ##  E.g. 'ciw-mul-eng:Weshki'.
        self.name = None
        ##  A URL.
        self.url = None
        ##  An ISBN.
        self.isbn = None
        ##  The author.
        self.author = None
        ##  The title.
        self.title = None
        ##  The publisher.
        self.publisher = None
        ##  The year of publication.
        self.year = None
        ##  The quality.
        self.quality = None
        ##  This usually, but not always, agrees with ap.
        self.uid = None
        ##  E.g. 'TG 147;FreeLang.Ojibwe_English.wb'.
        self.name2 = None
        ##  License type.
        self.license = None
        ##  Intellectual rights.
        self.rights = None
        ##  Contact name.
        self.contact_name = None
        ##  Contact email.
        self.contact_email = None
        ##  During compilation, this is a list.
        #   When loading from file, this is a string containing comma separators.
        self.variety_codes = None
        ##  Number of entries.
        self.nentries = None
        ##  Contents: varieties.
        self.varieties = None
        ##  Contents: meanings.
        self.meanings = None

    ##  Set the metadata.

    def set_metadata (self, args):
        if len(args) < 16: raise Exception('Not enough arguments')
        if len(args) > 18: raise Exception('Too many arguments')
        (self.id,
         self.date,
         self.name,  # e.g. 'ciw-mul-eng:Weshki'
         self.url,
         self.isbn,
         self.author,
         self.title,
         self.publisher,
         self.year,
         self.quality,
         self.uid,  # this usually, but not always, agrees with ap
         self.name2, # e.g. 'TG 147;FreeLang.Ojibwe_English.wb'
         self.license,
         self.rights,
         self.contact_name,
         self.contact_email) = args[:16]

        # during compilation, this is a list
        # when loading from file, this is a string containing comma separators
        self.variety_codes = None

        self.nentries = 0

        self.varieties = None
        self.meanings = None

        if len(args) > 16:
            self.variety_codes = args[16]

        if len(args) > 17:
            self.nentries = int(args[17])

    ##  Used during compilation.

    def add_variety_code (self, uid):
        if self.variety_codes is None:
            self.variety_codes = [uid]
        else:
            self.variety_codes.append(uid)

    ##  Used when loading dicts.

    def set_varieties (self, vtable):
        if self.varieties is not None:
            raise Exception('Attempt to reset varieties')
        self.varieties = []
        if self.variety_codes:
            for code in self.variety_codes.split(','):
                v = vtable[code]
                self.varieties.append(v)
                v.dicts.append(self)

    ##  Load.

    def load (self, config):
        mntab = {}
        # fill mntab
        with config.open('%s-defs' % self.id) as f:
            for line in f:
                meaning = Meaning(line.rstrip('\r\n').split('\t'))
                mntab[meaning.id] = meaning
        # load entries
        for v in self.varieties:
            with config.open('%s-%s' % (self.id, v.id)) as f:
                for line in f:
                    ent = Entry(line.rstrip('\r\n').split('\t'))
                    meaning = mntab[ent.meaning]
                    ent.meaning = meaning
                    meaning.entries.append(ent)
        self.meanings = list(mntab.values())

    ##  An entry for this dictionary.  A string.

    def entry (self):
        vc = self.variety_codes
        if vc is None: vc = ''
        elif isinstance(vc, list): vc = ','.join(vc)

        return '\t'.join([self.id,
                          self.date,
                          self.name,
                          self.url,
                          self.isbn,
                          self.author,
                          self.title,
                          self.publisher,
                          self.year,
                          self.quality,
                          self.uid,
                          self.name2,
                          self.license,
                          self.rights,
                          self.contact_name,
                          self.contact_email,
                          vc,
                          str(self.nentries)])

    ##  Pretty-print.

    def __pprint__ (self):
        keys = ['id', 'date', 'name', 'url', 'isbn', 'author', 'title', 'publisher',
                'year', 'quality', 'uid', 'name2', 'license', 'rights', 'contact_name',
                'contact_email', 'comments', 'variety_codes', 'nentries']
        pprint('Dictionary', self.id, '0x%x' % id(self))
        with pprint.indent():
            for k in keys:
                if hasattr(self, k):
                    v = getattr(self, k)
                    pprint('{:13}:'.format(k), repr(v))


##  An entry for a language.

class Entry (object):

    ##  Constructor.

    def __init__ (self, lemma):

        ##  The headword.
        self.lemma = lemma

        ##  The variety.
        self.variety = None

        ##  The search key.
        self.search_key = None

        ##  The part of speech.
        self.pos = None

        ##  List of properties.
        self.properties = []

        ##  The meaning.
        self.meaning = None

    ##  A string for inclusion in a tabular file.

    def record (self):
        return '\t'.join([self.lemma,
                          self.variety or '',
                          self.search_key or '',
                          self.pos or '',
                          ' '.join('%s=%s' % (k,v) for (k,v) in self.properties),
                          self.meaning or ''])

    ##  Set the contents from a record (a list of strings).

    def parse (self, record):
        self.lemma = record[0]
        self.variety = record[1] or None
        self.search_key = record[2] or None
        self.pos = record[3] or None
        self.properties = []
        for prop in record[4].split(' '):
            i = prop.index('=')
            self.properties.append((prop[:i], prop[i+1:]))
        self.meaning = record[5] or None


##  A meaning.

class Meaning (object):

    ##  Constructor.

    def __init__ (self, id):

        ##  The ID.
        self.id = id

        ##  The definition.
        self.definition = None

        ##  The semantic domain.
        self.domain = None

        ##  The entries for words that express it.
        self.entries = []

    ##  A string, suitable for inclusion in a tabular file.

    def record (self):
        return '\t'.join(self.id, self.domain or '', self.definition or '')

    ##  Set the contents from a record (list of strings).

    def parse (self, record):
        self.id = record[0]
        self.domain = record[1] or None
        self.definition = record[2] or None


#--  DictTable  ----------------------------------------------------------------

##  A dict mapping dictionary IDs to Dictionary instances.

class DictTable (dict):

    ##  Constructor.

    def __init__ (self, catalog):
        dict.__init__(self)
        config = catalog.config
        vtable = catalog.varieties.byuid
        with config.open('catalog') as f:
            for line in f:
                d = Dictionary()
                d.set_metadata(line.rstrip('\r\n').split('\t'))
                d.set_varieties(vtable)
                self[d.id] = d
                

#-------------------------------------------------------------------------------
#  Parser
#

##  A progress indicator.

class Progress (object):

    ##  Constructor.

    def __init__ (self):

        ##  Ticks so far.
        self.count = 0

    ##  Increment.  Print, if 1000 ticks have gone by.

    def incr (self):
        self.count += 1
        if self.count % 1000 == 0:
            print('Progress:', self.count, end='\r')

    ##  Reset.

    def reset (self):
        print('Progress:', self.count)
        self.count = 0


#--  VarietyTable  -------------------------------------------------------------

##  cl/data/panlex/varieties
#
#      0: lvid (int)
#      1: lvcode (iso-ddd)
#      2: name
#      3: lvid of name

def compile_varieties (config):

    pprint('Compile varieties')
    with pprint.indent():
    
        zf = config.zipfile()

        #  '%s-%03d' % (lang_code, relnum) is the variety's "UID" (uniform identifier)
        #  saves the variety list for (much) faster access
        
        pprint('Processing table lv')
        tab = zf.table('lv')
        with config.open('varieties', 'w') as f:
            for (lv, lc, vc, sy, am, ex, ex_tt, ex_lv) in tab:
                f.write('%s\t%s-%03d\t%s\t%s\n' % (lv, lc, int(vc), ex_tt, ex_lv))


##  Varieties are indexed both by code and id.

class Varieties (object):

    ##  Constructor.

    def __init__ (self, config):

        ##  Configuration.
        self.config = config

        ##  Table indexed by language variety code.
        self.bylv = {}

        ##  Tabled indexed by VAR-CODE codes.
        self.byuid = {}

        # Initially, v.dicts will be empty for all varieties
        # v.dicts gets set when one loads the dictionaries

        with config.open('varieties') as f:
            for line in f:
                (varid, uid, name, name_lv) = line.rstrip('\r\n').split('\t')
                v = Variety(varid, uid, name, name_lv)
                self.bylv[varid] = v
                self.byuid[uid] = v

    ##  The number of varieties.

    def __len__ (self):
        return len(self.byuid)

    ##  Iterate over the varieties.

    def __iter__ (self):
        return iter(self.byuid.values())


#--  LanguageTable  ------------------------------------------------------------

##  A dict mapping language IDs to lists of varieties.

class LanguageTable (dict):

    ##  Constructor.

    def __init__ (self, catalog):
        dict.__init__(self)
        for v in catalog.varieties:
            lg = v.langid
            if lg in self: self[lg].append(v)
            else: self[lg] = [v]


#--  Catalog  ------------------------------------------------------------------

##  cl/data/panlex/catalog
#
#      0: dictid (int)
#      1: date
#      2: name
#      3: url
#      4: isbn
#      5: author
#      6: title
#      7: publisher
#      8: year
#      9: quality
#      10: uid
#      11: name2
#      12: license
#      13: rights
#      14: contact_name
#      15: contact_email
#      16: varieties (comma-separated lvcodes)
#      17: nentries
#

def compile_catalog (config):
    pprint('Compile catalog')
    with pprint.indent():
        zf = config.zipfile()
        vtable = config._varieties().bylv
        table = dict()
    
        # ap ("approver") is a dictionary id
        # ap table: basic info, up to contact_email
        pprint("Processing table 'ap'")
        for apent in zf.table('ap'):
            d = Dictionary()
            d.set_metadata(apent)
            if d.id in table:
                pprint('Warning: duplicate entry for dictionary %s' % d.id)
            table[d.id] = d
    
        # av table: dict id, variety id
        pprint("Processing table 'av'")
        for (ap, lv) in zf.table('av'):
            if ap not in table:
                pprint('Warning: unknown ap in av: %s' % ap)
                continue
            if lv not in vtable:
                pprint('Warning: unknown lv in ap: %s' % lv)
            v = vtable[lv]
            d = table[ap]
            d.add_variety_code(v.uid)
    
        # aped table: miscellaneous; last field is comments
        pprint("Processing table 'aped'")
        for aped_ent in zf.table('aped'):
            id = aped_ent[0]
            if id in table:
                d = table[id]
                d.comments = aped_ent[-1]
            else:
                pprint('Warning: unknown ap in aped: %s' % id)
    
        # mn table: meanings: we just count them here
        pprint("Processing table 'mn'")
        for (mn, ap) in zf.table('mn'):
            if d.id != ap:
                if ap not in table:
                    pprint('Warning: unknown ap in mn: %s' % ap)
                    continue
                d = table[ap]
            d.nentries += 1
    
        # Write table
        with config.open('catalog', 'w') as f:
            for d in table.values():
                if not d.varieties:
                    pprint('Warning: dict without varieties: %s' % d.id)
                f.write(d.entry())
                f.write('\n')
