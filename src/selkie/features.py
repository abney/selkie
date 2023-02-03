##  \package seal.nlp.features
#   Features for a feature grammar.

from .io import iter_tokens, Syntax, outfile


##  The category type, sans features.  The input may be a Category or a string.
#   The output is a string.

def basecat (c):
    if isinstance(c, str): return c
    elif isinstance(c, Category): return c[0]
    else: raise Exception('Not a category: %s' % repr(c))

##  The number of features in the given category.  If it is a Category,
#   the value is one less than its length.  If it is a string, the value is 0.

def arity (c):
    if isinstance(c, str): return 0
    elif isinstance(c, Category): return len(c) - 1
    else: raise Exception('Not a category: %s' % repr(c))

##  Whether a word represents a variable.

def is_variable (s):
    return s.startswith('_')


#--  AtomSets  -----------------------------------------------------------------

##  A set of atoms.  (This is provided in lieu of using the AtomSet constructor,
#   because it is not possible to override tuple.__init__().)

def atomset (items):
    if not items: return None
    elif len(items) == 1: return items[0]
    else: return AtomSet(sorted(items))

##  A set of atoms.

class AtomSet (tuple):
    
    ##  Multiplication represents intersection.

    def __mul__ (self, other):
        if other is None:
            return None
        elif isinstance(other, AtomSet):
            inter = []
            i = 0
            j = 0
            while i < len(self) and j < len(other):
                if self[i] < other[j]: i += 1
                elif self[i] > other[j]: j += 1
                else:
                    inter.append(self[i])
                    i += 1
                    j += 1
            if inter:
                if len(inter) == 1: return inter[0]
                else: return AtomSet(inter)
            else:
                return None
        elif other == '*':
            return other
        elif other in self:
            return other
        else:
            return None

    ##  Addition represents union.

    def __add__ (self, other):
        if isinstance(other, AtomSet):
            union = []
            i = 0
            j = 0
            while i < len(self) and j < len(other):
                if self[i] < other[j]:
                    union.append(self[i])
                    i += 1
                elif self[i] > other[j]:
                    union.append(other[j])
                    j += 1
                else:
                    union.append(self[i])
                    i += 1
                    j += 1
            # at most one will apply
            if i < len(self): union.extend(self[i:])
            if j < len(other): union.extend(other[j:])
            if len(union) == 1: return union[0]
            else: return AtomSet(union)
        elif other == '*':
            return '*'
        elif other is None:
            return self
        else:
            union = []
            i = 0
            while i < len(self):
                if self[i] < other:
                    union.append(self[i])
                    i += 1
                elif self[i] == other:
                    i += 1
                    break
                else:
                    break
            union.append(other)
            if i < len(self): union.extend(self[i:])
            return AtomSet(union)

    ##  String representation.

    def __repr__ (self):
        return '/'.join(self)


### Categories -----------------------------------------------------------------

##  A category, which is a type and a list of features.

class Category (tuple):

    ##  Constructor.

    def __repr__ (self):
        f = outfile()
        write_category(self, f)
        return f.getvalue()

##  C is a convenience function that takes a string, tuple, or list, and 
#   returns a Category.

def C (x):
    if isinstance(x, Category):
        return x
    elif isinstance(x, str):
        return Category([x])
    elif isinstance(x, (list, tuple)):
        return Category(x)
    else:
        raise Exception('Cannot be coerced to a category: %s' % x)

##  Convert a value to a string.  Variables print out preceded by '_'.  Constants
#   print as themselves.

def value_string (val):
    if isinstance(val, int):
        return '_' + str(val)
    else:
        return str(val)

# def parse_category (s, symtab=None):
#     return Category(parse_value(elt, symtab) for elt in s.split('.'))
# 
# def parse_value (s, symtab=None):
#     if s.startswith('$'):
#         if symtab is None: raise Exception, "Variables not allowed"
#         sym = s[1:]
#         if sym in symtab:
#             return symtab[sym]
#         else:
#             ftr = len(symtab)
#             symtab[sym] = ftr
#             return ftr
#     elif s == '/':
#         return s
#     elif '/' in s:
#         return atomset(s.split('/'))
#     else:
#         return s


### Unification ----------------------------------------------------------------

##  Intersect two atomsets or wildcards.

def meet (v1, v2):
    if v1 is None or v2 is None: return None
    elif v1 == '*': return v2
    elif v2 == '*': return v1
    elif v1 == v2: return v1
    elif isinstance(v1, AtomSet): return v1 * v2
    elif isinstance(v2, AtomSet): return v2 * v1
    else: return None

