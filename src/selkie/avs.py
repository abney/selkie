##  @package seal.nlp.avs
#   Attribute-value structures.

from .io import Syntax, tokenize


##  Whether tracing is on.
TraceOn = False

##  Unification failure.

class Failure (Exception): pass


#--  AvsConstants  -------------------------------------------------------------

##  A constant.

class AvsConstant (object):
    ##  Constructor
    def __init__ (self, name):
        ##  Name.
        self.name = name
    ##  String representation.
    def __repr__ (self): return self.name


##  A constant; the most-general feature.
Top = AvsConstant('Top')
##  A constant; the inconsistent feature.
Bottom = AvsConstant('Bottom')


#--  AvPair  -------------------------------------------------------------------

##  An attribute-value pair.

class AvPair (object):

    ##  Constructor.

    def __init__ (self, att, value=Top):
        ##  The attribute.
        self.att = att
        ##  The value.
        self.value = value

    ##  String representation.

    def __repr__ (self):
        return '%s:%s' % (self.att, self.value)


#--  AvList  -------------------------------------------------------------------

##  A list of attribute-value pairs.

class AvList (list):

    ##  Constructor.

    def __init__ (self, avs):
        list.__init__(self)

        ##  The contents.
        self.avs = avs

    ##  Get the value for an attribute.  Error if not present.

    def getvalue (self, att):
        for pair in self:
            if pair.att == att: return pair.value
            elif pair.att > att: raise KeyError("Attribute not found: %s" % att)
        raise KeyError("Attribute not found: %s" % att)

    ##  Intern an attribute.  Attributes are kept in sort order.

    def intern (self, tgt):
        i = 0
        while i < len(self):
            att = self[i].att
            if att > tgt:
                break
            elif att == tgt:
                raise KeyError('Att already exists: %s' % tgt)
            i += 1
        pair = AvPair(tgt)
        self.insert(i, pair)
        return pair

    ##  Whether the given value is present in any feature.

    def contains (self, tgtvalue):
        for pair in self:
            if pair.value == tgtvalue:
                return True
        return False


#--  Avs  ----------------------------------------------------------------------

##  An attribute-value structure.

