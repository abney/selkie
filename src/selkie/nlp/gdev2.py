
from os.path import expanduser, exists, join
from io import StringIO
from nltk import ChartParser, FeatureChartParser, Valuation, Model, Assignment, Expression
from nltk.grammar import CFG, FeatureGrammar, Production, FeatStructNonterminal
from nltk.featstruct import TYPE
from random import Random
from collections import namedtuple

from .disk import VDisk
from .grammar import Grammar as SelkieGrammar
from .parser import Parser as _SelkieParser


#--  GDev  ---------------------------------------------------------------------

class GDev (object):

    def __init__ (self, fn, **flags):
        self.flags = flags
        self.filename = expanduser(fn)
        self.grammar = Grammar(self)
        self.parser = self.grammar.parser
        self.sents = Sentences(self)
        self.interpreter = None #Interpreter(self)



    def is_semantic (self):
        return exists(self.grammar_name + '.val')
    
    def create_vocab (self, sents):
        return set(word for sent in sents for word in sent)


#--  Grammar  ------------------------------------------------------------------

def first_of_list (lst, errmsg):
    if not lst:
        raise Exception(errmsg)
    else:
        return lst[0]

def first_of_iter (itr, errmsg):
    try:
        return next(itr)
    except StopIteration:
        pass
    raise Exception(errmsg)


class Grammar (object):

    def __init__ (self, gdev):
        self.gdev = gdev
        self._grammar = None
        self.parser = None

        self.load()

    def load (self):
        fn = join(self.gdev.filename, 'grammar')
        cfg_fn = fn + '.cfg'
        fcfg_fn = fn + '.fcfg'

        if exists(fn):
            self._grammar = SelkieGrammar(fn)
            self.parser = SelkieParser(self.gdev, _SelkieParser(self._grammar))

        elif exists(fcfg_fn):
            with open(fcfg_fn) as f:
                self._grammar = FeatureGrammar.fromstring(f.read())
            self.parser = NLTKParser(self.gdev, FeatureChartParser(self._grammar))

        elif exists(cfg_fn):
            with open(cfg_fn) as f:
                self._grammar = CFG.fromstring(f.read())
            self.parser = NLTKParser(self.gdev, ChartParser(self._grammar))

        else:
            raise Exception(f'Grammar not found: {fn}.  Tried suffixes .fcfg, .cfg')


#--  Parser  -------------------------------------------------------------------

class BaseParser (object):

    def __init__ (self, gdev, parser):
        self.gdev = gdev
        self._parser = parser

    def grammar (self):
        return self.gdev.grammar

    def _tosent (self, sent):
        if isinstance(sent, Sentence):
            return sent
        else:
            return Sentence(sent)

    def __call__ (self, sent):
        if isinstance(sent, Sentences):
            return self.batch(sent)
        else:
            return self.parse(self._tosent(sent))

    def count (self, sent):
        return len(self.parses(sent))

    def batch (self, sents=None):
        if sents is None:
            sents = self.gdev.sents
        for sent in sents:
            try:
                n = len(self.parses(sent))
                if n == 0:
                    resu = '*'
                elif n == 1:
                    resu = ' '
                else:
                    resu = '@'
            except:
                resu = '*'
            print(f'[{sent.index:-2d}]', resu, sent)

    def vocab (self, sents):
        vocab = sorted(set(word for sent in sents for word in sent))
        g = self.grammar()
        for word in vocab:
            if g.productions(rhs=word):
                print(' ', word)
            else:
                print('-', word)

    def evaluate (self):
        return SyntacticEvaluator(self.gdev)()


class NLTKParser (BaseParser):

    def parse (self, sent):
        return first_of_iter(self._parser.parse(sent), 'No parse')
        
    def parses (self, sent):
        return list(self._parser.parse(sent))

    def trace (self, sent):
        sent = self._tosent(sent)
        self._parser.chart_parse(sent, trace=2)

    def nodes (self, sent):
        c = self._parser.chart_parse(sent)
        d = {}
        for e in c:
            if e.is_complete() and e.rhs() and e.length() > 0:
                if e.span() in d: d[e.span()].append(e)
                else: d[e.span()] = [e]
        for span in sorted(d):
            print(' '.join(sent[span[0]:span[1]]))
            for e in d[span]:
                print('   ', repr(e.lhs()), '->', end=' ')
                for cat in e.rhs(): print(repr(cat), end=' ')
                print()


class SelkieParser (BaseParser):

    def parse (self, sent):
        return first_of_list(self._parser(sent), 'No parse')

    def parses (self, sent):
        return self._parser(sent) or []


#--  Sentences  ----------------------------------------------------------------

