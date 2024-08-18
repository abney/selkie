
from io import StringIO
from math import inf
from .fsa import NFsa, DFsa, determinize, minimize
from .fst import Fst


##  __tofsa__
##
##  The fundamental rule: only the owner creates
##  edges OUT of the start state or INTO the end state.
##
##  ALWAYS DO:
##
##      (start, end) = cons.state_pair()
##      ...
##      return (start, end)
##
##  After doing:
##
##      (s, e) = lang.__tofsa__(cons, side)
##
##  NEVER DO: 
##
##      _.edge(e)
##      s.edge(_)
##


class Language (object):

    def __eq__ (self, other):
        return self.__class__ == other.__class__ and self._contents == other._contents

    def __bool__ (self):
        raise Exception('Cannot determine')

    def is_epsilon (self):
        raise Exception('Cannot determine')

    def is_infinite (self):
        raise Exception('Cannot determine')

    def __len__ (self):
        raise Exception('Cannot determine')

    def __hash__ (self):
        return hash(self._contents)

    def __add__ (self, other):
        other = language(other)
        if self.is_epsilon():
            return other
        elif other.is_epsilon():
            return self
        else:
            return Concatenation(self, other)

    def __or__ (self, other):
        other = language(other)
        if not other:
            return self
        elif not self:
            return other
        else:
            return Union(self, other)

    def __mul__ (self, n):
        return KleeneClosure(self, n)

    def __getitem__ (self, n):
        return KleeneClosure(self, n)

    def opt (self):
        return KleeneClosure(self, (0, 1))

    def star (self):
        return KleeneClosure(self, (0, inf))

    def plus (self):
        return KleeneClosure(self, (1, inf))

    def fsa (self):
        fsa = FsaConstructor()(self)
        if isinstance(fsa, NFsa):
            fsa = determinize(fsa)
        if isinstance(fsa, DFsa):
            fsa = minimize(fsa)
        return fsa

    def fst (self):
        return FsaConstructor(True)(self)

    def __iter__ (self):
        for x in self.fsa():
            yield string(x)


class String (object):

    def __init__ (self, contents):
        assert isinstance(contents, tuple)
        assert all(isinstance(elt, Atom) for elt in contents)
        self._contents = contents

    def __bool__ (self):
        return bool(self._contents)

    def is_epsilon (self):
        return len(self._contents) == 0

    def __eq__ (self, other):
        return isinstance(other, String) and self._contents == other._contents

    def __lt__ (self, other):
        if isinstance(other, String):
            return self._contents < other._contents
        elif isinstance(other, (list, tuple)):
            return self._contents < other
        else:
            raise Exception(f'Not comparable: {repr(self)} {repr(other)}')

    def __hash__ (self):
        return hash(self._contents)

    def __contains__ (self, x):
        return x in self._contents
    
    def __len__ (self):
        return len(self._contents)

    def __getitem__ (self, i):
        return self._contents[i]

    def __iter__ (self):
        return iter(self._contents)

    def __add__ (self, other):
        other = string(other)
        return String(self._contents + other._contents)

    def __tofsa__ (self, cons, side):
        (start, end) = cons.state_pair()
        if len(self._contents) == 0:
            start.edge(end)
        else:
            atoms = self._contents
            last = start
            for atom in atoms:
                if not isinstance(atom, Atom):
                    raise EvalError('Non-string sequence not allowed in regex')
                (_,last) = atom.__tofsa__(cons, side, start=last)
            last.edge(end)
        return (start, end)

    def __repr__ (self):
#        if len(self._contents) == 0:
#            return '\u03b5'
        with StringIO() as out:
            out.write('<')
            first = True
            for elt in self._contents:
                if first: first = False
                else: out.write(', ')
                out.write(repr(elt))
            out.write('>')
            return out.getvalue()


class Atom (object):

    def __init__ (self, s):
        self._contents = s

    def __bool__ (self):
        return True

    def __eq__ (self, other):
        return isinstance(other, Atom) and self._contents == other._contents

    def __lt__ (self, other):
        if isinstance(other, Atom):
            return self._contents < other._contents
        elif isinstance(other, str):
            return self._contents < other
        else:
            raise Exception(f'Not comparable: {repr(self)} {repr(other)}')

    def __hash__ (self):
        return hash(self._contents)

    def __contains__ (self, x):
        raise Exception('An atom has no contents')

    def __len__ (self):
        raise Exception('An atom has no length')

    def __iter__ (self):
        yield self

    def __tofsa__ (self, cons, side, start=None):
        label = self._contents
        if start is None:
            start = cons.state()
        end = cons.state()
        if not cons.isfst:
            start.edge(end, label)
        elif side == 'both':
            start.edge(end, label, label)
        elif side == 'input':
            start.edge(end, label, None)
        elif side == 'output':
            start.edge(end, None, label)
        else:
            raise Exception('Bad value for side: %s' % side)
        return (start, end)

    _specials = {'<': r'\<',
                 '>': r'\>',
                 '\t': r'\t',
                 '\r': r'\r',
                 '\n': r'\n',
                 ' ': r'\s',
                 '\\': r'\\'}

    def __repr__ (self):
        with StringIO() as out:
            for c in self._contents:
                if c in self._specials:
                    out.write(self._specials[c])
                else:
                    out.write(c)
            return out.getvalue()


