##  \package seal.nlp.interp
#   Semantic interpreter.

from .tree import Tree, is_leaf, getsem, getchildren
from .expr import Expr, Variable, parse_expr, scan_expr, fresh_variable
from .grammar import GrammarLoader
from .parser import Parser


#--  Helpers  ------------------------------------------------------------------

##  True if the input is a complex expression whose first element is the
#   symbol 'lambda'.

def is_lambda_expr (x):
    return isinstance(x, Expr) and len(x) > 0 and x[0] == 'lambda'

##  Returns a tuple containing values for params in env.

def save_values (params, env):
    oldvals = []
    for i in range(len(params)):
        vbl = params[i]
        if vbl in env: oldvals.append(env[vbl])
        else: oldvals.append(None)
    return oldvals

##  Modifies env to restore an old set of values.

def restore_values (params, oldvals, env):
    for i in range(len(params)):
        vbl = params[i]
        if oldvals[i] is None:
            del env[vbl]
        else:
            env[vbl] = oldvals[i]


#--  Normalize  ----------------------------------------------------------------

##  Normalize an expression.  This appears to be standardize_variables() limited
#   to lambda expressions.

def normalize (x, repl=None):
    if repl is None: repl = {}
    if isinstance(x, Variable) and x in repl:
        return repl[x]
    elif not isinstance(x, Expr):
        return x
    elif not is_lambda_expr(x):
        return Expr(normalize(c, repl) for c in x)
    else:
        assert len(x) == 3
        params = x[1]
        body = x[2]
        if not isinstance(params, tuple):
            params = (params,)
        for param in params:
            assert isinstance(param, Variable)
        oldvals = save_values(params, repl)
        newparams = Expr(fresh_variable() for param in params)
        for param, newparam in zip(params, newparams):
            repl[param] = newparam
        body = normalize(body, repl)
        restore_values(params, oldvals, repl)
        return Expr(['lambda', newparams, body])


#--  Simplify  -----------------------------------------------------------------

##  Simplify an expression.  Find all lambda-expressions that are being applied
#   to arguments and do beta-reduction.  Keep going until they have all been
#   expanded.  (May get stuck in an infinite loop if the expression is pathological.)

def simplify (x, env=None):
    if env is None:
        return simplify(normalize(x), {})
    elif isinstance(x, Variable) and x in env:
        return normalize(env[x])
    elif not isinstance(x, Expr):
        return x
    elif x[0] == 'lambda':
        return Expr(['lambda', x[1], simplify(x[2], env)])
    else:
        x = Expr(simplify(c, env) for c in x)
        if is_lambda_expr(x[0]):
            return beta_reduce(x, env)
        else:
            return x

##  Beta-reduction.

def beta_reduce (x, env):
    assert x[0][0] == 'lambda'
    params = x[0][1]
    body = x[0][2]
    args = x[1:]
    for param, arg in zip(params, args):
        env[param] = arg
    result = simplify(body, env)
    for param in params:
        del env[param]
    return result


#--  Replace metavariables  ----------------------------------------------------

##  Replace metavariables throughout the tree.

def tree_replace_metavariables (tree):
    sem = getsem(tree)
    children = getchildren(tree)
    if children:
        for c in children:
            tree_replace_metavariables(c)
    if sem: tree.sem = replace_metavariables(sem)

##  Replace metavariables.

def replace_metavariables (expr, vars=None):
    if vars is None: vars = []
    if isinstance(expr, str) and expr[0] == '@':
        if len(expr) == 1: i = 0
        else: i = int(expr[1:]) - 1
        while len(vars) <= i: vars.append(fresh_variable())
        return vars[i]
    elif not isinstance(expr, Expr):
        return expr
    else:
        return Expr(replace_metavariables(c, vars) for c in expr)


#--  Fuse/translate  -----------------------------------------------------------

##  Paste a set of child expressions into a parent expression.
#   Returns a new expression (non-destructive).

def fuse (expr, childsems=None):
    if isinstance(expr, str) and expr[0] == '$':
        s = expr[1:]
        if s.isdigit():
            if childsems is None:
                raise Exception("$ not allowed in lexical entries")
            i = int(s) - 1
            if i < 0 or i >= len(childsems):
                raise Exception("$ index out of bounds: " + repr(expr))
            return childsems[i]
        else:
            return expr
    elif isinstance(expr, Expr):
        return Expr(fuse(c, childsems) for c in expr)
    else:
        return expr

##  Just a wrapper around fuse().

