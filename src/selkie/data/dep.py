##  @package seal.data.dep
#   The universal dependency treebank.

import sys
from seal.core import io
from seal.core.config import conll, udt
from seal.nlp.dep import conll_sents, umapped_sents, load_umap, apply_umap


#--  Dataset  ------------------------------------------------------------------

##  A dataset for a language.

class Dataset (object):

    ##  Constructor.

    def __init__ (self, name, desc, lang, version, trainfn, testfn, devfn=None):

        ##  The name.
        self.name = name

        ##  A description.
        self.desc = desc

        ##  The language.
        self.lang = lang

        ##  The version.
        self.version = version

        ##  Training data filename.
        self.train = trainfn

        ##  Test data filename.
        self.test = testfn

        ##  Development data filename.
        self.dev = devfn

    ##  Get one of the filenames by type: 'train', 'test', or 'dev'.

    def filespec (self, which):
        if which == 'train': fn = self.train
        elif which == 'test': fn = self.test
        elif which == 'dev': fn = self.dev
        else: raise Exception('Argument must be one of: train, test, dev')
        if fn.endswith('#proj'): return (fn[:-5], True)
        else: return (fn, False)

    ##  Return a list of filenames.

    def filespecs (self, which=None):
        return list(self.iter_filespecs(which))

    ##  Iterate over filenames.

    def iter_filespecs (self, which=None):
        if which is None: which = ['train', 'test', 'dev']
        for w in which:
            fspec = self.filespec(w)
            if not fspec: raise Exception('No filename: %s' % w)
            yield fspec

    ##  Iterate over sentences.

    def __iter__ (self):
        return self.sents()

    ##  Iterate over sentences.

    def sents (self, which=None):
        if isinstance(which, str):
            which = [which]
        for (fn,proj) in self.filespecs(which):
            for sent in conll_sents(fn, projective=proj):
                yield sent

    ##  Iterate over words.

    def words (self, which):
        for sent in self.sents(which):
            for word in sent.words():
                yield word

    ##  Return a DatasetStats object.

    def stats (self):
        return DatasetStats(self)

    ##  Pretty-print the stats.

    def print_stats (self):
        self.stats().pprint()

    ##  String representation.

    def __repr__ (self):
        return '<Dataset %s>' % (self.name)


##  Mapped to universal tagset.

class UMappedDataset (Dataset):

    ##  Constructor.

    def __init__ (self, name, desc, lang, version, trainfn, testfn, devfn=None, mapfn=None):
        if mapfn is None: raise Exception('Need mapfn')
        Dataset.__init__(self, name, desc, lang, version, trainfn, testfn, devfn)

        ##  The filename of the tag map.
        self.mapfn = mapfn

        self._map = None

    ##  Iterates over sentences.

    def sents (self, which):
        if isinstance(which, str):
            which = [which]
        for (fn,proj) in self.filespecs(which):
            for sent in umapped_sents(fn, self.map(), projective=proj):
                yield sent

    ##  Returns the map, loading it if necessary.

    def map (self):
        if self._map is None:
            self._map = load_umap(self.mapfn)
        return self._map


##  A filtered dataset.

class FilterDataset (Dataset):

    ##  Constructor.

    def __init__ (self, name, desc, lang, version, sents):
        Dataset.__init__(self, name, desc, lang, version, None, None)

        ##  The sentences.
        self.sents = sents


#--  Dataset Stats  ------------------------------------------------------------

##  Dataset statistics.

