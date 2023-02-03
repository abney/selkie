##  @package seal.cld.glab.lang
#   The syntax of the GLab language.

import traceback
import seal
from io import StringIO
from ..io import Syntax, iter_tokens, pprint


##  Constant representing an unbounded number of arguments.
Unlimited = -1


#--  Version History  ----------------------------------------------------------

# 0.1
#  - first svn deployment on cl.ling
#
# 0.2
#  - actually, several updates were necessary before I actually got it working
#    right, but I'm lumping them together
#  - this is the version I demo'd to the class
#
# 0.3
#  - svn version 261
#  - added 'include'
#
# 0.4
#  - svn version 270
#  - added a limit to the parser so that it doesn't run forever when there are
#    highly ambiguous sentences
#  - modified 'include' so that it keeps track of which notebooks have been
#    included into the env, and doesn't include them multiple times.  if a
#    grammar is included twice, all the duplicate rules cause massive spurious
#    ambiguity.
#
# 0.5
#  - made 'limit' be an init keyword for Parser.  should not affect functionality.
#  - fixed bug that arises if multiple delete requests are received for same text
#  - fixed bug re deprecation warning in HttpException
#
# 0.6 - Fall 2015
#  - added notebook deletion


#--  Exceptions  ---------------------------------------------------------------

##  The parent of SyntaxError and EvalError.

class Error (Exception):
    pass

##  A syntax error.

class SyntaxError (Error):
    pass

##  An evaluation error.

class EvalError (Error):
    pass


#===============================================================================
#
#                               PARSER
#

#--  tokenize  -----------------------------------------------------------------

_syntax = Syntax(special=True,
                 multi=['->', '<-', '=>', ':=', '@<', '@>'],
                 eol=False,
                 comments=False,
                 backslash=False,
                 stringtype='string')

##  Tokenize a string.

def tokenize (s):
    return iter_tokens(StringIO(s), syntax=_syntax)


#--  Grouped Expressions  ------------------------------------------------------

##  An expression.

class Expr (tuple):

    ##  Constructor.

    def __repr__ (self):
        lst = [self.__class__.__name__] + [repr(elt) for elt in self]
        return '<%s>' % ' '.join(lst)

    ##  Pretty-print.

    def __pprint__ (self):
        pprint(self.__class__.__name__, '{')
        with pprint.indent(4):
            for x in self:
                pprint(x)
        pprint('}')

##  A sequence expression.

class SeqExpr (Expr):

    ##  Convert it to a Funcall.

    def digest (self):
        return Funcall('seq', digest_args(self))

    ##  String representation.

    def __repr__ (self):
        return '<' + ', '.join(e.__repr__() for e in self) + '>'

##  A parenthesized expression.

class ParenExpr (Expr):

    ##  Convert it to a Funcall.

    def digest (self):
        if len(self) == 0:
            raise SyntaxError('Empty parentheses')
        elif len(self) == 1:
            return digest(self[0])
        else:
            raise SyntaxError('Run-on expression: %s' % ', '.join(self))

    ##  String representation.

    def __str__ (self):
        return '(' + ', '.join(str(e) for e in self) + ')'

##  A bracketed expression.

class BracketExpr (Expr):

    ##  Convert it to a Funcall.

    def digest (self):
        if len(self) == 0:
            raise SyntaxError('Empty brackets')
        elif len(self) == 1:
            return digest(self[0])
        else:
            raise SyntaxError('Run-on expression: %s' % ', '.join(self))

    ##  String representation.

    def __str__ (self):
        return '[' + ', '.join(str(e) for e in self) + ']'

##  An absolute value or size expression.

class AbsExpr (Expr):

    ##  Convert it to a Funcall.

    def digest (self):
        return Funcall('abs', digest_args(self))

    ##  String representation.

    def __str__ (self):
        return '|%s|' % ' '.join(str(x) for x in self)

##  An expression in braces, representing a set.

class BraceExpr (Expr):

    ##  Convert it to a Funcall.

    def digest (self):
        return Funcall('set', digest_args(self))

    ##  String representation.

    def __str__ (self):
        return '{' + ', '.join(str(e) for e in self) + '}'

##  An expression in slashes, representing a regular expression.

