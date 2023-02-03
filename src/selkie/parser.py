##  \package seal.nlp.parser
#   Chart parser.

import os
from .seq import cross_product, product
from .map import Index
from .io import OutputList
from .features import unify, subst
from .grammar import Grammar, Lexicon
from .tree import Tree
from itertools import chain


##  Just so that we can print out nodes & edges in the order of creation
timestep = 0


#--  Node  ---------------------------------------------------------------------

##  A node in the chart.

class Node (object):

    ##  Constructor.

    def __init__ (self, cat, expansion, i, j, sem=None):
        global timestep

        ##  Category.
        self.cat = cat

        ##  List of expansions.
        self.expansions = [expansion]

        ##  Start position.
        self.i = i

        ##  End position.
        self.j = j

        ##  Semantics.
        self.sem = sem
        timestep += 1

        ##  Sequence number.  Nodes and edges are numbered in the order created.
        self.timestep = timestep

    ##  String representation.

    def __repr__ (self):
        return '%d.%s.%d' % (self.i, self.cat, self.j)

    ##  Add an expansion.

    def add (self, expansion):
        self.expansions.append(expansion)


#--  Edge  ---------------------------------------------------------------------

##  An edge in the chart.

class Edge (object):

    ##  Constructor.

    def __init__ (self, prev, rule, expansion, bindings):
        global timestep

        ##  The edge that it extends, if any.
        self.prev = prev

        ##  The grammar rule.
        self.rule = rule

        ##  The children collected so far.
        self.expansion = expansion

        ##  Current bindings.
        self.bindings = bindings
        timestep += 1

        ##  Sequence number.  Nodes and edges are numbered in the order created.
        self.timestep = timestep

    ##  String representation.

    def __repr__ (self):
        s = '(' + str(self.rule.lhs) + ' ->'
        for node in self.expansion:
            s += ' ' + str(node)
        s += ' *'
        for cat in self.rule.rhs[len(self.expansion):]:
            s += ' ' + str(cat)
        s += ' {'
        s += ' '.join(str(val) for val in self.bindings)
        s += '})'
        return s

    ##  Rule lhs.

    def cat (self):
        return self.rule.lhs

    ##  Start position of first child.

    def start (self):
        return self.expansion[0].i

    ##  End position of last child so far.

    def end (self):
        return self.expansion[-1].j

    ##  Category after the dot.

    def afterdot (self):
        n = len(self.expansion)
        if n < len(self.rule.rhs):
            return self.rule.rhs[n]
        else:
            return None

    ##  Fuse the semantics with the semantics of the given children.

    def reduce (self, children):
        sem = self.rule.sem
        if sem and hasattr(sem, '__call__'):
            return sem([c.sem for c in children])
        else:
            return sem


#--  Parser  -------------------------------------------------------------------

##  The parser.