class Wildcard (Atom):

    def __init__ (self):
        pass

    def __eq__ (self, other):
        return isinstance(other, Wildcard)

    def __bool__ (self):
        raise Exception('Wildcard is a pseudo-atom')

    def __contains__ (self, x):
        raise Exception('Wildcard is a pseudo-atom')

    def __iter__ (self, x):
        raise Exception('Wildcard is a pseudo-atom')

    def __repr__ (self):
        return '__else__'


class Relation (Language):

    def __init__ (self, lang1, lang2):
        assert isinstance(lang1, Language)
        assert isinstance(lang2, Language)
        self._lang1 = lang1
        self._lang2 = lang2
    
    ##  Convert an atom

    def _label (self, x):
        if x == '_e_': return (True, None)
        elif x == '_0_': return (False, None)
        elif x == '_else_': return (True, True)
        elif isinstance(x, Var): return (False, None)
        elif isinstance(x, Symbol): return (True, x)
        else: return (False, None)

    ##  Convert a pair of regular expressions.

    def __tofsa__ (self, cons, side):
        ### TO FIX
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

    def __repr__ (self):
        return self._label1 + ':' + self._label2


class StringSet (Language):

    def __init__ (self, contents):
        assert isinstance(contents, set) and all(isinstance(elt, String) for elt in contents)
        self._contents = contents

    def __bool__ (self):
        return bool(self._contents)
        
    def is_epsilon (self):
        return len(self._contents) == 1 and all(s.is_epsilon() for s in self._contents)

    def is_infinite (self):
        return False

    def __len__ (self):
        return len(self._contents)

    def __contains__ (self, x):
        x = string(x)
        return x in self._contents

    def __tofsa__ (self, cons, side):
        (start, end) = cons.state_pair()
        for elt in self._contents:
            assert isinstance(elt, String)
            (s,e) = elt.__tofsa__(cons, side)
            start.edge(s)
            e.edge(end)
        return (start, end)

    def __repr__ (self):
        return repr(self._contents)


class ComplexLanguage (Language):

    __arity__ = None
    __operator__ = None

    def __init__ (self, *langs):
        if not (self.__arity__ is None or len(langs) == self.__arity__):
            raise Exception(f'Wrong number of arguments: {langs}')
        self._contents = tuple(langs)

    def __repr__ (self):
        first = True
        with StringIO() as out:
            if self.__arity__ == 1:
                lang = self._contents[0]
                out.write(repr(lang))
                out.write(self.__operator__)
            else:
                out.write('(')
                for lang in self._contents:
                    if first:
                        first = False
                    else:
                        out.write(' ')
                        out.write(self.__operator__)
                        out.write(' ')
                    out.write(repr(lang))
                out.write(')')
            return out.getvalue()


class Concatenation (ComplexLanguage):
    
    __operator__ = '+'

    def is_infinite (self):
        return any(lang.is_infinite() for lang in self._contents)

    def __len__ (self):
        return sum(len(lang) for lang in self._contents)

    def __tofsa__ (self, cons, side):
        (start, end) = cons.state_pair()
        last = start
        for lang in self._contents:
            (s, e) = lang.__tofsa__(cons, side)
            last.edge(s)
            last = e
        last.edge(end)
        return (start, end)


class Union (ComplexLanguage):

    __operator__ = '|'

    def is_infinite (self):
        return any(lang.is_infinite() for lang in self._contents)

    def __len__ (self):
        if len(self._contents) == 0:
            return 0
        elif len(self._contents) == 1:
            return len(self._contents[0])
        else:
            raise Exception('Cannot determine size of a union without enumerating it')

    def __tofsa__ (self, cons, side):
        (start, end) = cons.state_pair()
        for lang in self._contents:
            (s, e) = lang.__tofsa__(cons, side)
            start.edge(s)
            e.edge(end)
        return (start, end)

    
def _ispos (n):
    return (isinstance(n, int) and n >= 0) or n == inf


