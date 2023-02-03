
import sys, os
from ..io import null, redirect
from ..fsa import (Fsa as _Fsa, NFsa, SimpleFsa)
from ..fst import (Fst, compose as _compose)

from .lang import (Unlimited, EvalError, Var, Symbol, UnprintableSymbol,
                   Funcall, is_identifier)

from ..grammar import Grammar
from ..parser import Parser, print_fragments, print_nodes, TooManyParses
from ..features import Category, atomset, intern_variable


#--  Environment  --------------------------------------------------------------

##  A GLab function.

class Function (object):

    ##  Constructor.

    def __init__ (self, imp, min_nargs, max_nargs=None,
                  types=None, eval=None, envarg=False):
        if not hasattr(imp, '__call__'):
            raise Exception('Not a function: %s' % imp)
        if max_nargs is None: max_nargs = min_nargs

        ##  The name of the function.
        self.name = '(anonymous)'

        ##  The implementation, a python function.
        self.implementation = imp

        ##  Minimum number of args.
        self.min_nargs = min_nargs

        ##  Maximum number of args.
        self.max_nargs = max_nargs

        ##  Types of arguments.
        self.types = types

        ##  The evaluation pattern (which args should be evaluated).
        self.eval = eval

        ##  Whether to include the environment as a final argument.
        self.envarg = envarg

    ##  Returns self.

    def __glab_function__ (self): return self

    ##  String representation.

    def __repr__ (self):
        return '<Function %s>' % self.implementation.__name__


##  Environment, mapping symbols to values.

class Environment (object):

    ##  Constructor.

    def __init__ (self,
                  interp,
                  output=None,
                  show_syntax=False,
                  show_traceback=False,
                  notebook_dir='.'):

        ##  The interpreter.
        self.interp = interp

        ##  Setters.  Allows a complex expression on the lhs of set.
        self.setters = {
            'start': Function(set_start, 1, envarg=True)
            }

        ##  Symbols whose value cannot be modified.
        self.constants = set(['_0_', '_e_', '_else_'])

        ##  The symbol table.
        self.symtab = {
            '*notebook-dir*': notebook_dir,
            '*output*': output or sys.stdout,
            '*trace*': set(),

            '_0_': __emptyset__,
            '_e_': __epsilon__,
            '_else_': True,
            '_fsa_': None,
            '_corpus_': None,

            'apply': Function(apply_fsa, 0, 1, envarg=True),
            'bad': Function(bad_sent, 1, 2, envarg=True),
            'Bottom': LatticeElement(None),
            'abs': Function(lambda x: x.size(), 1),
            'accepts': Function(lambda x,y: x.accepts(y), 2, types=[Fsa, Seq]),
            'check': Function(check_io, 1, envarg=True),
            'compose': Function(compose, 2, Unlimited, envarg=True),
            'computation': Function(lambda x,y: x.computation(y), 2, types=[Fsa, Seq]),
            'concat': Function(concat, 1, Unlimited),
            'cross': Function(cross, 1, Unlimited),
            'E': Function(add_edge, 3, 4, envarg=True),
            'equals': Function(lambda x,y: x==y, 2),
            'ex': Function(add_example, 1, envarg=True),
            'exp': Function(exp, 2),
            'expand': Function(expand, 1, Unlimited, envarg=True),
            'F': Function(set_final, 1, envarg=True),
            'first': Function(first, 1),
            'fsa': Function(makefsa, 0, Unlimited),
            'good': Function(good_sent, 1, 2, envarg=True),
            'gt': Function(greater_than, 2),
            'include': Function(include, 1, envarg=True),
            'incr': Function(incr, 2),
            'intersection': Function(intersection, 2),
            'io': Function(io_example, 2, envarg=True),
            'islang': Function(islang, 1),
            'ismember': Function(lambda x,y: x in y, 2),
            'isstring': Function(isstring, 1),
            'L': Function(as_language, 1),
            'lang': Function(list_language, 1, 2, envarg=True),
            'lt': Function(less_than, 2),
            'makecat': Function(makecat, 1, Unlimited),
            'makelexent': Function(makelexent, 2, eval=[False], envarg=True),
            'makerule': Function(makerule, 1, Unlimited, eval=[False], envarg=True),
            'minus': Function(minus, 2),
            'new': Function(new, 1, eval=[False], envarg=True),
            'new_fsa': Function(new_fsa, 0, envarg=True),
            'new_grammar': Function(new_grammar, 0, envarg=True),
            'new_union': Function(new_union, 0, envarg=True),
            'pair': Function(Pair, 2),
            'parse': Function(parse_sent, 1, envarg=True),
            'plus': Function(plus, 2),
            'question': None,
            'quote': Function(quote, 1, eval=[False]),
            'rel': Function(list_relation, 1, 2, envarg=True),
            'regex': Function(regex, 1, eval=[False], envarg=True),
            'results': Function(regression, 0, envarg=True),
            'seq': Function(makeseq, 0, Unlimited),
            'set': Function(makeset, 0, Unlimited),
            'setdiff': None,
            'setvalue': Function(setvalue, 2, eval=[False, False], envarg=True),
            'show': Function(show, 1, envarg=True),
            'size': Function(lambda x: x.size(), 1),
            'star': None,
            'start': Function(get_start, 0, envarg=True),
            'sym': Function(sym, 1, Unlimited),
            'Top': LatticeElement('*'),
            'trace': Function(trace, 1, Unlimited, envarg=True),
            'type': Function(typename, 1),
            'untrace': Function(untrace, 1, Unlimited, envarg=True)
            }

        for (k,v) in self.symtab.items():
            if isinstance(v, Function):
                v.name = k

    ##  Get the value of a symbol, or None if undefined.
    def get (self, key): return self.symtab.get(key)

    ##  Get the value of a symbol, error if undefined.
    def __getitem__ (self, key): return self.symtab.__getitem__(key)

    ##  Set the value of a symbol.
    def __setitem__ (self, key, val): self.symtab.__setitem__(key, val)

    ##  Whether the symbol has a value.
    def __contains__ (self, key): return self.symtab.__contains__(key)
        

# [setvalue] [Op :=] setvalue

##  Set the value of a symbol.  The implementation of the ':=' operator and
#   the 'setvalue' function.

def setvalue (sym, value, env=None):
    if isinstance(sym, Var):
        if sym in env.constants:
            raise EvalError('%s is a constant' % sym)
        env[sym] = env.interp.eval(value)
    elif isinstance(sym, Funcall):
        if isinstance(sym.function, Symbol) and sym.function in env.setters:
            f = env.setters[sym.function]
            args = list(sym.args) + [value]
            if f.envarg: f.implementation(*args, env=env)
            else: f.implementation(*args)
        else:
            raise EvalError('Not a settable function: %s' % repr(sym.function))
    else:
        raise EvalError('Expected a variable or function call: %s' % repr(sym))


