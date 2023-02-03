##  @package seal.data.ptb
#   The Penn Treebank.

import os
from os.path import expanduser, join
from seal.core import config
from seal.core.io import data
from seal.nlp.tree import TreeBuilder

##  Home directory for the treebank.
Home = config.ptb
if not Home:
    raise Exception('Configuration variable not set: data.ptb')

##  The filename of the table of treebank files.
map_filename = join(data, 'seal', 'ptb_filenames')

_map = None
_reverse_map = None

##  Maps category name to (start, end) indices in the list of corpus files.
category_table = {
    'dev_train'   : (  0,   199),
    'train'       : ( 199, 2074),
    'reserve_test': (2074, 2157),
    'test'        : (2157, 2257),
    'dev_test'    : (2257, 2312),
    '00'          : (   0,   99),
    '01'          : (  99,  199),
    '02'          : ( 199,  299),
    '03'          : ( 299,  380),
    '04'          : ( 380,  480),
    '05'          : ( 480,  580),
    '06'          : ( 580,  680),
    '07'          : ( 680,  780),
    '08'          : ( 780,  801),
    '09'          : ( 801,  901),
    '10'          : ( 901, 1001),
    '11'          : (1001, 1101),
    '12'          : (1101, 1201),
    '13'          : (1201, 1301),
    '14'          : (1301, 1401),
    '15'          : (1401, 1501),
    '16'          : (1501, 1601),
    '17'          : (1601, 1701),
    '18'          : (1701, 1801),
    '19'          : (1801, 1901),
    '20'          : (1901, 2001),
    '21'          : (2001, 2074),
    '22'          : (2074, 2157),
    '23'          : (2157, 2257),
    '24'          : (2257, 2312)
    }


#--  Normalization  ------------------------------------------------------------

#  Functions that access pieces of the treebank take a pair of keyword arguments:
#  fileids, categories.  as_fileids() converts them to canonical form, which is
#  an explicit list of fileids.

##  Convert to a list.

def as_list (x):
    if x == None: return []
    elif isinstance(x, list): return x
    elif isinstance(x, (tuple, set, frozenset, range)): return list(x)
    else: return [x]

##  Convert to file IDs.

def as_fileids (fileids=None, categories=None):
    if categories == None:
        if fileids == None: return list(range(2312))
        else: return as_list(fileids)
    else:
        out = as_list(fileids)
        for c in as_list(categories):
            b,e = category_table[c]
            out += list(range(b,e))
        return out


#--  Fileids and categories  ---------------------------------------------------


##  An iterator over the filenames of the treebank files.

def fileids (categories=None, fileids=None):
    return as_fileids(fileids, categories)

##  An iterator over the categories of treebank files.

def categories (fileids=None):
    if fileids == None:
        return sorted(category_table.keys())
    else:
        return sorted(set(c for fid in as_list(fileids) \
                              for c, rng in list(category_table.items()) \
                                  if fid >= rng[0] and fid < rng[1]))


#--  Connecting fileids to the original files  ---------------------------------

##  Orig is a four-digit string, omitting 'wsj_' and '.mrg'.

def fileid_from_orig (orig):
    if len(orig) > 4 and orig[-4] == '.':
        orig = orig[:-4]
    if len(orig) > 4:
        orig = orig[-4:]
    sec = orig[:2]
    fnum = int(orig[2:])
    if sec == '00':
        if fnum == 0: raise Exception("Bad original ID")
        fnum -= 1
    elif sec not in category_table: raise Exception("Bad original ID")
    start,end = category_table[sec]
    id = start + fnum
    if id >= end: raise Exception("Bad original ID")
    return id
    
##  Just to make sure that fileid_from_orig() always does the right thing.

def check_fileids ():
    n = 0
    with open(MapFilename) as f:
        line = line.rstrip()
        id = fileid_from_orig(line)
        if id != n: raise Exception("Mismatch at orig=" + line)
        n += 1
    print("checked", n)

##  Get the filename map.  Loads and caches it the first time it is called.

