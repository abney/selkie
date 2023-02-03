    
class Edge (object):

    # A label that is boolean false counts as epsilon
    # But if labels are, say, sets, we don't want to replace the empty set with None -
    # that would make set operations fail later on.

    def __init__ (self, src, dst, label=None, outlabel=None):
        self._source = src
        self._dest = dst
        self._label = label
        self._outlabel = outlabel

    def source (self): return self._source
    def dest (self): return self._dest
    def outlabel (self): return self._outlabel

    def label (self):
        ##  Return the label.
        if self._label == self._outlabel:
            return self._label
        else:
            raise Exception('Edge does not have a simple label')

    def labels (self):
        return (self._label, self._outlabel)

    def is_epsilon (self):
        # In an FSA, outlabels equal labels by definition
        return (not self._label) and (not self._outlabel)

    def __str__ (self):
        words = [str(self._source._index), str(self._dest._index)]
        label = self._label or ''
        outlabel = self._outlabel or ''
        if label == outlabel:
            if label:
                words.append(label)
        else:
            if label:
                words.append(label)
            words.append(':')
            if outlabel:
                words.append(outlabel)
        return ' '.join(words)
    
    def __repr__ (self):
        s = self.__str__()
        return f'<Edge {s}>'

    def write (self, out):
        out.write(str(self._source))
        out.write('\t')
        out.write(str(self._dest))
        if self._label or self._outlabel:
            out.write('\t')
            out.write(self._label or '')
            if self._outlabel:
                out.write('\t')
                out.write(self._outlabel)
        out.write('\n')


FINAL = 1
DETERMINISTIC = 2
EFREE = 4
FSAFLAGS = DETERMINISTIC | EFREE

#
#   The FSAFLAGS can only be set at creation, and if the State is added to an FSA,
#   its FSAFLAGS must match the FSA's flags.
#
#   For the interpretation of wildcards, we 

