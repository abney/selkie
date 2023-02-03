##  \package seal.nlp.logic
#   Resolution-based theorem prover.

from itertools import chain
from heapq import heappush, heappop
from .io import iter_tokens, StringIO, ispathlike
from .seq import cross_product, concat, unique
from .expr import Variable, Expr, parse_expr, load_exprs, scan_expr, fresh_variable
from .interp import standardize_variables, Symtab


#--  Literal and clause  -------------------------------------------------------

##  A literal.

class Literal (object):

    ##  Constructor.

    def __init__ (self, polarity, expr):

        ##  The polarity.
        self.polarity = polarity

        ##  The atomic formula.
        self.expr = expr

    ##  Key for comparisons: (polarity, expression).

    def key (self):
        return (self.polarity, self.expr)

    ##  Comparison by key.

    def __lt__ (self, other):
        return self.key() < other.key()

    ##  Comparison by key.

    def __eq__ (self, other):
        return self.key() == other.key()

    ##  String representation.

    def __repr__ (self):
        if self.polarity: p = '+'
        else: p = '-'
        return p + str(self.expr)


##  A clause.

class Clause (object):

    ##  Supplies clause numbers.
    count = 0

    ##  Constructor.

    def __init__ (self, literals, answer_literal=None, provenance=None):
        Clause.count += 1

        ##  The clause number.
        self.index = Clause.count

        ##  The literals (without duplicates).
        self.literals = unique(literals)

        ##  The answer literal.
        self.answer_literal = answer_literal

        ##  Provenance.
        self.provenance = provenance

        ##  Weight.
        self.weight = None

    ##  Always true.

    def __bool__ (self):
        return True

    ##  Comparison by weight.

    def __lt__ (self, other):
        assert not (self.weight is None or other.weight is None)        
        return self.weight < other.weight

    ##  Comparison by weight.

    def __eq__ (self, other):
        assert not (self.weight is None or other.weight is None)        
        return self.weight == other.weight

    ##  Number of literals.

    def __len__ (self):
        return len(self.literals)

    ##  Returns the i-th literal.

    def __getitem__ (self, i):
        return self.literals[i]

    ##  Returns the argument of the answer literal, which must have '_Ans'
    #   as operator.

    def answer (self):
        assert self.answer_literal and self.answer_literal.expr[0] == '_Ans'
        return self.answer_literal.expr[1]

    ##  String representation.

    def __str__ (self):
        if self.answer_literal:
            ans = ' ; ' + repr(self.answer_literal)
        else:
            ans = ''
        if self.provenance:
            (c1, i, c2, j) = self.provenance
            prov = ' %d.%d+%d.%d' % (c1.index, i+1, c2.index, j+1)
        else:
            prov = ''
        if self.weight is not None:
            wt = ' wt=' + str(self.weight)
        else:
            wt = ''
        return str(self.index) + '. ' + ' '.join(repr(lit) for lit in self.literals) + ans + prov + wt

    ##  Brief representation.

    def __repr__ (self):
        return '<Clause %d>' % self.index


##  Parse a clause.

def parse_clause (s):
    toks = iter_tokens(StringIO(s))
    lits = []
    while toks.has_next():
        lits.append(scan_literal(toks))
    return Clause(lits)

##  Scan a literal.

def scan_literal (toks):
    sign = next(toks)
    if sign == '+': sign = True
    elif sign == '-': sign = False
    else: raise Exception("Bad sign: " + sign)
    expr = scan_expr(toks)
    return Literal(sign, expr)


#--  Check syntax  -------------------------------------------------------------

##  Table mapping operators to tuple of argument types (variable or expression).
syntax_table = {'wh': ('var', 'expr'),
                'forall': ('var', 'expr'),
                'exists': ('var', 'expr'),
                'if': ('expr', 'expr'),
                'iff': ('expr', 'expr'),
                'and': ('expr', 'expr'),
                'or': ('expr', 'expr'),
                'not': ('expr',),
                'yn': ('expr',)}

##  Check that the expression is well-formed.

def check_syntax (expr):
    if isinstance(expr, Expr) and expr[0] in syntax_table:
        argtypes = syntax_table[expr[0]]
        if len(expr) != 1 + len(argtypes):
            raise Exception("Wrong number of children: " + str(expr))
        else:
            for arg, argtype in zip(expr[1:], argtypes):
                if argtype == 'expr': pass
                elif argtype == 'var':
                    if not isinstance(arg, Variable):
                        raise Exception("Expecting variable in: " + str(expr))
                else:
                    raise Exception("Bad argtype")
    if isinstance(expr, Expr):
        for child in expr:
            check_syntax(child)