def get_map ():
    global _map
    if _map is None:
        _map = []
        with open(map_filename) as f:
            for line in f:
                line = line.rstrip('\r\n')
                (fno, section, origfn) = line.split('\t')
                _map.append(join(Home, origfn))
    return _map

##  Returns the filename of the original treebank file corresponding to the
#   i-th file.  The original files contain trees in lisp-style format.

def orig_filename (fileid):
    if fileid < 0 or fileid >= 2312:
        raise KeyError("Index out of bounds")
    return get_map()[fileid]

##  The keys are strings like '1462' for the file '14/wsj_1462.mrg'

def orig_to_fileid (orig_no):
    global _reverse_map
    if _reverse_map is None:
        _reverse_map = {}
        for (fileid,fn) in enumerate(get_map()):
            key = fn[-8:-4]
            _reverse_map[key] = fileid
    return _reverse_map[orig_no]


#--  PtbReader  ----------------------------------------------------------------

##  Keeps track of current line number.

class TrackingReader (object):

    ##  Constructor.

    def __init__ (self, fn):

        ##  The filename.
        self.filename = fn

        ##  The input stream.
        self.file = open(fn)

        ##  The current line number.
        self.lineno = 0

    ##  Returns self.

    def __iter__ (self): return self

    ##  Iterator method.

    def __next__ (self):
        line = self.file.__next__()
        self.lineno += 1
        return line

    ##  Signal an error, printing filename and line number.

    def error (self, msg):
        raise Exception('%s [%s:%d]' % (msg, self.filename, self.lineno))


##  A reader for treebank files.
#   The file format:
#
#    - Nodes are marked by ( )
#
#    - Categories are terminated by whitespace or parentheses
#        - Empty string is possible
#        - Complex category consists of hyphen-separated fields
#        - First field is cat proper
#        - Other alphameric fields are roles
#        - Other numeric fields are ids
#
#    - Examples: NP-SBJ NP-SBJ-1
#
#  Standard node members: cat, word, role, id.
#  Additional: gapid.

class PtbReader (object):

    ##  Constructor.

    def __init__ (self, fn):

        ##  A TrackingReader.
        self.reader = TrackingReader(fn)

        ##  Current line.
        self.line = None

        ##  Current position in the line.
        self.i = None

        ##  The trees for this file.
        self.trees = None

        t = TreeBuilder()

        for line in self.reader:
            self.line = line
            self.i = 0
            while self.i < len(self.line):
                c = self.line[self.i]
                if c == '(':
                    self.i += 1
                    cat = self.scan_word()
                    self.skip_whitespace()
                    word = None
                    if self.i < len(self.line):
                        c2 = self.line[self.i]
                        if c2 not in '()':
                            word = self.scan_word()
                            self.skip_whitespace()
                            c3 = self.line[self.i]
                            if c3 != ')':
                                self.reader.error("Expecting ')' at %d" % self.i)
                            self.i += 1
                    nonterm = (word is None)
                    if cat == '-NONE-':
                        cat = word
                        word = ''  # N.b., not None
                    (cat, role, id, ref) = parse_ptb_cat(cat)
                    if nonterm: node = t.start(cat, role=role, id=id)
                    else: node = t.leaf(cat, word, role=role, id=id)
                    node.ref = ref
                elif c == ')':
                    popped = t.end()
                    self.i += 1
                elif c.isspace():
                    self.i += 1
                else:
                    word = self.scan_word()
                    self.reader.error('Stray word: ' + word)

        self.trees = t.trees()
        self.i = 0

    ##  Scan a word.

    def scan_word (self):
        start = self.i
        while self.i < len(self.line):
            c = self.line[self.i]
            if c.isspace() or c in '()': break
            self.i += 1
        return self.line[start:self.i]

    ##  Skip whitespace.

    def skip_whitespace (self):
        while self.i < len(self.line) and self.line[self.i].isspace():
            self.i += 1

    ##  Returns self.

    def __iter__ (self): return self

    ##  Iterator method.

    def __next__ (self):
        if self.i < len(self.trees):
            t = self.trees[self.i]
            self.i += 1
            return t
        else:
            raise StopIteration