class State (object):

    def __init__ (self, name, flags=0):
        self._name = name
        self._edges = []
        self._index = None
        self._flags = flags

    def is_final (self): return self._flags & FINAL
    def set_final (self): self._flag |= FINAL

    def is_deterministic (self): return self._flags & DETERMINISTIC
    def is_efree (self): return self._flags & EFREE

    def __lt__ (self, other):
        return str(self) < str(other)

    def __eq__ (self, other):
        return str(self) == str(other)

    def __hash__ (self):
        return hash(self._name)
    
    def _find_edge (self, dest, label, outlabel):
        tgt = (label or None, outlabel or None)
        for e in self.edges:
            if (e._dest == dest and (e._label or None, e._outlabel or None) == tgt):
                return e

    def matching_edges (self, label):
        out = []
        known = False
        wild = []
        for e in self._edges:
            if e._label is True:
                wild.append(e)
            elif label and e._label == label:
                known = True
                out.append(e)
            elif (not label) and (not e._label):
                out.append(e)
        if label and wild:
                if self.fsa.sigma: known = inlabel in self.fsa.sigma
                if not known:
                    for e in wild:
                        if e.outlabel is True:
                            outlabel = inlabel
                        else:
                            outlabel = e.outlabel
                        out.append(Fst.Edge(self, e.dest, inlabel, outlabel))
            return out


    def edge (self, dest, label=None, outlabel=None, labels=None):
        if labels:
            assert label is None and outlabel is None, 'labels overrides label and outlabel'
            (label, outlabel) = labels
        det = self.is_deterministic()

        e = self._find_edge(dest, label, outlabel)


        ##  Add a new edge.
        #   Label_from is for use of eclosure; to generalize with Fsts.

        def edge (self, dest, label=None, label_from=None):

            e = self._find_edge(dest, label)
            if e is None:
                e = Fsa.Edge(self, dest, label)
                self.edges.append(e)
                if self.fsa and e.is_epsilon(): self.fsa.epsilon_free = False
            return e

    
        ##  Add a new edge.

        def edge (self, dest, label=None):
            if (not label): raise Exception('Attempt to add empty edge')
            for e in self.edges:
                if e.label == label:
                    if dest != e.dest:
                        raise Exception('Attempt to add multiple edges with same label')
                    return e
            e = Fsa.Edge(self, dest, label)
            self.edges.append(e)
            return e

        ##  Add a new edge.

        def edge (self, dest, inlabel=None, outlabel=None, label_from=None):


            if e is None:
                e = Fst.Edge(self, dest, inlabel, outlabel)
                self.edges.append(e)
                if self.fsa and (not inlabel) and (not outlabel):
                    self.fsa.epsilon_free = False
            return e



    ##  A state in a (non-deterministic) FSA.

    class State (object):

        ##  Returns a list of states.

        def __getitem__ (self, label):
            out = []
            for e in self.edges:
                if e.label == label or not (e.label or label):
                    out.append(e.dest)
            return out
    
        ##  Compute the epsilon-closure of this state.
        #   This will work for Fsts, too.

        def eclosure (self):
            todo = [self]
            out = set([])
            while todo:
                q = todo.pop()
                if q not in out:
                    out.add(q)
                    for e in q.edges:
                        # for fst, means labels are eps:eps
                        if e.is_epsilon():
                            todo.append(e.dest)
            return out
    
        ##  String representation.  If the name is a set, it sorts the
        #   element so that the name is uniquely determined by the set.

        def __str__ (self):
            if isinstance(self.name, frozenset):
                return '{' + ','.join(str(x) for x in sorted(self.name)) + '}'
            elif isinstance(self.name, tuple):
                return '(' + ','.join(str(x) for x in self.name) + ')'
            else:
                return str(self.name)
    
        ##  Brief string representation.

        def __repr__ (self):
            typename = self.__class__.__name__
            return '<' + typename + ' ' + self.__str__() + ' [' + str(self.index) + ']>'


        ----------------------------------------
    
    ##  A state in a deterministic FSA.

    class DFsa.State (Fsa.State):

        ##  Returns a single state, or None.

        def __getitem__ (self, label):
            for e in self.edges:
                if e.label == label or not (e.label or label):
                    return e.dest
            return None
    
        ----------------------------------------
    
    ##  A state in an Fst.

    class Fst.State (Fsa.State):

        ##  Returns the set of non-wildcard input labels on the edges out of this state.

        def mentioned (self):
            out = set()
            for e in self.edges:
                if e.inlabel and e.inlabel is not True:
                    out.add(e.inlabel)
            return out


--------------------------------------------------------------------------------


##  \PACKAGE seal.nlp.fsa
#   Finite-state automata.

from .io import iter_records, ispathlike


##  Input is a linked list in reverse

def _rcons_to_list (cons):
    lst = []
    while cons:
        lst.append(cons[0])
        cons = cons[1]
    return lst[::-1]

##  This is only used for sorting edges when printing

def _edge_key (e):
    if hasattr(e, 'label'):
        lab1 = str(e.label)
        lab2 = lab1
    elif hasattr(e, 'inlabel'):
        lab1 = str(e.inlabel)
        lab2 = str(e.outlabel)
    else:
        raise Exception('Not an edge')
    return (e.source.index, e.dest.index, lab1, lab2)


##  A generic finite-state automaton.  Presumed to be non-deterministic.