class Avs (list):

    ##  To assign unique IDs to AVSs.
    count = 0

    ##  Constructor.

    def __init__ (self):
        list.__init__(self)
        self.__import_table = {}

        ##  Unique ID.
        self.id = Avs.count

        Avs.count += 1

    ##  Whether this AVS can be modified.

    def is_mutable (self): return self.__import_table is not None

    ##  Freeze it: make it immutable.

    def freeze (self): self.__import_table = None


    #--  Hashing  --------------------------

    ##  Effectively treats it like a list of attributes and values.

    def __hash__ (self):
        return self.hash_atom(0)

    ##  Compute the hash value for a single atom.

    def hash_atom (self, atom):
        if isinstance(atom, str):
            return hash(atom)
        elif isinstance(atom, int):
            v, value = self.deref(atom)
            if isinstance(v, str):
                return hash(v)
            elif isinstance(value, AvsConstant):
                return hash(value.name)
            elif isinstance(value, AvList):
                return self.hash_avlist(value)
            else:
                raise Exception('Bad variable value: %s' % value)
        else:
            raise Exception('Bad atom: %s' % atom)

    ##  Compute the hash for an attribute-value list.

    def hash_avlist (self, lst):
        out = 0
        for pair in lst:
            out ^= hash(pair.att)
            out ^= self.hash_atom(pair.value)
        return out

    ##  Comparison.

    def __lt__ (self, other):
        return self.cmp(other) < 0

    ##  Comparison.

    def __eq__ (self, other):
        return self.cmp(other) == 0

    ##  Comparison.

    def cmp (self, other):
        if isinstance(other, avs):
            return self.cmp_atoms(0, other, 0)
        else:
            return self.cmp_atoms(0, self, other)

    ##  Compare atoms.

    def cmp_atoms (self, atom, other_avs, other_atom):
        atom1, value1 = self.deref(atom)
        atom2, value2 = other_avs.deref(other_atom)
        if isinstance(atom1, str):
            if isinstance(atom2, str):
                if atom1 < atom2: return -1
                elif atom1 > atom2: return 1
                else: return 0
            else:
                return -1
        elif isinstance(atom2, str):
            return 1
        else:
            assert isinstance(atom1, int)
            assert isinstance(atom2, int)
            return self.cmp_values(value1, value2)

    ##  Compare values.

    def cmp_values (self, value1, value2):
        if value1 is Top:
            if value2 is Top: return 0
            else: return -1
        elif value2 is Top:
            return 1
        else:
            assert isinstance(value1, AvList)
            assert isinstance(value2, AvList)
            i = 0
            while True:
                if i >= len(value1):
                    if i >= len(value2): return 0
                    else: return -1
                if i >= len(value2): return 1
                att1 = value1[i].att
                att2 = value2[i].att
                if att1 < att2: return -1
                elif att1 > att2: return 1
                else:
                    val1 = value1[i].value
                    val2 = value2[i].value
                    if val1 < val2: return -1
                    elif val1 > val2: return 1
                    else:
                        i += 1
            

    #--  Printing  -------------------------

    def __value_string (self, value):
        if isinstance(value, AvList) and value.avs is not self:
            return '%d:%s' % (value.avs.id, str(value))
        else:
            return str(value)

    ##  Raw version for printing.

    def raw (self):
        lines = ['AVS %d:' % self.id]
        for i, value in enumerate(self):
            lines.append('    %d -> %s' % (i, self.__value_string(value)))
        return '\n'.join(lines)

    ##  String representation.

    def __str__ (self):
        return self.__pprint(flat=False)

    ##  String representation.

    def __repr__ (self):
        return self.__pprint(flat=True)

    def __pprint (self, flat=False):
        pathto = {}
        out = []
        self.__pprint_variable(0, 1, [], pathto, flat, out)
        return ''.join(out)

    def __pprint_variable (self, v, indent, path, pathto, flat, out, forceprint=False):
        v, value = self.deref(v)
        if isinstance(v, str):
            out.append(value)
        elif (not forceprint) and (id(self),v) in pathto:
            out.append('= ')
            out.append(pathto[id(self),v])
        elif value is Top:
            out.append('[]')
        elif isinstance(value, AvList):
            value.avs.__pprint_avlist(value, indent, path, pathto, flat, out)
        else:
            out.append('**BAD_VAR_VALUE(%d,%s)**' % (v, value))

    def __pprint_avlist(self, value, indent, path, pathto, flat, out):
        out.append('[')
        first = True
        for pair in value:
            att = pair.att
            value = pair.value
            if first: first = False
            elif flat: out.append('; ')
            else: out.append('\n' + ' ' * indent)
            out.append(att)
            out.append(' ')
            if isinstance(value, str):
                out.append(value)
            elif isinstance(value, AvsConstant):
                out.append(value.name)
            elif isinstance(value, int):
                path.append(att)
                forceprint = False
                key = (id(self), value)
                if key not in pathto:
                    pathto[key] = '.'.join(path)
                    forceprint = True
                newindent = indent + len(att) + 2
                self.__pprint_variable(value, newindent, path, pathto, flat, out,
                                       forceprint=forceprint)
                path.pop()
            else:
                out.append('**BAD_ATT_VALUE(%s)**' % str(value))
        out.append(']')


    #--  Follow path  ----------------------

    ##  Returns a string or a Variable rooted here.

    def follow_path (self, path):
        return self.__follow_path(path, 0)

    def __follow_path (self, path, i):
        v, value = self.deref(0)
        while i < len(path):
            if not isinstance(value, AvList):
                raise Exception("Bad path: %s" % path)
            if value.avs is not self:
                return value.avs.__follow_path(path, i)
            v = value.getvalue(path[i])
            v, value = self.deref(v)
            i += 1
        if isinstance(v, str): return v
        else: return Variable(self, v)


    #--  Import  ---------------------------

    ##  Follow a path and import the atom.

    def import_path_target (self, avs, path):
        atom = avs.follow_path(path)
        if TraceOn: print('path %s -> %s' % (path, var))
        return self.import_atom(atom)

    ##  Import an atom.

    def import_atom (self, atom):
        if isinstance(atom, str): return atom
        elif isinstance(atom, int): return atom
        elif isinstance(atom, Variable): return self.import_variable(atom.avs, atom.v)
        elif isinstance(atom, Avs): return self.import_variable(atom, 0)
        else: raise Exception('Bad atom: %s' % atom)

    ##  May return a variable (int) or a constant (string).

    def import_variable (self, avs, u, import_value=False):
        u, value = avs.deref(u)
        if isinstance(u, str): return u
        if avs is self:
            assert not import_value
            return u

        key = (id(avs), u)
        if key in self.__import_table:
            v = self.__import_table[key]
            if import_value:
                if isinstance(value, AvList) and value.avs is not self:
                    self[v] = -1
                    self[v] = self.import_avlist(value)
        else:
            v = len(self)
            self.__import_table[key] = v
            self.append(Top)

            if import_value:
                value = self.import_avlist(value)
            self[v] = value

            if TraceOn:
                print('%d.%d' % (avs.id, u), '->', v)
                print(v, '->', self.__value_string(value))

            for p in avs.parents(u):
                self.import_variable(avs, p, import_value=True)

        return v

    ##  Import an attribute-value list.

    def import_avlist (self, lst):
        avs = lst.avs
        if avs is self: return lst
        out = AvList(self)
        for pair in lst:
            value = pair.value
            if isinstance(value, int):
                value = self.import_variable(avs, value)
            out.append(AvPair(pair.att, value))
        return out

    ##  Parents.

    def parents (self, v):
        out = []
        for u, value in enumerate(self):
            if isinstance(value, AvList) and value.contains(v):
                out.append(u)
        return out


    #--  Deref  ----------------------------

    ##  Returns (v,avlist) or (v,Top) or (str,str).

    def deref (self, v):
        if isinstance(v, str): return v, v
        elif not isinstance(v, int):
            raise Exception('Must be constant or variable: %s' % v)
        while True:
            value = self[v]
            if isinstance(value, str):
                return value, value
            elif isinstance(value, int):
                if value < 0: raise Failure
                v = value
            else:
                return v, value


    #--  Unification  ----------------------
    
    ##  Called for side effect.  x and y are imported into self.

    def unify (self, x, y):
        assert self.is_mutable()
        atom1 = self.import_atom(x)
        atom2 = self.import_atom(y)
        self.unify_atoms(atom1, atom2)
        self.pack()
        self.freeze()

    ##  Atom may be constant, local variable, or Top.

    def unify_atoms (self, atom1, atom2):
        orig1 = atom1
        orig2 = atom2
        atom1, value1 = self.deref(atom1)
        atom2, value2 = self.deref(atom2)

        if TraceOn: print('unify atoms', orig1, '->', atom1, ';', orig2, '->', atom2)

        if atom1 is atom2:
            return atom1
        elif value1 is Top:
            self[atom1] = atom2
            if TraceOn: print('%d -> %s' % (atom1, atom2))
            return atom2
        elif value2 is Top:
            self[atom2] = atom1
            if TraceOn: print('%d -> %s' % (atom2, atom1))
            return atom1
        elif isinstance(atom1, str) or isinstance(atom2, str):
            raise Failure
        else:
            self[atom2] = atom1
            self[atom1] = -1
            if TraceOn:
                print('%d -> %s' % (atom2, atom1))
                print('%d -> -1' % atom1)
            value = self.unify_lists(value1, value2)
            self[atom1] = value
            if TraceOn: print('%d -> %s' % (atom1, value))
            return atom1

    ##  Unify two lists.

    def unify_lists (self, list1, list2):

        if TraceOn: print('unify_lists', self.__value_string(list1), self.__value_string(list2))

        list1 = self.import_avlist(list1)
        list2 = self.import_avlist(list2)
        output = AvList(self)
        i = 0
        j = 0
        while i < len(list1) and j < len(list2):
            pair1 = list1[i]
            pair2 = list2[j]
            if pair1.att < pair2.att:
                output.append(pair1)
                i += 1
            elif pair1.att > pair2.att:
                output.append(pair2)
                j += 1
            else:
                value = self.unify_atoms(pair1.value, pair2.value)
                output.append(AvPair(pair1.att, value))
                i += 1
                j += 1
        while i < len(list1):
            output.append(list1[i])
            i += 1
        while j < len(list2):
            output.append(list2[j])
            j += 1
        return output


    #--  Pack  --------------------------------------

    def __newvars (self):
        output = [-1 for i in range(len(self))]
        todo = [0]
        n = 0
        while todo:
            v = todo.pop()
            if output[v] != -1: continue
            v2, value = self.deref(v)
            if isinstance(v2, int):
                if output[v2] == -1:
                    output[v2] = n
                    output[v] = n
                    n += 1
                    if isinstance(value, AvList) and value.avs is self:
                        for pair in value:
                            if isinstance(pair.value, int):
                                todo.append(pair.value)
                else:
                    output[v] = output[v2]
            else:
                output[v] = v2
        return n, output

    ##  Pack.

    def pack (self):
        if TraceOn:
            print('Before packing:')
            print(self.raw())
        nnew, newvars = self.__newvars()
        if nnew < len(self):
            for o in range(len(self)):
                n = newvars[o]
                if n != -1 and isinstance(n, int):
                    value = self[o]
                    if isinstance(value, int):
                        value = newvars[value]
                    elif isinstance(value, AvList) and value.avs is self:
                        value = self.__renumber_vars(value, newvars)
                    self[n] = value
            del self[nnew:]
        if TraceOn:
            print('After packing:')
            print(self.raw())

    def __renumber_vars (self, avlist, newvars):
        output = AvList(self)
        for i in range(len(avlist)):
            pair = avlist[i]
            if isinstance(pair.value, int):
                output.append(AvPair(pair.att, newvars[pair.value]))
            else:
                output.append(pair)
        return output


    #--  Constant equations  ---------------

    ##  Constant equations.

    def constant_equations (self, atom=0):
        out = []
        self.__collect_constant_equations(atom, [], out)
        return out

    def __collect_constant_equations (self, atom, path, out):
        if isinstance(atom, str):
            out.append(tuple(path + [atom]))
        elif isinstance(atom, int):
            v, value = self.deref(atom)
            if isinstance(value, str):
                out.append(tuple(path + [value]))
            elif isinstance(value, AvList):
                for pair in value:
                    self.__collect_constant_equations(pair.value, path + [pair.att], out)