#===============================================================================
#
#                          BUILTIN OBJECTS
#

##  A sequence.

class Seq (tuple):

    ##  Its length.

    def size (self):
        return len(self)

    ##  Concatenate it with another.

    def concat (self, other):
        if isinstance(other, Seq):
            return Seq(self + other)
        else:
            raise EvalError('Cannot concatenate sequence with non-sequence: %s' % other)

    ##  Concatenate with itself some number of times.

    def __pow__ (self, expt):
        if not isinstance(expt, int):
            raise EvalError('Not a valid exponent: %s' % expt)
        elif expt < 0:
            raise EvalError('Cannot raise a string to a negative power')
        elif expt == 0:
            return __epsilon__
        else:
            x = self
            expt -= 1
            while expt > 0:
                x = x.concat(self)
                expt -= 1
            return x

    ##  String representation.

    def __repr__ (self):
        return '<%s>' % ', '.join(repr(e) for e in self)


##  A string, which is a sequence of symbols.
#   This probably makes assumptions that will be violated in future Python releases.
#   It appears that tuples are initialized independently of the __init__ method.
#   So we make no effort to call tuple.__init__.

class String (Seq):

    ##  Constructor.

    def __init__ (*args):
        self = args[0]
        for x in self:
            if not isinstance(x, Symbol):
                raise EvalError('String containing non-symbol: %s %s' % (type(x), x))

    ##  Coerce to a language.

    def __lang__ (self): return Language([self])

    ##  Concatenate with another string.

    def concat (self, other):
        if isinstance(other, String):
            return String(self + other)
        elif isinstance(other, Seq):
            return Seq(self + other)
        else:
            raise EvalError('Cannot concatenate a sequence with a non-sequence: %s' % other)


##  A set.

class Set (object):

    ##  Constructor.

    def __init__ (self, members=None):
        if isinstance(members, frozenset):

            ##  A python set.
            self.contents = members

        elif members:
            self.contents = frozenset(members)
        else:
            self.contents = frozenset()

    ##  The number of members.

    def __len__ (self):
        return len(self.contents)

    ##  The number of members.

    def size (self):
        return len(self.contents)

    ##  Whether the given item is a member of the set.

    def __contains__ (self, elt):
        return self.contents.__contains__(elt)

    ##  Iterate over the members.

    def __iter__ (self):
        return iter(self.contents)

    ##  Two sets are equal if they have the same members.

    def __eq__ (self, other):
        if isinstance(other, Set):
            return self.contents.__eq__(other.contents)
        else:
            return False

    ##  Greater than means "is a superset".

    def __gt__ (self, other):
        if isinstance(other, Set):
            return self.contents.issuperset(other.contents)
        else:
            raise EvalError('Not a set: %s' % other)

    ##  Less than means "is a subset".

    def __lt__ (self, other):
        if isinstance(other, Set):
            return self.contents.issubset(other.contents)
        else:
            raise EvalError('Not a set: %s' % other)

    ##  Hash.  Note that all operations that affect contents are non-destructive:
    #   they make a copy.

    def __hash__ (self):
        return self.contents.__hash__()

    ##  Create a new set that is the union of this and the given set.

    def __add__ (self, other):
        return Set(self.contents + other.contents)

    ##  Create a new set that is the intersection of this and the given set.

    def intersection (self, other):
        return Set(self.contents.intersection(other.contents))

    ##  Create a new set that is the union of this and the given set.

    def union (self, other):
        return Set(self.contents.union(other.contents))

    ##  Create a new set that is the set difference of this and the given set.

    def __sub__ (self, other):
        return Set(self.contents.difference(other.contents))

    ##  String representation.

    def __repr__ (self):
        return '{%s}' % ', '.join(sorted(repr(e) for e in self))


##  A vocabulary (set of symbols).

class Vocabulary (Set):

    ##  Constructor.

    def __init__ (self, members=None):
        Set.__init__(self, members)
        if not all(isinstance(x, Symbol) for x in self):
            raise EvalError('Not all members are Symbols')

    ##  Coerce to a language.

    def __lang__ (self): return Language(String([s]) for s in self.contents)

    ##  Take the union with another vocabulary or set.  If the other is a Vocabulary,
    #   the return is a Vocabulary, and otherwise the return is a Set.

    def __add__ (self, other):
        if isinstance(other, Vocabulary): c = Vocabulary
        else: c = Set
        return c(self.contents + other.contents)

    ##  Intersection with another set.  The return is a Vocabulary.

    def intersection (self, other):
        s = self.contents.intersection(other.contents)
        if not s:
            return __emptyset__
        else:
            return Vocabulary(s)

    ##  Take the union with another set.  If the other is a Vocabulary, the return
    #   is a Vocabulary, and otherwise the return is a Set.

    def union (self, other):
        if isinstance(other, Vocabulary): c = Vocabulary
        else: c = Set
        return c(self.contents.union(other.contents))

    ##  Coerce to a Language and concatenate with the input.

    def concat (self, other):
        if isinstance(other, Language):
            return self.__lang__().concat(other)
        else:
            if isinstance(other, Vocabulary): other = [String([s]) for s in other]
            elif isinstance(other, String): other = [other]
            elif isinstance(other, Symbol): other = [String([other])]
            else: raise EvalError('Cannot be concatenated: %s' % other)
            return Language(String([x]).concat(y) for x in self for y in other)

    ##  Take the set difference with the input.  Returns a Vocabulary.

    def __sub__ (self, other):
        s = self.contents.difference(other.contents)
        if not s:
            return __emptyset__
        else:
            return Vocabulary(s)


##  A language.

class Language (Set):

    ##  Returns self.

    def __lang__ (self): return self

    ##  Take the union with another language.  If the input is a Language, the
    #   return value is a Language, otherwise the return value is a Set.

    def __add__ (self, other):
        if isinstance(other, Language): c = Language
        else: c = Set
        return c(self.contents + other.contents)

    ##  Take the intersection with another language.  The return value is a Language.

    def intersection (self, other):
        s = self.contents.intersection(other.contents)
        if not s:
            return __emptyset__
        elif isinstance(other, Language) or all(isinstance(x, String) for x in s):
            return Language(s)
        else:
            return Set(s)

    ##  Take the union with another language.  If the input is a Language, the
    #   return value is a Language, otherwise the return value is a Set.

    def union (self, other):
        if isinstance(other, Language): c = Language
        else: c = Set
        return c(self.contents.union(other.contents))

    ##  Concatenate with another language.  The input must be one of: a Language,
    #   a Vocabulary, a String, or a Symbol.  It is first coerced to be a
    #   language, then concatenated.  The return value is a Language.

    def concat (self, other):
        if isinstance(other, Language): pass
        elif isinstance(other, Vocabulary): other = [String([s]) for s in other]
        elif isinstance(other, String): other = [other]
        elif isinstance(other, Symbol): other = [String([other])]
        else: raise Exception('Cannot be concatenated with language: %s' % other)
        return Language(x.concat(y) for x in self for y in other)

    ##  Take the set difference with another set.  The return value is a Language.

    def __sub__ (self, other):
        s = self.contents.difference(other.contents)
        if not s:
            return __emptyset__
        else:
            return Language(s)

    ##  Convert this language to an FSA.  If it is the language of an FSA, the
    #   underlying FSA is returned.  Otherwise an FSA is created that generates
    #   exactly this set of strings.

    def fsa (self):
        if hasattr(self, '_fsa'): return self._fsa
        else:
            self._fsa = LanguageToFsa(self).fsa
            return self._fsa


