##  @package seal.nlp.dp.nnproj
#   Pseuo-projective parsing functions.

from ..cld.seal.io import tabular
from ..nlp.dep import Sentence


#--  Pseudo-projective parsing functions  --------------------------------------

##  The distance between governor and dependent.

def width (edge):
    (g,d) = edge
    if g <= d: return d - g
    else: return g - d

##  Compare two arcs first by width, then by which contains the earliest word.

def arc_cmp (span1, span2):
    if width(span1) < width(span2): return -1
    elif width(span1) > width(span2): return +1
    else:
        (g1,d1) = span1
        (g2,d2) = span2
        if (g1 < g2 and g1 < d2) or (d1 < g2 and d1 < d2): return -1
        elif (g2 < g1 and g2 < d1) or (d2 < g1 and d2 < d1): return +1
        else: return 0
    
##  Whether g is the governor of ... the governor of d.

def dominates (g, d, govrs):
    count = 0
    while d is not None:
        if d == g: return True
        count += 1
        if count >= len(govrs):
            raise Exception('Cycle detected')
        d = govrs[d]
    return False

##  Whether the given edge is crossed by any other edges.
#   Partition the words into the two words of the edge, the interior
#   (words between them), and the exterior (everything else).
#   The edge is nonproj if any word in the interior is connected by
#   an edge to any word in the exterior.

def is_nonproj (edge, govrs):
    (g,d) = edge
    if g <= d: (i,j) = (g,d)
    else: (i,j) = (d,g)
    for k in range(i+1, j):
        if not dominates(g, k, govrs):
            return True
    return False

##  Whether there are any nonproj edges.

def has_nonproj_arcs (govrs):
    for d in range(1, len(govrs)):
        g = govrs[d]
        if is_nonproj((g,d), govrs):
            return True
    return False

##  Check that the pgovrs are in fact projective.

def check_pgovrs (sent):
    govrs = [sent.pgovr(i) for i in range(len(sent))]
    return not has_nonproj_arcs(govrs)

##  An iteration over nonproj edges, if any.

def nonproj_arcs (govrs):
    for d in range(1, len(govrs)):
        g = govrs[d]
        arc = (g,d)
        if is_nonproj(arc, govrs):
            yield arc

##  The earliest nonproj edge.

def next_nonproj_arc (govrs):
    best_arc = None
    for d in range(1, len(govrs)):
        g = govrs[d]
        arc = (g,d)
        if is_nonproj(arc, govrs) and \
                (best_arc is None or arc_cmp(arc, best_arc) < 0):
            best_arc = arc
    return best_arc


#--  Projectivizer  ------------------------------------------------------------

##  Projetivize either a single sentence or a list of sentences.

def projectivize (x):
    if isinstance(x, Sentence):
        p = Projectivizer()
        return p(x)
    else:
        return projectivize_sents(x)

##  Projectivize a list of sentences.

def projectivize_sents (sents):
    p = Projectivizer()
    for sent in sents:
        yield p(sent)


##  For projectivizing a single sentence.

class Projectivizer (object):

    ##  Constructor.

    def __init__ (self):

        ##  The original sentence.
        self.orig = None

        ##  The governor array.
        self.govrs = None

        ##  Roles corresponding to the governors.
        self.roles = None

        ##  Which dependents have had their governors lifted so far.
        self.lifted = None

        ##  The number of lifts so far.
        self.nlifts = None

    ##  Replace the governor in the edge with its governor.

    def lift (self, edge):
        (g, d) = edge
        h = self.govrs[g]
        assert h is not None
        self.govrs[d] = h
        if not self.lifted[d]:
            self.lifted[d] = True
            self.roles[d] = '%s|%s' % (self.orig.role(g), self.orig.role(d))

    ##  String representation.

    def __str__ (self):
        arcs = ['(%d, %s)' % (self.govrs[i], i) for i in range(1, len(self.govrs))]
        return ' '.join(arcs)

    ##  Set the sentence to be processed.

    def set_sent (self, sent):
        self.orig = sent
        self.govrs = [sent[i].govr for i in range(len(sent))]
        self.roles = [sent[i].role for i in range(len(sent))]
        self.lifted = [False for i in range(len(sent))]
        for role in self.roles:
            if role and '|' in role:
                raise Exception("Role already lifted: contains '|'")
        self.nlifts = 0

    ##  Run it.

    def run (self):
        while True:
            arc = next_nonproj_arc(self.govrs)
            if arc is None: break
            self.lift(arc)
            self.nlifts += 1

    ##  Create a copy of the original sentence, using the governor and role
    #   arrays.

    def sentence (self):
        s = self.orig.copy()
        for i in range(1, len(s)):
            s[i].govr = self.govrs[i]
            s[i].role = self.roles[i]
        return s

    ##  Call it.  Calls set_sent(), then run(), then returns sentence().

    def __call__ (self, sent):
        self.set_sent(sent)
        self.run()
        return self.sentence()

    ##  Like __call__(), but returns a pair: the sentence and the number of lifts.

    def stats (self, sent):
        self.set_sent(sent)
        self.run()
        return (self.sentence(), self.nlifts)


#--  Reverter  -----------------------------------------------------------------

##  Undo projectivization.

def revert (x):
    if isinstance(x, Sentence):
        return Reverter()(x)
    else:
        return revert_sents(x)

##  Revert a list of sentences.

def revert_sents (sents):
    r = Reverter()
    for sent in sents:
        yield r(sent)