class SlashExpr (Expr):

    ##  Convert it to a Funcall.

    def digest (self):
        return Funcall('regex', digest_args(self))

    ##  String representation.

    def __str__ (self):
        return '/' + ', '.join(str(e) for e in self) + '/'

##  A toplevel expression.

class ToplevelExpr (Expr):

    ##  Convert it to a Funcall.

    def digest (self):
        if len(self) == 0: return None
        elif len(self) == 1: return digest(self[0])
        else:
            raise SyntaxError('Run-on toplevel expression: %s' % ', '.join(str(x) for x in self))

    ##  String representation.

    def __str__ (self):
        return 'Toplevel[' + ' '.join(str(x) for x in self) + ']'


#--  group  --------------------------------------------------------------------

_leftdelims = '[({<|/'
_rightdelims = '])}>|/'
_de_classes = [BracketExpr, ParenExpr, BraceExpr, SeqExpr, AbsExpr, SlashExpr]


##  Group the list of tokens by pairing up delimiters.

def group (toks):
    return ToplevelExpr(_pair_delimiters(iter(toks)))

def _pair_delimiters (toks):
    line = []
    try:
        while True:
            tok = next(toks)
            if tok in _leftdelims:
                line.append(_scan_list(tok, toks))
            else:
                line.append(tok)
    except StopIteration:
        pass
    return line

def _scan_list (leftdelim, toks):
    i = _leftdelims.index(leftdelim)
    rightdelim = _rightdelims[i]
    elts = []
    try:
        while True:
            tok = next(toks)
            if tok == rightdelim:
                return _de_classes[i](elts)
            elif tok in _leftdelims:
                elts.append(_scan_list(tok, toks))
            elif tok == '\n':
                pass
            else:
                elts.append(tok)
    except StopIteration:
        raise SyntaxError('Unmatched delimiter: %s' % leftdelim)


#--  atoms  --------------------------------------------------------------------

##  A symbol.

class Symbol (str):

    ##  Coerce it to a language.

    def __lang__ (self): return Language([String([self])])

    ##  String representation.

    def __repr__ (self): return self

    ##  Pretty-print.

    def __pprint__ (self):
        pprint(self.__class__.__name__, str(self))

##  An unprintable symbol.  Prints out as "sym(CODE)".

class UnprintableSymbol (Symbol):

    ##  String representation.

    def __repr__ (self):
        return 'sym(%s)' % ', '.join(str(ord(c)) for c in self)

##  An operator.

class Op (Symbol):

    ##  String representation.

    def __repr__ (self):
        return '<Op %s>' % self

##  A variable.

class Var (Symbol):

    ##  String representation.

    def __repr__ (self):
        return '<Var %s>' % self


#--  normalize  ----------------------------------------------------------------

def _makeop (s, prec, type=None, fnc=None, arity=None):
    op = Op(s)
    op.precedence = prec
    op.type = type
    op.function = fnc
    if arity is None:
        if type == 'S': arity = 1
        elif type == 'I': arity = 2
    op.arity = arity
    return op

#
#  'S' = suffix operator
#  'I' = infix operator
#
#  Number = precedence.  Higher number, binds more tightly.
#
_operators = {
    ':': _makeop(':', 7, 'I', 'pair'),
    '^': _makeop('^', 6, 'I', 'exp'),
    '*': _makeop('*', 5, 'S', 'star'),
    '?': _makeop('?', 5, 'S', 'question'),
    '.': _makeop('.', 4, 'I', 'concat'),
    'x': _makeop('x', 4, 'I', 'cross'),
    '&': _makeop('&', 4, 'I', 'intersection'),
    '+': _makeop('+', 3, 'I', 'plus'),
    '-': _makeop('-', 3, 'I', 'minus'),
    '\\': _makeop('\\', 3, 'I', 'setdiff'),
    '%': _makeop('%', 3, 'I', 'compose'),
    '=': _makeop('=', 2, 'I', 'equals'),
    '@': _makeop('@', 2, 'I', 'ismember'),
    '@<': _makeop('@<', 2, 'I', 'lt'),
    '@>': _makeop('@>', 2, 'I', 'gt'),
    ':=': _makeop(':=', 1, 'I', 'setvalue'),
    '->': _makeop('->', 1, 'I', 'makerule', arity=-1),
    '<-': _makeop('<-', 1, 'I', 'makelexent', arity=-1),
    '=>': _makeop('=>', 1, 'I', 'expand', arity=-1),
    ',': _makeop(',', 0)
    }