class Sentence (object):

    def __init__ (self, sent, index=-1, gloss=None):
        self.index = index
        self.words = sent.split()
        self.gloss = gloss

    def __iter__ (self): return self.words.__iter__()
    def __len__ (self): return self.words.__len__()
    def __getitem__ (self, i): return self.words.__getitem__(i)

    def __str__ (self):
        words = [f'[{self.index:2d}]']
        words.extend(self.words)
        line = ' '.join(words)
        if self.gloss:
            line += '\n    ' + self.gloss
        return line


class Sentences (object):

    def __init__ (self, gdev):
        self.gdev = gdev
        self.filename = self.get_filename()
        (self.good, self.bad) = self.load()

    def __iter__ (self): return self.good.__iter__()
    def __len__ (self): return self.good.__len__()
    def __getitem__ (self, i): return self.good.__getitem__(i)

    def __str__ (self):
        words = [str(s) for s in self.good]
        if self.bad:
            words.append('\nBAD:\n')
            words.extend(str(s) for s in self.bad)
        return '\n'.join(words)

    def get_filename (self):
        dfn = self.gdev.filename
        for name in ('tsents', 'sents'):
            fn = join(dfn, name)
            if exists(fn):
                return fn
        raise Exception('Cannot find sents file')

    def load (self):
        fn = self.filename
        if fn.endswith('.tsents'):
            return self.load_tsents()
        else:
            return self.load_sents()

    def load_sents (self):
        good = []
        bad = []
        with open(self.filename) as f:
            for line in f:
                line = line.strip()
                if (not line) or line.startswith('#'):
                    continue
                if line.startswith('*'):
                    bad.append(Sentence(line[1:], len(bad)))
                else:
                    good.append(Sentence(line, len(good)))
        if self.gdev.flags.get('generate_nonsents'):
            bad = self.generate_nonsents(good)
        return (good, bad)

    def load_tsents (self):
        good = []
        with open(self.filename) as f:
            state = 0
            sent = None
            for (lno, line) in enumerate(f, 1):
                line = line.rstrip('\r\n')
                if line:
                    if state == 0:
                        sent = Sentence(line, len(good))
                        good.append(sent)
                        state += 1
                    elif state == 1:
                        sent.gloss = self.parse_gloss(line)
                        state += 1
                    else:
                        raise Exception(f'Line {lno}: expecting an empty line')
                else:
                    state = 0
                    sent = None
        return (good, [])

    def parse_gloss (self, gloss):
        orig = gloss
        try:
            return Expression.fromstring(orig)
        except:
            return f'(Ill-formed expression: {orig}'
            
    def generate_nonsents (self, sents, vocab=None, n=None, seed=None):
        flags = self.gdev.flags
        if vocab is None:
            vocab = flags.get('vocab')
        if vocab is None:
            vocab = self.create_vocab(self.sents())
        if n is None:
            n = flags.get('n')
        if n is None:
            n = len(sents)
        rng = Random()
        if seed is None:
            seed = flags.get('seed')
        if seed is not None:
            rng.seed(seed)
        vocab = sorted(vocab)
        for index in range(n):
            sent = rng.choice(sents)
            # make a safe copy
            sent = sent[:]
            for _ in range(3):
                if not sent:
                    break
                i = rng.randrange(len(sent))
                del sent[i]
            for _ in range(3):
                i = rng.randrange(len(sent)+1)
                word = rng.choice(vocab)
                sent[i:i] = [word]
            yield Sentence(sent, index)


#--  SyntacticEvaluator  -------------------------------------------------------

class SyntaxStats (object):
    
    def __init__ (self, misses, false_pos, extra, sents):
        self.misses = misses
        self.false_pos = false_pos
        self.extra = extra
        self.sents = sents

    def __str__ (self):
        (fn, fp, x) = (self.misses, self.false_pos, self.extra)
        n1 = len(self.sents)
        n2 = len(self.sents.bad)
        N = n1 + n2
        e = fn + fp
        T = n1 + x

        with StringIO() as f:
            print(f'Misses:      {fn:-4d}',
                  '|',
                  f'#Sents:      {n1:-4d}',
                  '|',
                  f'Sensitivity: {1-fn/n1:-6.4f}', file=f)
            if n2:
                print(f'False pos:   {fp:-4d}',
                      '|',
                      f'#Nonsents:   {n2:-4d}',
                      '|',
                      f'Specificity: {1-fp/n2:-6.4f}', file=f)
            print(f'                 ',
                  '|',
                  f'                 ',
                  '|',
                  f'Accuracy:    {1-e/N:-6.4f}', file=f)
            print(f'Extra:       {x:-4d}',
                  '|',
                  f'                 ',
                  '|',
                  f'Parses/sent: {T/n1:-6.4f}', file=f)
            return f.getvalue()


