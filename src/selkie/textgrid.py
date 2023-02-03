##  \package seal.nlp.textgrid
#   A structured representation of a Praat text grid.

from numpy import empty


##  Symbol table.

class SymbolTable (dict):

    ##  Return the variable number associated with the given variable name.
    #   If no entry already exists, take the next number and add it to the
    #   the table.  "The next number" is the current size of the table.

    def intern (self, s):
        if s in self:
            return self[s]
        else:
            n = len(self)
            self[s] = n
            return n


##  A buffered input stream.

class BufferedLines (object):

    ##  Constructor.

    def __init__ (self, fn, **kwargs):
        
        ##  Input stream.
        self.stream = open(fn, **kwargs)

        ##  Lookahead.
        self.la = None

    ##  The next line of input.

    def shift (self):
        if self.la is None:
            if self.stream is None:
                return None
            else:
                try:
                    line = next(self.stream)
                    return line.rstrip(' \r\n')
                except StopIteration:
                    self.stream.close()
                    self.stream = None
                    return None
        else:
            line = self.la
            self.la = None
            return line

    ##  Push a line back.

    def unshift (self, line):
        if self.la is None:
            self.la = line
        else:
            raise Exception('Double pushback')


##  Text grid.

class TextGrid (object):

    ##  Constructor.

    def __init__ (self, fn=None, **kwargs):

        ##  The starting x value.
        self.xmin = None

        ##  The ending x value.
        self.xmax = None

        ##  A list of tiers.
        self.tiers = []

        if fn: self.load(fn, **kwargs)

    ##  String representation.

    def __repr__ (self):
        return '<TextGrid %g:%g %s>' % (self.xmin, self.xmax, ' '.join(t.name for t in self.tiers))

    ##  Load from file.

    def load (self, fn, **kwargs):
        f = BufferedLines(fn, **kwargs)
        self.read(f)

    ##  Save to file.

    def save (self, fn):
        with open(fn, 'w') as f:
            self.write(f)

    ##  Read from a buffered input stream.

    def read (self, f):
        assert f.shift() == 'File type = "ooTextFile"'
        assert f.shift() == 'Object class = "TextGrid"'
        assert f.shift() == ''
    
        fields = f.shift().split()
        assert fields[0] == 'xmin' and fields[1] == '='
        self.xmin = float(fields[2])
    
        fields = f.shift().split()
        assert fields[0] == 'xmax' and fields[1] == '='
        self.xmax = float(fields[2])
    
        assert f.shift() == 'tiers? <exists>'
    
        fields = f.shift().split()
        assert fields[0] == 'size' and fields[1] == '='
        ntiers = int(fields[2])
    
        assert f.shift() == 'item []:'

        self.tiers = [Tier() for i in range(ntiers)]
        for (i,tier) in enumerate(self.tiers):
            assert f.shift() == '    item [%d]:' % (i+1)
            tier.read(f)

    ##  Write to an output stream.

    def write (self, f):
        f.write('File type = "ooTextFile"\n')
        f.write('Object class = "TextGrid"\n')
        f.write('\n')
        f.write('xmin = %g\n' % self.xmin)
        f.write('xmax = %g\n' % self.xmax)
        f.write('tiers? <exists>\n')
        f.write('size = %d\n' % len(self.tiers))
        f.write('item []:\n')
        for (i,tier) in enumerate(self.tiers):
            f.write('    item [%d]:\n' % (i+1))
            tier.write(f)

    ##  The number of tiers.

    def __len__ (self):
        return len(self.tiers)

    ##  The i-th tier.

    def __getitem__ (self, i):
        if isinstance(i, int):
            return self.tiers[i]
        elif isinstance(i, tuple):
            if not len(i) == 2:
                raise KeyError('Expected one or two indices')
            return self.tiers[i[0]][i[1]]
        else:
            raise KeyError('Bad index: %s' % i)

    def __setitem__ (self, i, tier):
        self.tiers[i] = tier

    ##  Add a tier.

    def add_tier (self, type, name):
        tier = Tier(type, name, self.xmin, self.xmax)
        self.tiers.append(tier)
        return tier
    
    ##  Duplicate it.

    def clone (self):
        grid = TextGrid()
        grid.xmin = self.xmin
        grid.xmax = self.xmax
        grid.tiers = self.tiers[:]
        return grid
        

##  A tier.