##  Parse a treebank category.
#   Returns a 4-tuple: category, role, ID, ref.
#   The ID is the node's own ID.  The ref is the ID of an antecedent node.
#   (In the original, the ID follows a hyphen and the ref follows an equal sign.)

def parse_ptb_cat (s):

    # Strip id, e.g. "-1"
    id = None
    ref = None
    n = len(s)
    while n > 0 and s[n-1].isdigit():
        n -= 1
    if n < len(s) and n-1 > 0 and s[n-1] == '-':
        id = s[n:]
        s = s[:n-1]
        n -= 1
    while n > 0 and s[n-1].isdigit():
        n -= 1
    if n < len(s) and n-1 > 0 and s[n-1] == '=':
        ref = s[n:]
        s = s[:n-1]

    # Strip role, e.g. "-SBJ"
    role = None
    i = s.find('-')
    if i > 0:
        role = s[i+1:]
        s = s[:i]

    return (s, role, id, ref)


#--  Trees, nodes, words, sents  -----------------------------------------------
    
##  An iterator over the trees of the treebank.

def iter_trees (fileids=None, categories=None):
    for fid in as_fileids(fileids, categories):
        for t in PtbReader(orig_filename(fid)):
            yield t

##  A list of trees.

def trees (fileids=None, categories=None):
    return list(iter_trees(fileids, categories))

##  An iterator over the nodes of all trees.

def nodes (fileids=None, categories=None):
    for tree in iter_trees(fileids, categories):
        for node in tree:
            yield node

##  An iterator over (tag,word) pairs.

def tagged_words (fileids=None, categories=None):
    for tree in iter_trees(fileids, categories):
        for tword in seal.tree.tagged_words(tree):
            yield tword

##  An iterator over the words.

def words (fileids=None, categories=None):
    for fid in as_fileids(fileids, categories):
        f = open(text_filename(fid))
        for word in f.read().split():
            yield word
        f.close()

##  An iterator over sentences.

def sents (fileids=None, categories=None):
    for fid in as_fileids(fileids, categories):
        f = open(text_filename(fid))
        for line in f:
            yield line.split()
        f.close()

##  An iterator over sentence strings.

def raw_sents (fileids=None, categories=None):
    for fid in as_fileids(fileids, categories):
        f = open(text_filename(fid))
        for line in f:
            yield line.rstrip('\n')
        f.close()

#--  Summaries  ----------------------------------------------------------------

##  A list of nonterminal categories.
nonterminal_categories = ['ADJP', 'ADVP', 'ADVP|PRT', 'CONJP', 'FRAG', 'INTJ', 'LST', 'NAC', 'NP', 'NX', 'PP', 'PRN', 'PRT', 'PRT|ADVP', 'QP', 'RRC', 'S', 'SBAR', 'SBARQ', 'SINV', 'SQ', 'UCP', 'VP', 'WHADJP', 'WHADVP', 'WHNP', 'WHPP', 'X']

##  A list of terminal categories.
parts_of_speech = ['#', '$', "''", ',', '-LRB-', '-RRB-', '.', ':', 'CC', 'CD', 'DT', 'EX', 'FW', 'IN', 'JJ', 'JJR', 'JJS', 'LS', 'MD', 'NN', 'NNP', 'NNPS', 'NNS', 'PDT', 'POS', 'PRP', 'PRP$', 'RB', 'RBR', 'RBS', 'RP', 'SYM', 'TO', 'UH', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'WDT', 'WP', 'WP$', 'WRB', '``']

##  A list of empty categories.
empty_categories = ['*', '*?*', '*EXP*', '*ICH*', '*NOT*', '*PPA*', '*RNR*', '*T*', '*U*', '0']

def _iter_categories ():
    for node in nodes():
        if node.children:
            type = 0
        elif node.word:
            type = 1
        else:
            type = 2
        yield (node.cat, type)

##  Returns a tuple containing three sets: the set of categories actually
#   appearing on nonterminal nodes (nodes with children), the set of categories
#   actually appearing on nodes with a value for node.word, and the set of
#   categories for empty nodes (neither children nor word).

def collect_categories ():
    cats = [set(), set(), set()]
    for (c,t) in _iter_categories():
        cats[t].add(c)
    return cats
