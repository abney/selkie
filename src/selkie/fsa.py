##  \package seal.nlp.fsa
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
    
    ##  A state in a (non-deterministic) FSA.

    class State (object):
    
        ##  Constructor.

        def __init__ (self, name):

            ##  The name of the state.
            self.name = name

            ##  Its edges, a list.
            self.edges = []

            ##  Whether it is a final state.
            self.is_final = False

            ##  Its index.
            self.index = None

            ##  The fsa that it belongs to.
            self.fsa = None

        ##  Comparison is by string representation.

        def __lt__ (self, other):
            return str(self) < str(other)
    
        ##  Comparison is by string representation.

        def __eq__ (self, other):
            return str(self) == str(other)

        ##  Hashes the string representation.

        def __hash__ (self):
            return hash(self.name)
    
        ##  Add a new edge.
        #   Label_from is for use of eclosure; to generalize with Fsts.

        def edge (self, dest, label=None, label_from=None):
            if label_from:
                assert label is None
                label = label_from.single_label()
            e = self._find_edge(dest, label)
            if e is None:
                e = Fsa.Edge(self, dest, label)
                self.edges.append(e)
                if self.fsa and e.is_epsilon(): self.fsa.epsilon_free = False
            return e
    
        def _find_edge (self, dest, label):
            for e in self.edges:
                if e.dest == dest and (e.label == label or not (e.label or label)):
                    return e

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
    
    ##  A state in a deterministic FSA.

    class State (Fsa.State):

        ##  Returns a single state, or None.

        def __getitem__ (self, label):
            for e in self.edges:
                if e.label == label or not (e.label or label):
                    return e.dest
            return None
    
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

