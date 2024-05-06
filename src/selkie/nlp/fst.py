
from .fsa import (Fsa, History)


#--  Fst  ----------------------------------------------------------------------

##  A finite-state transducer.

class Fst (Fsa):

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

    
    ##  A state in an Fst.

    class State (Fsa.State):

        ##  Add a new edge.

        def edge (self, dest, inlabel=None, outlabel=None, label_from=None):
            if label_from:
                assert inlabel is None and outlabel is None
                (inlabel, outlabel) = label_from.label_pair()
            e = self._find_edge(dest, inlabel, outlabel)
            if e is None:
                e = Fst.Edge(self, dest, inlabel, outlabel)
                self.edges.append(e)
                if self.fsa and (not inlabel) and (not outlabel):
                    self.fsa.epsilon_free = False
            return e
    
        def _find_edge (self, dest, inlabel, outlabel):
            for e in self.edges:
                if e.dest == dest \
                        and (e.inlabel == inlabel or not (e.inlabel or inlabel)) \
                        and (e.outlabel == outlabel or not (e.outlabel or outlabel)):
                    return e

        ##  Returns a list of states.

        def __getitem__ (self, inlabel):
            out = []
            known = False
            wild = []
            for e in self.edges:
                if e.inlabel is True:
                    wild.append(e)
                elif inlabel:
                    if e.inlabel == inlabel:
                        known = True
                        out.append(e)
                elif not e.inlabel:
                    out.append(e)
            if inlabel and wild:
                if self.fsa.sigma: known = inlabel in self.fsa.sigma
                if not known:
                    for e in wild:
                        if e.outlabel is True:
                            outlabel = inlabel
                        else:
                            outlabel = e.outlabel
                        out.append(Fst.Edge(self, e.dest, inlabel, outlabel))
            return out

        def advance (q, i):
            edges = q[i]
            if len(edges) == 0:
                return (None, None)
            elif len(edges) == 1:
                return (edges[0].dest, edges[0].outlabel)
            else:
                raise Exception('Not a deterministic automaton')

        ##  Returns the set of non-wildcard input labels on the edges out of this state.

        def mentioned (self):
            out = set()
            for e in self.edges:
                if e.inlabel and e.inlabel is not True:
                    out.add(e.inlabel)
            return out

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

def _advance_intern (fst, q, i):
    edges = q[i]
    if len(edges) == 0:
        r = fst.state(len(fst))
        return q.edge(r, i)
    elif len(edges) == 1:
        return edges[0]
    else:
        raise Exception(f'Non-deterministic state: {q} {i}')

def _advance_on_e (q, sink, eos):
    edges = q[eos]
    if len(edges) == 0:
        return q.edge(sink, eos)
    elif len(edges) == 1:
        if e.dest != sink:
            raise Exception(f'Edge on eos does not lead to sink: {q}')
        return edges[0]
    else:
        raise Exception(f'Non-deterministic on eos: {q}')

def from_list (lst, use_sink=False, eos='<eos>'):
    fst = Fst()
    fst.start = start = fst.state(0)
    if use_sink:
        sink = fst.state(1)
    for word in lst:
        q = start
        for c in word:
            e = _advance_intern(fst, q, c)
            q = e.dest
        if use_sink:
            e = _advance_on_e(q, sink, eos)
            q = e.dest
            assert q is sink, f'Bad edge from _advance_on_e: {e}'
        if e.outlabel and e.outlabel != word:
            raise Exception(f'Attempt to change output word: {e.source} {i} {word}, was {e.outlabel}')
        e.outlabel = word
        fst.final_state(q)
    return fst
