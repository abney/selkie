##  \package seal.nlp.gen
#   Generates random sentences from a grammar.

from .features import unify as unify_cats, subst
from .avs import unify
from .grammar import Rule, ReverseLexicon
from .tree import Tree


##  Trace flag.
TraceOn = False


##  A node in a generated tree.

class Node (object):

    ##  Constructor.

    def __init__ (self, gen, cat, sem):

        ##  The generator.
        self.gen = gen

        ##  Category.
        self.cat = cat

        ##  Semantics.
        self.sem = sem

        ##  Callers.
        self.callers = []

        ##  Trees.
        self.trees = []
        
    ##  String representation.

    def __repr__ (self):
        return '(Node %s %s)' % (self.cat, repr(self.sem))

    ##  Pushes new states onto todo.

    def expand (self):
        g = self.gen.grammar
        for rule in g.expansions(self.cat[0]):
            bindings = unify_cats(rule.lhs, self.cat, rule.bindings)
            if bindings is None: continue
            sem = rule.sem.match(self.sem)
            if sem is None: continue
            state = State(self, rule, bindings, sem)
            self.gen.add_state(state)
        lex = self.gen.lexicon
        for entry in lex[self.cat[0], self.sem]:
            if unify_cats(entry.pos, self.cat, []) is None: continue
            self.add_tree(Tree(entry.pos, word=entry.word, sem=entry.sem))

    ##  Add a caller.

    def add_caller (self, caller):
        if TraceOn: print('Add caller', repr(caller), 'to', repr(self))
        self.callers.append(caller)
        n = len(self.trees)
        for i in range(n):
            caller.extend(self.trees[i])

    ##  Add a tree.

    def add_tree (self, tree):
        if TraceOn: print('Add tree', repr(tree), 'to', repr(self))
        self.trees.append(tree)
        n = len(self.callers)
        for i in range(n):
            self.callers[i].extend(tree)


##  A state of the generator.

class State (object):

    ##  Constructor.

    def __init__ (self, node, rule, bindings, sem, children=[]):

        ##  Current node.
        self.node = node

        ##  The rule used.
        self.rule = rule

        ##  Bindings.
        self.bindings = bindings

        ##  Semantics.
        self.sem = sem

        ##  Children.
        self.children = children

    ##  String representation.

    def __repr__ (self):
        rhs = [str(cat) for cat in self.rule.rhs]
        i = len(self.children)
        rhs[i:i] = '*'
        return '(State %s -> %s : %s)' % (self.rule.lhs, ' '.join(rhs), self.sem)

    ##  Called when the state is popped off todo.

    def advance (self):
        i = len(self.children)
        n = len(self.rule.rhs)
        if i < n:
            cat = subst(self.bindings, self.rule.rhs[i])
            sem = self.sem[1+i]
            node = self.node.gen.intern(cat, sem)
            node.add_caller(self)
        else:
            cat = subst(self.bindings, self.rule.lhs)
            sem = self.sem.avs
            self.node.add_tree(Tree(cat, self.children, sem=sem))

    ##  Called each time the node gets a new tree.

    def extend (self, tree):
        i = len(self.children)
        bindings = unify_cats(self.rule.rhs[i], tree.cat, self.bindings)
        if bindings is None: return
        sem = self.sem.extend(tree.sem)
        if sem is None: return
        children = self.children + [tree]
        state = State(self.node, self.rule, bindings, sem, children)
        self.node.gen.add_state(state)


##  The generator.

class Generator (object):

    ##  Constructor.

    def __init__ (self, grammar):

        ##  The grammar.
        self.grammar = grammar

        ##  The lexicon.
        self.lexicon = ReverseLexicon(grammar.lexicon)

        ##  Trees.
        self.trees = None

        ##  Nodes.
        self.nodes = None

        ##  To be processed.
        self.todo = None


    ##  Called when a complete tree is created.

    def extend (self, tree):
        if TraceOn: print('Add root', repr(tree))
        self.trees.append(tree)

    ##  Add a state to the to-do list.

    def add_state (self, state):
        if TraceOn: print('Add state', state)
        self.todo.append(state)

    ##  Returns self, which behaves as an iteration.

    def __call__ (self, sem):
        self.trees = []
        self.nodes = {}
        self.todo = []
        node = self.intern(self.grammar.start, sem)
        node.add_caller(self)
        return self

    ##  Intern a cat and semantics.

    def intern (self, cat, sem):
        key = (cat, sem)
        if key in self.nodes:
            return self.nodes[key]
        else:
            node = Node(self, cat, sem)
            self.nodes[key] = node
            if TraceOn: print('New node:', node)
            node.expand()
            return node

    ##  Iteration method.

    def __next__ (self):
        while not self.trees:
            if self.todo:
                q = self.todo.pop()
                if TraceOn: print('Process state', q)
                q.advance()
            else:
                raise StopIteration
        return self.trees.pop()

    ##  Returns self.

    def __iter__ (self):
        return self