##  Reverter.

class Reverter (object):

    ##  Constructor.

    def __init__ (self):

        ##  Original sentence.
        self.orig = None

        ##  Governors array.
        self.govrs = None

        ##  Roles.
        self.roles = None

        ##  Dependent lists, one for each word.
        self.deps = None


    ##  Set the sentence.

    def set_sent (self, sent):
        self.orig = sent
        self.govrs = [sent.govr(i) for i in range(len(sent))]
        self.roles = [sent.role(i) for i in range(len(sent))]
        self.deps = [[] for i in range(len(sent))]
        for d in range(len(sent)):
            g = self.govrs[d]
            if g is not None:
                self.deps[g].append(d)

    ##  Call it.  Call set_sent(), then run(), then return sentence().

    def __call__ (self, sent):
        self.set_sent(sent)
        self.run()
        return self.sentence()

    ##  Run it.  It uses roles containing "|" to give guidance about where
    #   to unlift governors.

    def run (self):
        for d in range(1, len(self.roles)):
            if '|' in self.roles[d]:
                self.lower(d)
        
    ##  Unlift.

    def lower (self, d):
        role = self.roles[d]
        (grole, drole) = role.split('|')
        old_g = self.govrs[d]
        new_g = self.find_govr(old_g, grole)
        if new_g is None:
            self.roles[d] = drole
        else:
            self.govrs[d] = new_g
            self.roles[d] = drole
            self.deps[old_g].remove(d)
            ds = self.deps[new_g]
            ds.append(d)
            ds.sort()

    ##  Find a word with a given role.

    def find_govr (self, w, grole):
        assert isinstance(w,int)
        todo = []
        todo.extend(self.deps[w])
        while todo:
            w = todo.pop(0)
            if self.roles[w] == grole:
                return w
            todo.extend(self.deps[w])

    ##  Return a copy of the original sentence, using the governor and role arrays.

    def sentence (self):
        s = self.orig.copy()
        for i in range(1, len(s)):
            s[i].govr = self.govrs[i]
            s[i].role = self.roles[i]
        return s

    ##  String representation.

    def __str__ (self):
        lines = [(i, self.govrs[i], self.roles[i]) for i in range(len(self.govrs))]
        return tabular(lines)
        

#--  Stats  --------------------------------------------------------------------

##  Call a StatCompiler to create a set of statistics.

def stats (x):
    return StatCompiler()(x)

##  Print out statistics.

def print_stats (sents):
    index = StatCompiler()(sents)
    proj = rev_nontriv = notrev = nsents = 0
    keys = sorted(index)
    rev_lifts = {}
    notrev_lifts = {}

    for key in keys:
        n = len(index[key])
        nsents += n
        if not isinstance(key, tuple): raise Exception('Bad key')
        elif key[0] == 'not-revertible':
            nlifts = key[1]
            if nlifts == 0:
                raise Exception('Failed trivial sentences')
            else:
                notrev += n
                if nlifts in notrev_lifts: notrev_lifts[nlifts] += n
                else: notrev_lifts[nlifts] = n
        elif key[0] == 'revertible':
            nlifts = key[1]
            if nlifts == 0: proj += n
            else:
                rev_nontriv += n
                if nlifts in rev_lifts: rev_lifts[nlifts] += n
                else: rev_lifts[nlifts] = n
        else: raise Exception('Bad key')

    # non-projective
    nonproj = rev_nontriv + notrev

    print('Projective:      ', proj, '/', nsents, '(%f%%)' % ((proj*100.0)/nsents))
    print('Not projective:  ', nonproj, '/', nsents, '(%f%%)' % ((nonproj*100.0)/nsents))
    print()
    if nonproj > 0:
        print('Not projective:')
        print('  Revertible:    ', rev_nontriv, '/', nonproj, '(%f%%)' % ((rev_nontriv*100.0)/nonproj))
        print('  Not revertible:', notrev, '/', nonproj, '(%f%%)' % ((notrev*100.0)/nonproj))
        print()

    if rev_lifts:
        print('Revertible:')
        for nlifts in sorted(rev_lifts):
            print('  %2d lifts: %5d' % (nlifts, rev_lifts[nlifts]))
        print()

    if notrev_lifts:
        print('Not revertible:')
        for nlifts in sorted(notrev_lifts):
            print('  %2d lifts: %5d' % (nlifts, notrev_lifts[nlifts]))

##  Stat compiler.

class StatCompiler (object):

    ##  Constructor.

    def __init__ (self):

        ##  A Projectivizer.
        self.p = Projectivizer()

        ##  A Reverter.
        self.r = Reverter()

    ##  Call it on a single sentence or a list of sentences.

    def __call__ (self, x):
        if isinstance(x, Sentence):
            return self.stats(x)
        else:
            return self.stats_table(x)

    ##  Construct a stats table.

    def stats_table (self, sents):
        index = {}
        for sent in sents:
            key = self.stats(sent)
            if key in index: index[key].append(sent.index())
            else: index[key] = [sent.index()]
        return index        

    ##  Compute statistics for a single sentence.
    #   Determines whether projectivizing and then reverting successfully restores
    #   the original sentence.  Return value is a pair: either 'revertible' or
    #   'not-revertible', and the number of lifts needed.

    def stats (self, sent):
        (psent, nlifts) = self.p.stats(sent)
        rsent = self.r(psent)
        if rsent == sent: rev = 'revertible'
        else: rev = 'not-revertible'
        return (rev, nlifts)