class Fsa (object):
    
    ##  An edge.

    class Edge (object):
    
        ##  Constructor.

        def __init__ (self, src, dst, label=None):

            ##  The state that the edge comes from.
            self.source = src

            ##  The state that the edge goes to.
            self.dest = dst

            ##  The edge label.
            self.label = label
    
        ##  Whether it is an epsilon edge.  An epsilon edge is one whose label
        #   is boolean false.

        def is_epsilon (self):
            return (not self.label)

        ##  Return the label.

        def single_label (self): return self.label

        ##  Return a pair consisting of the label twice.

        def label_pair (self): return (self.label, self.label)

        ##  String representation.

        def __str__ (self):
            s = str(self.source.index) + " " + str(self.dest.index)
            if (not self.label): return s
            else: return s + " " + str(self.label)
    
        ##  Typed string representation.

        def __repr__ (self):
            return '<Edge %s %s %s>' % (str(self.source), str(self.dest), self.label)
    
        ##  Write it to an output stream.

        def write (self, out):
            s = str(self.source) + "\t" + str(self.dest)
            if self.label: s += "\t" + str(self.label)
            out.write(s + "\n")
    

    ##  Constructor for Fsa.

    def __init__ (self, initzr=None):

        ##  The states, a dict.
        self.state_dict = {}

        ##  The states as a list.
        self.states = []

        ##  The start state.
        self.start = None

        ##  Whether the fsa is epsilon-free.
        self.epsilon_free = True

        if initzr:
            if ispathlike(initzr):
                self.load(initzr)
            else:
                self.initialize_from(initzr)

    ##  Not implemented.

    def initialize_from (self, fsa):
        raise Exception('Not implemented')

    ##  Create a state.

    def state_constructor (self, name):
        return Fsa.State(name)

    ##  Create an edge.

    def edge (self, src, dest, label=None):
        src = self.state(src)
        dest = self.state(dest)
        return src.edge(dest, label)

    ##  Iterate over all edges of all states.

    def edges (self):
        for q in self.states:
            for e in q.edges:
                yield e

    ##  Returns a set containing all edge labels.

    def labels (self):
        out = set()
        for e in self.edges():
            if e.label:
                out.add(e.label)
        return out

    ##  Whether or not the state with the given name is final.

    def final_state (self, state):
        q = self.state(state)
        q.is_final = True

    ##  Load from a file.

    def load (self, fn):
        file = iter_records(fn)
        for r in file:
            if len(r) == 3:
                self.edge(r[0], r[1], r[2])
            elif len(r) == 2:
                self.edge(r[0], r[1])
            elif len(r) == 1:
                self.final_state(r[0])
            else:
                file.error('Expected one, two, or three fields')

    ##  The number of states.

    def __len__ (self):
        return len(self.states)

    ##  Returns an existing state.  Error if no state exists with the given name.

    def __getitem__ (self, name):
        return self.state_dict[name]

    ##  If a state with the given name exists, returns it.  Otherwise adds a new
    #   state to the automaton and returns it.

    def state (self, name):
        if name in self.state_dict:
            return self.state_dict[name]
        else:
            q = self.state_constructor(name)
            q.fsa = self
            q.index = len(self.states)
            self.state_dict[name] = q
            self.states.append(q)
            if not self.start: self.start = q
            return q

    ##  Change the state names to be the state indices as strings.
    #   Destructive.

    def rename_states (self):
        self.state_dict = {}
        for q in self.states:
            q.name = str(q.index)
            self.state_dict[q.name] = q

    ##  Iterates over generated strings.

    def __iter__ (self):
        n = 0
        todo = [(self.start, ())]
        while todo:
            if n > len(self.states):
                raise Exception('Caught in a loop')
            (q, h) = todo.pop()
            n += 1
            if q.is_final:
                yield _rcons_to_list(h)
                n = 0
            for e in q.edges:
                if e.label: h1 = (e.label, h)
                else: h1 = h
                todo.append((e.dest, h1))

    ##  Dump the contents.

    def dump (self, file=None):
        print(self.__class__.__name__ + ':', file=file)
        for q in self.states:
            isstart = '  '
            isfin = ' '
            if q == self.start: isstart = '->'
            if q.is_final: isfin = '#'
            print("  " + isstart + str(q.index) + isfin + " [" + str(q) + "]", file=file)
        for q in self.states:
            for e in sorted(q.edges, key=_edge_key):
                print("    " + str(e), file=file)
    
    ##  Eliminate epsilon edges.
    #   Works for Fst, too.
    #   Not destructive; creates a new automaton.

    def eliminate_epsilons (self, rename_states=True):
        if self.epsilon_free: return self

        new_fsa = self.__class__()
    
        # So that the results are not sensitive to the (unpredictable)
        # orderings of edges, we compute the new state set up front.
        # An old state has a counterpart in the new fsa only if it is
        # the old start state, or if there is a non-epsilon edge terminating
        # in it.

        map = [None for q in self.states]
        map[self.start.index] = True
        for e in self.edges():
            if not e.is_epsilon():
                map[e.dest.index] = True
        byset = {}
        for i in range(len(map)):
            if map[i]:
                q = self.states[i]
                s = frozenset(q.eclosure())
                if s in byset:
                    map[i] = byset[s]
                else:
                    map[i] = byset[s] = new_fsa.state(s)
                        
        # Now translate all the non-epsilon edges

        new_fsa.start = map[self.start.index]

        for new_q in map:
            if new_q is None: continue
            for q in sorted(new_q.name):
                if q.is_final: new_q.is_final = True
                for e in q.edges:
                    if not e.is_epsilon():
                        new_r = map[e.dest.index]
                        if new_r is None: raise Exception("This can't happen")
                        new_q.edge(new_r, label_from=e)
    
        # new_fsa.dump()

        if rename_states:
            new_fsa.rename_states()

        # print('Rename:')
        # new_fsa.dump()

        return new_fsa