class DatasetStats (object):

    ##  Constructor.

    def __init__ (self, ds):

        ##  The dataset.
        self.dataset = ds

        ##  The statistics.  Keys are 'train', 'test', 'dev'.
        self.stats = {'train': self.filestats(ds.train),
                      'test': self.filestats(ds.test),
                      'dev': self.filestats(ds.dev)}

    ##  The file statistics for a given partition.
    #   Returns a dict with the following keys: 'n_sents',
    #   'n_words', 'n_bad_records', 'n_lemma', 'n_cpos', 'n_fpos',
    #   'n_cpos_ne_fpos', 'cpos_values', 'fpos_values', 'n_morph', 'n_govr',
    #   'n_role', 'role_values', 'prole_values', 'n_pgovr', 'n_prole',
    #   'n_govr_ne_pgovr', 'ds_proj'.

    def filestats (self, spec):
        (fn, ds_proj) = spec
        if fn is None: return None
        n_sents = 0
        n_words = 0
        n_bad_records = 0
        n_lemma = 0
        n_cpos = 0
        n_fpos = 0
        n_cpos_ne_fpos = 0
        cpos_values = set()
        fpos_values = set()
        n_morph = 0
        n_govr = 0
        n_role = 0
        role_values = set()
        prole_values = set()
        n_pgovr = 0
        n_prole = 0
        n_govr_ne_pgovr = 0

        for block in io.iter_record_blocks(fn):
            n_sents += 1
            for record in block:
                n_words += 1
                if len(record) != 10:
                    n_bad_records += 1
                else:
                    for i in range(len(record)):
                        if record[i] == '_': record[i] = ''
                    (i, form, lemma, cpos, fpos, morph, govr, role, pgovr, prole) = record
                    if not lemma: n_lemma += 1
                    if not cpos: n_cpos += 1
                    else: cpos_values.add(cpos)
                    if not fpos: n_fpos += 1
                    else: fpos_values.add(fpos)
                    if cpos != fpos: n_cpos_ne_fpos += 1
                    if not morph: n_morph += 1
                    if not govr: n_govr += 1
                    if not role: n_role += 1
                    else: role_values.add(role)
                    if not pgovr: n_pgovr += 1
                    if not prole: n_prole += 1
                    else: prole_values.add(prole)
                    if govr != pgovr or role != prole:
                        n_govr_ne_pgovr += 1

        return {'n_sents': n_sents,
                'n_words': n_words,
                'n_bad_records': n_bad_records,
                'n_lemma': n_lemma,
                'n_cpos': n_cpos,
                'n_fpos': n_fpos,
                'n_cpos_ne_fpos': n_cpos_ne_fpos,
                'cpos_values': cpos_values,
                'fpos_values': fpos_values,
                'n_morph': n_morph,
                'n_govr': n_govr,
                'n_role': n_role,
                'role_values': role_values,
                'prole_values': prole_values,
                'n_pgovr': n_pgovr,
                'n_prole': n_prole,
                'n_govr_ne_pgovr': n_govr_ne_pgovr,
                'ds_proj': ds_proj}

    ##  Pretty-print.

    def pprint (self):
        rows = [['', 'S', 'W', 'Bad', 'Lem', 'CP', 'FP', 'CP!=FP', 'Mor', 'Gov', 'Rol', 'Pgv', 'Pro', 'G!=PG']]
        for which in self.stats:
            d = self.stats[which]
            if d:
                nw = d['n_words']
                rows.append([which, d['n_sents'], d['n_words'],
                             _n(d['n_bad_records'], nw),
                             _n(d['n_lemma'], nw),
                             _n(d['n_cpos'], nw),
                             _n(d['n_fpos'], nw),
                             _n(d['n_cpos_ne_fpos'], nw),
                             _n(d['n_morph'], nw),
                             _n(d['n_govr'], nw),
                             _n(d['n_role'], nw),
                             _n(d['n_pgovr'], nw),
                             _n(d['n_prole'], nw),
                             _n(d['n_govr_ne_pgovr'], nw)])
        print(io.tabular(rows))
        
        for which in self.stats:
            d = self.stats[which]
            if d:
                if d['ds_proj'] and d['n_pgovr'] > 0:
                    print()
                    print('Using PGOVR/PROLE, but not always present')
                elif (not d['ds_proj']) and d['n_govr'] > 0:
                    print()
                    print('Using GOVR/ROLE, but not always present')

        for which in self.stats:
            d = self.stats[which]
            if d:
                print()
                print('%s:' % which.upper())
                print('cpos:', ' '.join(sorted(d['cpos_values'])))
                print('fpos:', ' '.join(sorted(d['fpos_values'])))
                print('role:', ' '.join(sorted(d['role_values'])))
                print('prol:', ' '.join(sorted(d['prole_values'])))