##  Unify two categories.  The output is a new set of bindings, or None on failure.
#   The y category must not contain variables.

def unify (x, y, bindings):
    if x[0] != y[0]: return None
    if len(x) != len(y):
        raise Exception('Categories not conformal: %s %s' % (x, y))
    bindings = bindings[:]
    for i in range(len(x)):
        v1 = x[i]
        v2 = y[i]
        assert not isinstance(v2, int)
        if isinstance(v1, int):
            value = meet(bindings[v1], v2)
            if not value: return None
            bindings[v1] = value
        elif not meet(v1, v2): return None
    return bindings

##  Returns a new variable-free Category in which the bindings have been
#   substituted into the input category.

def subst (bindings, cat):
    out = [cat[0]]
    for val in cat[1:]:
        if isinstance(val, int):
            out.append(bindings[val])
        else:
            out.append(val)
    return Category(out)


#--  join, subsume  ------------------------------------------------------------

##  Join two values.

def join (v1, v2):
    if v1 is None: return v2
    elif v2 is None: return v1
    elif v1 == '*' or v2 == '*': return '*'
    elif isinstance(v1, AtomSet): return v1 + v2
    elif isinstance(v2, AtomSet): return v2 + v1
    elif v1 == v2: return v1
    else: return atomset([v1,v2])

##  V1 subsumes v2 if their meet equals v2.
#   Viewing categories as sets of atoms, subsumption is superset.

def subsumes (v1, v2):
    return meet(v1,v2) == v2


#--  Feature Table  ------------------------------------------------------------

##  A feature definition, which is an entry in a feature table.

class Feature (object):

    ##  Constructor.

    def __init__ (self, name, value, dflt=None):
        if dflt is None: dflt = value

        ##  The feature name.
        self.name = name

        ##  If this is a synonym for another feature, this is the name of
        #   the other feature.  Otherwise it is the same as name.
        self.value = value

        ##  The default value.
        self.dflt = dflt

    ##  Comparison is by name.

    def __lt__ (self, other):
        return self.name < other.name

    ##  Comparison is by name.

    def __eq__ (self, other):
        return self.name == other.name

    ##  String representation.

    def __repr__ (self):
        return '<Feature %s %s %s>' % (self.name, self.value, self.dflt)


##  A table containing feature declarations.

class FeatureTable (dict):

    ##  Intern a feature by name.

    def intern (self, name):
        if name in self:
            return self[name].value
        else:
            value = name
            self[name] = Feature(name, value)
            return value

    ##  Define a feature.  Signals an error if the given name already has
    #   an entry.

    def define (self, name, value, dflt=None):
        if name in self:
            raise Exception('Duplicate feature definition: ' + name)
        self[name] = Feature(name, value, dflt)

    ##  Listing of entries.

    def __str__ (self):
        lines = ['Features:']
        for ftr in sorted(self.values()):
            lines.append('    ' + repr(ftr))
        return '\n'.join(lines)


#--  CategoryTable  ------------------------------------------------------------

##  A parameter in a category definition.

class Parameter (object):

    ##  Constructor.

    def __init__ (self, name, type):

        ##  Parameter name.
        self.name = name

        ##  Parameter type.
        self.type = type

    ##  String representation.

    def __repr__ (self):
        return '%s:%s' % (self.name, self.type.name)


##  A table containing category declarations.

class CategoryTable (dict):

    ##  An entry in the table.

    class Entry (object):

        ##  Constructor.

        def __init__ (self, name, params):

            ##  The category name.
            self.name = name

            ##  A tuple of parameters.
            self.params = params

        ##  Comparison is by category name.

        def __lt__ (self, other):
            return self.name < other.name

        ##  Comparison is by category name.

        def __eq__ (self, other):
            return self.name == other.name

        ##  The position for the given parameter name.
        #   Searches through the parameter list.

        def index (self, att):
            if not att: raise Exception('Attempt to get index for empty att')
            for i in range(len(self.params)):
                if self.params[i].name == att:
                    return i
            return -1

        ##  String representation.

        def __repr__ (self):
            return '<Entry %s[%s]>' % \
                (self.name, ','.join(repr(param) for param in self.params))

    ##  Define a new category.  An error is signalled if there is already
    #   a definition for the given name.

    def define (self, name, params=()):
        if name in self:
            raise Exception('Duplicate category definition: ' + name)
        self[name] = CategoryTable.Entry(name, params)

    ##  Content listing as a string.

    def __str__ (self):
        lines = ['Categories:']
        for cat in sorted(self.values()):
            lines.append('    ' + repr(cat))
        return '\n'.join(lines)