# class _Node (object):
# 
#     def __init__ (self, state, prev):
#         self.state = state
#         self.prev = prev
        

##  A non-deterministic fsa.

class NFsa (Fsa):

    ##  Whether it accepts the given list of symbols.

    def accepts (self, input, trace=False):
        #if trace: self.dump()
        states = self.start.eclosure()
        i = 0
        while i < len(input):
            label = input[i]
            if trace:
                print('[%d]' % i, 'states', ' '.join(str(q) for q in states))
            i += 1
            if not states: return False
            newstates = set()
            for q0 in states:
                for q1 in q0[label]:
                    if trace: print('    edge', q0, label, q1)
                    newstates.update(q1.eclosure())
            states = newstates
        if trace: print('[%d]' % i, 'states', ' '.join(str(q) for q in states))
        for q in states:
            if q.is_final: return True
        return False


##  An NFsa in which state names equal their indices.

class SimpleFsa (NFsa):

    ##  Constructor.

    def __init__ (self):
        NFsa.__init__()
        self.state_dict = None

    ##  Returns an existing state.

    def __getitem__ (self, i):
        return self.states[i]

    ##  Creates a new state.

    def state (self):
        i = len(self.states)
        q = self.state_constructor(i)
        q.fsa = self
        q.index = i
        self.states.append(q)
        if not self.start: self.start = q
        return q

    ##  Signals an error.

    def rename_states (self):
        raise Exception('State renaming is not possible with SimpleFsa')


##  A deterministic fsa.

class DFsa (Fsa):

    ##  Returns a DFsa.State.

    def state_constructor (self, name):
        return DFsa.State(name)

    ##  Whether it accepts the given symbol list.

    def accepts (self, input):
        q = self.start
        for sym in input:
            q = q[sym]
            if q == None: return False
        return q.is_final


##  Determinize an fsa.  Non-destructive.  Returns a DFsa.

def determinize (old_fsa, rename_states=True):
    old_fsa = old_fsa.eliminate_epsilons()
    new_fsa = DFsa()
    new_fsa.state(frozenset([old_fsa.start]))
    ndone = 0

    while ndone < len(new_fsa.states):
        q1 = new_fsa.states[ndone]
        ndone += 1
        table = {}
        for q in sorted(q1.name):
            for e in q.edges:
                if e.label in table:
                    table[e.label].add(e.dest)
                else:
                    table[e.label] = set([e.dest])
            if q.is_final: q1.is_final = True
        for (label, dests) in sorted(table.items()):
            q1.edge(new_fsa.state(frozenset(dests)), label)

    if rename_states: new_fsa.rename_states()
    return new_fsa
            

##  An incompatibility table, used in minimization.

