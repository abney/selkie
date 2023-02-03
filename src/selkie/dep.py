##  @package seal.nlp.dep
#   Dependency trees.

import os
from .data import path
from .io import as_ascii, tabular, iter_records, \
    iter_record_blocks, outfile, StringIO
from .tree import Tree, head_index, is_dependency_tree, textorder, \
    getcat, getchildren, getid, getrole, getword, copy_tree
from .head import mark_heads, mark_cc_heads
from .stemmer import stemmer


#--  Top level  ----------------------------------------------------------------

##  Convert among tree types.  The sequence is:
#    - 'tree' - an undigested tree.
#    - 'headed' - tree with heads marked.
#    - 'dep' - a tree of dependencies.
#    - 'stemma' - a dependency stemma.
#    - 'efstemma' - an epsilon-free stemma.
#   One may convert from any type in the sequence to any later type.
#
#   Conversion is non-destructive.  If a destructive step is called, the tree
#   is copied first.

def convert (tree, input='tree', output='efstemma', destructive=False,
             projections=False, reductions=False, ccheads=False):
    t = input
    if t == output: return tree
    if t == 'tree':
        if not destructive: tree = copy_tree(tree)
        if ccheads: mark_cc_heads(tree)
        mark_heads(tree)
        t = 'headed'
        if t == output: return tree
    if t == 'headed':
        tree = dependency_tree(tree, projections, reductions)
        t = 'dep'
        if t == output: return tree
    if t == 'dep':
        tree = stemma(tree)
        t = 'stemma'
        if t == output: return tree
    if t == 'stemma':
        tree = tree.eliminate_epsilons()
        t = 'efstemma'
        if t == output: return tree
    raise Exception('Bad input-output types: %s -> %s' % (input, output))


#--  Conversion to dependency tree  --------------------------------------------

##  Convert to a dependency tree.  Non-destructive.
#   Signals an error unless every interior node has a head.


def dependency_tree (tree, projections=False, reductions=False):
    return Projection(tree).tree(projections, reductions)


#--  Projection  ---------------------------------------------------------------

##  A projection.  Used in the conversion from a tree to a dependency tree.

class Projection (object):

    ##  Constructor.

    def __init__ (self, node, lr=None, parent=None, headsib=None):

        ##  Whether this projection is a left dependent ('L') or right dependent
        #   ('R') of its governor.
        self.lr = lr

        ##  The parent node.
        self.parent = parent

        ##  The governing sibling of this projection.
        self.headsib = headsib

        ##  The children.
        self.nodes = []

        ##  The left dependents.
        self.ldeps = []

        ##  The right dependents.
        self.rdeps = []

        self.append(node)

    ##  String representation.

    def __repr__ (self):
        return '<Projection ' + ' '.join(getcat(n) for n in self.nodes) + \
            ' ' + getword(self.nodes[-1]) + '>'

    ##  Add a node to the projection.  It non-head children are converted
    #   to Projections and become dependents of this projection.

    def append (self, node):
        self.nodes.append(node)
        children = getchildren(node)
        if children:
            h = head_index(node)
            if h < 0:
                if len(children) == 1: h = 0
                else: raise Exception("Cannot convert unheaded tree to dependencies")
            head = children[h]
            for child in children[:h]:
                self.ldeps.append(Projection(child, "L", node, head))
            self.append(head)
            for child in children[h+1:]:
                self.rdeps.append(Projection(child, "R", node, head))

    ##  Convert this to a Tree.

    def tree (self, projections=False, reductions=False):
        if projections: cat = '_'.join(getcat(n) for n in self.nodes)
        else: cat = getcat(self.nodes[-1])
        
        if self.parent:
            if reductions:
                role = Reduction(self.lr,
                                 getcat(self.nodes[0]), getrole(self.nodes[0]),
                                 getcat(self.parent), getcat(self.headsib))
            else: role = getrole(self.nodes[0])
        else:
            if reductions: role = Reduction(role='root')
            else: role = 'root'

        if self.ldeps or self.rdeps:
            nld = len(self.ldeps)
            children = [child.tree(projections, reductions)
                        for child in self.ldeps + self.rdeps]
        else:
            nld = None
            children = None

        ids = [getid(n) for n in self.nodes if getid(n)]
        if ids: id = '_'.join(ids)
        else: id = None

        return Tree(cat, children, nld=nld, word=getword(self.nodes[-1]),
                    role=role, id=id)