class Tier (object):

    ##  Constructor.

    def __init__ (self, type=None, name=None, xmin=None, xmax=None):

        ##  The tier type.  Legal values are 'IntervalTier' and 'TextTier'.
        self.type = None

        ##  The data type, either Interval or Point.
        self.dtype = None

        ##  Either 'intervals' or 'points'.
        self.aname = None

        ##  The name of the tier.
        self.name = name

        ##  Initial x value.
        self.xmin = xmin

        ##  Final x value.
        self.xmax = xmax

        ##  Contents, a list of dtype objects.
        self.contents = []

        ##  Symbol table.
        self.symtab = None

        if type is not None: self.set_type(type)

    ##  String representation.

    def __repr__ (self):
        if len(self.contents) > 6:
            s = '%s %s %s ... %s %s %s' % tuple(self.contents[i].string() for i in (0,1,2,-3,-2,-1))
        else:
            s = ' '.join(elt.string() for elt in self.contents)
        if self.type == 'IntervalTier':
            t = 'I'
        elif self.type == 'TextTier':
            t = 'P'
        else:
            t = '_'
        return '<Tier %s %s %s>' % (self.name, t, s)

    ##  Set the type.  The argument must be 'IntervalTier' or 'TextTier'.

    def set_type (self, type):
        assert self.type is None
        self.type = type
        if type == 'IntervalTier':
            self.dtype = Interval
            self.aname = 'intervals'
        elif type == 'TextTier':
            self.dtype = Point
            self.aname = 'points'
        else: raise Exception('Bad type: %s' % type)

    ##  Read from a buffered input stream.

    def read (self, f):
        fields = f.shift().split()
        assert fields[0] == 'class' and fields[1] == '='
        self.set_type(fields[2][1:-1])

        fields = f.shift().split()
        assert fields[0] == 'name' and fields[1] == '='
        self.name = fields[2][1:-1]

        fields = f.shift().split()
        assert fields[0] == 'xmin' and fields[1] == '='
        self.xmin = float(fields[2])

        fields = f.shift().split()
        assert fields[0] == 'xmax' and fields[1] == '='
        self.xmax = float(fields[2])

        fields = f.shift().split()
        assert fields[0] == self.aname + ':' and fields[1] == 'size' and fields[2] == '='
        nelts = int(fields[3])

        self.contents = [self.dtype(self) for i in range(nelts)]

        for (i,elt) in enumerate(self.contents):
            assert f.shift().strip() == self.aname + ' [%d]' % (i+1) + ':'
            elt.read(f)

    ##  Write to an output stream.

    def write (self, f):
        f.write('        class = "%s"\n' % self.type)
        f.write('        name = "%s"\n' % self.name)
        f.write('        xmin = %g\n' % self.xmin)
        f.write('        xmax = %g\n' % self.xmax)
        f.write('        %s: size = %d\n' % (self.aname, len(self.contents)))
        for (i, elt) in enumerate(self.contents):
            f.write('        %s [%d]:\n' % (self.aname, i+1))
            elt.write(f)

    ##  The number of intervals or points.

    def __len__ (self):
        return len(self.contents)

    ##  The i-th interval or point.

    def __getitem__ (self, i):
        return self.contents[i]

    ##  Delete the i-th interval or point.

    def __delitem__ (self, i):
        del self.contents[i]

    ##  The ending position of the last interval or point.  Same as the initial x
    #   position, if the tier is empty.

    def x (self):
        if self.contents: return self.contents[-1].xmax
        else: return self.xmin

    ##  Add an interval or point.

    def add (self, **kwargs):
        elt = self.dtype(self, **kwargs)
        self.contents.append(elt)
        return elt

    ##  Returns an array of (center, label) pairs.

    def array (self):
        if self.symtab is None:
            self.symtab = SymbolTable()
        tab = self.symtab
        n = len(self.contents)
        X = empty((n,2))
        for (i, elt) in enumerate(self.contents):
            X[i,0] = elt.center()
            X[i,1] = elt.symbol(tab)
        return X

    ##  Duplicate it.

    def clone (self):
        newtier = Tier(self.type, self.name, self.xmin, self.xmax)
        newtier.contents = [e.clone() for e in self.contents]
        return newtier


##  An interval.

class Interval (object):

    ##  Constructor.

    def __init__ (self, tier, text=None, xmin=None, xmax=None):
        if xmin is None: xmin = tier.x()

        ##  The tier it belongs to.
        self.tier = tier

        ##  Its start position.
        self.xmin = xmin

        ##  Its end position.
        self.xmax = xmax

        ##  Its text.
        self.text = text

    ##  Read it from a buffered input stream.

    def read (self, f):
        fields = f.shift().split()
        assert fields[0] == 'xmin' and fields[1] == '='
        self.xmin = float(fields[2])

        fields = f.shift().split()
        assert fields[0] == 'xmax' and fields[1] == '='
        self.xmax = float(fields[2])

        fields = f.shift().split()
        assert fields[0] == 'text' and fields[1] == '='
        self.text = fields[2][1:-1]

    ##  Write it to an output stream.

    def write (self, f):
        f.write('            xmin = %g\n' % self.xmin)
        f.write('            xmax = %g\n' % self.xmax)
        f.write('            text = "%s"\n' % self.text)

    ##  Compute the center position: the arithmetic mean of start and end positions.

    def center (self):
        return (self.xmin + self.xmax)/2

    ##  Intern the text in the symbol table.

    def symbol (self, symtab):
        return symtab.intern(self.text)

    ##  The original text.

    def string (self):
        return self.text

    ##  Duplicate it.

    def clone (self):
        return Interval(self.tier, self.text, self.xmin, self.xmax)


##  A point.

class Point (object):

    ##  Constructor.

    def __init__ (self, tier, number=None, mark=None):

        ##  The tier it belongs to.
        self.tier = tier

        ##  Its position in the tier.
        self.number = number

        ##  Its label.
        self.mark = mark

    ##  Read it from a buffered input stream.

    def read (self, f):
        fields = f.shift().split()
        assert fields[0] == 'number' and fields[1] == '='
        self.number = float(fields[2])
        
        fields = f.shift().split()
        assert fields[0] == 'mark' and fields[1] == '='
        self.mark = fields[2][1:-1]

    ##  Write it to an output stream.

    def write (self, f):
        f.write('            number = %g\n' % self.number)
        f.write('            mark = "%s"\n' % self.mark)

    ##  Its center is just its position.

    def center (self):
        return self.number

    ##  Intern its label in the symbol table.

    def symbol (self, symtab):
        return symtab.intern(self.mark)

    ##  The original label.

    def string (self):
        return self.mark

    ##  Duplicate it.

    def clone (self):
        return Point(self.tier, self.number, self.mark)