##  The language of an FSA.

class FsaLanguage (object):

    ##  Constructor.

    def __init__ (self, fsa):
        if isinstance(fsa, Fsa):
            
            ##  The underlying FSA.
            self.fsa = fsa.fsa

        elif isinstance(fsa, (Fst, _Fsa)):
            self.fsa = fsa
        else:
            raise Exception('Not an fsa')

    ##  Iterate over language of the FSA.  If the FSA is a transducer, this
    #   iterates over the input language.

    def __iter__ (self):
        fsa = self.fsa
        if isinstance(fsa, Fst):
            visited = set()
            for (i,o) in fsa:
                if i not in visited:
                    visited.add(i)
                    yield String(i)
        else:
            for s in fsa:
                yield String(s)

    ##  Whether the given string belongs to the language.

    def __contains__ (self, s):
        return self.fsa.accepts(s)

    ##  String representation.

    def __repr__ (self):
        return '(the language of an FSA)'


##  Converts a language to an FSA.

class LanguageToFsa (object):

    ##  Constructor.

    def __init__ (self, lang, type=NFsa):

        ##  The FSA.
        self.fsa = type()

        ##  The start state.
        self.start = self.fsa.start = self.state()

        ##  The end state.
        self.end = self.state()

        self.end.is_final = True
        for s in sorted(lang):
            self.add_sentence(s)

    ##  Allocate a new state.

    def state (self):
        n = len(self.fsa.states)
        return self.fsa.state(n)

    ##  Add a string to the language of the FSA.

    def add_sentence (self, sent):
        q = self.start
        n = len(sent)
        if n == 0:
            q.is_final = True
        else:
            for i in range(n-1):
                r = self.state()
                q.edge(r, sent[i])
                q = r
            q.edge(self.end, sent[n-1])


##  The empty set.

class EmptySet (Vocabulary, Language): pass

##  The empty string.  Available in GLab as '_e_'.
__epsilon__ = String()

##  The empty set.  Available in GLab as '_0_'.
__emptyset__ = EmptySet()


##  A node in a lattice.

class LatticeElement (object):

    ##  Constructor.

    def __init__ (self, x):

        ##  The node represented as a set of atoms.
        self.atomset = x

    ##  String representation.

    def __repr__ (self):
        x = self.atomset
        if x is None: return 'Bottom'
        elif x == '*': return 'Top'
        elif isinstance(x, str): return x
        else: return '+'.join(x)


#===============================================================================
#
#                           FSAS, REGEXES
#

##  A corpus.

class Corpus (object):

    ##  Constructor.

    def __init__ (self, elts=None):
        if elts is None:

            ##  The strings belonging to the corpus.
            self.examples = []

        else:
            self.examples = list(elts)
            for ex in self.examples:
                if not isinstance(ex, String):
                    raise EvalError('Corpus elements must be string: %s' % ex)

    ##  Add another string to the corpus.

    def append (self, example):
        if not isinstance(example, String):
            raise EvalError('Corpus elements must be strings: %s' % example)
        self.examples.append(example)

    ##  Iterate over the strings in the corpus.

    def __iter__ (self): return self.examples.__iter__()

    ##  Fetch the i-th string.

    def __getitem__ (self, i): return self.examples.__getitem__(i)

    ##  The number of strings.

    def __len__ (self): return self.examples.__len__()

    ##  String representation.

    def __repr__ (self):
        return '\n'.join('[%d] %s' % (i,ex) for (i,ex) in enumerate(self.examples))


##  Convert to an FST.  The input may be an Fst, Fsa, or RegLang.

def as_fst (x):
    if isinstance(x, RegLang):
        fst = x.fsa
    elif isinstance(x, Fsa):
        fst = x.fsa
    elif isinstance(x, Fst):
        fst = x
    else:
        raise EvalError('Cannot be converted to an FST: %s' % x)
    if not isinstance(fst, Fst):
        raise EvalError('Not an FST: %s' % x)
    return fst

##  Convert to a regular relation, represented as an iteration over Pairs
#   of strings.  The input may be either an FSA or an FST.  The relation
#   of an FSA is defined to be the set of pairs (s,s) for strings s belonging
#   to the language of the FSA.

def fsa_rel (fsa):
    if isinstance(fsa, Fst):
        for (i,o) in fsa:
            yield Pair(String(i), String(o))
    else:
        assert isinstance(fsa, _Fsa)
        for s in fsa:
            s = String(s)
            yield Pair(s,s)


##  A finite-state automaton.