class Incompatibility:

    ##  Constructor.

    def __init__ (self, fsa):

        ##  The fsa.
        self.fsa = fsa

        ##  The contents.
        self.table = None

        n = len(fsa)
        symbols = sorted(fsa.labels())

        # n+1 because state "n" is the trap state
        self.table = [[set([]) for x in symbols] for q in range(n+1)]
        
        symbol_table = {}
        for (i,sym) in enumerate(symbols):
            symbol_table[sym] = i
        
        for e in fsa.edges():
            i = e.dest.index
            j = symbol_table[e.label]
            self.table[i][j].add(e.source.index)

        #  if there is no transition q[sym], then add q to row n
        for (i,sym) in enumerate(symbols):
            self.table[n][i].add(n)
            for q in fsa.states:
                if not q[sym]:
                    self.table[n][i].add(q.index)

    ##  Propagate an incompatibility.

    def propagate (self, p):
        row0 = self.table[p[0]]
        row1 = self.table[p[1]]
        for j in range(len(row0)):
            for q0 in row0[j]:
                for q1 in row1[j]:
                    yield pair(q0,q1)

    ##  Dump out the contents.

    def dump (self, file=None):
        for (i,row) in enumerate(self.table):
            rowstr = str(i) + " :"
            for cell in row:
                first = True
                rowstr += " {"
                for q in cell:
                    if first: first = False
                    else: rowstr += ","
                    rowstr += str(q)
                rowstr += "}"
            print(rowstr, file=file)


##  A lower triangular matrix, used in minimization.