#--  Expand query  -------------------------------------------------------------

##  Expand out 'wh' and 'yn' operators into forms containing '_Ans'.

def expand_query (expr):
    if expr[0] == 'wh':
        v, body = expr[1:]
        return Expr(['forall', v, Expr(['if', body, Expr(['_Ans', v])])])
    elif expr[0] == 'yn':
        body = expr[1]
        return Expr(['and',
                     Expr(['if', body, Expr(['_Ans', 'yes'])]),
                     Expr(['if', Expr(['not', body]), Expr(['_Ans', 'no'])])])
    else:
        return expr


#--  Eliminate implications  ---------------------------------------------------

##  Expand implications.

def eliminate_implications (expr):
    if not isinstance(expr, Expr):
        return expr
    elif expr[0] == 'if':
        cond = eliminate_implications(expr[1])
        body = eliminate_implications(expr[2])
        return Expr(['or', Expr(['not', cond]), body])
    elif expr[0] == 'iff':
        p = eliminate_implications(expr[1])
        q = eliminate_implications(expr[2])
        return Expr(['and',
                     Expr(['or', Expr(['not', p]), q]),
                     Expr(['or', Expr(['not', q]), p])])
    else:
        return Expr(eliminate_implications(c) for c in expr)


#--  Lower negation  -----------------------------------------------------------

##  Lower negation.

def lower_negation (expr):
    if not isinstance(expr, Expr):
        return expr
    elif expr[0] == 'not':
        return negate(expr[1])
    else:
        return Expr(lower_negation(c) for c in expr)

##  Negate an expression, returning an expression in which all negation has
#   been lowered.

def negate (expr):
    if not isinstance(expr, Expr):
        return Expr(['not', expr])
    elif expr[0] == 'and':
        return Expr(['or'] + [negate(c) for c in expr[1:]])
    elif expr[0] == 'or':
        return Expr(['and'] + [negate(c) for c in expr[1:]])
    elif expr[0] == 'forall':
        return Expr(['exists', expr[1], negate(expr[2])])
    elif expr[0] == 'exists':
        return Expr(['forall', expr[1], negate(expr[2])])
    elif expr[0] == 'not':
        return lower_negation(expr[1])
    else:
        return Expr(['not', expr])


#--  Skolemize  ----------------------------------------------------------------

##  Skolemize, eliminating 'exists' and 'forall'.
#   (The argument uvars contains universally bound variables whose scope we are in.)

def skolemize (expr, symtab=None, uvars=None):
    if symtab is None: symtab = Symtab()
    if uvars is None: uvars = []
    if isinstance(expr, Variable) and expr in symtab:
        return symtab[expr]
    elif not isinstance(expr, Expr):
        return expr
    elif expr[0] == 'exists':
        var = expr[1]
        oldval = symtab[var]
        if uvars:
            symtab[var] = Expr([newfun()] + uvars)
        else:
            symtab[var] = newfun()
        expr = skolemize(expr[2], symtab, uvars)
        symtab[var] = oldval
        return expr
    elif expr[0] == 'forall':
        uvars.append(expr[1])
        expr = skolemize(expr[2], symtab, uvars)
        uvars.pop()
        return expr
    else:
        return Expr(skolemize(c, symtab, uvars) for c in expr)

##  To assign numbers to Skolem functions.
function_count = 0

##  Create a Skolem function.

def newfun ():
    global function_count
    function_count += 1
    return '_Sk' + str(function_count)


#--  Conjunctive normal form  --------------------------------------------------

##  Convert to conjunctive-normal form.
#   Returns a list of lists (conjunction of disjunctions).

def cnf (expr):
    if not isinstance(expr, Expr):
        return [[expr]]
    elif expr[0] == 'or':
        conjunctions = [cnf(c) for c in expr[1:]]
        return [concat(disjunctions)
                for disjunctions in cross_product(conjunctions)]
    elif expr[0] == 'and':
        return concat(cnf(c) for c in expr[1:])
    else:
        check_no_juncts(expr)
        return [[expr]]

##  Check that there are no 'and' or 'or' operators anywhere in the
#   expression.

