##  \package seal.nlp.expr
#   Predicate-calculus expressions.

import re
from .io import iter_tokens, tokenize, scanable_string


#--  Expr, Variable  -----------------------------------------------------------

##  Whether the given string contains a whitespace character.

def contains_space (s):
    for c in s:
        if c.isspace(): return True
    return False


##  A predicate-calculus expression.
#   It is a specialization of tuple, so the usual tuple operations can also
#   be used.

class Expr (tuple):

    ##  Convert to a string.

    def __str__ (self):
        return expr_string(self, 0)

    ##  String representation.

    def __repr__ (self):
        cs = []
        for c in self:
            if isinstance(c, str):
                if contains_space(c):
                    cs.append(scanable_string(c))
                else:
                    cs.append(c)
            else:
                cs.append(repr(c))
        return '(' + ' '.join(cs) + ')'


##  Convert an expression to a string.

def expr_string (e, indent):
    if isinstance(e, Expr):
        if len(e) == 0: return '()'
        s = '('
        indent += 1
        if isinstance(e[0], Expr):
            s += expr_string(e[0], indent)
        else:
            s0 = str(e[0])
            s += s0
            if len(e) > 1:
                if isinstance(e[1], Expr):
                    indent += len(s0) + 1
                    s += ' ' + expr_string(e[1], indent)
                    i = 2
                else:
                    indent += 2
                    i = 1
                    while i < len(e) and not isinstance(e[i], Expr):
                        s += ' ' + str(e[i])
                        i += 1
                for c in e[i:]:
                    s += '\n' + (' ' * indent) + expr_string(c, indent)
            s += ')'
        return s
    else:
        return str(e)


##  Variable.  Just a string, but specialized class so that constant
#   strings and variables can be distinguished.  Also, displays without quotes.

class Variable (str):

    ##  String representation.

    def __repr__ (self):
        return self


##  Used by fresh_variable().

variable_count = 0

##  Allocate a fresh anonymous variable.

def fresh_variable ():
    global variable_count
    variable_count += 1
    return Variable('_%d' % variable_count)

##  Restart anonymous variable count.  Not for general use; only used
#   for consistency of results in examples or tests.

def restart_variables ():
    global variable_count
    variable_count = 0


#--  Parse expr  ---------------------------------------------------------------

##  Whether this looks like a variable.  Returns True if the string consists
#   of exactly one letter (either upper or lower case), optionally preceded
#   by an underscore, and optionally followed by any number of digits.

def is_variable_symbol (s):
    return bool(re.match(r'^_?[A-Za-z][0-9]*$', s))

##  Parse an expression.

def parse_expr (s):
    assert isinstance(s, str)
    toks = tokenize(s)
    t = scan_expr(toks)
    toks.require('eof')
    return t

##  Scan an expression from a list of tokens.

def scan_expr (toks):
    if toks.accept('('):
        children = []
        while not toks.accept(')'):
            c = scan_expr(toks)
            children.append(c)
        return Expr(children)
    elif toks.has_next(')'):
        toks.error("Unexpected ')'")
    elif toks.has_next('eof'):
        toks.error('Premature EOF')
    else:
        s = next(toks)
        if is_variable_symbol(s):
            s = Variable(s)
        return s

##  Load a file containing expressions.

def load_exprs (filename):
    toks = iter_tokens(filename)
    exprs = []
    while toks:
        exprs.append(scan_expr(toks))
    return exprs