class Fsa (object):

    ##  Constructor.

    def __init__ (self, fsa=None):
        if fsa is None: fsa = NFsa()

        ##  The underlying object of class _Fsa.
        self.fsa = fsa

    ##  Convert to an FST.  This is destructive!

    def convert_to_fst (self):
        if not isinstance(self.fsa, Fst):
            self.fsa = Fst(self.fsa)

    ##  Add an edge.

    def add_edge (self, source, label, dest):
        if isinstance(label, Pair):
            self.convert_to_fst()
            self.fsa.edge(source, dest, label.x, label.y)
        elif isinstance(self.fsa, Fst):
            self.fsa.edge(source, dest, label, label)
        else:
            self.fsa.edge(source, dest, label)

    ##  Make q a final state.

    def set_final (self, q):
        self.fsa.final_state(self.fsa.state(q))

    ##  The GLab function is the __call__() method.

    def __glab_function__ (self):
        return Function(self.__call__, 1, 2, envarg=True)

    ##  Calling it as an acceptor.  The return value is True or False.

    def __call__ (self, sent, trace=False, env=None):
        if 'fsa' in env['*trace*']:
            trace = True
        if trace:
            with redirect(env['*output*']):
                return self._call1(sent, trace, env)
        else:
            return self._call1(sent, trace, env)

    def _call1 (self, sent, trace, env):
        if isinstance(self.fsa, Fst):
            out = []
            T = Set
            if isinstance(sent, (Set, Corpus)):
                T = sent.__class__
                for s in sent:
                    out.extend(self.fsa(s, trace=trace, cutoff=1000))
            else:
                out.extend(self.fsa(sent, trace=trace, cutoff=1000))
            return T(String(s) for s in out)
        else:
            return self.fsa.accepts(sent, trace=trace)

    ##  Returns the computation, as a string.

    def computation (self, sent):
        output = Printout()
        self.trace(sent, output)
        return output

    ##  Print out the states and edges.

    def show (self, output):
        # self.fsa.dump(output)
        self._show1(output)

    def _show1 (self, output):
        if isinstance(self.fsa, Fst): s = 'FST:'
        else: s = 'FSA:'
        print(s, file=output)
        start = self.fsa.start
        for e in self.fsa.edges():

            # '->' before start state
            if first and e.source == start: s = '->'
            else: s = '  '

            # '(F)' after final state
            if e.dest.is_final: f = ' (F)'
            else: f = ''

            # label(s)
            if isinstance(self.fsa, Fst):
                if e.inlabel is None: ilab = '_e_'
                else: ilab = e.inlabel
                if e.outlabel is None: olab = '_e_'
                else: olab = e.outlabel
                lab = '%s %s' % (ilab, olab)
            else:
                if e.label is None: lab = '_e_'
                else: lab = e.label

            # assembly
            print(' %s %s %s %s%s' % (s, e.source, lab, e.dest, f), file=output)

    ##  Convert to a language.  Non-destructive.

    def __lang__ (self):
        return FsaLanguage(self.fsa)

    ##  Convert to a regular relation.  Non-destructive.

    def relation (self):
        return fsa_rel(self.fsa)

    ##  String representation.

    def __repr__ (self):
        if isinstance(self.fsa, Fst): s = 'FST'
        else: s = 'FSA'
        return '(An %s containing %d states)' % (s, len(self.fsa.states))


_re_info = {'pair': (':', 5),
            'star': ('*', 4),
            'question': ('?', 4),
            'concat': ('.', 3),
            'plus': ('+', 2)}

def _regex_str (re, outerop=None, outerprec=0):
    if isinstance(re, Funcall):
        if re.function == 'seq':
            return _quoted_seq(re.args)
        else:
            (op, prec) = _re_info[re.function]
            lp = '('
            rp = ')'
            first = re.args[0]
            rest = re.args[1:]
            if prec > outerprec or (prec == outerprec and op == outerop):
                lp = rp = ''
            return lp \
                + _regex_str(first, op, prec) \
                + op \
                + op.join(_regex_str(e, op, prec) for e in rest) \
                + rp
    elif re is None:
        return '_0_'
    else:
        return repr(re)

def _quoted_seq (syms):
    if any(len(s) > 1 for s in syms):
        return '"' + ' '.join(syms) + '"'
    else:
        return "'" + ''.join(syms) + "'"

def _lisp_contains (lst, item):
    while lst:
        if lst[0] == item: return True
        lst = lst[1]
    return False

def _expand_variables (regex, env, visited=()):
    if isinstance(regex, Var):
        var = regex
        if _lisp_contains(visited, var):
            raise EvalError('Circular definition detected: %s' % var)
        if var in ['_e_', '_else_', '_0_']:
            return var
        v = env[var]
        if isinstance(v, RegLang): regex = v.regex
        else: raise EvalError('Value of %s is not a regular expression' % var)
        return _expand_variables(regex, env, (var, visited))
    elif isinstance(regex, Symbol):
        return regex
    elif regex is None:
        return None
    elif isinstance(regex, Funcall):
        return Funcall(regex.function, [_expand_variables(x, env, visited)
                                        for x in regex.args])
    else:
        raise Exception('Bad component in regex: %s' % repr(regex))
        

##  The language of a regular expression.

class RegLang (object):

    ##  Constructor.

    def __init__ (self, regex=None, env=None):

        ##  The regular expression.
        self.regex = None

        ##  The result of converting the regular expression to an FSA.
        self.fsa = None  # a bare NFsa or Fst

        if regex: self._set_regex(regex, env)

    def _set_regex (self, regex, env=None):
        self.regex = regex
        self.fsa = convert_regex(regex, env)

    ##  Whether the given string is a member of the language.

    def __contains__ (self, s):
        if not isinstance(s, String):
            raise EvalError('Not a string: %s' % s)
        if self.fsa:
            return self.fsa.accepts(s)
        else:
            return False

    ##  Produces the language.

    def __lang__ (self):
        if self.fsa:
            return FsaLanguage(self.fsa)
        else:
            return __emptyset__

    ##  Produces a regular relation.

    def relation (self):
        if self.fsa:
            return fsa_rel(self.fsa)
        else:
            return __emptyset__

    ##  The __call__() method represented as a GLab function.

    def __glab_function__ (self):
        if isinstance(self.fsa, Fst):
            return Function(self.__call__, 1)

    ##  Calls the FSA as a transducer.  Not sure what I was thinking here;
    #   it needs to be looked at.

    def __call__ (self, x):
        if self.fsa:
            return Language(Seq(s) for s in self.fsa(x))
        else:
            return __emptyset__

    ##  String representation.

    def __repr__ (self):
        return '/' + _regex_str(self.regex) + '/'


def _contains_pair (regex, env):
    if regex in ['_e_', '_0_', '_else_']:
        return False
    elif isinstance(regex, Var):
        if regex not in env:
            raise EvalError('Undefined variable: %s' % regex)
        v = env[regex]
        if isinstance(v, (RegLang, Fsa)):
            return isinstance(v.fsa, Fst)
        else:
            raise EvalError('Variable does not have regex or fsa as value: %s' % regex)
    elif isinstance(regex, Symbol):
        return False
    elif regex.function == 'pair':
        return True
    elif isinstance(regex, Funcall):
        return any(_contains_pair(a, env) for a in regex.args)
    else:
        raise EvalError('Not a valid regex: %s' % repr(regex))


##  Convert a regular expression to an FSA or FST.
#   The output is an FST if there are any colon expressions, otherwise it is an FSA.

def convert_regex (regex, env):
    return RegexConverter(regex, env).fsa


##  Object that converts regular expressions to FSAs.