#--  Unify  --------------------------------------------------------------------

##  Unify two AVSs.  This is non-destructive.

def unify (x, y, trace=False):
    global TraceOn
    if trace: TraceOn = True
    if TraceOn:
        print('----------------------------------------')
    try:
        if x is Top: out = y
        elif y is Top: out = x
        else:
            out = Avs()
            out.unify(x, y)
    except Failure:
        out = Bottom
        if TraceOn:
            print('FAILURE')
    if TraceOn:
        print(repr(out))
        print('----------------------------------------')
    return out


#--  AvState  ------------------------------------------------------------------

##  An AV state.

class AvState (object):

    ##  Constructor.

    def __init__ (self, avs, targets, i=1):

        ##  The AVS.
        self.avs = avs

        ##  Targets.
        self.targets = targets

        ##  Index.
        self.i = i
        assert not self.targets[0]

    ##  Avs representing type of i-th child.

    def __getitem__ (self, i):
        if self.targets[i] is None:
            return Top
        elif self.avs is Top:
            assert self.targets[i] == []
            return Top
        else:
            return self.avs.follow_path(self.targets[i])

    ##  Match.  Returns an AvState.

    def match (self, parentsem):
        if parentsem is Top:
            return self
        elif self.avs is Top:
            return AvState(parentsem, self.targets, self.i)
        elif isinstance(self.avs, str):
            if self.avs == parentsem: return self
            else: return Bottom
        else:
            avs = Avs()
            v = avs.import_atom(self.avs)
            assert v == 0
            avs.unify(0, parentsem)
            return AvState(avs, self.targets, self.i)

    ##  Extend.  Returns an AvState.

    def extend (self, other):
        path = self.targets[self.i]
        if path is None:
            avs = self.avs
        elif other is None:
            return None
        else:
            avs = Avs()
            v = avs.import_atom(self.avs)
            assert v == 0
            atom1 = self.avs.follow_path(path)
            avs.unify(atom1, other)
        return AvState(avs, self.targets, self.i+1)

    ##  Execute it on a list of child semantic representations.

    def __call__ (self, childsems):
        q = self
        for sem in childsems:
            q = q.extend(sem)
            if q is None: return None
        if q.i < len(q.targets):
            raise Exception('Wrong number of children')
        return q.avs

    ##  String representation.

    def __repr__ (self):
        words = ['(AvState']
        for i, path in enumerate(self.targets):
            if i == self.i: words.append('*')
            path = self.targets[i]
            if path is None: words.append('-')
            elif not path: words.append('.')
            else: words.append('.'.join(path))
        words.append(':')
        words.append(repr(self.avs) + ')')
        return ' '.join(words)