class SyntacticEvaluator (object):
        
    def __init__ (self, res):
        self.gdev = res

    def __call__ (self):
        print(self.stats())

    def stats (self):
        res = self.gdev
        parse = res.parser
        sents = res.sents

        fp = fn = extra_trees = 0

        for sent in sents:
            ntrees = parse.count(sent)
            if ntrees > 0:
                extra_trees += ntrees - 1
            else:
                fn += 1

        for nonsent in sents.bad:
            ntrees = parse.count(nonsent)
            if ntrees > 0:
                fp += 1

        return SyntaxStats(fn, fp, extra_trees, sents)


#--  Meaning  ------------------------------------------------------------------

class Meaning (object):

    def __init__ (self, interp, sent):
        if isinstance(sent, Expression):
            (sent, tree, expr) = (None, None, sent)
        else:
            tree = interp.parse(sent)
            expr = tree.label().get('v')

        self.interpreter = interp
        self.sent = sent
        self.tree = tree
        self.expr = expr
        self.target = None
        self.value = None

        if self.sent is not None:
            self.target = self.sent.gloss

        if not (expr is None or interp is None):
            try:
                self.value = interp(expr)
            except:
                self.value = 'ERROR'

    def is_correct (self):
        return self.expr == self.target

    def __str__ (self):
        with StringIO() as f:
            ast = ' ' if self.is_correct() else '*'
            print('Target: ', self.sent.gloss, file=f)
            print('Trans:', ast, self.expr, file=f)
            print('Value:  ', self.value, file=f)
            return f.getvalue()


class Meanings (object):

    def __init__ (self, meanings):
        self.meanings = meanings
        
    def __iter__ (self): return self.meanings.__iter__()
    def __len__ (self): return self.meanings.__len__()
    def __getitem__ (self, i): return self.meanings.__getitem__(i)

    def __str__ (self):
        with StringIO() as f:
            first = True
            for m in self.meanings:
                if first: first = False
                else: print(file=f) 
                i = m.sent.index
                ast = ' ' if m.is_correct() else '*'
                tr = m.sent.gloss or '(no translation)'
                v = m.value or '(no value)'
                print(f'[{i:2d}]', ast, tr, file=f)
                print('    ', ' ', v, file=f)
            return f.getvalue()


#--  Interpreter  --------------------------------------------------------------

class Interpreter (object):
    
    def __init__ (self, res):
        self.gdev = res
        self.domain = None
        self.model = None
        self.g = None
        self.filename = self.get_filename()

        self.load()
        
    def get_filename (self):
        return self.gdev.grammar_name + '.val'

    def load (self):
        if exists(self.filename):
            with open(self.filename) as f:
                v = Valuation.fromstring(f.read())
            self.domain = d = self.domain_from_valuation(v)
            self.model = Model(d,v)
            self.g = Assignment(d)

    def domain_from_valuation (self, v):
        dom = set()
        for (key, val) in v.items():
            if isinstance(val, str):
                dom.add(val)
            elif isinstance(val, set):
                for tup in val:
                    assert isinstance(tup, tuple)
                    for x in tup:
                        assert isinstance(x, str)
                        dom.add(x)
        return dom

    def parse (self, sent):
        return self.gdev.parser(sent)

    def meaning (self, sent):
        return Meaning(self, sent)

    def meanings (self, sents):
        return Meanings([Meaning(self, sent) for sent in sents])
        
    def __call__ (self, x):
        if isinstance(x, Sentence):
            return self.meaning(x)
        elif isinstance(x, Sentences):
            return self.meanings(x)
        elif isinstance(x, Expression):
            return self.value(x)
        else:
            raise Exception(f'Cannot interpret {x}')

    def value (self, expr):
        if isinstance(expr, str):
            return self.model.evaluate(expr, self.g)
        elif isinstance(expr, Expression):
            return self.model.satisfy(expr, self.g)
        else:
            raise Exception(f'Not a string or expression: {expr}')

    def __getitem__ (self, vbl):
        return self.g[vbl]
    
    def __setitem__ (self, vbl, val):
        self.g[vbl] = val

    def let (self, vbl, val):
        return TemporarySetting(self, vbl, val)


class TemporarySetting (object):

    def __init__ (self, interp, vbl, val):
        self.interpreter = interp
        self.variable = vbl
        self.value = val
        self.old_value = None

    def __enter__ (self):
        interp = self.interpreter
        vbl = self.variable
        if vbl in interp.g:
            self.old_value = interp.g[vbl]
        interp.g[vbl] = self.value

    def __exit__ (self, t, v, tb):
        g = self.interpreter.g
        vbl = self.variable
        if self.old_value is None:
            del g[vbl]
        else:
            g[vbl] = self.old_value


#--  Semantic Evaluator  -------------------------------------------------------

class SemanticEvaluator (object):

    def __init__ (self, res):
        self.gdev = res
        
    def stats (self):
        res = self.gdev