def _n (v, w):
    if v == w: return '--'
    else: return v

##  Print a summary.

def print_summary ():
    rows = [['', 'S', 'W', 'Bad', 'Lem', 'CP', 'FP', 'CP!=FP', 'Mor', 'Gov', 'Rol', 'Pgv', 'Pro', 'G!=PG', 'DSG', '']]
    for ds in datasets():
        if isinstance(ds, Dataset) and not isinstance(ds, UMappedDataset):
            sys.stdout.write('.')
            sys.stdout.flush()
            row = [ds.name]
            stats = ds.stats()
            dicts = [d for d in stats.stats.values() if d]
            nw = sum(d['n_words'] for d in dicts)
            row.append(sum(d['n_sents'] for d in dicts))
            row.append(nw)
            row.append(_n(sum(d['n_bad_records'] for d in dicts), nw))
            row.append(_n(sum(d['n_lemma'] for d in dicts), nw))
            row.append(_n(sum(d['n_cpos'] for d in dicts), nw))
            row.append(_n(sum(d['n_fpos'] for d in dicts), nw))
            row.append(_n(sum(d['n_cpos_ne_fpos'] for d in dicts), nw))
            row.append(_n(sum(d['n_morph'] for d in dicts), nw))
            row.append(_n(sum(d['n_govr'] for d in dicts), nw))
            row.append(_n(sum(d['n_role'] for d in dicts), nw))
            row.append(_n(sum(d['n_pgovr'] for d in dicts), nw))
            row.append(_n(sum(d['n_prole'] for d in dicts), nw))
            row.append(_n(sum(d['n_govr_ne_pgovr'] for d in dicts), nw))
            proj = sum(d['ds_proj'] for d in dicts)
            nproj = sum(1-d['ds_proj'] for d in dicts)

            if proj and nproj: row.append('mix')
            elif proj: row.append('p')
            elif nproj: row.append('n')
            else: row.append('--')
            
            if sum(d['n_govr'] * (1-d['ds_proj']) + d['n_pgovr'] * d['ds_proj']
                   for d in dicts):
                row.append('**')
            else:
                row.append('')

            rows.append(row)

    print()
    print(io.tabular(rows))


#--  Dataset tables  -----------------------------------------------------------

_by_language = {}
_by_version = {}
_by_name = {}

##  Register a dataset.

def register (ds):
    if ds.name in _by_name:
        raise Exception('Duplicate dataset: ' + ds.name)
    _by_name[ds.name] = ds
        
    if ds.lang in _by_language: _by_language[ds.lang].append(ds)
    else: _by_language[ds.lang] = [ds]

    if ds.version in _by_version: _by_version[ds.version].append(ds)
    else: _by_version[ds.version] = [ds]

##  Get a dataset by name.

def dataset (name):
    if name in _by_name: return _by_name[name]
    else: raise KeyError('No such dataset: ' + repr(name))

##  Gets a list of datasets.

def datasets (lang=None, version=None):
    if lang and version:
        return dataset('%s.%s' % (lang, version))
    elif lang:
        if lang in _by_language: return _by_language[lang]
        else: return []
    elif version:
        if version in _by_version: return _by_version[version]
        else: return []
    else:
        return list(_by_name.values())

##  Iterates over the sentences of a named segment of a named dataset.

def sents (name, segment):
    return dataset(name).sents(segment)

##  Prints name and description for all datasets.

def ls ():
    for name in sorted(_by_name):
        ds = _by_name[name]
        print(name, ds.desc)


#--  Catalog  ------------------------------------------------------------------

## orig

register(Dataset(
        'arb.orig',
        'Arabic, CoNLL-2006',
        'arb',
        'orig',
        conll/'2006/Arabic/data/arabic/PADT/treebank/arabic_PADT_train.conll',
        conll/'2006/2006_CoNLL_test_complete/data/arabic/PADT/treebank/arabic_PADT_test.conll'))

register(Dataset(
        'eus.orig',
        'Basque, CoNLL-2006',
        'eus',
        'orig',
        None,
        None))