class RegexConverter (object):

    ##  Constructor.

    def __init__ (self, regex, env):

        ##  The environment.
        self.env = env

        if _contains_pair(regex, env):

            ##  Which type of automaton to produce: Fst or NFsa.
            self.type = Fst

        else:
            self.type = NFsa

        ##  The automaton.
        self.fsa = self.type()

        (s, e) = self.convert(regex, 'both')
        self.fsa.start = s
        e.is_final = True
        # print('Convert', _regex_str(regex))
        # self.fsa.dump()
        # self.fsa = self.fsa.eliminate_epsilons()

    ##  Allocate a state.

    def state (self):
        n = len(self.fsa.states)
        return self.fsa.state(n)

    ##  Allocate a state pair.

    def state_pair (self):
        return (self.state(), self.state())

    ##  Convert the given regular expression.  Side indicates what should be
    #   done with a transducer: 'input' means ignore the output side, 'output'
    #   means ignore the input side, and 'both' means produce a transducer.

    def convert (self, regex, side):
    
        if regex == '_e_':
            (s,e) = self.state_pair()
            s.edge(e)

        elif regex == '_0_':
            return self.state_pair()

        elif regex == '_else_':
            if self.type != Fst:
                raise EvalError('Can only use _else_ in an FST')
            return self.convert_atom(True, side)

        elif isinstance(regex, Var):
            v = self.env[regex]
            if isinstance(v, RegLang):
                return self.convert(v.regex, side)
            elif isinstance(v, Fsa):
                return self.copy(v.fsa, side)
            elif isinstance(v, Language):
                return self.copy(v.fsa(), side)
            else:
                raise Exception('Bad value, should have been caught earlier')

        elif isinstance(regex, Symbol):
            return self.convert_atom(regex, side)

        elif isinstance(regex, Funcall):
            if regex.function == 'seq':
                return self.convert_string(regex.args, side)
            elif regex.function == 'pair':
                return self.convert_pair(regex.args[0], regex.args[1], side)
            elif regex.function == 'plus':
                return self.convert_union(regex.args[0], regex.args[1], side)
            elif regex.function == 'concat':
                return self.convert_concat(regex.args[0], regex.args[1], side)
            elif regex.function == 'star':
                return self.convert_kleene(regex.args[0], side)
            elif regex.function == 'question':
                return self.convert_optional(regex.args[0], side)
            elif regex.function == 'compose':
                return self.convert_compose(regex.args[0], regex.args[1], side)
            else:
                raise Exception('Invalid function in regex: %s', regex.function)

        else:
            raise Exception('Not a regex: %s' % repr(regex))

    ##  Convert an atom.

    def convert_atom (self, label, side, s=None):
        if s: e = self.state()
        else: (s, e) = self.state_pair()
        if self.type == NFsa:
            s.edge(e, label)
        elif side == 'both':
            s.edge(e, label, label)
        elif side == 'input':
            s.edge(e, label, None)
        elif side == 'output':
            s.edge(e, None, label)
        else:
            raise Exception('Bad value for side: %s' % side)
        return (s,e)
    
    ##  Convert a string.

    def convert_string (self, symbols, side):
        q = s = self.state()
        for sym in symbols:
            if not isinstance(sym, Symbol):
                raise EvalError('Non-string sequence not allowed in regex')
            (_,q) = self.convert_atom(sym, side, s=q)
        return (s,q)

    def _label (self, x):
        if x == '_e_': return (True, None)
        elif x == '_0_': return (False, None)
        elif x == '_else_': return (True, True)
        elif isinstance(x, Var): return (False, None)
        elif isinstance(x, Symbol): return (True, x)
        else: return (False, None)

    ##  Convert a pair of regular expressions.

    def convert_pair (self, regex1, regex2, side):
        if side != 'both':
            raise EvalError('Not permitted: colon embedded in argument of colon')
        (islab1, label1) = self._label(regex1)
        (islab2, label2) = self._label(regex2)
        if islab1 and islab2:
            (s, e) = self.state_pair()
            s.edge(e, label1, label2)
            return (s, e)
        else:
            (s, e1) = self.convert(regex1, 'input')
            (s1, e) = self.convert(regex2, 'output')
            e1.edge(s1)
            return (s,e)

    ##  Produce a subautomaton representing the union of two regular expressions.

    def convert_union (self, regex1, regex2, side):
        (s, e) = self.state_pair()
        (s1, e1) = self.convert(regex1, side)
        (s2, e2) = self.convert(regex2, side)
        s.edge(s1)
        s.edge(s2)
        e1.edge(e)
        e2.edge(e)
        return (s,e)
    
    ##  Produce a subautomaton representing the intersection of two regular
    #   expressions.

    def convert_concat (self, regex1, regex2, side):
        (s, e1) = self.convert(regex1, side)
        (s1, e) = self.convert(regex2, side)
        e1.edge(s1)
        return (s,e)
    
    ##  Produce a subautomaton representing the Kleene closure of a regular
    #   expression.

    def convert_kleene (self, regex, side):
        (s, e) = self.state_pair()
        (s1, e1) = self.convert(regex, side)
        s.edge(s1)
        s.edge(e)
        e1.edge(s1)
        e1.edge(e)
        return (s,e)
    
    ##  Produce a subautomaton representing an optional regular expression.

    def convert_optional (self, regex, side):
        (s, e) = self.state_pair()
        (s1, e1) = self.convert(regex, side)
        s.edge(s1)
        s.edge(e)
        e1.edge(e)
        return (s,e)

    ##  Produce a subautomaton representing the composition of two regular
    #   expressions.

    def convert_compose (self, regex1, regex2, side):
        if side != 'both':
            raise EvalError('Cannot embed composition in one side of transduction')
        fst1 = as_fst(convert_regex(regex1, self.env))
        fst2 = as_fst(convert_regex(regex2, self.env))
        return self.copy(_compose(fst1, fst2), side)

    ##  Copy (one side of) an automaton.

    def copy (self, fsa, side):
        start = None
        end = self.state()
        newstates = [self.state() for i in range(len(fsa.states))]
        for i in range(len(fsa.states)):
            q = fsa.states[i]
            newq = newstates[i]
            if q == fsa.start: start = newq
            if q.is_final: newq.edge(end)
            for e in q.edges:
                newdest = newstates[e.dest.index]
                if side == 'input':
                    newq.edge(newdest, inlabel=e.single_label())
                elif side == 'output':
                    newq.edge(newdest, outlabel=e.single_label())
                else:
                    newq.edge(newdest, label_from=e)
        return (start, end)


#===============================================================================
#
#                         BUILTIN FUNCTIONS
#

# [->] makerule  -----------------------

##  The implementation of the '->' operator and the 'makerule' function.

def makerule (*args, env=None):
    if len(args) < 1:
        raise EvalError('Rule requires lefthand side')
    g = need_grammar(env)
    symtab = {}
    lhs = intern_category(args[0], symtab=symtab)
    rhs = [intern_category(arg, symtab=symtab) for arg in args[1:]]
    try:
        g.define(lhs, rhs, symtab=symtab)
    except Exception as e:
        raise EvalError(str(e))

