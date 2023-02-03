##  \package seal.nlp.grammar
#   Feature grammar.

import os
from .map import Index
from .io import iter_tokens, Fn, Syntax, StringIO
from .features import Category, join, subsumes, scan_category, Declarations, \
                          Parameter, basecat, arity
from .avs import scan_avs, scan_avstate, Copier
from .expr import scan_expr


#--  Lexicon  ------------------------------------------------------------------

##  Lexicon.

class Lexicon (object):

    ##  A lexical entry.

    class Entry (object):

        ##  Constructor.

        def __init__ (self, word, pos, sem=None):

            ##  The word.
            self.word = word

            ##  The part of speech.
            self.pos = pos

            ##  The semantics.
            self.sem = sem

        ##  String representation.

        def __str__ (self):
            if self.sem: semstr = ' : ' + str(self.sem)
            else: semstr = ''
            return '%s %s%s' % (self.word, self.pos, semstr)

        ##  String representation.

        def __repr__ (self):
            if self.sem: semstr = ' : ' + str(self.sem)
            else: semstr = ''
            return '<Entry %s %s%s>' % (self.word, self.pos, semstr)

    ##  Constructor.

    def __init__ (self, arities=None):
        if arities is None: arities = Arities()

        ##  Index from word to list of entries, differing by part of speech or sem.
        self.by_word = Index()

        ##  Arities.
        self.arities = arities

    ##  Add a new entry.

    def define (self, word, pos, sem=None, tokens=None):
        entry = Lexicon.Entry(word, pos, sem)
        self.arities.check_cat(pos, tokens)
        self.by_word.add(word, entry)

    ##  Fetch the entries for the given word.

    def __getitem__ (self, word):
        return self.by_word[word]

    ##  Iterate over entries.

    def __iter__ (self):
        for word in self.by_word:
            for ent in self.by_word[word]:
                yield ent

    ##  The number of words (not the number of entries).

    def __len__ (self):
        return len(self.by_word)

    ##  String representation.

    def __str__ (self):
        return '\n'.join(sorted(str(e) for e in self))


#--  Reverse Lexicon  ----------------------------------------------------------

##  Inverse lexical mapping.

class ReverseLexicon (object):

    ##  Constructor.

    def __init__ (self, lexicon):
        self.__bysem = Index()
        for entry in lexicon:
            if isinstance(entry.sem, str):
                self.__bysem.add((entry.pos[0], entry.sem), entry)
            elif isinstance(entry.sem, Avs):
                for eqn in entry.sem.constant_equations():
                    self.__bysem.add((entry.pos[0], eqn), entry)

    ##  Input is a (pos, sem) pair.

    def __getitem__ (self, xxx_todo_changeme):
        (pos, sem) = xxx_todo_changeme
        if sem is None:
            return []
        elif isinstance(sem, str):
            return self.__bysem[pos, sem]
        else:
            out = []
            for eqn in sem.constant_equations():
                vals = self.__bysem[pos, eqn]
                if vals: out.extend(vals)
            return out

    ##  Contents represented as a string.

    def __str__ (self):
        lines = []
        for key in self.__bysem:
            first = True
            for entry in self.__bysem[key]:
                if first:
                    first = False
                    lines.append('%s: %s %s' % (repr(key), entry.word, entry.pos))
                else:
                    lines.append('    %s %s' % (entry.word, entry.pos))
            return '\n'.join(lines)


#--  Rule  ---------------------------------------------------------------------

##  A grammar rule.