class Parser (object):

    ##  Constructor.

    def __init__ (self, grammar=None, limit=None):
        if isinstance(grammar, Grammar):

            ##  Filename.
            self.filename = grammar.filename

            ##  Grammar.
            self.grammar = grammar

        else:
            self.filename = grammar
            self.grammar = Grammar(grammar)

        ##  The node chart.
        self.chart = dict()

        ##  The edges table.
        self.edges = Index()

        ##  The trace flag.
        self.trace = False

        ##  Rule to be traced, if any.
        self.trace_rule = None

        ##  Trace output.
        self.trace_output = None

        ##  Input words.
        self.words = None

        ##  Todo list.
        self.todo = None

        ##  Maximum number of parses allowed.
        self.limit = limit

        ##  Parsing actions.
        self.actions = {'node': self.add_node, 'edge': self.add_edge}

    ##  Call it on input words.

    def __call__ (self, words, trace=False):
        self.start_sentence(words, trace)
        n = len(self.words)
        for j in range(1, n+1):
            self.shift(j)
            while self.todo:
                self.step()
        s = self.grammar.start
        if (s, 0, n) in self.chart:
            return unwind(self.chart[s, 0, n], self.limit)
        else:
            return None

    ##  Set up the chart etc.

    def start_sentence (self, words, trace=False):
        if isinstance(words, str): words = words.split()
        if not isinstance(trace, type(True)):
            self.trace_output = trace
            trace = True
        self.words = words
        self.chart.clear()
        self.edges.clear()
        self.trace = trace
        self.todo = []

    ##  Add a todo item.

    def add (self, *args):
        self.todo.append(tuple(args))

    ##  Execute one step.

    def step (self):
        action = self.todo.pop()
        f = self.actions[action[0]]
        args = action[1:]
        f(*args)

    ##  Scan next word of input.

    def shift (self, j):
        w = self.words[j-1]
        ents = self.grammar.lexicon[w]
        if (not ents) and self.trace:
            print('Unknown Word:', w, file=self.trace_output)
        for entry in ents:
            self.add('node', entry.pos, entry, j-1, j)

    ##  Find rules that this node can be the first child of.

    def start (self, node):
        for rule in self.grammar.continuations(node.cat[0]):
            try:
                bindings = unify(rule.rhs[0], node.cat, rule.bindings)
            except Exception as e:
                lines = ['**Error in start %s' % node]
                lines.append('  unifying %s %s' % (rule.rhs[0], node.cat))
                lines.append('  rule %s' % rule)
                lines.append('  %s' % str(e))
                raise Exception('\n'.join(lines))

            edge = None
            if bindings is None:
                if self.trace_rule == rule.index:
                    print('Start:', node, '!~', subst(rule.bindings, rule.rhs[0]), file=self.trace_output)
            else:
                edge = Edge(None, rule, [node], bindings)
                if self.trace_rule == rule.index:
                    print('Start', edge, file=self.trace_output)
                self.add('edge', edge)

    ##  Find edges that can combine with this node.

    def combine (self, node):
        for edge in self.edges[node.i, node.cat[0]]:
            try:
                bindings = unify(edge.afterdot(), node.cat, edge.bindings)
            except Exception as e:
                lines = ['**Error unifying %s %s in combine %s' %
                         (edge.afterdot(), node.cat, node)]
                lines.append('  %s' % e)
                raise Exception('\n'.join(lines))
            if bindings is None:
                if self.trace_rule == edge.rule.index:
                    print('Combine', edge, node, 'unification failure', file=self.trace_output)
            else:
                newedge = Edge(edge, edge.rule, edge.expansion + [node], bindings)
                if self.trace_rule == edge.rule.index:
                    print('Combine', edge, node, '=>', newedge, file=self.trace_output)
                self.add('edge', newedge)

    ##  The dot is at the end; create a node.

    def complete (self, edge):
        if self.trace_rule == edge.rule.index:
            print('Complete', edge, file=self.trace_output)
        cat = subst(edge.bindings, edge.cat())
        self.add('node', cat, edge, edge.start(), edge.end())

    ##  Add a new node.  But if one already exists, just add a new expansion.

    def add_node (self, X, expansion, i, j, sem=None):
        if (X,i,j) in self.chart:
            node = self.chart[X,i,j]
            node.add(expansion)
            if self.trace: print('Add Expansion', node, expansion, file=self.trace_output)
        else:
            node = Node(X, expansion, i, j)
            self.chart[X,i,j] = node
            if self.trace: print('Add Node', node, expansion, file=self.trace_output)
            self.combine(node)
            self.start(node)

    ##  Add a new edge.

    def add_edge (self, edge):
        if self.trace: print('Add Edge', edge, file=self.trace_output)
        cat = edge.afterdot()
        if cat:
            self.edges.add((edge.end(), cat[0]), edge)
        else:
            self.complete(edge)        

    ##  Contents as a string.

    def __str__ (self):
        items = chain(iter(self.chart.values()), iter(self.edges.values()))
        lines = [str(item) for item in sorted(items, key=lambda x:x.timestep)]
        return '\n'.join(lines)

    ##  Reload the grammar.

    def reload (self):
        self.grammar = Grammar(self.filename)


#--  Unwind  -------------------------------------------------------------------

##  Unwind trees out of the chart.

def unwind (node, limit=None):
    out = []
    for e in node.expansions:
        if isinstance(e, Lexicon.Entry):
            out.append(Tree(e.pos, word=e.word, sem=e.sem))
        elif len(e.expansion) == 0:
            out.append(Tree(node.cat), [], sem=e.reduce([]))
        else:
            for childlist in tree_expansions(e.expansion, limit):
                tree = Tree(node.cat, childlist, sem=e.reduce(childlist))
                out.append(tree)
    return out

##  Convert an expansion containing nodes into a list of expansions containing
#   trees.

def tree_expansions (node_expansion, limit=None):
    choices = [unwind(n, limit) for n in node_expansion]
    if limit:
        if product(len(s) for s in choices) > limit:
            raise TooManyParses('Too many parses')
    return cross_product(choices)

##  Limit exceeded.

class TooManyParses (Exception): pass


#--  Fragments  ----------------------------------------------------------------

##  Get the best fragments out of the chart.