def translation (tree):
    if is_leaf(tree):
        return tree.sem
    else:
        childsems = [translation(c) for c in tree.children]
        return fuse(tree.sem, childsems)


#--  Replace gaps  -------------------------------------------------------------

##  Replace all gap operators (!g=, $g) in an expression.

def replace_gaps (expr, g=None):
    if expr == '$g':
        if g is None:
            raise Exception('Unbound gap')
        return g
    elif isinstance(expr, Expr):
        if len(expr) >= 1 and expr[0] == '!g=':
            if len(expr) != 3: raise Exception("Bad syntax for !g=: " + str(expr))
            return replace_gaps(expr[2], g=expr[1])
        # alt syntax
        elif len(expr) >= 2 and expr[0] == '!g' and expr[1] == '=':
            if len(expr) != 4: raise Exception('Bad syntax for !g=: ' + str(expr))
            return replace_gaps(expr[3], g=expr[2])
        else:
            return Expr(replace_gaps(c, g) for c in expr)
    else:
        return expr


#--  Standardize variables  ----------------------------------------------------

##  A symbol table for use in standardization.

class Symtab (dict):

    ##  Fetch the value for a given variable.

    def __getitem__ (self, k):
        if k in self: return dict.__getitem__(self, k)
        else: return None

    ##  Set the value for a variable.

    def __setitem__ (self, k, v):
        if v is None: dict.__delitem__(self, k)
        else: dict.__setitem__(self, k, v)

    ##  Contents as a string.

    def __str__ (self):
        items = [(str(k), repr(v)) for (k,v) in self.items()]
        lines = [k + ' -> ' + v for (k,v) in sorted(items)]
        return '\n'.join(lines)


##  Set of variable-binding operators.
VariableBindingOperators = set(['lambda', 'forall', 'exists', 'wh'])

##  Make sure each instance of a variable-binding operator binds a unique variable.

def standardize_variables (expr, replacements=None):
    if replacements is None: replacements = Symtab()
    if isinstance(expr, Variable) and expr in replacements:
        return replacements[expr]
    elif not isinstance(expr, Expr):
        return expr
    elif len(expr) > 0 and expr[0] in VariableBindingOperators:
        assert len(expr) == 3
        if isinstance(expr[1], Expr):
            vars = expr[1]
        else:
            vars = [expr[1]]
        oldvals = [replacements[v] for v in vars]
        for var in vars:
            replacements[var] = fresh_variable()
        expr = Expr(standardize_variables(c, replacements) for c in expr)
        for (var, val) in zip(vars, oldvals):
            replacements[var] = val
        return expr
    else:
        return Expr(standardize_variables(c, replacements) for c in expr)


#--  Raise quantifiers  --------------------------------------------------------

##  Whether the expression is complex and has op as first child.

def hasop (op, expr):
    return isinstance(expr, Expr) and len(expr) > 0 and expr[0] == op

##  Raise quantifiers.

def raise_quantifiers (tree):
    if is_leaf(tree):
        return tree
    elif hasop('!qs', tree.sem):
        if len(tree.sem) != 2:
            raise Exception("Bad syntax for !qs: " + str(tree.sem))
        qs = []
        tree = Tree(tree.cat,
                    [excise_quantifiers(c, qs) for c in tree.children],
                    sem=tree.sem[1])
        while qs:
            q = qs.pop()
            i = len(q.children) + 1
            sem = Expr(q.sem[1:] + ('$%d' % i,))
            tree = Tree(q.cat, q.children + [tree], sem=sem)
        return tree
    else:
        return Tree(tree.cat,
                    [raise_quantifiers(c) for c in tree.children],
                    sem=tree.sem)

##  Excise quantifiers, leaving traces behind.  This is part of raising
#   quantifiers.

def excise_quantifiers (tree, qs):
    if is_leaf(tree):
        return tree
    elif hasop('!q', tree.sem):
        assert len(tree.sem) > 2
        var = tree.sem[2]
        qs.append(raise_quantifiers(tree))
        return Tree(tree.cat, sem=var)
    elif hasop(tree, '!qs'):
        return raise_quantifiers(tree)
    else:
        return Tree(tree.cat,
                    [excise_quantifiers(c, qs) for c in tree.children],
                    sem=tree.sem)


#--  Expand definitions  -------------------------------------------------------

##  Deep copy, replacing the given variables with the given values. 