register(Dataset(
        'bul.orig',
        'Bulgarian, CoNLL-2006',
        'bul',
        'orig',
        conll/'2006/bulgarian/bultreebank/train/bulgarian_bultreebank_train.conll#proj',
        conll/'2006/bulgarian/bultreebank/test/bulgarian_bultreebank_test.conll#proj'))

register(Dataset(
        'cat.orig',
        'Catalan, CoNLL-2006',
        'cat',
        'orig',
        None,
        None))

register(Dataset(
        'cmn.orig',
        'Chinese, CoNLL-2006',
        'cmn',
        'orig',
        None,
        None))

register(Dataset(
        'ces.orig',
        'Czech, CoNLL-2006',
        'ces',
        'orig',
        conll/'2006/Czech/data/czech/pdt/treebank/czech_pdt_train.conll',
        conll/'2006/2006_CoNLL_test_complete/data/czech/pdt/treebank/czech_pdt_test.conll'))

register(Dataset(
        'dan.orig',
        'Danish, CoNLL-2006',
        'dan',
        'orig',
        conll/'2006/danish/ddt/train/danish_ddt_train.conll',
        conll/'2006/danish/ddt/test/danish_ddt_test.conll'))

register(Dataset(
        'nld.orig',
        'Dutch, CoNLL-2006',
        'nld',
        'orig',
        conll/'2006/dutch/alpino/train/dutch_alpino_train.conll',
        conll/'2006/dutch/alpino/test/dutch_alpino_test.conll'))

register(Dataset(
        'deu.orig',
        'German, CoNLL-2006',
        'deu',
        'orig',
        conll/'2006/german/tiger/train/german_tiger_train.conll#proj',
        conll/'2006/german/tiger/test/german_tiger_test.conll#proj'))

register(Dataset(
        'ell.orig',
        'Greek, CoNLL-2006',
        'ell',
        'orig',
        None,
        None))

register(Dataset(
        'hun.orig',
        'Hungarian, CoNLL-2006',
        'hun',
        'orig',
        None,
        None))

register(Dataset(
        'ita.orig',
        'Italian, CoNLL-2006',
        'ita',
        'orig',
        None,
        None))

register(Dataset(
        'jpn.orig',
        'Japanese, CoNLL-2006',
        'jpn',
        'orig',
        None,
        None))

register(Dataset(
        'por.orig',
        'Portuguese, CoNLL-2006',
        'por',
        'orig',
        conll/'2006/portuguese/bosque/treebank/portuguese_bosque_train.conll',
        conll/'2006/portuguese/bosque/test/portuguese_bosque_test.conll'))

register(Dataset(
        'slv.orig',
        'Slovenian, CoNLL-2006',
        'slv',
        'orig',
        conll/'2006/slovene/sdt/treebank/slovene_sdt_test.conll',
        conll/'2006/slovene/sdt/treebank/slovene_sdt_train.conll'))

register(Dataset(
        'spa.orig',
        'Spanish, CoNLL-2006',
        'spa',
        'orig',
        conll/'2006/spanish/cast3lb/train/spanish_cast3lb_train.conll#proj',
        conll/'2006/spanish/cast3lb/test/spanish_cast3lb_test.conll#proj'))

register(Dataset(
        'swe.orig',
        'Swedish, CoNLL-2006',
        'swe',
        'orig',
        conll/'2006/swedish/talbanken05/train/swedish_talbanken05_train.conll',
        conll/'2006/swedish/talbanken05/test/swedish_talbanken05_test.conll'))

register(Dataset(
        'tur.orig',
        'Turkish, CoNLL-2006',
        'tur',
        'orig',
        conll/'2006/turkish/metu_sabanci/train/turkish_metu_sabanci_train.conll',
        conll/'2006/turkish/metu_sabanci/test/turkish_metu_sabanci_test.conll'))

## umap

# also available:
# 'de-negra'
# 'en-brown'
# 'en-ptb'
# 'en-tweet'
# 'fi-tdt'
# 'fr-paris'
# 'iw-mila'
# 'ja-verbmobil'
# 'ko-sejong'
# 'pl-ipipan'
# 'ru-rnc'
# 'zh-ctb6'