def fragments (p):
    n = len(p.words)
    starting_at = [[] for i in range(n)]
    best_ending_at = [None for i in range(n+1)]
    for node in p.chart.values():
        starting_at[node.i].append(node)
    for i in range(len(p.words)):
        starting_at[i].append(Node(None, p.words[i], i, i+1))
    best_ending_at[0] = (None, 0)
    for i in range(n):
        old = best_ending_at[i]
        if old:
            v = old[1] + 1
            for node in starting_at[i]:
                j = node.j
                alt = best_ending_at[j]
                if alt is None or v < alt[1]:
                    best_ending_at[j] = (node, v)
    return list(reversed(list(_unwind(best_ending_at))))

def _unwind (ending):
    (node, v) = ending[-1]
    yield node
    while node.i > 0:
        (node, v) = ending[node.i]
        yield node

##  Print the best fragments.

def print_fragments (p, output=None):
    for node in fragments(p):
        print(node.cat, ' '.join(p.words[node.i:node.j]), file=output)

##  Print the nodes of the chart.

def print_nodes (p, cat=None, output=None):
    if not isinstance(cat, (type(None), str)):
        raise Exception('Cat must be a string')
    for key in sorted(p.chart.keys()):
        node = p.chart[key]
        if cat is None or basecat(node.cat) == cat:
            print(node.cat, ' '.join(p.words[node.i:node.j]), file=output)


#--  Chart  --------------------------------------------------------------------

##  This is only for debugging, not actually used during parsing.

class Chart (object):

    ##  Constructor.

    def __init__ (self, parser):

        ##  The parser.
        self.parser = parser

        ##  The input words.
        self.words = parser.words

        ##  Chart contents.  It contains both nodes and edges.
        self.entries = Index()

        for node in parser.chart.values():
            span = (node.i, node.j)
            self.entries.add(span, node)

        for edge in parser.edges.values():
            span = (edge.start(), edge.end())
            self.entries.add(span, edge)

    ##  Number of entries.

    def __len__ (self): return len(self.entries)

    ##  Iterate over the keys.

    def __iter__ (self): return iter(self.entries)

    ##  Get the entry for the given key.

    def __getitem__ (self, i): return self.entries[i]

    ##  Contents, as a string.

    def __str__ (self):
        out = OutputList()
        for (i, (b,e)) in enumerate(sorted(self.entries)):
            print('[%d]' % i, ' '.join(self.words[b:e]), file=out)
            for (j, x) in enumerate(self.entries[b,e]):
                if isinstance(x, Node):
                    s = '<%d>' % len(x.expansions)
                else:
                    s = ''
                print('  [%d]' % j, x, s, file=out)
        return '\n'.join(out)


#    def __str__ (self):
#        wordline = []
#        numline = []
#        for i, word in enumerate(self.words):
#            s = str(i)
#            wordline.append(' ' * len(s))
#            numline.append(s)
#            wordline.append(word)
#            numline.append(' ' * len(word))
#        numline.append(str(len(self.words)))
#            
#        lines = [''.join(wordline), ''.join(numline)]
#        for i, entry in enumerate(self.entries):
#            lines.append('[%d] %s <%d>' % (i, entry, len(entry.expansions)))
#        return '\n'.join(lines)


##  History.

class History (object):

    ##  Constructor.

    def __init__ (self, edge):

        ##  The edge.
        self.edge = edge

        ##  Entries.
        self.entries = []

        entry = edge
        while entry:
            self.entries.append(entry)
            entry = entry.prev
        self.entries.reverse()

    ##  Number of entries.

    def __len__ (self): return len(self.entries)

    ##  Iterate over entries.

    def __iter__ (self): return iter(self.entries)

    ##  I-th entry.

    def __getitem__ (self, i): return self.entries[i]

    ##  String representation.

    def __str__ (self):
        return '\n'.join('[%d] %s' % (i, entry) for i, entry in enumerate(self.entries))


### Tester --------------------------------------------------------------

##  Tester.

class Tester (object):

    ##  Constructor.

    def __init__ (self, name):

        ##  Grammar name.
        self.name = name

        ##  Sentence.
        self.sent = None

        ##  Parser.
        self.parser = Parser(name)

        ##  Sents file.
        self.batchfile = name + '.sents'

    ##  Run it.

    def __call__ (self, sent=None):
        if sent is None:
            if self.sent:
                self.reload()
                sent = self.sent
            elif sent is None:
                raise Exception("No sentence")
            else:
                self.sent = sent
        trees = self.parser(sent)
        if trees:
            for tree in trees:
                print()
                print(tree)
        else:
            print()
            print('(No parse)')

    ##  Reload the grammar.

    def reload (self):
        self.parser.grammar = Grammar(self.name)

    ##  Run a batch.

    def batch (self, batchfile=None):
        if batchfile:
            self.batchfile = batchfile
        else:
            batchfile = self.batchfile
        for sent in open(batchfile):
            sent = sent.strip()
            print()
            print(sent)
            self(sent)