##  Normalize an expression.

def normalize (expr):
    if isinstance(expr, str):
        return normalize_token(expr)
    elif isinstance(expr, tuple):
        elts = [normalize(elt) for elt in expr]
        # _digest_funcalls(elts)
        elts = op_parse(elts)
        elts = [elt for elt in elts if elt != ',']
        return expr.__class__(elts)
    else:
        return expr

##  Normalize a token.

def normalize_token (s):
    if s.type == 'string':
        if s.quotes == "'":
            return SeqExpr(normalize_symbol(x) for x in s)
        elif s.quotes == '"':
            return SeqExpr(normalize_symbol(x) for x in s.split())
        else:
            raise Exception("Unexpected values for 'quotes'")
    elif s.type == 'word':
        if s.startswith('_'):
            if is_identifier(s):
                return Var(s)
            else:
                raise SyntaxError('Variable contains illegal chars: %s' % s)
        else:
            return normalize_symbol(s)
    elif s in _operators:
        return _operators[s]
    else:
        raise SyntaxError('Unrecognized operator: %s' % s)

##  Returns True if x consists solely of alphanumerics and underscore,
#   and does not start with a digit.

def is_identifier (x):
    return (all((c.isalnum() or c == '_') for c in x)
            and not x[0].isdigit())

##  Normalize a symbol.

def normalize_symbol (x):
    if is_identifier(x):
        return Symbol(x)
    elif x.isdigit():
        return int(x)
    else:
        return Funcall('sym', [ord(c) for c in x])


#--  operator-precedence parsing  ----------------------------------------------

##  A function call.

class Funcall (object):

    ##  Constructor.

    def __init__ (self, f, args):

        ##  The function.
        self.function = f

        ##  The arguments.
        self.args = args

    ##  String representation.

    def __str__ (self):
        return '%s(%s)' % (str(self.function), ', '.join([str(arg) for arg in self.args]))

    ##  String representation.

    def __repr__ (self):
        return '<Funcall %s %s>' % (repr(self.function), repr(self.args))

    ##  Pretty-print.

    def __pprint__ (self):
        pprint('Funcall {')
        with pprint.indent(4):
            pprint(self.function)
            for arg in self.args:
                pprint(arg)
        pprint('}')

##  An operator-precedence parser.