#--  Reduction  ----------------------------------------------------------------

##  A complex dependency role.  The form is: L/R dep-cat role parent-cat head-cat.

class Reduction (object):

    ##  Constructor.

    def __init__ (self, lr=None, dep=None, role=None, parent=None, head=None):

        ##  Whether this is a left ('L') or right ('R') dependent of its governor.
        self.lr = lr

        ##  The dependent's category.
        self.dep = dep

        ##  The role category.
        self.role = role

        ##  The parent category.
        self.parent = parent

        ##  The head category.
        self.head = head

    ##  Comparison is based on string representation.

    def __lt__ (self, other):
        return str(self) < str(other)

    ##  Comparison is based on string representation.

    def __eq__ (self, other):
        return str(self) == str(other)

    ##  Hash value is based on string representation.

    def __hash__ (self):
        return hash(str(self))

    ##  The string representation: L/R dep-cat role par-cat head-cat.

    def __str__ (self):
        if self.role == 'root':
            return self.role
        else:
            if self.dep: d = str(self.dep)
            else: d = ''
            if self.role: r = ':' + str(self.role)
            else: r = ''
            if self.parent: p = str(self.parent)
            else: p = ''
            if self.head: h = str(self.head)
            else: h = ''
            return self.lr + '_' + d + r + '_' + p + '_' + h

    ##  String representation.

    def __repr__ (self):
        return "<Reduction %s>" % str(self)


#-- Conversion to stemma  ------------------------------------------------------

##  Convert to a stemma.
#   A stemma is a list of Word instances.

def stemma (d):
    nodes = [None] + list(textorder(d))
    words = [Word(index=i,
                  form=getword(nodes[i]),
                  role=getrole(nodes[i]),
                  cat=getcat(nodes[i]))
             for i in range(len(nodes))]
    # compute governors
    nodeindex = dict((node,i) for (i,node) in enumerate(nodes))
    for (i,govr) in enumerate(nodes):
        children = getchildren(govr)
        if children:
            for child in children:
                j = nodeindex[child]
                w = words[j]
                if w.govr:
                    raise Exception("Multiple governors for " + repr(w))
                w.govr = i
    return Sentence(words)

##  Converts a stemma to a list of governor indices.

def governor_array (x):
    if not isinstance(x, Sentence):
        x = stemma(x)
    return [d.govr for d in x[1:]]


#--  Word and Sentence  --------------------------------------------------------

def _catstr (cat):
    if isinstance(cat, tuple): return '.'.join(cat)
    else: return cat

##  A word in a stemma.

class Word (object):

    ##  Constructor.

    def __init__ (self, index=None, form=None, cat=None, lemma=None, morph=None, govr=0, role=None, cpos=None):

        ##  The sentence.
        self.sent = None

        ##  Its position in the sentence.
        self.index = index

        ##  The word string.
        self.form = form

        ##  The word's category.
        self.cat = cat

        ##  The coarse part of speech.
        self.cpos = cpos

        ##  The lemma.
        self.lemma = lemma

        ##  The morphological analysis.
        self.morph = morph

        ##  The index of the governor.
        self.govr = govr

        ##  The role.
        self.role = role

    ##  Duplicate.

    def copy (self):
        return Word(None, self.form, self.cat, self.lemma, self.morph, self.govr, self.role, self.cpos)

    ##  An immutable key.  A tuple of form, cat, lemma, morph, govr, role, cpos.

    def key (self):
        return (self.form or '',
                self.cat or '',
                self.lemma or '',
                self.morph or '',
                self.govr or '',
                self.role or '',
                self.cpos or '')

    ##  Comparison is based on keys.

    def __lt__ (self, other):
        return self.key() < other.key()

    ##  Comparison is based on keys.

    def __eq__ (self, other):
        return self.key() == other.key()

    ##  A readable brief representation.

    def analysis_string (self):
        if self.lemma: s = as_ascii(self.lemma)
        else: s = ''
        if self.cpos: s += '/' + self.cpos
        if self.morph: s += '.' + self.morph
        return s

    ##  String representation.

    def __repr__ (self):
        if self.cat: catstr = '/' + _catstr(self.cat)
        else: catstr = ''
        if self.lemma or self.cpos or self.morph:
            s = self.analysis_string()
            if len(s) > 15: s = s[:12] + '...'
            lemstr = ' (' + s + ')'
        else:
            lemstr = ''
        if self.role: rolestr = ':%s' % self.role
        else: rolestr = ''
        if self.govr is None: govrstr = ''
        else: govrstr = ' govr=' + str(self.govr)

        return '<Word %s %s%s%s%s%s>' % \
            (self.index, as_ascii(self.form), catstr, rolestr, lemstr, govrstr)

    ##  Tagged word string.

    def tagged_string (self):
        return str(self.form) + '_' + str(self.cat)