#--  Scanning  -----------------------------------------------------------------

##  The syntax of a category.

CategorySyntax = Syntax('[:,/]')

def __scan_atomset (tokens, first=None):
    if first is None: value = tokens.require('word')
    else: value = first
    while tokens.accept('/'):
        value = join(value, tokens.require('word'))
    return value

##  Intern a variable in the given symbol table.

def intern_variable (var, symtab):
    if var in symtab:
        n = symtab[var]
    else:
        n = len(symtab)
        symtab[var] = n
    return n

##  Scan a category from a token list.

def scan_category (tokens, symtab=None):
    tokens.push_syntax(CategorySyntax)
    values = [tokens.require('word')]
    if tokens.accept('['):
        while not tokens.accept(']'):
            first = tokens.require('word')
            if tokens.has_next(':'):
                first.error('No declarations: keyword parameters are not allowed')
            if is_variable(first[0]):
                value = intern_variable(first, symtab)
            else:
                value = __scan_atomset(tokens, first)
            values.append(value)
            tokens.accept(',')
    tokens.pop_syntax()
    return Category(values)

def __unscan_atomset (aset, out):
    first = True
    for atom in aset:
        if first: first = False
        else: out.write('/')
        out.write(CategorySyntax.scanable_string(atom))

def __unscan_variable (variables, i, out):
    if variables:
        if i < 0 or i >= len(variables):
            raise Exception("Bad variable: %d" % i)
        out.write(variables[i])
    else:
        out.write('_')
        out.write(str(i))

##  Write a category.

def write_category (cat, out, variables=None):
    out.write(CategorySyntax.scanable_string(cat[0]))
    if len(cat) > 1:
        out.write('[')
        for i in range(1, len(cat)):
            if i > 1: out.write(',')
            value = cat[i]
            if isinstance(value, int):
                __unscan_variable(variables, value, out)
            elif isinstance(value, AtomSet):
                __unscan_atomset(value, out)
            else:
                out.write(CategorySyntax.scanable_string(value))
        out.write(']')


#--  Declarations  -------------------------------------------------------------

##  A set of grammar declarations.

class Declarations (object):

    ##  Constructor.

    def __init__ (self, features=None, categories=None, variables=None):
        if features is None: features = FeatureTable()
        if categories is None: categories = CategoryTable()
        if variables is None: variables = {}

        ##  A FeatureTable.
        self.features = features

        ##  A CategoryTable.
        self.categories = categories

        ##  A dict.
        self.variables = variables

    ##  Content listing as a string.

    def __str__ (self):
        return str(self.features) + '\n\n' + str(self.categories)

    def __scan_value (self, tokens):
        return self.features.intern(tokens.require('word'))

    def __scan_atomset (self, tokens, first=None):
        if first is None: value = self.__scan_value(tokens)
        else: value = first
        while tokens.accept('/'):
            value = join(value, self.__scan_value(tokens))
        return value

    ##  Scan an atomset.

    def scan_atomset (self, tokens):
        tokens.push_syntax(CategorySyntax)
        aset = self.__scan_atomset(tokens)
        tokens.pop_syntax()
        return aset

    ##  Scan a category.

    def scan_category (self, tokens, symtab=None):
        tokens.push_syntax(CategorySyntax)
        name = tokens.require('word')
        if name not in self.categories:
            name.error('Unrecognized category: ' + name)
        entry = self.categories[name]
        params = entry.params
        values = [param.type.dflt for param in params]
        if tokens.accept('['):
            doing_kwargs = False
            i = 0
            while not tokens.accept(']'):
                first = tokens.require('word')
                if tokens.accept(':'):
                    doing_kwargs = True
                    i = entry.index(first)
                    if i < 0:
                        first.error('%s: feature not in parameter list: %s' % (name, first))
                    first = tokens.require('word')
                elif doing_kwargs:
                    first.error('%s: positional argument %s following keyword args' % (name, first))
                elif i >= len(params):
                    first.error('%s: too many features provided' % name)
                if is_variable(first[0]):
                    value = intern_variable(first, symtab)
                else:
                    value = self.__scan_atomset(tokens, first)
                    if not subsumes(params[i].type.value, value):
                        first.error('%s: value %s not subsumed by parameter type %s'
                                    % (name, repr(value), repr(params[i].type.value)))
                values[i] = value
                i += 1
                tokens.accept(',')
        tokens.pop_syntax()
        return Category([name] + values)

    ##  Unscan a category.

    def write_category (self, cat, out):
        write_category(cat, out)