class OPParser (object):

    ##  Constructor.

    def __init__ (self):

        ##  The input elements.
        self.elts = None

        ##  The categories of the input elements.
        self.cats = None

        ##  The stack, initially set to the empty list.
        self.stack = None

        ##  The current position in the input, initially set to 0.
        self.i = None

    ##  Get the operator-precedence category of x.

    def getcat (self, x):
        if x == ',': return ','
        elif isinstance(x, Op): return 'O' + x.type
        elif isinstance(x, ParenExpr): return 'PA'
        elif isinstance(x, BracketExpr): return 'P'
        elif isinstance(x, Symbol): return 'AY'
        else: return 'A'

    ##  Whether we are currently looking at the given pattern of categories.

    def lookingat (self, ptn):
        for k in range(len(ptn)):
            if ptn[k] == '#':
                if self.i + k < len(self.elts): return False
            else:
                if self.i + k >= len(self.elts): return False
                if ptn[k] not in self.cats[self.i + k]: return False
        return True

    ##  Shift the next n elements onto the stack.

    def shift (self, n):
        # print('shift', n)
        self.stack.append(self.i)
        self.i += n

    ##  Reduce the top three elements to a Funcall; the second is the function.

    def reduce_AIA (self):
        # print('reduce_AIA')
        op = self.elts[self.i+1]
        expr = Funcall(op.function, [self.elts[self.i], self.elts[self.i+2]])
        if op.arity < 0:
            cats = 'AL'
            expr.precedence = op.precedence
        else:
            cats = 'A'
        self.elts[self.i : self.i+3] = [expr]
        self.cats[self.i : self.i+3] = [cats]
        if self.stack: self.i = self.stack.pop()

    ##  Reduce the top two elements to a Funcall; the first is the function.

    def reduce_LA (self):
        # print('reduce_LA')
        f = self.elts[self.i]
        arg = self.elts[self.i+1]
        f.args.append(arg)
        del self.elts[self.i+1]
        del self.cats[self.i+1]
        if self.stack: self.i = self.stack.pop()

    ##  Reduce the top two elements to a Funcall; the second is the function.

    def reduce_AS (self):
        # print('reduce_AS')
        op = self.elts[self.i+1]
        expr = Funcall(op.function, [self.elts[self.i]])
        self.elts[self.i : self.i+2] = [expr]
        self.cats[self.i : self.i+2] = ['A']
        if self.stack: self.i = self.stack.pop()

    ##  Reduce the top two elements to a Funcall; the second is the function.

    def reduce_YP (self):
        # print('reduce_YP')
        arglist = self.elts[self.i+1]
        if isinstance(arglist, ParenExpr):
            expr = Funcall(self.elts[self.i], arglist)
        elif isinstance(arglist, BracketExpr):
            expr = Funcall(Symbol('makecat'), (self.elts[self.i],) + arglist)
        self.elts[self.i : self.i+2] = [expr]
        self.cats[self.i : self.i+2] = ['A']
        if self.stack: self.i = self.stack.pop()

    ##  Call the parser.

    def __call__ (self, elts):
        # print('parse', elts)
        self.elts = elts
        self.cats = [self.getcat(elt) for elt in elts]
        self.i = 0
        self.stack = []

        while self.i < len(self.elts):
            # print('i=', self.i, 'cats=', self.cats)
            if self.lookingat('AIAO'):
                if elts[self.i+3].precedence > elts[self.i+1].precedence:
                    self.shift(2)
                else:
                    self.reduce_AIA()
            elif self.lookingat('LAO'):
                if elts[self.i+2].precedence > elts[self.i].precedence:
                    self.shift(1)
                else:
                    self.reduce_LA()
            elif self.lookingat('AIAP'):
                self.shift(2)
            elif self.lookingat('LAP'):
                self.shift(1)
            elif self.lookingat('AIA'):
                self.reduce_AIA()
            elif self.lookingat('LA'):
                self.reduce_LA()
            elif self.lookingat('YP'):
                self.reduce_YP()
            elif self.lookingat('AS'):
                self.reduce_AS()
            else:
                # print('punt')
                self.stack = []
                self.i += 1

        return self.elts

##  An instance of OPParser.
op_parse = OPParser()


#--  digest  -------------------------------------------------------------------

##  Convert an expression to a Funcall.

def digest (x):
    if isinstance(x, Expr):
        return x.digest()
    elif isinstance(x, Funcall):
        return Funcall(x.function, digest_args(x.args))
    else:
        return x

##  Digest the arguments.

def digest_args (args):
    return [digest(x) for x in args]

##  Convert x to a string printed in Lisp style.

def lisp_string (x):
    with StringIO() as f:
        _write_lisp_string(x, f)
        return f.getvalue()

def _write_lisp_string (x, f):
    if isinstance(x, Funcall):
        f.write('(')
        _write_lisp_string(x.function, f)
        for arg in x.args:
            f.write(' ')
            _write_lisp_string(arg, f)
        f.write(')')
    else:
        f.write(str(x))


#--  parse  --------------------------------------------------------------------

##  Parse the given string.  Calls tokenize() then group() then normalize()
#   then digest().

def parse (s):
    return digest(normalize(group(tokenize(s))))

##  Parse the named file.  Returns an iterator over triples (EXPR, EXCEP, LINE).
#    - Empty line or comment: (None, None, LINE).
#    - Parse error: (None, EXCEP, LINE).
#    - Successful parse: (EXPR, None, LINE).

def parse_file (file, env=None):
    for line in file:
        line = line.rstrip('\r\n')
        if not line or line.startswith('#'):
            yield (None, None, line)
        else:
            try:
                yield (parse(line), None, line)
            except Exception as e:
                if env and 'stack' in env['*trace*']:
                    traceback.print_exc(file=env['*output*'])
                yield (None, e, line)