class KleeneClosure (ComplexLanguage):

    __operator__ = '*'
    __arity__ = 1

    def __init__ (self, lang, n=None):
        ComplexLanguage.__init__(self, lang)
        if n is None:
            self._minimum = 0
            self._maximum = inf
        elif isinstance(n, int):
            self._minimum = self._maximum = n
        elif isinstance(n, slice):
            self._minimum = n.start
            self._maximum = n.stop
        else:
            (self._minimum, self._maximum) = n
        if not (_ispos(self._minimum) and _ispos(self._maximum)):
            raise Exception(f'Bad range argument: {repr(n)}')

    def is_infinite (self):
        lang = self._contents[0]
        return ((self._maximum == inf and not lang.is_epsilon()) or
                (lang.is_infinite() and self._minimum > 0))

    def __len__ (self):
        if self._maximum == inf:
            raise Exception('Infinite')
        n = len(self._contents[0])
        return sum(n**i for i in range(self._minimum, self._maximum+1))

    def __tofsa__ (self, cons, side):
        lang = self._contents[0]
        (start, end) = cons.state_pair()
        last = start
        if self._minimum > 0:
            for _ in range(self._minimum):
                (s, e) = lang.__tofsa__(cons, side)
                last.edge(s)
                last = e
        if self._maximum == inf:
            (s, e) = lang.__tofsa__(cons, side)
            last.edge(end)
            last.edge(s)
            e.edge(s)
            e.edge(end)
        else:
            for _ in range(self._maximum - self._minimum):
                (s, e) = lang.__tofsa__(cons, side)
                last.edge(s)
                last.edge(end)
                last = e
            last.edge(end)
        return (start, end)
    
    def __repr__ (self):
        lang = self._contents[0]
        n = (self._minimum, self._maximum)
        if n == (0, 1):
            return repr(lang) + '?'
        elif n == (0, inf):
            return repr(lang) + '*'
        elif n == (1, inf):
            return repr(lang) + '+'
        else:
            return f'{repr(lang)}[{self._minimum}:{self._maximum}]'


class Optional (ComplexLanguage):

    __operator__ = '?'
    __arity__ = 1

    def __tofsa__ (self, cons, side):
        (s, e) = cons.state_pair()
        (s1, e1) = self._contents[0].__tofsa__(cons, side)
        s.edge(s1)
        s.edge(e)
        e1.edge(e)
        return (s,e)


class Composition (ComplexLanguage):

    __operator__ = '@'

    def __init__ (self, *langs):
        self._contents = tuple(langs)

    def __tosfsa__ (self, cons, side):
        if side != 'both':
            raise EvalError('Cannot embed composition in one side of transduction')
        ### TO FIX ###
        fst1 = as_fst(convert_regex(regex1, self.env))
        fst2 = as_fst(convert_regex(regex2, self.env))
        return self.copy(seal.nlp.fsa.compose(fst1, fst2), side)


class FsaConstructor (object):

    def __init__ (self, isfst=False):
        self.isfst = isfst
        self.fsa = None

    def __call__ (self, lang):
        cls = Fst if self.isfst else NFsa
        self.fsa = cls()
        (s, e) = lang.__tofsa__(self, 'both')
        self.fsa.start = s
        e.is_final = True
        fsa = self.fsa
        self.fsa = None
        return fsa

    def state (self):
        n = len(self.fsa.states)
        return self.fsa.state(n)

    def state_pair (self):
        return (self.state(), self.state())

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


def language (x):
    if isinstance(x, Language):
        return x
    else:
        return stringset(x)


def atom (x):
    if isinstance(x, Atom):
        return x
    elif isinstance(x, str):
        return Atom(x)
    else:
        raise Exception(f'Cannot coerce to an atom: {repr(x)}')


__space__ = atom(' ')
__tab__ = atom('\t')
__newline__ = atom('\n')
__else__ = Wildcard()


def _flatten (elts):
    for elt in elts:
        if isinstance(elt, (str, Atom)):
            yield elt
        elif isinstance(elt, String):
            yield from elt._contents
        else:
            yield from _flatten(elt)

def string (*contents):
    flat = tuple(_flatten(contents))
    return String(tuple(atom(elt) for elt in flat))


def elements (x):
    if isinstance(x, String):
        return stringset(*x._contents)
    elif isinstance(x, Atom):
        return x


def words (s):
    return string(*s.split())


def chars (s):
    return string(*s)


def stringset (*contents):
    contents = set(string(elt) for elt in contents)
    return StringSet(contents)


def itern (x, n=20):
    for (i, elt) in enumerate(x):
        if i == n:
            break
        yield elt

def head (x, n=20):
    return list(itern(x, n))