# [<-] makelexent  ---------------------

##  The implementation of the '<-' operator and the 'makelexent' function.

def makelexent (w, pos, env=None):
    g = need_grammar(env)
    lex = g.lexicon
    try:
        lex.define(w, intern_category(pos))
    except Exception as e:
        raise EvalError(e)

# [=>] expand  -------------------------

##  The implementation of the '=>' operator and 'expand' function.

def expand (*args, env=None):
    lhs = args[0]
    rhs = args[1:-1]
    tree = need_tree(env)
    tree.expand(lhs, rhs)
    print(tree.todo_string())

# [apply]  -----------------------------

##  The implementation of 'apply'.

def apply_fsa (input=None, env=None):
    if env is None:
        raise Exception('env is required')
    if input is None:
        input = need_corpus(env)
    trace = 'fsa' in env['*trace*']
    fsa = env['_fsa_']
    return fsa(input, trace=trace, env=env)

# [bad] bad_sent  ----------------------

##  The implementation of 'bad'.

def bad_sent (sent, out=None, env=None):
    sents = need_sents(env)
    if out:
        sents.append(('bad', sent, out))
    else:
        sents.append(('bad', sent))

# [check] ------------------------------

##  The implementation of 'check'.

def check_io (fsa, env=None):
    if isinstance(fsa, RegLang): fsa = fsa.fsa
    elif isinstance(fsa, Fsa): fsa = fsa.fsa
    elif isinstance(fsa, (NFsa, Fst)): pass
    else: raise EvalError('Can only check regex or fst')
        
    if '*sentences*' not in env:
        raise EvalError('No io examples defined')

    for spec in env['*sentences*']:
        status = spec[0]
        input = spec[1]
        pred = Language(String(s) for s in fsa(input))

        if len(spec) > 2:
            output = spec[2]

            if ((isinstance(output, String) and output in pred) or
                (isinstance(output, Language) and output == pred)):
                pstatus = 'good'
            else:
                pstatus = 'bad'

            if status == pstatus: stars = ':)'
            else: stars = '**'
            print('{} {} {} -> {}'.format(stars, status, input, output))

        else:
            if pred: pstatus = 'good'
            else: pstatus = 'bad'
            if status == pstatus: stars = ':)'
            else: stars = '**'
            print('{} {} {}'.format(stars, status, input))

# [compose]  ---------------------------

##  The implementation of the '%' operator and the 'compose' function.

def compose (*rels, env=None):
    trace = ('composition' in env['*trace*'])
    if len(rels) < 1:
        raise EvalError('No arguments given to compose')
    elif len(rels) == 1:
        return rels[0]
    else:
        f = as_fst(rels[0])
        for rel in rels[1:]:
            g = as_fst(rel)
            f = _compose(f, g, trace)
        return Fsa(f)

# [concat] [OP .] concat  --------------

##  True if x is a String or Symbol, or has a method 'concat'.

def concatenatable (x):
    if hasattr(x, 'concat'):
        return x
    elif isinstance(x, Symbol):
        return String([x])
    else:
        raise EvalError('Cannot be concatenated with anything: %s' % x)

##  The implementation of the '.' operator (when used outside of a regular expression),
#   and the 'concat' function.

def concat (*items):
    out = concatenatable(items[0])
    for x in items[1:]:
        out = out.concat(concatenatable(x))
    return out

# [cross] [OP x] [OP :] cross  ---------

##  The implementation of the 'x' operator and the 'cross' function.

def cross (*args):
    set1 = args[0]
    if not isinstance(set1, Set):
        raise EvalError("Argument to 'x' must be a set")
    i = 1
    while i < len(args):
        set2 = args[i]
        i += 1
        out = set()
        for x in set1:
            for y in set2:
                out.add(seqconcat(x,y))
        set1 = Set(out)
    return set1

##  Concatenate some number of sequences.

def seqconcat (*items):
    elts = []
    for x in items:
        if isinstance(x, SeqExpr): elts.extend(x)
        else: elts.append(x)
    return SeqExpr(elts)

# [E] Edge  ----------------------------

##  The implementation of 'E'.

def add_edge (source, label, dest, env=None):
    if isinstance(label, Pair):
        fsa = need_fst(env)
    else:
        fsa = need_fsa(env)
    fsa.add_edge(source, label, dest)


# [ex]  --------------------------------

##  The implementation of 'ex'.

def add_example (example, env=None):
    corpus = need_corpus(env)
    corpus.append(example)

# [exp] --------------------------------

##  The implementation of the '^' operator and the 'exp' function.

def exp (base, expt):
    if not hasattr(base, '__pow__'):
        raise EvalError('Cannot be raised to a power: %s' % base)
    return base.__pow__(expt)


# [F] FinalState  ----------------------

##  The implementation of 'F'.

def set_final (state, env=None):
    need_fsa(env).set_final(state)

# [first] first  -----------------------

##  The implementation of 'first'.

def first (x):
    if hasattr(x, '__getitem__'):
        return x[0]
    else:
        raise EvalError('Must be a string or sequence')

# [fsa] makefsa  -----------------------

##  The implementation of 'fsa'.

def makefsa (x):
    if isinstance(x, RegLang):
        return Fsa(x.fsa)
    elif isinstance(x, Language):
        return Fsa(x.fsa())
    else:
        raise Exception('Cannot convert to fsa: %s' % x)

# def makefsa (*edges):
#     if len(edges) == 1 and isinstance(edges[0], RegLang):
#         return Fsa(edges[0].fsa)
#     else:
#         if not all(isinstance(e, Edge) for e in edges):
#             raise EvalError('Arguments of fsa() must be edges')
#         fsa = Fsa()
#         for e in edges:
#             fsa.add(e)
#         return fsa

# [gt]  --------------------------------

##  The implementation of the '@>' operator and the 'gt' function.

def greater_than (x, y):
    if hasattr(x, '__gt__'):
        return x.__gt__(y)
    else:
        raise EvalError('Cannot be used with @>: %s' % x)

# [good] [COM] good_sent  --------------

##  The implementation of 'good'.

def good_sent (sent, out=None, env=None):
    sents = need_sents(env)
    if out:
        sents.append(('good', sent, out))
    else:
        sents.append(('good', sent))

# [include] [COM] include  -------------

##  The implementation of 'include'.

def include (name, env=None):
    output = env['*output*']
    included = env.get('*included*')
    if included is None:
        included = set([])
        env['*included*'] = included
    if name in included:
        print('Already included', file=output)
    else:
        included.add(name)
        dir = env['*notebook-dir*']
        fn = os.path.join(dir, '%s.gn' % name)
        if not os.path.exists(fn):
            raise EvalError('Notebook does not exist: %s' % name)
        with open(fn) as file:
            try:
                env['*output*'] = null
                env.interp.batch(file)
            finally:
                env['*output*'] = output