def check_no_juncts (expr):
    if isinstance(expr, Expr):
        if expr[0] in ('and', 'or'):
            raise Exception("Buried and/or")
        for c in expr[1:]:
            check_no_juncts(c)


#--  Clauses  ------------------------------------------------------------------

##  Convert a conjunctive-normal form expression to a list of clauses.

def clauses (conj, apart=False):
    conj = simplify_conjunction(conj)
    if conj is True: return []
    clauses = [as_clause(d) for d in conj]
    if apart:
        for i in range(1, len(clauses)):
            clauses[i] = standardize_apart(clauses[i])
    return clauses

##  Convert a disjunction to a clause.

def as_clause (disj):
    literals = [as_literal(e) for e in disj]
    (literals, ans) = isolate_answer_literal(literals)
    return Clause(literals, answer_literal=ans)

##  Returns a pair (literals, ans), where ans is the answer literal
#   and literals are the others.

def isolate_answer_literal (literals):
    a = None
    for i in range(len(literals)):
        lit = literals[i]
        if lit.expr[0] == '_Ans':
            if lit.polarity is False:
                raise Exception("Negative answer literal")
            if a is not None:
                raise Exception("Multiple answer literals")
            a = i
    if a is None:
        ans = None
    else:
        ans = literals[a]
        del literals[a]
    return (literals, ans)

##  Convert an atomic formula or negated atomic formula to a literal.

def as_literal (expr):
    if isinstance(expr, Expr) and expr[0] == 'not':
        return Literal(False, expr[1])
    else:
        return Literal(True, expr)

##  A True element can be dropped from a conjunction.
#   An empty conjunction is True.
#   A False element makes the whole conjunction False.

def simplify_conjunction (conj):
    out = []
    for disj in conj:
        disj = simplify_disjunction(disj)
        if disj is True: pass
        elif disj is False: return False
        else: out.append(disj)
    if out: return out
    else: return True

##  A False literal can be dropped from a disjunction.
#   An empty disjunction is False.
#   A True literal makes the whole disjunction True.

def simplify_disjunction (disj):
    out = []
    for lit in disj:
        v = boolean_value(lit)
        if v is True: return True
        elif v is False: pass
        else: out.append(lit)
    if out: return out
    else: return False

##  Convert an expression to a boolean value.

def boolean_value (expr):
    if expr == 'True': return True
    elif expr == 'False': return False
    elif not isinstance(expr, Expr): return None
    elif expr[0] == 'not':
        v = boolean_value(expr[1])
        if v is None: return None
        else: return not v
    else: return None


#--  Clausify  -----------------------------------------------------------------

##  Clausify an expression.
#   The steps are, in order: variable standardization, query expansion,
#   elimination of implications, lowering of negation, Skolemization,
#   conversion to conjunctive normal form, conversion to clauses.

def clausify (expr, apart=False, trace=False):
    check_syntax(expr)
    expr = standardize_variables(expr)
    if trace:
        print('#Standardize variables:')
        print(' ', expr)
    expr = expand_query(expr)
    if trace:
        print('#Expand query:')
        print(' ', expr)
    expr = eliminate_implications(expr)
    if trace:
        print('#Eliminate implications:')
        print(' ', expr)
    expr = lower_negation(expr)
    if trace:
        print('#Lower negation:')
        print(' ', expr)
    expr = skolemize(expr)
    if trace:
        print('#Skolemize:')
        print(' ', expr)
    conj = cnf(expr)
    if trace:
        print('#Conjunctive normal form:')
        print(' ', conj)
    out = clauses(conj, apart)
    if trace:
        print('#Clauses:')
        for clause in out:
            print(' ', clause)
    return out


#--  KB  -----------------------------------------------------------------------

##  A knowledge base.