def _visible (s):
    if s is None or s == '': return '_'
    else: return s


##  A sentence.

class Sentence (object):

    ##  The root sentinel, of type Word.
    Root = Word(index=0, form='*root*', govr=None)

    ##  Constructor.

    def __init__ (self, words=None, index=None):
        if not isinstance(index, (type(None), int, str)):
            raise Exception('Index must be an integer or string: %s' % repr(index))
        self._index = index
        self._words = [self.Root]
        if words:
            for w in words:
                self.append(w)

    ##  Duplicate.

    def copy (self):
        return Sentence((w.copy() for w in self._words[1:]),
                        self._index)

    ##  The index of the sentence in the corpus.

    def index (self):
        return self._index

    ##  Sentence provenance.

    def provenance (self):
        if self._index is None: return ''
        else: return str(self._index)

    ##  Number of words, including Root.  The "real" words are at positions 1-n, inclusive.

    def __len__ (self):
        return len(self._words)

    ##  Iteration over the words; Root is the first.

    def __iter__ (self):
        return iter(self._words)

    ##  Returns the i-th word, with Root being word 0.

    def __getitem__ (self, i):
        return self._words[i]

    ##  A copy of the list of word forms, excluding Root.

    def words (self):
        return [self._words[i].form for i in range(1, len(self._words))]

    ##  A copy of the list of lemmas, excluding Root.

    def lemmata (self):
        return [self._words[i].lemma for i in range(1, len(self._words))]

    ##  The number of "real" words (excluding Root).

    def nwords (self):
        return len(self._words) - 1

    ##  A key for the entire sentence.

    def key (self):
        return list(self._words[i] for i in range(1, len(self._words)))

    ##  Comparison is by key.

    def __lt__ (self, other):
        return self.key() < other.key()

    ##  Comparison is by key.

    def __eq__ (self, other):
        return self.key() == other.key()

    ##  Add a word to the sentence.  The word type must be the same as Root's type.

    def append (self, w):
        if w.__class__ != self.Root.__class__:
            raise Exception('Wrong type of word for sentence')
        if w.index is None and w.sent is None:
            w.index = len(self._words)
            w.sent = self
            self._words.append(w)
        elif w.index == 0 and len(self._words) == 1:
            pass
        elif w.index != len(self._words):
            raise Exception('Wrong index: %s' % repr(w))
        elif w.sent:
            raise Exception('This word already belongs to a sentence')
        else:
            self._words.append(w)
            w.sent = self

    ##  The form of the i-th word.

    def form (self, i):
        return self._words[i].form

    ##  The category of the i-th word.

    def cat (self, i):
        return self._words[i].cat

    ##  The coarse part of speech of the i-th word.

    def cpos (self, i):
        return self._words[i].cpos

    ##  The lemma of the i-th word.

    def lemma (self, i):
        return self._words[i].lemma

    ##  The morphological form of the i-th word.

    def morph (self, i):
        return self._words[i].morph

    ##  The governor of the i-th word.

    def govr (self, i):
        return self._words[i].govr

    ##  The role of the i-th word.

    def role (self, i):
        return self._words[i].role

    ##  In the tabular format, the column corresponding to the given feature name.
    #   The valid names are: 'form', 'cat', 'lemma', 'morph', 'govr', 'role'.
    #   The return value is a list of feature values, one for each word including Root.

    def column (self, name):
        assert name in ['form', 'cat', 'lemma', 'morph', 'govr', 'role']
        f = getattr(self, name)
        return tuple(f(i) for i in range(0, len(self._words)))

    ##  The (tabular) string representation.

    def __str__ (self):
        return tabular((_visible(d.index),
                        _visible(d.form),
                        _visible(_catstr(d.cat)),
                        _visible(d.analysis_string()),
                        _visible(d.role),
                        _visible(d.govr)) for d in self._words)

    ##  Whether there are any words whose form is boolean false.

    def contains_epsilons (self):
        for w in self._words:
            if not w.form: return True
        return False

    ##  Eliminate empty words.  Adjusts governor indices.  Non-destructive;
    #   returns a new Sentence.

    def eliminate_epsilons (self):
        if not self.contains_epsilons():
            return self
        newwords = []
        newindex = [None for i in range(len(self._words))]
        for (i,w) in enumerate(self._words):
            if w.form:
                w2 = w.copy()
                newindex[i] = w2.index = len(newwords)
                newwords.append(w2)
        for w in newwords[1:]:
            g = w.govr
            while not self._words[g].form:
                g = self._words[g].govr
            w.govr = newindex[g]
            if w.govr is None: raise Exception('Missing govr: %d' % g)
        return Sentence(index=self._index, words=newwords[1:])

    ##  Sets values for lemma, cpos, and morph.
    #   It calls the stemmer on each word form to get the lemma (throwing
    #   away the suffix).  Calls split_pos() on the category to produce
    #   cpos and morph.

    def lemmatize (self):
        self._words[0].lemma = '*root*'
        for i in range(1, len(self._words)):
            w = self._words[i]
            (lemma, _) = stemmer(w.form)
            (cpos, morph) = split_pos(w.cat)
            w.lemma = lemma
            w.cpos = cpos
            w.morph = morph