class Rule (object):

    ##  Constructor.

    def __init__ (self, lhs=None, rhs=None, sem=None,
                  index=None, symtab=None, decls=None, source=None, bindings=None):

        ##  The rule number.
        self.index = index
        if source:

            ##  The left-hand side category.
            self.lhs = source.lhs

            ##  The tuple of right-hand side categories.
            self.rhs = source.rhs

            ##  The semantics.
            self.sem = source.sem

            ##  Bindings.
            self.bindings = source.bindings

            ##  Variables.
            self.variables = source.variables
        else:
            self.lhs = None
            self.rhs = None
            self.sem = None
            self.bindings = None
            self.variables = None

        if lhs: self.lhs = lhs
        if rhs: self.rhs = rhs
        assert self.lhs is not None
        assert self.rhs is not None

        if sem: self.sem = sem
        if bindings:
            assert symtab is None
            self.bindings = bindings
        elif symtab:
            self.bindings = ['*' for i in range(len(symtab))]
            self.variables = [None for i in range(len(symtab))]
            for var,i in symtab.items():
                self.variables[i] = var
                if decls and var in decls.variables:
                    self.bindings[i] = decls.variables[var]
        elif self.bindings is None:
            max = -1
            for cat in [lhs] + rhs:
                for val in cat[1:]:
                    if isinstance(val,int):
                        if val > max: max = val
            self.bindings = ['*' for i in range(max+1)]
            self.variables = None

    ##  Key for comparison: (lhs, rhs, index).

    def key (self):
        return (self.lhs, self.rhs, self.index)

    ##  Compare by key.

    def __lt__ (self, other):
        return self.key() < other.key()

    ##  Compare by key.

    def __eq__ (self, other):
        return self.key() == other.key()

    def __catstr (self, c):
        if len(c) == 1 or not self.variables:
            return str(c)
        else:
            vals = []
            for v in c[1:]:
                if isinstance(v, int):
                    vals.append(self.variables[v])
                else:
                    vals.append(str(v))
            return c[0] + '[' + ','.join(vals) + ']'

    ##  String representation.

    def __str__ (self):
        if self.sem: semstr = ' : ' + str(self.sem)
        else: semstr = ''
        return '%s -> %s%s' % (self.__catstr(self.lhs),
                               ' '.join(self.__catstr(cat) for cat in self.rhs),
                               semstr)

    ##  String representation.

    def __repr__ (self):
        return '<%s -> %s>' % (self.__catstr(self.lhs),
                               ' '.join(self.__catstr(cat) for cat in self.rhs))


#--  Semantics  ----------------------------------------------------------------

##  A generic scanner for semantic expressions.  Accommodates different
#   metalanguages.

class Semantics (object):

    ##  Constructor.

    def __init__ (self, scan_rule, default_rule, scan_lex):

        ##  Function to scan a rule.
        self.scan_rule = scan_rule

        ##  Default rule.
        self.default_rule = default_rule

        ##  Function to scan a lexical entry.
        self.scan_lex = scan_lex

##  Scan an expression.

def scan_sem_expr (tokens, nchildren=None):
    return scan_expr(tokens)

##  AVS semantic representations.
avs_semantics = Semantics(scan_avstate, Copier, scan_avs)

##  Predicate-calculus semantic representations.
expr_semantics = Semantics(scan_sem_expr, None, scan_sem_expr)


#--  Grammar  ------------------------------------------------------------------

##  A grammar.

class Grammar (object):

    ##  Constructor.

    def __init__ (self, filename=None):

        ##  Filename.
        self.filename = filename

        ##  Start category.
        self.start = None

        ##  Index mapping lh category to list of rules.
        self.by_lhs = Index()

        ##  Index mapping first rhs category to list of rules.
        self.by_first = Index()

        ##  Category and feature declarations.
        self.declarations = None

        ##  Arities.
        self.arities = Arities()

        ##  Lexicon.
        self.lexicon = Lexicon(arities=self.arities)

        ##  Grammar rules.
        self.rules = []

        ##  The semantic scanner.
        self.semantics = expr_semantics
        
        if filename: GrammarLoader(self).load(filename)

    ##  Add a rule.

    def define (self, lhs, rhs, sem=None, symtab=None, tokens=None):
        i = len(self.rules)
        rule = Rule(lhs, rhs, sem, index=i, symtab=symtab, decls=self.declarations)
        self.arities.check_rule(rule, tokens)
        self.rules.append(rule)
        self.by_lhs.add(lhs[0], rule)
        if rule.rhs:
            self.by_first.add(rhs[0][0], rule)
        if self.start is None:
            self.start = lhs

    ##  Set a property.  Currently the only property is 'sem', and its possible
    #   values are 'avs' and 'expr'.

    def setprop (self, prop, value):
        if prop == 'sem':
            if value == 'avs': self.semantics = avs_semantics
            elif value == 'expr': self.semantics = expr_semantics
            else: raise Exception('Unrecognized semantics: %s' % value)
        else:
            raise Exception('Unrecognized property: %s' % prop)

    ##  Expansions of a given lhs category.

    def expansions (self, lhs):
        return self.by_lhs[lhs]

    ##  Continuations of a given first child category.

    def continuations (self, first_type):
        return self.by_first[first_type]

    ##  Fetch a rule by number.

    def __getitem__ (self, i):
        return self.rules.__getitem__(i)

    ##  Returns an iterator over the rules.

    def __iter__ (self):
        return iter(self.rules)

    ##  Returns the number of rules.

    def __len__ (self):
        return len(self.rules)

    ##  Contents as a string.

    def __str__ (self):
        out = StringIO()
        print('Start:', self.start, file=out)
        print(file=out)
        out.write('Rules:')
        w = len(str(len(self.rules) - 1))
        for r in self.rules:
            out.write('\n')
            out.write('    [%*d] %s' % (w, r.index, str(r)))
        if len(self.lexicon) > 0:
            out.write('\n\nLexicon:')
            for s in sorted(str(e) for e in self.lexicon):
                out.write('\n')
                out.write('    ')
                out.write(s)
        s = out.getvalue()
        out.close()
        return s


