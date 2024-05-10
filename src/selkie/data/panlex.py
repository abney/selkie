
# This is version 2.  data/panlex.py is version 1.

import csv, sys
from collections import namedtuple
from os import makedirs, listdir
from os.path import expanduser, join, exists, abspath
from zipfile import ZipFile
from ..pyx.com import Main
from ..pyx.formats import File, Format, lines_to_blocks, blocks_to_lines, Dicts
from ..pyx.io import pprint, redirect
from ..pyx.object import MapProxy


def expr_lvid (expr): return expr[:5]
def expr_str (expr): return expr[6:]


#--  Cache  --------------------------------------------------------------------

class Cache (object):

    def __init__ (self):
        self.table = {}

    def get (self, key, compute):
        if key in self.table:
            return self.table[key]
        else:
            value = compute()
            self.table[key] = value
            return value


#--  Panlex  -------------------------------------------------------------------

class Panlex (object):

    def __init__ (self, tgtdir='.', csvdir=None):
        tgtdir = abspath(expanduser(tgtdir))
        if csvdir is None:
            csvdir = tgtdir + '-csv'

        self.tgtdir = tgtdir
        self.csvdir = csvdir
        self.cache = Cache()

    def csv (self):
        return self.cache.get('csv', lambda: CSVDatabase(self))

    def installer (self):
        return Installer(self)

    def variety (self, lvid):
        tab = self.cache.get('variety', lambda: Index(self.varieties(), 'lvid'))
        return tab[lvid]
    
    def varieties (self):
        return self.cache.get('varieties', lambda: Table(self, 'varieties', Variety))

    def lang_varieties (self, lg):
        tab = self.cache.get('lang_varieties', self._compute_lang_varieties)
        return tab[lg]

    def default_variety (self, lg):
        for variety in self.lang_varieties(lg):
            if variety.var_code == '0':
                return variety

    def _compute_lang_varieties (self):
        idx = Index(self.varieties(), 'lang_code', multi=True)
        return {lg:vv for (lg, vv) in idx.items()}
            
    def lv_dicts (self, lvid):
        tab = self.cache.get('lv_dicts', self._compute_lv_dicts)
        return tab.get(lvid, [])

    def _compute_lv_dicts (self):
        idx = Index(Table(self, 'dict_lv', DictLVEntry), 'lvid', multi=True)
        return {lvid:[ent.did for ent in ents] for (lvid, ents) in idx.items()}

    def dictionary (self, did):
        idx = self.cache.get('dictionary', lambda: Index(Table(self, 'dicts', Dictionary), 'did'))
        return idx[did]

    def bilex (self, name):
        return Bilex(Dicts(join(self.tgtdir, name)))


#--  Data objects  -------------------------------------------------------------

class Object (object):

    def __init__ (self):
        for name in self.filekeys.values():
            setattr(self, name, None)
    
    def __str__ (self):
        with redirect() as s:
            pprint(self.__class__.__name__)
            with pprint.indent():
                for name in self.filekeys.values():
                    pprint(name, repr(getattr(self, name)))
            return str(s)


class Variety (Object):

    filekeys = {'id': 'lvid',
                'lg': 'lang_code',
                'va': 'var_code',
                'mu': 'mutable',
                'na': 'name',
                'sc': 'script',
                're': 'region',
                'ui': 'uid',
                'gr': 'grp'}

    indexattr = 'lvid'

    def __repr__ (self):
        return f'<Variety {self.lvid} {self.uid}>'


class Dictionary (Object):

    filekeys = {'id': 'did',
                'da': 'reg_date',
                'la': 'label',
                'ur': 'url',
                'bn': 'isbn',
                'au': 'author',
                'ti': 'title',
                'pu': 'publisher',
                'yr': 'year',
                'qu': 'quality',
                'gr': 'grp',
                'no': 'note',
                'li': 'license',
                'i1': 'ip_claim',
                'i2': 'ip_claimant',
                'i3': 'ip_claimant_email'}

class DictLVEntry (Object):

    filekeys = {'did': 'did', 'lvid': 'lvid'}


#--  Table  --------------------------------------------------------------------

class Table (object):

    def __init__ (self, panlex, tabname, rowtype):
        self.panlex = panlex
        self.tabname = tabname
        self.fmt = Format(lambda lines: lines_to_objects(rowtype, lines), objects_to_lines)
        self.filename = join(self.panlex.tgtdir, tabname)
        self._contents = list(self.fmt(File(self.filename)))

    def __len__ (self): return len(self._contents)
    def __iter__ (self): return iter(self._contents)
    def __getitem__ (self, i): return self._contents[i]