register(UMappedDataset(
        'arb.umap',
        'Arabic, CoNLL-2006 mapped to Das/Petrov universal tags',
        'arb',
        'umap',
        conll/'2006/Arabic/data/arabic/PADT/treebank/arabic_PADT_train.conll#proj',
        conll/'2006/2006_CoNLL_test_complete/data/arabic/PADT/treebank/arabic_PADT_test.conll#proj',
        mapfn=conll/'2006/universal-pos-tags/ar-padt.map'))

register(UMappedDataset(
        'eus.umap',
        'Basque, CoNLL-2006 mapped to Das/Petrov universal tags',
        'eus',
        'umap',
        None,
        None,
        mapfn=conll/'2006/universal-pos-tags/eu-eus3lb.map'))

register(UMappedDataset(
        'bul.umap',
        'Bulgarian, CoNLL-2006 mapped to Das/Petrov universal tags',
        'bul',
        'umap',
        conll/'2006/bulgarian/bultreebank/train/bulgarian_bultreebank_train.conll#proj',
        conll/'2006/bulgarian/bultreebank/test/bulgarian_bultreebank_test.conll#proj',
        mapfn=conll/'2006/universal-pos-tags/bg-btb.map'))

register(UMappedDataset(
        'cat.umap',
        'Catalan, CoNLL-2006 mapped to Das/Petrov universal tags',
        'cat',
        'umap',
        None,
        None,
        mapfn=conll/'2006/universal-pos-tags/ca-cat3lb.map'))

register(UMappedDataset(
        'cmn.umap',
        'Chinese, CoNLL-2006 mapped to Das/Petrov universal tags',
        'cmn',
        'umap',
        None,
        None,
        mapfn=conll/'2006/universal-pos-tags/zh-sinica.map'))

register(UMappedDataset(
        'ces.umap',
        'Czech, CoNLL-2006 mapped to Das/Petrov universal tags',
        'ces',
        'umap',
        conll/'2006/Czech/data/czech/pdt/treebank/czech_pdt_train.conll',
        conll/'2006/2006_CoNLL_test_complete/data/czech/pdt/treebank/czech_pdt_test.conll',
        mapfn=conll/'2006/universal-pos-tags/cs-pdt.map'))

register(UMappedDataset(
        'dan.umap',
        'Danish, CoNLL-2006 mapped to Das/Petrov universal tags',
        'dan',
        'umap',
        conll/'2006/danish/ddt/train/danish_ddt_train.conll',
        conll/'2006/danish/ddt/test/danish_ddt_test.conll',
        mapfn=conll/'2006/universal-pos-tags/da-ddt.map'))

register(UMappedDataset(
        'nld.umap',
        'Dutch, CoNLL-2006 mapped to Das/Petrov universal tags',
        'nld',
        'umap',
        conll/'2006/dutch/alpino/train/dutch_alpino_train.conll',
        conll/'2006/dutch/alpino/test/dutch_alpino_test.conll',
        mapfn=conll/'2006/universal-pos-tags/nl-alpino.map'))

register(UMappedDataset(
        'deu.umap',
        'German, CoNLL-2006 mapped to Das/Petrov universal tags',
        'deu',
        'umap',
        conll/'2006/german/tiger/train/german_tiger_train.conll#proj',
        conll/'2006/german/tiger/test/german_tiger_test.conll#proj',
        mapfn=conll/'2006/universal-pos-tags/de-tiger.map'))

register(UMappedDataset(
        'ell.umap',
        'Greek, CoNLL-2006 mapped to Das/Petrov universal tags',
        'ell',
        'umap',
        None,
        None,
        mapfn=conll/'2006/universal-pos-tags/el-gdt.map'))

register(UMappedDataset(
        'hun.umap',
        'Hungarian, CoNLL-2006 mapped to Das/Petrov universal tags',
        'hun',
        'umap',
        None,
        None,
        mapfn=conll/'2006/universal-pos-tags/hu-szeged.map'))

register(UMappedDataset(
        'ita.umap',
        'Italian, CoNLL-2006 mapped to Das/Petrov universal tags',
        'ita',
        'umap',
        None,
        None,
        mapfn=conll/'2006/universal-pos-tags/it-isst.map'))