##  A copier.

class Copier (object):

    ##  Constructor.

    def __init__ (self, nchildren, i=1, avs=Top):
        assert i <= nchildren + 1

        ##  Number of children.
        self.nchildren = nchildren
        ##  Position.
        self.i = i
        ##  AVS.
        self.avs = avs

    ##  String representation.

    def __repr__ (self):
        rhs = ['X'] * self.nchildren
        i = self.i - 1
        rhs[i:i] = ['*']
        return '(Copier %s : %s)' % (' '.join(rhs), repr(self.avs))

    ##  Fetch the i-th AVS.

    def __getitem__ (self, i):
        if i == self.i:
            return self.avs
        else:
            return Top

    ##  Add a new child semantics.

    def extend (self, childsem):
        if self.i == self.nchildren - 1:
            avs = childsem
        else:
            avs = self.avs
        return Copier(self.nchildren, self.i + 1, avs=avs)

    ##  Reduce.

    def reduce (self, childsems):
        last = None
        for sem in childsems:
            last = sem
        return last

    ##  Match.

    def match (self, parentsem):
        assert self.avs is Top
        assert self.i == 1
        return Copier(self.nchildren, self.i, avs=parentsem)


#--  Variable  -----------------------------------------------------------------

##  A variable.

class Variable (object):

    ##  Constructor.

    def __init__ (self, avs, v):
        ##  The AVS.
        self.avs = avs
        ##  Variable number.
        self.v = v

    ##  Its value.

    def value (self):
        v, value = self.avs.deref(self.v)
        return value

    ##  Constant equations.

    def constant_equations (self):
        return self.avs.constant_equations(self.v)

    ##  String representation.

    def __repr__ (self):
        return '%d.%d' % (self.avs.id, self.v)


