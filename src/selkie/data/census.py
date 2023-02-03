##  @package seal.data.census
#   Personal and family names from the U.S. census.
#   The data comes the U.S. Census Bureau.  The URL is:
#
#       http://www.census.gov/genealogy/names/names_files.html
#
#   Being a US government publication, it is in the public domain.

from seal.core.config import Dest
from math import log


##  The name table.
Names = None

##  Designated empty entry.
EmptyEntry = None


##  An entry.

class Entry (object):

    ##  Constructor.

    def __init__ (self, string=None, freq=0.0, cumfreq=0.0, rank=0):

        ##  The name.
        self.string = string

        ##  Its relative frequency.
        self.freq = freq

        ##  Cumulative frequency of this and all more-frequent names.
        self.cumfreq = cumfreq

        ##  Its rank.
        self.rank = rank

    ##  String representation.

    def __repr__ (self):
        return '<Entry %s %f %f %d>' % (self.string, self.freq, self.cumfreq, self.rank)


##  A name.

class Name (object):

    ##  Constructor.

    def __init__ (self, string, male=None, female=None, last=None):
        global EmptyEntry
        if EmptyEntry == None: EmptyEntry = Entry()

        if male == None: male = EmptyEntry
        if female == None: female = EmptyEntry
        if last == None: last = EmptyEntry

        ##  The name.
        self.string = string

        ##  Its entry as a male name, or None.
        self.male = male

        ##  Its entry as a female name, or None.
        self.female = female

        ##  Its entry as a last name, or None.
        self.last = last

    ##  The proportion of first-name occurrences in which it is male.

    def maleness (self):
        m = self.male.freq
        f = self.female.freq
        tot = m+f
        if tot == 0: return 0.5
        else: return m/tot

    ##  String representation.

    def __repr__ (self):
        m = self.male.rank
        f = self.female.rank
        l = self.last.rank
        words = ['<Name', self.string]
        if m: words.append('mr=%s' % m)
        if f: words.append('fr=%s' % f)
        if l: words.append('lr=%s' % l)
        return ' '.join(words) + '>'


##  Get a name from the Names table.  Load if necessary.

def get (name):
    global Names
    if Names == None: load()
    name = name.upper()
    if name in Names:
        return Names[name]
    else:
        return None


##  Load the Names table.

def load ():
    global Names
    Names = {}
    load1('male.first', 'male', Names)
    load1('female.first', 'female', Names)
    load1('all.last', 'last', Names)


##  Load one file: male.first, female.first, or all.last.

def load1 (which, att, d):
    for line in open('%s/data/census/dist.%s' % (Dest, which)):
        string, freq, cumfreq, rank = line.split()
        entry = Entry(string, float(freq), float(cumfreq), int(rank))

        if string in d:
            name = d[string]
        else:
            name = Name(string)
            d[string] = name

        setattr(name, att, entry)


##  Iterate over the names.  Load if necessary.

def names ():
    global Names
    if Names is None: load()
    return iter(Names.values())