##  Table used by split_pos().
split_pos_table = {'VBZ': ('V', '3s'),
                   'VBG': ('V', 'ing'),
                   'VBN': ('V', 'en'),
                   'VBP': ('V', 'pl'),
                   'VBD': ('V', 'ed'),
                   'NN': ('N', 'sg'),
                   'NNS': ('N', 'pl')}
                   
##  Split a part of speech into coarse part of speech and morphology.
#   The categories that get split are listed in split_pos_table.
#   Otherwise, the coarse POS is identical to the category and morph is
#   the empty string.

def split_pos (pos):
    global split_pos_table
    if pos in split_pos_table:
        return split_pos_table[pos]
    else:
        return (pos, '')


##  Create a Sentence containing n empty words.
#   Each word has a correct index, but otherwise no information.

def make_sentence (n, index=None):
    s = Sentence(index=index)
    for i in range(1, n+1):
        s.append(Word(index=i))
    return s


#--  Conversion to dep lists  --------------------------------------------------

##  Conversion to lists of dependents.

class DepLists (object):

    ##  Constructor.

    def __init__ (self, sent):

        ##  The sentence.
        self.sentence = sent

        ##  Lists of dependents, one list for each word.
        self.deps = [list() for i in range(len(sent._words))]

        for j in range(1, len(sent._words)):
            i = sent._words[j].govr
            self.deps[i].append(j)

    ##  The number of words (including Root).

    def __len__ (self):
        return self.deps.__len__()

    ##  The i-th word.

    def __getitem__ (self, i):
        return self.deps.__getitem__(i)

    ##  Iterate over the lists of dependents.

    def __iter__ (self):
        return self.deps.__iter__()

    ##  String representation.

    def __str__ (self):
        output = StringIO()
        for i in range(len(self.sentence)):
            if i: output.write('\n')
            output.write('[%d] %s' % (i, self.sentence[i].form))
            for j in self.deps[i]:
                output.write('\n')
                output.write('        %s: [%d] %s' % (self.sentence[j].role, j, self.sentence[j].form))
        s = output.getvalue()
        output.close()
        return s


#--  ConllFile  ----------------------------------------------------------------