##  A dict mapping a category to its arity (number of features).

class Arities (dict):

    ##  Check that the categories in the rule have the correct arities.

    def check_rule (self, rule, tokens=None):
        self.check_cat(rule.lhs, tokens)
        for cat in rule.rhs:
            self.check_cat(cat, tokens)

    ##  Check that the given category has the correct arity.

    def check_cat (self, cat, tokens=None):
        sym = basecat(cat)
        n = arity(cat)
        if sym in self:
            if n != self[sym]:
                msg = 'Arity should be %d: %s' % (self[sym], cat)
                if tokens is None: raise Exception(msg)
                else: tokens.error(msg)
        else:
            self[sym] = n


#--  GrammarFile  --------------------------------------------------------------

##  A Syntax declaration for grammar files.
GrammarSyntax = Syntax('%=/:[,]()', eol=True)


##  Grammar loader.

class GrammarLoader (object):

    ##  Constructor.

    def __init__ (self, grammar):

        ##  The grammar.
        self.grammar = grammar

        ##  Features.
        self.features = None

        ##  Categories.
        self.categories = None

        ##  Variables.
        self.variables = None

        ##  Lexicon.
        self.lexicon = grammar.lexicon

    ##  Load a file.

    def load (self, fn, dir=None):
        if dir and not os.path.isabs(fn):
            fn = os.path.join(dir, fn)
        if os.path.isdir(fn):
            dir = fn
            name = os.path.basename(fn)
            fn = os.path.join(fn, name)
        else:
            dir = os.path.dirname(fn)

        if os.path.exists(fn):
            self.load_generic(fn)
        else:
            gfn = fn + '.g'
            if not os.path.exists(gfn):
                raise Exception('File not found: %s[.g]' % fn)
            #self.load_g(gfn)
            self.load_generic(gfn)
            lfn = fn + '.lex'
            if os.path.exists(lfn):
                self.load_lex(lfn)

    ##  Load a generic grammar file.

    def load_generic (self, fn):
        tokens = iter_tokens(fn, syntax=GrammarSyntax)
        while tokens.accept('%'):
            what = tokens.require('word').lower()
            if not self.handle_section(what, tokens):
                tokens.error('Unrecognized header: ' + what)

        if not tokens.has_next('eof'):
            tokens.error('Unparseable material')

    ##  Specializations may wrap this.  If the section is handled,
    #   it should return True.  Example:
    #
    #       def handle_section (self, what, tokens):
    #           if GrammarLoader.handle_section(self, what tokens):
    #               return True
    #           elif what == 'foo':
    #               self.scan_foo(tokens)
    #               return True
    #           else:
    #               return False
    
    def handle_section (self, what, tokens):
        if what == 'start':
            self.grammar.start = self.scan_category(tokens)
            tokens.require('\n')
            return True

        elif what in ('features', 'categories', 'variables'):
            tokens.require('\n')
            if self.grammar.declarations is None:
                if len(self.grammar) > 0:
                    what.error('Declarations must precede rules and lexicon')
                self.grammar.declarations = Declarations()
                self.features = self.grammar.declarations.features
                self.categories = self.grammar.declarations.categories
                self.variables = self.grammar.declarations.variables
            if what == 'features': self.scan_feature_definitions(tokens)
            elif what == 'categories': self.scan_category_definitions(tokens)
            elif what == 'variables': self.scan_variable_definitions(tokens)
            else: raise Exception('This cannot happen')
            return True

        elif what == 'rules':
            tokens.require('\n')
            self.scan_rules(tokens)
            return True

        elif what == 'lexicon':
            tokens.require('\n')
            self.scan_lexicon(tokens)
            return True

        elif what == 'include':
            fn = tokens.require('word')
            tokens.require('\n')
            self.load(fn, dir)
            return True

        elif what == 'set':
            var = tokens.require('word')
            val = tokens.require('word')
            tokens.require('\n')
            self.grammar.setprop(var.lower(), val.lower())
            return True

        else:
            return False

    ##  Load a '.g' file.

    def load_g (self, fn):
        tokens = iter_tokens(fn, syntax=GrammarSyntax)
        self.scan_rules(tokens)
        if not tokens.has_next('eof'):
            tokens.warning('Expecting eof, unparsed material')

    ##  Load a '.lex' file.

    def load_lex (self, fn):
        tokens = iter_tokens(fn, syntax=GrammarSyntax)
        self.scan_lexicon(tokens)
        if not tokens.has_next('eof'):
            tokens.warning('Expecting eof, unparsed material')

    ##  Scan an atomset.

    def scan_atomset (self, tokens):
        return self.grammar.declarations.scan_atomset(tokens)
        
    ##  Scan a Category.

    def scan_category (self, tokens, symtab=None):
        if self.grammar.declarations:
            return self.grammar.declarations.scan_category(tokens, symtab)
        else:
            return scan_category(tokens, symtab)

    ##  Scan feature definitions.

    def scan_feature_definitions (self, tokens):
        while self.scan_feature_definition(tokens):
            pass

    ##  Scan one feature definition.

    def scan_feature_definition (self, toks):
        if toks.has_next('%'): return False
        name = toks.require('word')
        toks.require('=')
        value = self.scan_atomset(toks)
        dflt = value
        if toks.accept(string='default'):
            dflt = toks.require('word')
            if not subsumes(value, dflt):
                dflt.error('Bad default value')
        try:
            self.features.define(name, value, dflt)
        except Exception as e:
            name.error(e)
        toks.require('\n')
        return True

    ##  Scan category declarations.

    def scan_category_definitions (self, tokens):
        while self.scan_category_definition(tokens):
            pass

    ##  Scan one category declaration.

    def scan_category_definition (self, tokens):
        if not tokens.has_next('word'):
            return False
        name = next(tokens)
        tokens.require('[')
        params = []
        while not tokens.accept(']'):
            params.append(self.scan_parameter(tokens))
            tokens.accept(',')
        tokens.require('\n')
        try:
            self.categories.define(name, params)
        except Exception as e:
            name.error(e)
        return True

    ##  Scan one parameter.

    def scan_parameter (self, tokens):
        att = tokens.require('word')
        tokens.require(':')
        type = tokens.require('word')
        if type not in self.features:
            type.error('Undefined type: ' + type)
        type = self.features[type]
        return Parameter(att, type)

    ##  Scan variable declarations.

    def scan_variable_definitions (self, tokens):
        while self.scan_variable_definition(tokens):
            pass

    ##  Scan one variable declaration.

    def scan_variable_definition (self, tokens):
        if not tokens.has_next('word'): return False
        vbl = tokens.require('word')
        if vbl in self.variables: vbl.error('Attempt to redefine variable %s' % vbl)
        ftr = self.scan_atomset(tokens)
        self.variables[vbl] = ftr
        tokens.require('\n')
        return True

    ##  Scan rules.

    def scan_rules (self, tokens):
        while self.scan_rule(tokens):
            pass

    ##  Scan one rule.

    def scan_rule (self, tokens):
        if not tokens.has_next('word'): return False
        symtab = {}
        lhs = self.scan_category(tokens, symtab)
        tokens.require(string='->')
        rhs = []
        bindings = []
        while not (tokens.has_next('\n') or tokens.has_next(':')):
            rhs.append(self.scan_category(tokens, symtab))
        if tokens.accept(':'):
            sem = self.grammar.semantics.scan_rule(tokens, len(rhs))
        elif self.grammar.semantics.default_rule:
            sem = self.grammar.semantics.default_rule(len(rhs))
        else:
            sem = None
        tokens.require('\n')
        self.grammar.define(lhs, rhs, sem, symtab, tokens)
        return True

    ##  Scan the lexicon.

    def scan_lexicon (self, tokens):
        while self.scan_lexical_entry(tokens):
            pass

    ##  Scan one lexical entry.

    def scan_lexical_entry (self, tokens):
        if not tokens.has_next('word'): return False
        word = tokens.require('word')
        pos = self.scan_category(tokens)
        sem = None
        if tokens.accept(':'):
            sem = self.grammar.semantics.scan_lex(tokens)
        tokens.require('\n')
        self.lexicon.define(word, pos, sem, tokens)
        return True