def lines_to_objects (typ, lines):
    for block in lines_to_blocks(lines):
        yield block_to_object(typ, block)

def block_to_object (typ, block):
    obj = typ()
    for rec in block:
        if len(rec) != 1:
            raise Exception(f'Unexpected multi-field record in block: {rec}')
        line = rec[0]
        i = line.find(' ')
        if i < 0:
            raise Exception(f'No space in line: {repr(line)}')
        fkey = line[:i]
        attname = typ.filekeys[fkey]
        setattr(obj, attname, line[i+1:])
    return obj

def objects_to_lines (objects):
    return blocks_to_lines(objects_to_blocks(objects))

def objects_to_blocks (objects):
    for obj in objects:
        yield object_to_block(obj)
    
def object_to_block (obj):
    return list(_object_to_block(obj))

def _object_to_block (obj):
    for (fkey, attname) in obj.filekeys.items():
        yield [fkey + ' ' + getattr(obj, attname)]


#--  Index  --------------------------------------------------------------------

class Index (object):

    def __init__ (self, table, keyattr, multi=False):
        self._index = {}
        if multi: add = self._add2
        else: add = self._add1
        for row in table:
            key = getattr(row, keyattr)
            add(key, row)

    def _add1 (self, key, value):
        if key in self._index:
            raise Exception(f'Multiple records for key {repr(key)}')
        self._index[key] = value

    def _add2 (self, key, value):
        if key in self._index:
            self._index[key].append(value)
        else:
            self._index[key] = [value]

    def __len__ (self): return len(self._index)
    def __getitem__ (self, i): return self._index[i]
    def __contains__ (self, key): return key in self._index
    def get (self, key, dflt=None): return self._index.get(key, dflt)
    def keys (self): return self._index.keys()
    def values (self): return self._index.values()
    def items (self): return self._index.items()


#--  CSV files  ----------------------------------------------------------------

class CSVTable (object):

    def __init__ (self, tabname, fn):
        self.header = None
        self.typ = None
        self.rows = None

        with open(fn) as f:
            r = csv.reader(f)
            self.header = next(r)
            self.typ = namedtuple(tabname, self.header)
            self.rows = rows = []
            for rec in r:
                if len(rec) == len(self.header):
                    rows.append(self.typ(*rec))
                else:
                    print('** In', tabname, 'skipping bad record:', rec)

    def print_header (self):
        for (i, name) in enumerate(self.header):
            print(f'[{i}] {name}')

    def __len__ (self): return len(self.rows)
    def __iter__ (self): return iter(self.rows)
    def __getitem__ (self, k): return self.rows[k]


class CSVDatabase (object):

    def __init__ (self, panlex):
        self.panlex = panlex
        self.table_names = set()
        self.tables = {}

        for name in listdir(panlex.csvdir):
            if name.endswith('.csv'):
                self.table_names.add(name[:-4])

    def __getitem__ (self, tabname):
        if tabname in self.tables:
            return self.tables[tabname]
        elif tabname in self.table_names:
            tab = CSVTable(tabname, join(self.panlex.csvdir, tabname + '.csv'))
            self.tables[tabname] = tab
            return tab
        else:
            raise KeyError(f'No such table: {tabname}')


#--  Installer  ----------------------------------------------------------------

