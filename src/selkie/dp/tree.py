##  @package seal.nlp.dp.tree
#   Dependency tree.  Not actually used.


#--  DepTree (not used)  -------------------------------------------------------

##  A dependency tree.

class DepTree (object):

    ##  Constructor.

    def __init__ (self, conll):

        ##  CoNLL dataset.
        self.conll = conll
        n = len(conll)

        ##  Dependent lists, one for each word including Root.
        self.dependents = [[] for i in range(n)]

        ##  Spans, one for each word including Root.
        self.pspans = [None for i in range(n)]

        ##  Governors, one for each word including Root.
        self.governors = [None] + [self.conll.govr(i)
                                   for i in range(1, len(self.dependents))]

        self.compute_dependents()
        self.compute_pspan(0)

    ##  Called by constructor.

    def compute_dependents (self):
        for d in range(1, len(self.dependents)):
            g = self.conll.govr(d)
            self.dependents[g].append(d)

    ##  Iterates over positions of words that have no dependents.

    def leaves (self):
        for g in range(len(self.dependents)):
            if not self.dependents[g]:
                yield g

    ##  Called by constuctor.

    def compute_pspan (self, g):
        deps = self.dependents[g]
        for d in deps:
            self.compute_pspan(d)
        h = 0
        while h < len(deps) and deps[h] < g:
            h += 1
        ldeps = deps[h-1::-1]
        rdeps = deps[h:]
            
        i = j = g
        for d in ldeps:
            (di,dj) = self.pspans[d]
            if dj == i - 1:
                i = di
            else:
                break
        for d in rdeps:
            (di,dj) = self.pspans[d]
            if di == j + 1:
                j = dj
            else:
                break
        self.pspans[g] = (i,j)

    ##  String representation.

    def __str__ (self):
        lines = ['Governors:']
        lines += ['%d: %s' % (i,g)
                  for (i,g) in enumerate(self.governors)]
        lines += ['Dependents:']
        lines += ['%d: %s' % (i, deps)
                  for (i,deps) in enumerate(self.dependents)]
        lines += ['P-Spans:']
        lines += ['%d: %d %d' % (i, j, k)
                  for (i,(j,k)) in enumerate(self.pspans)]
        return '\n'.join(lines)