register(UMappedDataset(
        'jpn.umap',
        'Japanese, CoNLL-2006 mapped to Das/Petrov universal tags',
        'jpn',
        'umap',
        None,
        None,
        mapfn=conll/'2006/universal-pos-tags/ja-kyoto.map'))

register(UMappedDataset(
        'por.umap',
        'Portuguese, CoNLL-2006 mapped to Das/Petrov universal tags',
        'por',
        'umap',
        conll/'2006/portuguese/bosque/treebank/portuguese_bosque_train.conll',
        conll/'2006/portuguese/bosque/test/portuguese_bosque_test.conll',
        mapfn=conll/'2006/universal-pos-tags/pt-bosque.map'))

register(UMappedDataset(
        'slv.umap',
        'Slovenian, CoNLL-2006 mapped to Das/Petrov universal tags',
        'slv',
        'umap',
        conll/'2006/slovene/sdt/treebank/slovene_sdt_test.conll',
        conll/'2006/slovene/sdt/treebank/slovene_sdt_train.conll',
        mapfn=conll/'2006/universal-pos-tags/sl-sdt.map'))

register(UMappedDataset(
        'spa.umap',
        'Spanish, CoNLL-2006 mapped to Das/Petrov universal tags',
        'spa',
        'umap',
        conll/'2006/spanish/cast3lb/train/spanish_cast3lb_train.conll#proj',
        conll/'2006/spanish/cast3lb/test/spanish_cast3lb_test.conll#proj',
        mapfn=conll/'2006/universal-pos-tags/es-cast3lb.map'))

register(UMappedDataset(
        'swe.umap',
        'Swedish, CoNLL-2006 mapped to Das/Petrov universal tags',
        'swe',
        'umap',
        conll/'2006/swedish/talbanken05/train/swedish_talbanken05_train.conll',
        conll/'2006/swedish/talbanken05/test/swedish_talbanken05_test.conll',
        mapfn=conll/'2006/universal-pos-tags/sv-talbanken.map'))

register(UMappedDataset(
        'tur.umap',
        'Turkish, CoNLL-2006 mapped to Das/Petrov universal tags',
        'tur',
        'umap',
        conll/'2006/turkish/metu_sabanci/train/turkish_metu_sabanci_train.conll',
        conll/'2006/turkish/metu_sabanci/test/turkish_metu_sabanci_test.conll',
        mapfn=conll/'2006/universal-pos-tags/tu-metusbanci.map'))

## ch

register(Dataset(
        'deu.ch',
        'German, McDonald universal DTB, content-head version',
        'deu',
        'ch',
        udt/'2.0/ch/de/de-universal-ch-train.conll',
        udt/'2.0/ch/de/de-universal-ch-test.conll',
        udt/'2.0/ch/de/de-universal-ch-dev.conll'))

register(Dataset(
        'spa.ch',
        'Spanish, McDonald universal DTB, content-head version',
        'spa',
        'ch',
        udt/'2.0/ch/es/es-universal-ch-train.conll',
        udt/'2.0/ch/es/es-universal-ch-test.conll',
        udt/'2.0/ch/es/es-universal-ch-dev.conll'))

register(Dataset(
        'fin.ch',
        'Finnish, McDonald universal DTB, content-head version',
        'fin',
        'ch',
        udt/'2.0/ch/fi/fi-universal-ch-train.conll',
        udt/'2.0/ch/fi/fi-universal-ch-test.conll',
        udt/'2.0/ch/fi/fi-universal-ch-dev.conll'))

register(Dataset(
        'fra.ch',
        'French, McDonald universal DTB, content-head version',
        'fra',
        'ch',
        udt/'2.0/ch/fr/fr-universal-ch-train.conll',
        udt/'2.0/ch/fr/fr-universal-ch-test.conll',
        udt/'2.0/ch/fr/fr-universal-ch-dev.conll'))