class LTM:

    ##  Constructor.

    def __init__ (self, n):

        ##  The number of columns.
        self.n = n

        ##  The contents.
        self.contents = [None] * (n * (n+1) // 2)

    ##  The contents is a list.  This translates an index pair to a position
    #   in the list.

    @staticmethod
    def index (p):
        i = p[0]
        j = p[1]
        return (i * (i-1) // 2) + j

    ##  Get the contents of a cell.

    def __getitem__ (self, p):
        return self.contents[LTM.index(p)]

    ##  Set the contents of a cell.

    def __setitem__ (self, p, value):
        self.contents[LTM.index(p)] = value

    ##  Iterate over all pairs.

    def __iter__ (self):
        return pairs(self.n)

    ##  Dump the contents.

    def dump (self):
        for p in pairs(self.n):
            print(p, self[p])


##  Iterates over pairs (i,j) in which both lie in the range
#   [0,n), and j < i.

def pairs (n):
    for i in range(1, n):
        for j in range(0, i):
            yield (i,j)

##  Sorts i and j from greater to lesser, returning a pair.
#   Signals an error if i == j.

def pair (i, j):
    if i > j: return (i, j)
    elif i < j: return (j, i)
    else: raise Exception("Cannot pair a state with itself")

##  Minimize an automaton.  Instantiates and calls a Minimizer.
#   Non-destructive.

def minimize (fsa):
    if not isinstance(fsa, DFsa):
        raise Exception("Must determinize first")
    m = Minimizer(fsa)
    return m()


##  A minimizer.

class Minimizer:

    ##  Constructor.

    def __init__ (self, fsa):

        ##  The fsa.
        self.fsa = fsa

        ##  An Incompatibility table.
        self.itab = Incompatibility(fsa)

        ##  An LTM indicating which pairs are marked.
        self.marked = LTM(len(fsa))

        ##  Pairs to propagate.
        self.todo = []

        ##  State map.
        self.state_map = None

        ##  Number of states in the new automaton.
        self.new_nstates = None

        ##  The new automaton.
        self.newfsa = None
    
        n = len(fsa)

        for q1 in fsa.states:
            if q1.is_final:
                p = pair(n, q1.index)
                self.todo.append(p)
                self.marked[p] = True
                for q2 in fsa.states:
                    if not q2.is_final:
                        p = pair(q1.index, q2.index)
                        self.todo.append(p)
                        self.marked[p] = True

    ##  Run.

    def propagate (self):
        fsa = self.fsa
        itab = self.itab
        marked = self.marked
        todo = self.todo

        while todo:
            p = todo.pop()
            for newp in itab.propagate(p):
                if not marked[newp]:
                    todo.append(newp)
                    marked[newp] = True

    ##  Create a map from old states to new states.

    def create_map (self):
        marked = self.marked
        n = len(self.fsa)
        state_map = [None] * n
        new_n = 0
    
        for p in pairs(n):
            if not marked[p]:
                i = p[0]
                j = p[1]
                if state_map[j] == None:
                    state_map[j] = new_n
                    new_n += 1
                if state_map[i] == None:
                    state_map[i] = state_map[j]
                elif state_map[i] != state_map[j]:
                    raise Exception("map[i] != map[j]")
            
        for i in range(n):
            if state_map[i] == None:
                state_map[i] = new_n
                new_n += 1

        self.state_map = state_map
        self.new_nstates = new_n

    ##  Create the new automaton.

    def create_newfsa (self):
        state_map = self.state_map
        oldfsa = self.fsa
        newfsa = DFsa()

        for i in range(self.new_nstates):
            newfsa.state(str(i))

        for q in oldfsa.states:
            q1 = newfsa.states[state_map[q.index]]
            for e in q.edges:
                q1.edge(newfsa.states[state_map[e.dest.index]], e.label)
            if q.is_final: q1.is_final = True
    
        self.newfsa = newfsa
        return newfsa

    ##  Call it.  Does propagate(), create_map(), create_newfsa().

    def __call__ (self):
        self.propagate()
        self.create_map()
        return self.create_newfsa()


##  A configuration in a non-deterministic fsa computation.

class History (object):

    ##  Constructor.

    def __init__ (self, i, state, outlabel=None, older=None, inlabel=None):

        ##  Input index.
        self.i = i

        ##  Current state.
        self.state = state

        ##  Output label.
        self.outlabel = outlabel

        ##  Next older configuration.
        self.older = older

        ##  Input label.
        self.inlabel = inlabel

    def __collect_output (self, out):
        if self.older:
            self.older.__collect_output(out)
        if self.outlabel:
            out.append(self.outlabel)

    ##  Returns the output corresponding to this computation.

    def output (self):
        out = []
        self.__collect_output(out)
        return out

    ##  Returns the input-output pair corresponding to this computation.

    def pair (self):
        input = []
        output = []
        self.__collect_pair(input, output)
        return (input, output)

    def __collect_pair (self, input, output):
        if self.older:
            self.older.__collect_pair(input, output)
        if self.inlabel: input.append(self.inlabel)
        if self.outlabel: output.append(self.outlabel)

--------------------------------------------------------------------------------





from .fsa import (Fsa, History)


#--  Fst  ----------------------------------------------------------------------

##  A finite-state transducer.

class Fst (Fsa):

    ##  An edge.

    class Edge (Fsa.Edge):
    
        ##  Constructor.

        def __init__ (self, src, dst, inlabel=None, outlabel=None):

            ##  The state it comes from.
            self.source = src

            ##  The state it goes to.
            self.dest = dst

            ##  Its input label.
            self.inlabel = inlabel

            ##  Its output label.
            self.outlabel = outlabel

            if not self.inlabel: self.inlabel = None
            if not self.outlabel: self.outlabel = None
    
        ##  Only true if both the input and output labels are epsilon.

        def is_epsilon (self):
            return (not self.inlabel) and (not self.outlabel)

        ##  Returns the label, if both input and output labels are the same.
        #   Otherwise signals an error.

        def single_label (self):
            if self.inlabel == self.outlabel and self.inlabel is not True:
                return self.inlabel
            else:
                raise Exception('Non-trivial FST edge cannot be interpreted as FSA edge')

        ##  Returns a pair of input and output labels.

        def label_pair (self):
            return (self.inlabel, self.outlabel)

        ##  Detailed string.

        def __str__ (self):
            s = str(self.source.index) + " " + str(self.dest.index)
            if (not self.inlabel) and (not self.outlabel): return s
            elif self.inlabel and self.outlabel:
                return s + " " + str(self.inlabel) + " : " + str(self.outlabel)
            elif self.inlabel:
                return s + " " + str(self.inlabel) + " :"
            elif self.outlabel:
                return s + " : " + str(self.outlabel)
    
        ##  String representation.

        def __repr__ (self):
            return '<Edge %s %s %s %s>' % (str(self.source), str(self.dest), self.inlabel, self.outlabel)
    
        ##  Write to output stream.

        def write (self, out):
            s = str(self.source) + "\t" + str(self.dest)
            if self.inlabel or self.outlabel:
                s += "\t"
                if self.inlabel: s += str(self.inlabel)
                s += "\t"
                if self.outlabel: s += str(self.outlabel)
            out.write(s + "\n")


    ##  Constructor.

    def __init__ (self, initzr=None):

        ##  The start state.
        self.start = None

        ##  The input vocabulary.
        self.sigma = None

        Fsa.__init__(self, initzr)

    ##  Initialize from an fsa.

    def initialize_from (self, fsa):
        assert isinstance(fsa, Fsa)
        for q in fsa.states:
            q1 = self.state(q.name)
            for e in q.edges:
                q1.edge(self.state(e.dest.name), e.label, e.label)
            if q.is_final: q1.is_final = True
        self.start = self.state(fsa.start.name)

    ##  Create a new edge.

    def edge (self, src, dest, inlabel=None, outlabel=None):
        src = self.state(src)
        dest = self.state(dest)
        return src.edge(dest, inlabel, outlabel)

    ##  The set of input labels.  (Excludes epsilon.)

    def inlabels (self):
        out = set()
        for e in self.edges():
            if e.inlabel:
                out.add(e.inlabel)
        return out

    ##  The set of output labels.  (Excludes epsilon.)

    def outlabels (self):
        out = set()
        for e in self.edges():
            if e.outlabel:
                out.add(e.outlabel)
        return out

    ##  Load from a file.

    def load (self, fn):
        file = iter_records(fn)
        for r in file:
            if len(r) == 4:
                self.edge(r[0], r[1], r[2], r[3])
            elif len(r) == 3:
                self.edge(r[0], r[1], r[2], r[2])
            elif len(r) == 2:
                self.edge(r[0], r[1])
            elif len(r) == 1:
                self.final_state(r[0])
            else:
                file.error('Expected one, two, three, or four fields')

    ##  Construct a state.

    def state_constructor (self, name):
        return Fst.State(name)

    ##  Call it on an input.

    def __call__ (self, input, trace=False, cutoff=None):
        if trace: print('input=', input)
        todo = [History(0, self.start)]
        out = []
        n = 0
        while todo:
            if cutoff and n >= cutoff:
                raise Exception('Exceeded cutoff, possible loop')
            n += 1
            h = todo.pop()
            if trace: print('[%s]' % h.i,
                            'state %s%s' % (h.state,
                                            ' (F)' if h.state.is_final else ''))
            if h.i == len(input):
                if h.state.is_final:
                    if trace: print('    accept')
                    out.append(h.output())
            else:
                inlabel = input[h.i]
                for e in h.state[inlabel]:
                    if trace: print('    edge', e.source, '%s:%s' % (e.inlabel, e.outlabel), e.dest)
                    todo.append(History(h.i + 1, e.dest, e.outlabel, h))
            for e in h.state[None]:
                if trace: print('    edge', e.source, '%s:%s' % (e.inlabel, e.outlabel), e.dest)
                todo.append(History(h.i, e.dest, e.outlabel, h))
        return out

    ##  Whether it accepts a given input.

    def accepts (self, input):
        return bool(self.__call__(input))

    ##  Its vocabulary.  One can specify either the 'left' (input) vocabulary,
    #   the 'right' (output) vocabulary, or 'both'.  The default is 'both'.

    def vocabulary (self, side='both'):
        left = right = False
        if side == 'left' or side == 'both': left = True
        if side == 'right' or side == 'both': right = True
        v = set()
        for q in self.states:
            for e in q.edges:
                if left and not (e.inlabel is None or e.inlabel is True):
                    v.add(e.inlabel)
                if right and not (e.outlabel is None or e.outlabel is True):
                    v.add(e.outlabel)
        return v

    ##  Creates a new FST.

    def globalize_wildcards (self, vocab):
        out = Fst()
        out.sigma = vocab
        for q in self.states:
            q1 = out.state(q.name)
            q1.is_final = q.is_final
            unmentioned = None
            for e in q.edges:
                d1 = out.state(e.dest.name)

                if e.inlabel is True:
                    q1.edge(d1, e.inlabel, e.outlabel)
                    if unmentioned is None: unmentioned = vocab - q.mentioned()
                    if e.outlabel is True:
                        for s in unmentioned:
                            q1.edge(d1, s, s)
                    else:
                        for s in unmentioned:
                            q1.edge(d1, s, e.outlabel)

                elif e.outlabel is True:
                    raise Exception('Wildcard on outlabel but not on inlabel')

                else:
                    q1.edge(d1, e.inlabel, e.outlabel)

        out.start = out.state(self.start.name)
        return out

    ##  Iterate over the valid input strings.

    def __iter__ (self):
        vocab = self.vocabulary('left')
        todo = [History(0, self.start)]
        n = 0
        while todo:
            if n > len(self.states):
                raise Exception('Caught in a loop')
            h = todo.pop()
            q = h.state
            n += 1
            if q.is_final:
                yield h.pair()
                n = 0
            wildcards = False
            attested = set()
            for e in q.edges:
                if e.inlabel is None:
                    todo.append(History(h.i, e.dest, older=h,
                                        inlabel=None, outlabel=e.outlabel))
                elif e.inlabel is True:
                    wildcards = True
                else:
                    attested.add(e.inlabel)
                    todo.append(History(h.i+1, e.dest, older=h,
                                        inlabel=e.inlabel, outlabel=e.outlabel))
            if wildcards:
                rest = vocab - attested
                for e in q.edges:
                    if e.inlabel is True:
                        for inlabel in rest:
                            if e.outlabel is True: outlabel = inlabel
                            else: outlabel = e.outlabel
                            todo.append(History(h.i+1, e.dest, older=h,
                                                inlabel=inlabel, outlabel=outlabel))


##  Composes two transducers.

class Composer (object):

    ##  Constructor.

    def __init__ (self):

        ##  The new transducer.
        self.out = None

        ##  States that still need to be processed.
        self.todo = None

    ##  Create a new state, which is a pairing of states of the input automata.

    def state (self, q1, q2):
        name = (q1.index, q2.index)
        if name in self.out.state_dict:
            return self.out.state_dict[name]
        else:
            r = self.out.state(name)
            r.is_final = q1.is_final and q2.is_final
            self.todo.append(r)
            return r

    ##  Compute the input vocabulary.

    def compute_sigma (self, fst1, fst2):
        sigma = fst1.vocabulary('left')
        if any(e.inlabel is True and e.outlabel is True for e in fst2.edges()):
            sigma.update(fst2.vocabulary('left'))
        return sigma

    ##  Call it.

    def __call__ (self, fst1, fst2, trace=False):
        fst1 = fst1.eliminate_epsilons()
        fst2 = fst2.eliminate_epsilons()
        sigma = self.compute_sigma(fst1, fst2)
        fst1 = fst1.globalize_wildcards(sigma)
        fst2 = fst2.globalize_wildcards(sigma)
        if trace:
            print('fst1:')
            fst1.dump()
            print('fst2:')
            fst2.dump()
        out = self.out = Fst()
        out.sigma = sigma
        self.todo = []
        out.start = self.state(fst1.start, fst2.start)
        if trace: print('Start', out.start)

        while self.todo:
            q = self.todo.pop()
            if trace: print('Do', q)
            q1 = fst1.states[q.name[0]]
            q2 = fst2.states[q.name[1]]

            # Edges of T1 state
            for e in q1.edges:
                if trace: print('  T1 edge %s:%s' % (e.inlabel, e.outlabel))
                # x:_e_ - advance T1, not T2
                if e.outlabel is None:
                    r = self.state(e.dest, q2)
                    if trace: print('    Edge', q, '%s:None' % e.inlabel, r)
                    q.edge(r, e.inlabel, None)
                # x:y
                else:
                    for e2 in q2[e.outlabel]:
                        r = self.state(e.dest, e2.dest)
                        if trace: print('    Edge', q, '%s:%s' % (e.inlabel, e2.outlabel), r)
                        q.edge(r, e.inlabel, e2.outlabel)

            # Edges of T2 with epsilon input - advance T2, not T1
            for e2 in q2.edges:
                if not e2.inlabel:
                    r = self.state(q1, e2.dest)
                    if trace: print('    Edge', q, 'None:%s' % e2.outlabel, r)
                    q.edge(r, None, e2.outlabel)

        out = out.eliminate_epsilons()
        if trace:
            print('out, before renaming states:')
            out.dump()
        out.rename_states()

        return out


##  An instance of Composer; behaves like a function.
compose = Composer()


#--  From List  ----------------------------------------------------------------

def fst_from_list (lst):
    
    for string in lst:
        
        pass
