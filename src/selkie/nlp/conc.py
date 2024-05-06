##  @package seal.nlp.conc
#   Concordance.

from .tree import Tree, child_index, terminal_string, set_parents
from .map import Index
from .seq import intersect
from .com import more


##  Return a line of output, ready for printing.

def render_string (data, i):
    lc = []
    nc = 0
    for j in range(i-1, -1, -1):
        lc.append(data[j])
        nc += len(data[j]) + 1
        if nc >= 40: break
    lc = ' '.join(reversed(lc))
    if len(lc) > 40: lc = lc[-40:]
    
    rc = []
    nc = 0
    for j in range(i, len(data)):
        rc.append(data[j])
        nc += len(data[j]) + 1
        if nc >= 50: break
    rc = ' '.join(rc)
    if len(rc) > 50: rc = rc[:50]

    return '%40s  %50s' % (lc, rc)


##  Produced a line of output for a bracketed expression.

def render_node (data, i):
    node = data[i]
    parent = node.parent
    if parent:
        i = child_index(parent, node)
        pc = parent.cat
        if len(pc) > 6: pc = pc[:5] + '~'

        lc = ' '.join('[%s %s]' % (sib.cat, terminal_string(sib))
                      for sib in parent.children[:i])
        rc = ' '.join('[%s %s]' % (sib.cat, terminal_string(sib))
                      for sib in parent.children[i+1:])

        if len(lc) > 40: lc = lc[-40:]
        lc = '[%-6s %40s' % (pc, lc)

        if len(rc) > 40: rc = rc[:40]

    else:
        lc = ''
        rc = ''

    s = '%s %s' % (node.cat, terminal_string(node))
    if len(s) > 15: s = s[:12] + '...'
    s = '[' + s + ']'

    return '%48s %-17s %-40s' % (lc, s, rc)
        

##  A return set, displayable as a concordance.

class ReturnSet (object):

    ##  Constructor.

    def __init__ (self, conc, items):
        ##  The Concordance.
        self.conc = conc
        ##  The return-set items.
        self.items = items

    ##  Returns the subset (type ReturnSet) that satisfies the given predicate.

    def select (self, pred):
        data = self.conc.data
        items = [i for i in self.items if pred(data[i])]
        return ReturnSet(self.conc, items)

    ##  Returns the subset (type ReturnSet) whose value for the given feature is given.

    def where (self, feature, value):
        fitems = self.conc.indices[feature][value]
        items = intersect(self.items, fitems)
        return ReturnSet(self.conc, items)

    ##  Print out the concordance.

    def show (self, n=None):
        self.conc.show(n, self.items)


##  A concordance.

class Concordance (object):

    ##  Constructor.

    def __init__ (self, data, render=None, pager=True):

        ##  An index of which data items have which features.
        self.indices = {}

        ##  A copy of the list of items.
        self.data = list(data)

        ##  Rendering method
        self.render = None

        ##  Whether to use a pager.
        self.pager = pager

        if render:
            self.render = render
        elif isinstance(self.data[0], str):
            self.render = render_string
        elif isinstance(self.data[0], Tree):
            self.render = render_node
        else:
            raise Exception("No method to render object %s" % self.data[0])

    ##  Fetch an item.

    def __getitem__ (self, i):
        return self.data[i]

    ##  Add a feature to the indices.

    def add_feature (self, name, extractor):
        index = Index( (extractor(item),i) for (i,item) in enumerate(self.data) )
        self.indices[name] = index

    ##  Get all values for the given feature.

    def values (self, feature):
        return sorted(self.indices[feature].keys())

    ##  A ReturnSet containing items that have the given value for the given feature.

    def where (self, feature, value):
        return ReturnSet(self, self.indices[feature][value])

    ##  Selects a ReturnSet that satisfies the given predicate.

    def select (self, pred):
        return ReturnSet(self, [i for (i,item) in enumerate(self.data) if pred(item)])

    ##  Displays using a pager.

    def show (self, n=None, items=None):
        if items is None: items = range(len(self.data))
        if n is None and self.pager:
            more("%6d: %s" % (idx, self.render(self.data, idx)) for idx in items)
        else:
            if n is None: n = len(items)
            for i in range(n):
                if i >= len(items): break
                idx = items[i]
                print('%6d: %s' % (idx, self.render(self.data, idx)))