def replace_variables (vars, values, expr):
    if isinstance(expr, Variable):
        try:
            return values[vars.index(expr)]
        except:
            return expr
    elif not isinstance(expr, Expr):
        return expr
    else:
        return Expr(replace_variables(vars, values, c) for c in expr)


##  A macro definition.

class Definition (object):

    ##  Constructor.

    def __init__ (self, op, params, body):

        ##  The operator.
        self.op = op

        ##  The parameters.
        self.params = [Variable(p) for p in params]

        ##  The body.
        self.body = body


##  A set of macro definitions.

class Macros (object):

    ##  Constructor.

    def __init__ (self, filename=None):

        ##  Contents.
        self.defs = {}

        if filename:
            self.load(filename)

    ##  Load from file.

    def load (self, filename):
        with open(filename) as f:
            for line in f:
                line = line.strip()
                if (not line) or line.startswith('#'): continue
                i = line.index(':')
                template = line[:i].split()
                op = template[0]
                params = template[1:]
                body = parse_expr(line[i+1:].strip())
                self.define(op, params, body)

    ##  Add a definition.

    def define (self, op, params, body):
        if op in self.defs:
            raise Exception("Duplicate definition: " + op)
        self.defs[op] = Definition(op, params, body)

    ##  Fetch the definition for a given operator.

    def __getitem__ (self, op):
        return self.defs[op]

    ##  Do macro expansion within an expression.

    def __call__ (self, expr):
        if not isinstance(expr, Expr):
            return expr
        elif len(expr) > 0 and isinstance(expr[0], str) and expr[0] in self.defs:
            dfn = self.defs[expr[0]]
            args = expr[1:]
            expr = replace_variables(dfn.params, args, dfn.body)
            return self(expr)
        else:
            return Expr(self(c) for c in expr)


##  A version of GrammarLoader that includes macro definitions.

class SemGrammarLoader (GrammarLoader):

    def __init__ (self, interpreter):
        GrammarLoader.__init__(self, interpreter.grammar)

        ##  Interpreter.
        self.interpreter = interpreter

    ##  Wraps the default handler; adds a handler for a 'macros' section.

    def handle_section (self, what, tokens):
        if GrammarLoader.handle_section(self, what, tokens):
            return True
        elif what == 'macros':
            self.scan_macros(tokens)
            return True
        else:
            return False

    ##  Handler for the 'macros' section.

    def scan_macros (self, tokens):
        macros = self.interpreter.macros
        tokens.require('\n')
        while tokens.has_next('word'):
            op = tokens.require('word')
            params = []
            while not tokens.has_next(':'):
                params.append(tokens.require('word'))
            tokens.require(':')
            body = scan_expr(tokens)
            tokens.require('\n')
            macros.define(op, params, body)


#--  Interpreter  --------------------------------------------------------------

##  The semantic interpreter.

class Interpreter (object):

    ##  Constructor.

    def __init__ (self, name):

        ##  The grammar name.
        self.name = name

        ##  The parser.
        self.parser = Parser()

        ##  The grammar.
        self.grammar = self.parser.grammar

        ##  The macro definitions.
        self.macros = Macros()

        self.reload()

    ##  Parse and interpret a sentence.

    def __call__ (self, s, trace=False):
        if trace:
            print()
            print(s)
        trees = self.parser(s)
        if trees:
            return [self.interpret(t, trace) for t in trees]
        elif trace:
            print('#No parse')

    ##  Interpret a tree.
    #   The steps it goes through are, in order: metavariable replacement,
    #   quantifier raising, translation, gap replacement, 
    #   macro expansion, variable standardization, simplification.

    def interpret (self, tree, trace=False):
        if trace:
            print('#Tree:')
            print(tree)
        tree_replace_metavariables(tree)
        if trace:
            print('#Replace metavariables:')
            print(tree)
        tree = raise_quantifiers(tree)
        if trace:
            print('#Raise quantifiers:')
            print(tree)
        expr = translation(tree)
        if trace:
            print('#Translation:')
            print(' ', expr)
        expr = replace_gaps(expr)
        if trace:
            print('#Replace gaps:')
            print(' ', expr)
        expr = self.macros(expr)
        if trace:
            print('#Macros:')
            print(' ', expr)
        expr = standardize_variables(expr)
        if trace:
            print('#Standardize variables:')
            print(' ', expr)
        expr = simplify(expr)
        if trace:
            print('#Simplify:')
            print(' ', expr)
        return expr

    ##  Reload the parser and definitions.

    def reload (self):
        SemGrammarLoader(self).load(self.name)