#--  Scan  ---------------------------------------------------------------------

##  Syntax for reading AVSs.
AvsSyntax = Syntax('[;.=$]', eol=True)

##  Parse an AVS.

def parse_avs (s):
    scanner = Scanner(tokenize(s))
    return scanner.scan_avs()

##  Scan from a stream.

def scan_avs (stream):
    return Scanner(stream).scan_avs()

##  Parse an AV state.

def parse_avstate (s, nchildren):
    scanner = Scanner(tokenize(s))
    return scanner.scan_avstate(nchildren)

##  Scan from a stream.

def scan_avstate (stream, nchildren):
    return Scanner(stream).scan_avstate(nchildren)


##  The scanner.

class Scanner (object):

    ##  Constructor.

    def __init__ (self, input):
        ##  The input stream.
        self.input = input
        ##  The AVS.
        self.avs = None
        ##  Targets.
        self.targets = None

    ##  Scan an AV state.

    def scan_avstate (self, nchildren):
        self.targets = [None for i in range(nchildren+1)]
        self.targets[0] = []
        avs = self.scan_avs()
        if isinstance(avs, str):
            return avs
        else:
            return AvState(avs, self.targets)

    ##  Scan an AVS.

    def scan_avs (self):
        self.input.push_syntax(AvsSyntax)
        try:
            self.avs = Avs()
            pair = AvPair(Top)
            self.scan_value(pair, [])
            if isinstance(pair.value, str):
                return pair.value
            else:
                return self.avs
        finally:
            self.input.pop_syntax()

    ##  Scan an AV list.

    def scan_avlist (self, pair, path):
        self.input.require('[')
        v = len(self.avs)
        pair.value = v
        if self.input.accept(']'):
            self.avs.append(Top)
        else:
            lst = AvList(self.avs)
            self.avs.append(lst)
            while not self.input.accept(']'):
                self.input.accept(';')
                att = self.input.require('word')
                pair = lst.intern(att)
                self.scan_value(pair, path + [att])

    ##  Scan a value.

    def scan_value (self, pair, path):
        while True:
            if self.input.has_next('='):
                self.scan_reentrancy(pair)
            elif self.input.has_next('['):
                self.scan_avlist(pair, path)
            elif self.input.accept('$'):
                self.scan_dollar_variable(path)
                continue
            elif self.input.has_next('word'):
                pair.value = next(self.input)
            else:
                v = len(self.avs)
                self.avs.append(Top)
                pair.value = v
            break

    ##  Scan a reentrancy.

    def scan_reentrancy (self, pair):
        self.input.require('=')
        path = [self.input.require('word')]
        while self.input.accept('.'):
            path.append(self.input.require('word'))
        var = self.avs.follow_path(path)
        if var.avs is not self.avs:
            raise Exception('Reentrancy path leads out of avs: %s' % path)
        pair.value = var.v

    ##  Scan a dollar variable.

    def scan_dollar_variable (self, path):
        if self.targets is None:
            raise Exception('No targets vector provided')
        s = self.input.require('word')
        if not s.isdigit():
            s.error('Expecting an integer: %s' % s)
        i = int(s)
        if i < 0 or i >= len(self.targets):
            s.error('Illegal variable: $%d' % i)
        if self.targets[i] is not None:
            s.error('Variable appears multiple times: $%d' % i)
        self.targets[i] = tuple(path)
        return i