# [incr] [COM] incr  -------------------

##  The implementation of 'incr'.

def incr (x, y):
    if hasattr(x, 'add'):
        x.add(y)
    else:
        raise EvalError('Cannot be an operand to addition: %s' % repr(x))

# [intersect]  -------------------------

##  The implementation of the '&' operator and the 'intersection' function.

def intersection (x, y):
    if not (isinstance(x, Set) and isinstance(y, Set)):
        raise EvalError('Only sets can be intersected')
    return x.intersection(y)

# [io] ---------------------------------

##  The implementation of the 'io' function.

def io_example (input, output, env=None):

    if not isinstance(input, String):
        raise EvalError('Input must be a string')

    if not isinstance(output, (String, Language)):
        raise EvalError('Output must be a string or language')
    
    if '*io*' in env:
        env['*io*'].append((input, output))
    else:
        env['*io*'] = [(input,output)]
    

# [islang]  ----------------------------

##  The implementation of the 'islang' function.

def islang (x):
    return isinstance(x, Language)

# [isstring]  --------------------------

##  The implementation of the 'ismember' function.

def isstring (x):
    return isinstance(x, String)

# [L]  ---------------------------------

##  The implementation of the 'L' function.

def as_language (x):
    if hasattr(x, '__lang__'):
        return x.__lang__()
    else:
        raise EvalError('Cannot convert to language: %s' % x)        

# [lang]  ------------------------------

##  The implementation of the 'lang' function.

def list_language (x, n=10, env=None):
    output = env['*output*']
    for (i,elt) in enumerate(as_language(x)):
        if i >= n:
            print('...', file=output)
            break
        print('[%d]' % i, str(elt), file=output)

# [lt]  --------------------------------

##  The implementation of the '@<' operator and the 'lt' function.

def less_than (x, y):
    if hasattr(x, '__lt__') and not isinstance(x, Symbol):
        return x.__lt__(y)
    else:
        raise EvalError('Cannot be used with @<: %s' % x)

# [makecat]  ---------------------------

##  The implementation of the 'makecat' function.

def makecat (*args):
    return Category(args)

# [minus]  -----------------------------

##  Implementation of the '-' operator and the 'minus' function.

def minus (x, y):
    if not hasattr(x, '__sub__'):
        raise EvalError('Not a valid object for subtraction: %s' % x)
    return x.__sub__(y)

# [new]  -------------------------------

##  The implementation of the 'new' function.

def new (var, env):
    if var == '_fsa_': env['_fsa_'] = Fsa()
    else: raise EvalError("Bad argument for 'new'")

# [new_fsa]  ---------------------------

##  The implementation of the 'new_fsa' function.

def new_fsa (env):
    env['_fsa_'] = fsa = Fsa()
    return fsa

# [new_grammar]  -----------------------

##  The implementation of the 'new_grammar' function.

def new_grammar (env):
    g = Grammar()
    env['_grammar_'] = g
    return g

# [new_union]  -------------------------

##  The implementation of the 'new_union' function.

def new_union (env):
    env['_union_'] = lang = RegLang()
    return lang

# [Pair]  ------------------------------

##  An ordered pair; the implementation of the
#   ':' operator and the 'pair' function.

class Pair (object):

    ##  Constructor.

    def __init__ (self, x, y):

        ##  The first element.
        self.x = x

        ##  The second element.
        self.y = y
    
    ##  String representation.

    def __repr__ (self):
        return '(%s:%s)' % (self.x, self.y)


# [parse] [COM] parse_sent  ------------

##  The implementation of the 'parse' function.

def parse_sent (sent, env=None):
    output = env['*output*']
    if 'parse' in env.get('*trace*'):
        trace = output
    else:
        trace = False
    p = need_parser(env)
    try:
        trees = p(sent, trace=trace)
    except Exception as e:
        raise EvalError(e)
    if trees:
        print(file=output)
        for t in trees:
            print(t, file=output)
            print(file=output)
    else:
        print('No Parse', file=output)
        print(file=output)
        print('Best Fragments:', file=output)
        print_fragments(p, output=output)
        print(file=output)
        print('All Nodes:', file=output)
        print_nodes(p, output=output)

# [plus] [OP +] plus  ------------------

##  The implementation of the '+' operator and the 'plus' function.

def plus (*args):
    if isinstance(args[0], Set):
        s = args[0]
        for arg in args[1:]:
            s = s.union(arg)
        return s
    else:
        x = as_number(args[0])
        if x is not None:
            for y in args[1:]:
                y = as_number(y)
                if y is None: raise EvalError('Improper operands for +')
                x += y
            return x
        else:
            return LatticeElement(atomset(args))

##  Coerce to a number or None.

def as_number (x):
    if not isinstance(x, str): return None
    if not x: return None
    i = 0
    if x[0] in '+-': i = 1
    j = x.find('.')
    if j >= 0:
        if x[i:j].isdigit() and x[j+1:].isdigit():
            return float(x)
        else:
            return None
    elif x[i:].isdigit():
        return int(x)
    else:
        return None

##  The implementation of the 'quote' function.

def quote (expr):
    return str(expr)

# [regex]  -----------------------------

##  The implementation of the '/.../' syntax and the 'regex' function.

def regex (expr, env=None):
    return RegLang(expr, env)

# [rel]  ------------------------------

##  The implementation of the 'rel' function.

def list_relation (x, n=10, env=None):
    output = env['*output*']
    for (i,elt) in enumerate(x.relation()):
        if i >= n:
            print('...', file=output)
            break
        print('[%d]' % i, str(elt), file=output)

# [results] [COM] regression  ----------

##  The implementation of the 'results' function.

def regression (env=None):
    output = env['*output*']
    sents = need_sents(env)
    p = need_parser(env)
    for ref in sents:
        if len(ref) == 2:
            (label, sent) = ref
            np = 0
            try:
                np = len(p(sent))
            except TooManyParses:
                np = -1
            except Exception as e:
                np = 0
            stars = ':)'
            if (label == 'good' and np == 0) or (label == 'bad' and np > 0):
                stars = '**'
            elif np < 0:
                stars = '!!'
            print('%2s %4s %s' % (stars, label, sent), file=output)
        elif len(ref) == 3:
            (label, i, o) = ref
            try:
                out = p(i)
                acc = (o in out)
                if (acc and label == 'good') or ((not acc) and label == 'bad'):
                    stars = ':)'
                else:
                    stars = '**'
            except Exception:
                stars = '!!'
            print('%2s %4s %s %s' % (stars, label, i, o), file=output)


# [set] makeset  -------------------