class KB (object):

    ##  Constructor.

    def __init__ (self, filename=None):

        ##  The clauses.
        self.clauses = []
        if filename:
            self.load(filename)

        ##  The prover.
        self.prover = None

    ##  Load from a file.

    def load (self, filename):
        for expr in load_exprs(filename):
            self.add(expr)
        
    ##  The number of clauses.

    def __len__ (self):
        return len(self.clauses)

    ##  Get the i-th clause.

    def __getitem__ (self, i):
        return self.clauses[i]

    ##  Delete the i-th clause.

    def __delitem__ (self, i):
        del self.clauses[i]

    ##  Delete the clause with the given ID (clause number).

    def delete (self, id):
        for i in range(len(self.clauses)):
            if clause.index == id:
                del self.clauses[i]
                break

    ##  Delete all clauses.

    def clear (self):
        self.clauses = []

    ##  Iterate over the clauses.

    def __iter__ (self):
        return iter(self.clauses)

    ##  Add a new expression.  It is first clausified.

    def add (self, expr):
        if isinstance(expr, str): expr = parse_expr(expr)
        for clause in clausify(expr):
            self.clauses.append(clause)

    ##  Answer a query.

    def ask (self, expr):
        if isinstance(expr, str): expr = parse_expr(expr)
        if self.prover is None: self.prover = Prover(self)
        return self.prover(expr)

    ##  String representation.

    def __str__ (self):
        return '\n'.join(str(clause) for clause in self.clauses)


#--  Unification  --------------------------------------------------------------

##  Unification failure.

class Fail (Exception): pass

##  Called for side effect: modifies env.  Raises Fail on failure.

def unify (x, y, env):
    if isinstance(x, Literal) and isinstance(y, Literal):
        if x.polarity != y.polarity: raise Fail
        unify1(x.expr, y.expr, env)
    else:
        unify1(x, y, env)

##  Called for side effect: modifies env.  Raises Fail on failure.

def unify1 (x, y, symtab):
    if isinstance(x, Variable): unify_var(x, y, symtab)
    elif isinstance(y, Variable): unify_var(y, x, symtab)
    elif isinstance(x, Expr) and isinstance(y, Expr):
        if len(x) != len(y): raise Fail
        for i in range(0, len(x)):
            unify1(x[i], y[i], symtab)
    elif x != y: raise Fail

##  Unify a variable with a given value.

def unify_var (v, x, symtab):
    if v in symtab:
        unify1(symtab[v], x, symtab)
    elif isinstance(x, Variable) and x in symtab:
        unify1(v, symtab[x], symtab)
    else:
        if occurs(v, x, symtab): raise Fail
        symtab[v] = x

##  Occurs check.

def occurs (var, expr, symtab):
    if var == expr:
        return True
    elif isinstance(expr, Variable) and expr in symtab:
        return occurs(var, symtab[expr], symtab)
    elif not isinstance(expr, Expr):
        return False
    else:
        for c in expr[1:]:
            if occurs(var, c, symtab): return True
        return False

##  Resolve the i-th literal of clause1 with the j-th literal of clause2.

def resolve (clause1, i, clause2, j):
    if clause1[i].polarity == clause2[j].polarity: return None
    try:
        return resolve1(clause1, i, clause2, j, {})
    except Fail:
        return None
        
##  Helper function.

def resolve1 (clause1, i, clause2, j, env):
    unify(clause1[i].expr, clause2[j].expr, env)
    if clause1.answer_literal:
        ans = clause1.answer_literal
        if clause2.answer_literal:
            unify(clause1.answer_literal, clause2.answer_literal, env)
    else:
        ans = clause2.answer_literal

    literals = clause2[:j] + clause2[j+1:] + clause1[:i] + clause1[i+1:]
    return standardize_apart(Clause(literals, answer_literal=ans,
                                    provenance=(clause1, i, clause2, j)),
                             env)

##  Unify pairs of literals; returns a list of new clauses.

def factor (clause):
    out = []
    n = len(clause)
    for i in range(n-1):
        for j in range(i+1, n):
            try:
                env = {}
                unify(clause[i], clause[j], env)
                literals = clause[:j] + clause[j+1:]
                out.append(standardize_apart(Clause(literals,
                                                    clause.answer_literal,
                                                    (clause, i, clause, j)),
                                             env))
            except Fail:
                pass
    return out

##  Make sure every clause has its only variables.

def standardize_apart (x, env=None, newvars=None):
    if newvars is None: newvars = {}
    if env is None: env = {}
    if isinstance(x, Clause):
        literals = [standardize_apart(t, env, newvars) for t in x.literals]
        if x.answer_literal: ans = standardize_apart(x.answer_literal, env, newvars)
        else: ans = None
        return Clause(literals, answer_literal=ans, provenance=x.provenance)
    elif isinstance(x, Literal):
        return Literal(x.polarity, standardize_apart(x.expr, env, newvars))
    elif isinstance(x, Variable):
        if x in env:
            return standardize_apart(env[x], env, newvars)
        elif x in newvars:
            return newvars[x]
        else:
            y = fresh_variable()
            newvars[x] = y
            return y
    elif not isinstance(x, Expr):
        return x
    else:
        return Expr(standardize_apart(c, env, newvars) for c in x)