class Installer (object):

    def __init__ (self, panlex):
        self.panlex = panlex
        self.csv = panlex.csv()
        self.cache = Cache()
        self.tgtdir = self.panlex.tgtdir

    #--  Load, Install, Convert  -----------

    def load (self, name, compute):
        return self.cache.get(name, lambda: self._load(name, compute))

    def _load (self, name, compute):
        print('Loading', name, '...', end='', file=sys.stderr)
        sys.stderr.flush()
        tab = compute()
        print(' done', file=sys.stderr)
        return tab

    def install (self, tgt, write):
        fn = join(self.tgtdir, tgt)
        if exists(fn):
            print('Already installed', file=sys.stderr)
        else:
            print('Installing', fn, file=sys.stderr)
            self.need_tgtdir()
            with open(fn, 'w') as f:
                write(f)

    def convert (self, csvname, tgtname, specs):
        self.install(tgtname, lambda f: self._convert(f, csvname, specs))

    def _convert(self, f, csvname, specs):
        first = True
        for rec in self.csv[csvname].rows:
            if first: first = False
            else: print(file=f)
            self._convert_rec(rec, specs, f)

    def _convert_rec (self, rec, specs, f):
        for (field, spec) in zip(rec, specs):
            if spec is None: continue
            if isinstance(spec, tuple):
                (key, parse) = spec
                value = parse(field)
            else:
                key = spec
                value = field
            print(key, value, file=f)

    #--  General  --------------------------

    def expr_entry (self, exid):
        idx = self.load('expr', lambda: Index(self.csv['expr'], 'id'))
        return idx[exid]

    def expr (self, exid):
        return self.expr_entry(exid).txt
    
    def need_tgtdir (self):
        if not exists(self.tgtdir):
            makedirs(self.tgtdir)

    def denotations (self, mid):
        idx = self.load('denotations', lambda: Index(self.csv['denotation'], 'meaning', multi=True))
        return idx.get(mid, [])

    def meanings (self, did):
        idx = self.load('meanings', lambda: Index(self.csv['meaning'], 'source', multi=True))
        return idx.get(did, [])

    #--  Targets  --------------------------

    def __call__ (self, lang=None, lvid1=None, lvid2=None):
        if lang is None:
            self.bilexica()
        else:
            self.bilex(lang, lvid1, lvid2)

    def varieties (self):
        self.convert('langvar', 'varieties',
                     ['id', 'lg', 'va', 'mu', ('na', self.expr), ('sc', self.expr), None, ('re', self.expr), ('ui', self.expr), 'gr'])

    def dictionary_list (self):
        self.convert('source_langvar', 'dict_lv', ['did', 'lvid'])
        self.convert('source', 'dicts',
                     ['id','da','la','ur','bn','au','ti','pu','yr','qu','gr','no','li','i1','i2','i3'])

    # A meaning is a list of denotations

    def bilex (self, name, lvid1=None, lvid2=None):
        if lvid1 is None:
            lvid1 = self.panlex.default_variety(name).lvid
        if lvid2 is None:
            lvid2 = '187'
        self.install(name, lambda f: self._install_bilex(f, name, lvid1, lvid2))

    def _install_bilex (self, f, name, lvid1, lvid2):
        first = True
        for (w,g) in self._bilex_pairs(lvid1, lvid2):
            if first: first = False
            else: print(file=f)
            print('w', '\t'.join(w), file=f)
            print('g', '\t'.join(g), file=f)

    def _bilex_pairs (self, lvid1, lvid2):
        for did in self.panlex.lv_dicts(lvid1):
            for m in self.meanings(did):
                pair = self._bilex_pair(m.id, lvid1, lvid2)
                if pair:
                    yield pair

    def _bilex_pair (self, mid, lvid1, lvid2):
        w1 = []
        w2 = []
        for dn in self.denotations(mid):
            e = self.expr_entry(dn.expr)
            if e.langvar == lvid1:
                w1.append(e.txt)
            elif e.langvar == lvid2:
                w2.append(e.txt)
        if w1 and w2:
            return (w1, w2)

    def bilexica (self):
        with open(join(self.tgtdir, 'lexica')) as f:
            for line in f:
                (name, lvid1, lvid2) = line.split()
                print('Install', name, lvid1, lvid2, file=sys.stderr)
                self.bilex(name, lvid1, lvid2)


#--  Bilex  --------------------------------------------------------------------
                
class Bilex (MapProxy):

    def __init__ (self, entries):
        self.table = {}
        for entry in entries:
            w = entry['w']
            g = entry['g']
            if w in self.table:
                self.table[w].append(g)
            else:
                self.table[w] = [g]

    def __map__ (self):
        return self.table


#--  Main  ---------------------------------------------------------------------

class PanlexMain (Main):

    def __init__ (self):
        Main.__init__(self)
        self.panlex = Panlex()
        self.install = self.panlex.installer()

    def com_install (self, lang=None, lvid1=None, lvid2=None):
        self.install(lang, lvid1, lvid2)

    def com_install_varieties (self):
        self.install.varieties()

    def com_varieties (self, lgid):
        for variety in self.panlex.lang_varieties(lgid):
            print(variety)


if __name__ == '__main__':
    PanlexMain()()