##  The implementation of the '{...}' syntax and the 'set' function.

def makeset (*items):
    s = frozenset(items)
    if all(isinstance(x, String) for x in s):
        return Language(s)
    elif all(isinstance(x, Symbol) for x in s):
        return Vocabulary(s)
    else:
        return Set(s)

# [seq] makeseq  -----------------------

##  The implementation of the '<...>' syntax and the 'seq' function.

def makeseq (*items):
    s = Seq(items)
    if all(isinstance(x, Symbol) for x in s):
        s = String(s)
    return s

# [show] [COM] show  -------------------

##  The implementation of the 'show' function.

def show (item, env=None):
    output = env['*output*']
    if hasattr(item, 'show'):
        item.show(output)
    elif hasattr(item, 'dump'):
        stdout = sys.stdout
        try:
            sys.stdout = output
            item.dump()
        finally:
            sys.stdout = stdout
    else:
        print(item, file=output)

# [start] get_start  -------------------

##  The implementation of the 'start' function.

def get_start (env=None):
    g = need_grammar(env)
    return g.start

# [set start] set_start  ---------------

##  The implementation of '(start ...) := ...'.

def set_start (sym, env=None):
    g = need_grammar(env)
    if isinstance(sym, str):
        g.start = Category([sym])
    elif isinstance(sym, Category):
        g.start = sym
    else:
        raise EvalError('Must be a string or category: %s' % sym)

# [sym] sym  ---------------------------

##  The implementation of the 'sym' function.

def sym (*ords):
    s = ''.join(chr(o) for o in ords)
    if is_identifier(s):
        return Symbol(s)
    else:
        return UnprintableSymbol(s)

# [trace] [COM] trace  -----------------

##  The implementation of the 'trace' function.

def trace (*args, env=None):
    env['*trace*'].update(args)

# [type]  ------------------------------

##  The implementation of the 'typename' function.

def typename (x):
    return Symbol(type(x).__name__)

# [untrace]  ---------------------------

##  The implementation of the 'untrace' function.

def untrace (*args, env=None):
    env['*trace*'].difference_update(args)

#--  Utility functions  --------------------------------------------------------

##  Turn parsing on or off.

def parse_on_off (value):
    if value == 'on': return True
    elif value == 'off': return False
    else: raise EvalError("Expected 'on' or 'off': %s" % value)

#--  need_  ----------------------------

##  Get the current FSA, creating an empty one if necessary.

def need_fsa (env):
    fsa = env['_fsa_']
    if fsa is None:
        fsa = Fsa()
        env['_fsa_'] = fsa
    return fsa

##  Destructively convert the current FSA to an FST.  If there is no current
#   FSA, create an empty FST and make it current.

def need_fst (env):
    fsa = env['_fsa_']
    if fsa is None:
        fsa = Fsa(Fst())
        env['_fsa_'] = fsa
    else:
        fsa.convert_to_fst()
    return fsa

##  Get the current corpus, creating an empty corpus if necessary.

def need_corpus (env):
    c = env['_corpus_']
    if c is None:
        c = Corpus()
        env['_corpus_'] = c
    return c

##  Get the current grammar, creating an empty grammar if necessary.

def need_grammar (env):
    g = None
    if '_grammar_' in env:
        g = env['_grammar_']
    if g is None:
        g = Grammar()
        env['_grammar_'] = g
    return g

#--  intern_category  ------------------

##  Intern a category in the given symbol table.

def intern_category (x, symtab=None):
    if isinstance(x, str):
        return Category([x])
    elif isinstance(x, Category):
        return Category(_intern_tuple(x, symtab))
    elif isinstance(x, Funcall) and x.function == 'makecat':
        return Category(_intern_tuple(x.args, symtab))
    else:
        raise Exception('Cannot coerce to category: %s' % repr(x))

##  Intern the value of the given variable (which must be a string)
#   in the symbol table.

def intern_value (x, symtab):
    if isinstance(x, Var):
        if symtab is None: return '*'
        else: return intern_variable(x, symtab)
    elif x == 'Top': return '*'
    elif x == 'Bot': return None
    else: return x

def _intern_tuple (x, symtab):
    yield x[0]
    for i in range(1, len(x)):
        yield intern_value(x[i], symtab)

#--  need_parser  ----------------------

##  Create a parser for the current grammar, creating an empty grammar if necessary.

def need_parser (env):
    p = Parser(need_grammar(env), limit=32)
    return p

#--  need_tree  ------------------------

##  Get the current tree ('*tree*'), creating a new one if necessary.

def need_tree (env):
    if '*tree*' in env:
        return env['*tree*']
    else:
        t = TopDownTree()
        env['*tree*'] = t
        return t

##  A node in a TopDownTree.

class TopDownNode (object):

    ##  Constructor.

    def __init__ (self, cat):

        ##  The category.
        self.cat = cat

        ##  The children, a list of TopDownNode instances.
        self.children = None

    ##  Set the children, given a list of categories.

    def expand (self, rhs):
        self.children = [TopDownNode(cat) for cat in rhs]


##  An interactively constructible tree.

class TopDownTree (object):

    ##  Constructor.

    def __init__ (self):

        ##  The root node.
        self.root = None

        ##  The leaves.
        self.leaves = []

        ##  Unexpanded nodes.
        self.unexpanded = []

    ##  Set the root node.  It becomes an unexpanded node.

    def start (self, cat):
        node = TopDownNode(cat)
        self.root = node
        self.unexpanded.append(node)

    ##  Expand the first unexpanded node, replacing it in the list of
    #   unexpanded nodes.

    def expand (self, lhs, rhs):
        if self.root is None:
            self.start(lhs)
        i = self.index(lhs)
        if i > 0:
            self.leaves.extend(self.unexpanded[:i])
            del self.unexpanded[:i]
        node = self.unexpanded[0]
        node.expand(rhs)
        self.unexpanded[0:1] = node.children
        
    ##  Find the first unexpanded node with the given category.
    #   Signals an EvalError on failure.

    def index (self, cat):
        for i in range(len(self.unexpanded)):
            if self.unexpanded[i].cat == cat:
                return i
        raise EvalError("No unexpanded node with cat %s" % cat)

    ##  A readable rendering of where things stand.

    def todo_string (self):
        words = []
        if len(self.leaves) > 1: words.append('...')
        if self.leaves: words.append(self.leaves[-1].cat)
        for node in self.unexpanded:
            words.append(node.cat)
        return ' '.join(words)

#--  need_sents  -----------------------

##  Get the current list of sentences ('*sentences*'), creating an empty
#   list if necessary.

def need_sents (env):
    if '*sentences*' in env:
        return env['*sentences*']
    else:
        sents = []
        env['*sentences*'] = sents
        return sents
        