#--  Prover  -------------------------------------------------------------------

##  Instantiate and call a prover.

def solve (query, kb, trace=False, maxsteps=None):
    p = Prover(kb)
    return p(query, trace, maxsteps)

##  Theorem prover.

class Prover (object):
    
    ##  Constructor.

    def __init__ (self, kb):
        if ispathlike(kb):
            kb = KB(kb)
        assert isinstance(kb, KB)

        ##  The knowledge base.
        self.kb = kb

        ##  List of clauses that have been processed and can still be used passively.
        self.usable = None

        ##  List of active clauses that are yet to be processed.
        self.sos = None

        ##  Answers found so far.
        self.answers = None

        ##  Trace flag.
        self.tracing = False

        ##  Weight component for number of literals.
        self.literal_weight = 1

        ##  Weight component for number of nodes.
        self.node_weight = 1

        ##  Weight component for number of variables.
        self.variable_weight = 1

        ##  How many steps before we give up.
        self.maxsteps = 200

    ##  Run it.

    def __call__ (self, query, trace=False, maxsteps=None):
        if maxsteps is None: maxsteps = self.maxsteps
        self.tracing = trace
        self.answers = {}
        self.set_query(query)
        if self.tracing:
            print('KB')
            for clause in self.kb: print(clause)
            print('USABLE')
            for clause in self.usable: print(clause)
            print('SOS')
            for clause in self.sos: print(clause)
        while self.sos:
            if len(self.usable) >= maxsteps:
                if self.tracing: print('OUT OF TIME')
                break
            self.step()
        self.usable = None
        self.sos = None
        return list(self.answers.keys())
        
    ##  Set the query.  Clear the usable list and initialize the SOS list.

    def set_query (self, query):
        if isinstance(query, str): query = parse_expr(query)
        clauses = clausify(query, apart=True)
        self.usable = []
        self.sos = []
        for clause in clauses:
            if clause.answer_literal is None:
                self.usable.append(clause)
            else:
                clause.weight = 0
                self.sos.append(clause)

    ##  Do one resolution.

    def step (self):
        clause = heappop(self.sos)
        if self.tracing: print('Resolve', clause)
        if len(clause) == 0:
            if self.tracing: print('ANSWER', clause)
            ans = clause.answer()
            if ans in self.answers:
                self.answers[ans].append(clause)
            else:
                self.answers[ans] = [clause]
        else:
            # will we ever want to resolve a clause with itself?
            self.usable.append(clause)
            for other in chain(self.kb, self.usable):
                for j in range(len(other)):
                    newclause = resolve(clause, 0, other, j)
                    if newclause: self.add(newclause)
            for newclause in factor(clause):
                self.add(newclause)

    ##  Add a new clause.

    def add (self, newclause):
        self.set_weight(newclause)
        heappush(self.sos, newclause)
        if self.tracing: print('   ', newclause)

    ##  Set the weight for a clause.

    def set_weight (self, clause):
        nnodes = sum(self.expr_size(lit.expr) - 1 for lit in clause)
        vars = set()
        for lit in clause: self.collect_variables(lit.expr, vars)
        clause.weight = \
            self.literal_weight * len(clause) + \
            self.node_weight * nnodes + \
            self.variable_weight * len(vars)

    ##  Compute the size of an expression.

    def expr_size (self, expr):
        if not isinstance(expr, Expr): return 0
        else: return 1 + sum(self.expr_size(c) for c in expr[1:])

    ##  Collect the variables occurring in an expression.

    def collect_variables (self, expr, vars):
        if isinstance(expr, Variable):
            vars.add(expr)
        elif isinstance(expr, Expr):
            for child in expr[1:]:
                self.collect_variables(child, vars)

    ##  Contents as a string.

    def __str__ (self):
        lines = []
        if self.kb:
            lines.append('KB:')
            lines.append(str(self.kb))
        if self.usable:
            lines.append('Usable:')
            for clause in self.usable:
                lines.append(str(clause))
        if self.sos:
            lines.append('SOS:')
            for clause in self.sos:
                lines.append(str(clause))
        return '\n'.join(lines)