##  Iterates over the records of a CoNLL-format file, convert to Sentences.
#   If the filename ends with '\#proj', or projective=True, the input is
#   converted to projective form.

def conll_parse_file (fn, projective=None):
    fn = str(fn)
    if fn.endswith('#proj'):
        if projective is None: projective = True
        fn = fn[:-5]
    elif fn.endswith('#std'):
        if projective is None: projective = False
        fn = fn[:-4]
    index = 0
    sent = None
    for record in iter_records(fn):
        # Word record
        if len(record) == 10:
            if sent is None:
                sent = Sentence(index=index)
                index += 1
            sent.append(conll_parse_record(record, projective))
        elif len(record) == 1:
            if sent is not None:
                yield sent
                sent = None
            if record[0] != '':
                yield record[0]
    if sent is not None:
        yield sent

##  Parse one record.  Returns a Word.

def conll_parse_record (record, projective=False):
    for i in range(len(record)):
        if record[i] == '_': record[i] = ''
    (i, form, lemma, cpos, fpos, morph, govr, role, pgovr, prole) = record
    i = int(i)
    if projective:
        govr = pgovr
        role = prole
    if govr: govr = int(govr)
    if fpos:
        cat = fpos
    elif cpos:
        cat = cpos
        cpos = None
    else:
        cat = ''
    w = Word(i, form, cat, lemma, morph, govr, role)
    w.cpos = cpos
    return w

##  An iterator over the sentences of a CoNLL-format file.
#   This calls conll_parse_file() and (optionally) lemmatizes each
#   sentence.

def conll_sents (fn, projective=None, lemmatize=False):
    for sent in conll_parse_file(fn, projective):
        if isinstance(sent, Sentence):
            if lemmatize: sent.lemmatize()
            yield sent

##  Load a umap.
#   A umap maps parts of speech to universal POS tags.

def load_umap (fn):
    if not os.path.isabs(fn):
        fn = path('conll', '2006', 'universal-pos-tags', fn)
    pairs = [line.rstrip('\r\n').split('\t') for line in open(fn)]
    return dict(pairs)

##  Destructively convert the categories in a sentence.

def apply_umap (map, sent):
    for w in sent[1:]:
        w.cat = map[w.cat]

##  Call conll_sents() and then apply_umap() on each sentence.
#   Iterates over Sentences.

def umapped_sents (fn, map, projective=False):
    for sent in conll_sents(fn, projective):
        apply_umap(map, sent)
        yield sent


#--  Iter/Load/Save Sentences  -------------------------------------------------

##  Synonym for conll_sents().

def iter_sentences (fn, lemmatize=False):
    return conll_sents(fn, lemmatize=lemmatize)

##  Calls iter_sentences() and constructs a list.

def load_sentences (fn, lemmatize=False):
    return list(iter_sentences(fn, lemmatize))

##  Save sentences to a file.

def save_sentences (sents, fn):
    file = outfile(fn)
    for sent in sents:
        write_sentence(sent, file)
    file.close()

##  Write sentences to an output stream.

def write_sentence (sent, f):
    for word in sent:
        if word.index > 0:
            f.write('%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t_\t_\n' %
                    (word.index,
                     word.form or '_',
                     word.lemma or '_',
                     word.cpos or '_',
                     word.cat or '_',
                     word.morph or '_',
                     word.govr,
                     word.role or '_'))
    f.write('\n')


#--  Paragraphs  ---------------------------------------------------------------

##  Iterate over paragraphs.
#   Empty lines in the original mark paragraph boundaries.

def iter_paragraphs (fn, projective=None, lemmatize=False):
    par = []
    for item in conll_parse_file(fn, projective):
        if isinstance(item, Sentence):
            par.append(item)
        else:
            if par:
                yield par
                par = []
    if par:
        yield par

##  Load a list of paragraphs from a file.

def load_paragraphs (fn, projective=None, lemmatize=False):
    return list(iter_paragraphs(fn, projective, lemmatize))

##  Save paragraphs.

def save_paragraphs (pars, fn):
    f = outfile(fn)
    for par in pars:
        f.write('P\n')
        for sent in par:
            write_sentence(sent, f)
    f.close()