register(Dataset(
        'swe.ch',
        'Swedish, McDonald universal DTB, content-head version',
        'swe',
        'ch',
        udt/'2.0/ch/sv/sv-universal-ch-train.conll',
        udt/'2.0/ch/sv/sv-universal-ch-test.conll',
        udt/'2.0/ch/sv/sv-universal-ch-dev.conll'))

## uni

register(Dataset(
        'deu.uni',
        'German, McDonald universal DTB, standard version',
        'deu',
        'uni',
        udt/'2.0/std/de/de-universal-train.conll',
        udt/'2.0/std/de/de-universal-test.conll',
        udt/'2.0/std/de/de-universal-dev.conll'))

register(Dataset(
        'spa.uni',
        'Spanish, McDonald universal DTB, standard version',
        'spa',
        'uni',
        udt/'2.0/std/es/es-universal-train.conll',
        udt/'2.0/std/es/es-universal-test.conll',
        udt/'2.0/std/es/es-universal-dev.conll'))

register(Dataset(
        'fra.uni',
        'French, McDonald universal DTB, standard version',
        'fra',
        'uni',
        udt/'2.0/std/fr/fr-universal-train.conll',
        udt/'2.0/std/fr/fr-universal-test.conll',
        udt/'2.0/std/fr/fr-universal-dev.conll'))

register(Dataset(
        'ind.uni',
        'Indonesian, McDonald universal DTB, standard version',
        'ind',
        'uni',
        udt/'2.0/std/id/id-universal-train.conll',
        udt/'2.0/std/id/id-universal-test.conll',
        udt/'2.0/std/id/id-universal-dev.conll'))

register(Dataset(
        'ita.uni',
        'Italian, McDonald universal DTB, standard version',
        'ita',
        'uni',
        udt/'2.0/std/it/it-universal-train.conll',
        udt/'2.0/std/it/it-universal-test.conll',
        udt/'2.0/std/it/it-universal-dev.conll'))

register(Dataset(
        'jpn.uni',
        'Japanese, McDonald universal DTB, standard version',
        'jpn',
        'uni',
        udt/'2.0/std/ja/ja-universal-train.conll',
        udt/'2.0/std/ja/ja-universal-test.conll',
        udt/'2.0/std/ja/ja-universal-dev.conll'))

register(Dataset(
        'kor.uni',
        'Korean, McDonald universal DTB, standard version',
        'kor',
        'uni',
        udt/'2.0/std/ko/ko-universal-train.conll',
        udt/'2.0/std/ko/ko-universal-test.conll',
        udt/'2.0/std/ko/ko-universal-dev.conll'))

register(Dataset(
        'por.uni',
        'Portuguese, McDonald universal DTB, standard version',
        'por',
        'uni',
        udt/'2.0/std/pt-br/pt-br-universal-train.conll',
        udt/'2.0/std/pt-br/pt-br-universal-test.conll',
        udt/'2.0/std/pt-br/pt-br-universal-dev.conll'))

register(Dataset(
        'swe.uni',
        'Swedish, McDonald universal DTB, standard version',
        'swe',
        'uni',
        udt/'2.0/std/sv/sv-universal-train.conll',
        udt/'2.0/std/sv/sv-universal-test.conll',
        udt/'2.0/std/sv/sv-universal-dev.conll'))

##  Iterator over Penn Treebank sentences.

def ptb_sents (which=None):
    from seal.data import ptb
    from seal.head import mark_heads
    from seal.dep import dependency_tree, stemma, convert
    for tree in ptb.iter_trees(categories=which):
        yield convert(tree, reductions=True, ccheads=True)

register(FilterDataset(
        'eng.dep',
        'English, Penn Treebank, Magerman-Collins heads',
        'eng',
        'dep',
        ptb_sents))

##  Iterator over Penn Treebank umapped sentences.

def ptb_umap_sents (which=None):
    map = load_umap(conll/'2006/universal-pos-tags/en-ptb.map')
    for sent in ptb_sents(which):
        apply_umap(map, sent)
        yield sent

register(FilterDataset(
        'eng.umap',
        'English, Penn Treebank, Magerman-Collins heads, mapped to Das/Petrov tags',
        'eng',
        'umap',
        ptb_umap_sents))
