##  @package seal.core.misc
#   Miscellaneous useful Python extensions.

import datetime, os, pty, unicodedata, sys, imp, threading, traceback, importlib
import signal
from itertools import islice, chain
from importlib import import_module
from .version import Version, Revision, Patchlevel
from io import StringIO
from time import time
from math import inf
import collections


#--  General  ------------------------------------------------------------------

##  Seal hello.

def hello ():
    print("Hello.  This is Seal %d.%d.%d." % (Version, Revision, Patchlevel))


##  Returns the arithmetic mean of two numbers.

def mean (x, y):
    return (x + y)/2


##  Checks whether the object has the given type.

def check_type (x, t):
    xnames = [c.__name__ for c in x.__class__.__mro__]
    if isinstance(t, (tuple, list)):
        types = t
    else:
        types = [t]
    for ty in types:
        if isinstance(ty, str):
            name = ty
        else:
            name = ty.__name__
        if name in xnames:
            return
    raise Exception('Object does not have required type: %s, %s' % (x, t))


#--  Matching  -----------------------------------------------------------------

##  Indicates whether the object matches the description.

def matches (x, descr):
    for (k, v) in descr.items():
        if v is None: continue
        if not hasattr(x, k): return False
        val = getattr(x, k)
        if isinstance(val, collections.Callable): val = val()
        if isinstance(v, list):
            if val not in v: return False
        else:
            if val != v: return False
    return True


#--  Index  --------------------------------------------------------------------

##  A specialization of dict in which keys are associated with lists of values.

class Index (dict):

    ##  Constructor.

    def __init__ (self, *pairs):
        dict.__init__(self)
        if len(pairs) == 1 and hasattr(pairs[0], '__next__'):
            pairs = pairs[0]
        for (k,v) in pairs:
            self.add(k,v)

    ##  Add a value.

    def __setitem__ (self, key, value):
        if key in self:
            dict.__getitem__(self, key).append(value)
        else:
            dict.__setitem__(self, key, [value])

    ##  Add a value.

    def add (self, key, value):
        self.__setitem__(key, value)

    ##  Fetch a list of values.  Returns the empty list if the key is missing.

    def __getitem__ (self, key):
        if key in self:
            return dict.__getitem__(self, key)
        else:
            return []

    ##  Iterate over all values.

    def itervalues (self):
        for vlist in dict.values(self):
            for v in vlist:
                yield v

    ##  Returns a list containing all values.

    def values (self):
        return list(self.itervalues())

    ##  Returns the number of values for the given key.

    def count (self, key):
        return len(self[key])

    ##  Deletes the given value.

    def delete (self, key, value):
        values = dict.__getitem__(self, key)
        values.remove(value)
        if not values: dict.__delitem__(self, key)

    ##  String representation.

    def __str__ (self):
        lines = ['%s -> %s' % (k, str(self[k])) for k in sorted(self.keys())]
        return '\n'.join(lines)


#--  Strings  ------------------------------------------------------------------

##  Describe each character in a unicode string.

def unidescribe (s):
    for (i,c) in enumerate(s):
        print(i, hex(ord(c)), unicodedata.name(c))


##  A <b>word</b> consists only of alphanumerics and underscore, and
#   is not the empty string.

def isword (s):
    return len(s) > 0 and all(c.isalnum() or c == '_' for c in s)


##  Break the string into its lines.  The lines do not include carriage return
#   and newline.

def lines (s):
    if isinstance(s, (bytes, bytearray)):
        cr = 13
        nl = 10
    else:
        cr = '\r'
        nl = '\n'
    i = 0
    while True:
        k = s.find(nl, i)
        if k < 0: break
        j = k
        if j > i and s[j-1] == cr:
            j -= 1
        yield s[i:j]
        i = k + 1


#--  as_ascii  -------------------------

def _objectionable_codepoint (x):
    return (x < 32 or x == 123 or x == 125 or x >= 127)

def _is_unobjectionable (s):
    if isinstance(s, str):
        for c in s:
            x = ord(c)
            if _objectionable_codepoint(x): return False
        return True
    else:
        return False

_my_names = {7: 'bel',
             8: 'bs',
             9: 'tab',
             10: 'nl',
             11: 'vt',
             12: 'ff',
             13: 'ret',
             27: 'esc',
             123: 'lb',
             125: 'rb',
             127: 'del',
             8211: 'end', # 2013
             8212: 'emd', # 2014
             8216: 'lsq', # 2018
             8217: 'rsq', # 2019
             8220: 'ldq', # 201c
             8221: 'rdq'} # 201d

_my_names_inv = None

_substitutions = {9: ' ',    # tab
                  11: '\n',  # vert tab
                  12: '\n',  # form feed
                  8211: '-', # en-dash
                  8212: '-', # em-dash
                  8216: "'", # left single quote
                  8217: "'", # right single quote
                  8220: '"', # left double quote
                  8221: '"'} # right double quote

def _write_name (c, x, out):
    try:
        out.write(unicodedata.name(c))
    except Exception:
        out.write(hex(x)[2:])

def _write_hex (c, x, out):
    s = hex(x)[2:]
    if len(s) == 0:
        raise Exception('Empty hex string')
    elif len(s) == 1:
        out.write('0')
        out.write(s)
    elif len(s) == 2:
        out.write(s)
    else:
        for i in range(4-len(s)):
            out.write('0')
        out.write(s)

##  Convert a string to ASCII.

def as_ascii (s, use='hex'):
    if not isinstance(s, str):
        return as_ascii(str(s), use)
    elif _is_unobjectionable(s):
        return s
    if use in (None, 'alts'):
        with StringIO() as out:
            for c in s:
                x = ord(c)
                if x == 10 or 32 <= x <= 126:
                    out.write(c)
                elif use == 'alts' and x in _substitutions:
                    out.write(_substitutions[x])
            return out.getvalue()
    else:
        if use == 'names': f = _write_name
        elif use == 'hex': f = _write_hex
        else: raise Exception('Bad value for use: %s' % use)
        with StringIO() as out:
            for c in s:
                x = ord(c)
                if _objectionable_codepoint(x):
                    out.write('{')
                    if x in _my_names:
                        out.write(_my_names[x])
                    else:
                        f(c, x, out)
                    out.write('}')
                else:
                    out.write(c)
            return out.getvalue()

##  Undo as_ascii().

def from_ascii (s):
    global _my_names_inv
    if '{' in s:
        out = StringIO()
        i = 0
        while i < len(s):
            c = s[i]
            if c == '{':
                i += 1
                j = s.find('}', i)
                if j < 0:
                    raise Exception("'{' without matching '}'")
                name = s[i:j]
                if name.isdigit():
                    c = chr(int(name, 16))
                else:
                    if _my_names_inv is None:
                        _my_names_inv = {}
                        for (k,v) in _my_names.items():
                            _my_names_inv[v] = chr(k)
                    c = _my_names_inv[name]
                out.write(c)
                i = j+1
            else:
                out.write(c)
                i += 1
        s = out.getvalue()
        out.close()
        return s
    else:
        return s


##  Convert a string to printable ASCII characters.  Here, a "printable"
#   character is a character in the range U+0020 (space) to U+007e inclusive,
#   or newline (U+000a).  That is, space and newline are considered printable,
#   all other whitespace and control characters are not; nor is DEL (U+007f).
#   Use substitutions for "smart quotes" and related characters.  Replace tab
#   with space; replace vertical tab, and formfeed with newline.  Delete all
#   other characters that are not printable ASCII.  Returns an iteration over
#   characters.

def ascii_chars (s):
    for c in s:
        n = ord(c)
        if n in _substitutions:
            yield _substitutions[n]
        elif n >= 0x20 and n <= 0x7e:
            yield c
        elif n == 0x0a:
            yield c

##  Convert a single character to a (possibly escaped) form that is safe for
#   inclusion between double quotes.  Double quotes and backslashes are escaped
#   with backslashes, and newline is replaced with backslash-en.  Returns an
#   iteration over strings.

def quotable_chars (s):
    for c in s:
        if c == '"':
            yield '\\"'
        elif c == '\\':
            yield '\\\\'
        elif c == '\n':
            yield '\\n'
        else:
            yield c

##  Like repr(), but always returns a double-quoted string.  May be called as:
#   quote(ascii_chars(s)).

def quoted (s):
    with StringIO() as f:
        f.write('"')
        for c in quotable_chars(s):
            f.write(c)
        f.write('"')
        return f.getvalue()


#--  deaccent  -------------------------

_deaccent_map = [
    None, None, None, None, None, None, None, None, None, '\t', '\n', None, None, '\r', None, None,
    None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
    ' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?',
    '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
    'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\', ']', '^', '_',
    '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
    'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~', None,
    None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
    None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
    None, '!', 'c', 'L', 'O', 'Y', None, None, None, 'c', 'a', '<<', '-', None, 'R', None,
    None, '+/-', '2', '3', None, 'm', None, '.', None, '1', 'o', '>>', '1/4', '1/2', '3/4', '?',
    'A', 'A', 'A', 'A', 'A', 'A', 'AE', 'C', 'E', 'E', 'E', 'E', 'I', 'I', 'I', 'I',
    'Dh', 'N', 'O', 'O', 'O', 'O', 'O', '*', 'O', 'U', 'U', 'U', 'U', 'Y', 'Th', 'ss',
    'a', 'a', 'a', 'a', 'a', 'a', 'ae', 'c', 'e', 'e', 'e', 'e', 'i', 'i', 'i', 'i',
    'dh', 'n', 'o', 'o', 'o', 'o', 'o', '/', 'o', 'u', 'u', 'u', 'u', 'y', 'th', 'y'
    ]

##  Map accented characters to their unaccented form.

def deaccent (s):
    asc = []
    for u in s:
        i = ord(u)
        if i >= 0 and i < len(_deaccent_map):
            a = _deaccent_map[i]
            if a:
                asc.append(a)
    return ''.join(asc)


##  Interpret an ASCII string as UTF8.

def utf8 (s, fn=None):
    if fn is None:
        print(' '.join(hex(c)[2:] for c in s.encode('utf8')))
    else:
        with open(fn, 'w', encoding='utf8') as f:
            print(s, file=f)

##  Convert to a boolean value.

def as_boolean (s):
    if s == 'False': return False
    elif s == 'True': return True
    else: raise Exception('Not a boolean: ' + str(s))

##  Convert the string to ASCII and trim it to fit in a field with
#   fixed width w.

def trim (w, s=None):
    if s is None:
        s = w
        w = 0
    s = as_ascii(s, use='hex')
    if w > 0 and len(s) > w: return s[:w]
    else: return s


#--  Date-Time string, Size string  --------------------------------------------

##  Print out a timestamp readably.

def dtstr (timestamp):
    return datetime.datetime.fromtimestamp(timestamp).isoformat().replace('T',' ')

##  Print out a file size readably.

def sizestr (nbytes):
    if nbytes >= 1000000000000000:
        return '%5.3f PB' % (nbytes/1000000000000000)
    elif nbytes >= 1000000000000:
        return '%5.3f TB' % (nbytes/1000000000000)
    elif nbytes >= 1000000000:
        return '%5.3f GB' % (nbytes/1000000000)
    elif nbytes >= 1000000:
        return '%5.3f MB' % (nbytes/1000000)
    elif nbytes >= 1000:
        return '%5.3f KB' % (nbytes/1000)
    else:
        return '%d B' % nbytes


#--  Reflection  ---------------------------------------------------------------

##  Returns a module given its name.
#   May raise ModuleNotFoundError

def string_to_module (s):
    if not s:
        raise Exception('Require nonempty name')
    return import_module(s)

##  Takes a fully-qualified name and gets the object.

def string_to_object (s):
    j = s.rfind('.')
    if j < 0:
        raise Exception('Require fully qualified name')
    m = string_to_module(s[:j])
    return m.__dict__[s[j+1:]]


#--  Lists  --------------------------------------------------------------------

##  Converts x to a list.

def as_list (x):
    if x == None: return []
    elif isinstance(x, list): return x
    elif isinstance(x, (tuple, set, frozenset, range, dict)): return list(x)
    elif hasattr(x, '__next__'): return list(x)
    else: return [x]

##  Returns an iterable.

def repeatable (x):
    if x == None: return []
    elif hasattr(x, '__next__'): return iter(x)
    elif hasattr(x, '__iter__'): return x
    else: raise Exception('Does not appear to be iterable: %s' % repr(x))

##  Concatenates multiple lists.

def concat (lists):
    out = []
    for list in lists:
        out.extend(list)
    return out

##  Eliminates duplicates from a list.  Otherwise preserves order.

def unique (elts):
    out = []
    for elt in elts:
        if elt not in out:
            out.append(elt)
    return out

##  Cross product.

def cross_product (lists):
    if len(lists) == 1:
        return [(x,) for x in lists[0]]
    else:
        return [(x,) + rest
                for x in lists[0]
                for rest in cross_product(lists[1:])]


#--  Edit distance  ------------------------------------------------------------

##  Works with arbitrary sequences; requires len and [].
#   The cost function should accept pairs of elements (x,y).
#       (x,None) = deletion of x
#       (None,y) = insertion of y
#       (x,y) otherwise = substitution of y for x.  Possibly x=y.
#   A "cell" represents a pair of positions: i in the input, j in the output.
#   Both i and j range from 0 to the end of their sequence, inclusive.
#   i + j is the "norm" of the cell.  To fill in a cell, the cells we need
#   all have smaller norms, so we guarantee they have already been filled by
#   visiting by increasing norm.

class EDNode (object):

    def __init__ (self, i, j):
        self.i = i
        self.j = j
        self.cost = None
        self.prev = None

    def __repr__ (self):
        return '<EDNode %d %d>' % (self.i, self.j)


def simple_cost (x, y):
    if x != y: return 1
    else: return 0


class EditDistance (object):

    def __init__ (self, cost=simple_cost):
        self.cost_function = cost

    def table (self, inseq, outseq):
        cost = self.cost_function
        m = len(inseq)
        n = len(outseq)
        nc = n + 1
        maxnorm = m + n

        nodes = [EDNode(i,j) for i in range(m+1) for j in range(n+1)]
        nodes[0].cost = 0
    
        for norm in range(1, maxnorm + 1):  # include the case norm = maxnorm
            imin = 0 if norm < n else norm - n
            imax = m if m < norm else norm
            for i in range(imin, imax + 1):  # include the case i = imax
                j = norm - i

                node = nodes[i*nc + j]
                node.cost = inf
                node.prev = None
    
                # substitution
                if i > 0 and j > 0:
                    prev = nodes[(i-1)*nc + (j-1)]
                    c = prev.cost + cost(inseq[i-1], outseq[j-1])
                    if c < node.cost:
                        node.cost = c
                        node.prev = prev
    
                # deletion
                if i > 0:
                    prev = nodes[(i-1)*nc + j]
                    c = prev.cost + cost(inseq[i-1], None)
                    if c < node.cost:
                        node.cost = c
                        node.prev = prev
    
                # insertion
                if j > 0:
                    prev = nodes[i*nc + (j-1)]
                    c = prev.cost + cost(None, outseq[j-1])
                    if c < node.cost:
                        node.cost = c
                        node.prev = prev
    
        return nodes

    def __call__ (self, inseq, outseq):
        nodes = self.table(inseq, outseq)
        return nodes[-1].cost


#--  Sorted lists  -------------------------------------------------------------

##  Eliminates duplicates, assuming that the list is sorted.

def uniq (sortedlst):
    out = []
    for elt in sortedlst:
        if len(out) == 0 or elt != out[-1]:
            out.append(elt)
    return out

##  Intersects two sorted lists.  Unpredictable results if the lists are not
#   sorted.

def intersect (list1, list2):
    out = []
    i1 = 0
    i2 = 0
    n1 = len(list1)
    n2 = len(list2)
    while i1 < n1 and i2 < n2:
        if list1[i1] < list2[i2]:
            i1 += 1
        elif list2[i2] < list1[i1]:
            i2 += 1
        else:
            out.append(list1[i1])
            i1 += 1
            i2 += 1
    return out

##  Takes the union of two sorted lists.  Unpredictable results if the lists
#   are not sorted.

def union (list1, list2):
    out = []
    i1 = 0
    i2 = 0
    n1 = len(list1)
    n2 = len(list2)
    while i1 < n1 and i2 < n2:
        if list1[i1] < list2[i2]:
            out.append(list1[i1])
            i1 += 1
        elif list2[i2] < list1[i1]:
            out.append(list2[i2])
            i2 += 1
        else:
            out.append(list1[i1])
            i1 += 1
            i2 += 1
    # only one of these loops will actually be used
    while i1 < n1:
        out.append(list1[i1])
        i1 += 1
    while i2 < n2:
        out.append(list2[i2])
        i2 += 1
    return out

##  Returns the set difference of two sorted lists.  Unpredictable results if
#   the lists are not sorted.

def difference (list1, list2):
    out = []
    i1 = 0
    i2 = 0
    n1 = len(list1)
    n2 = len(list2)
    while i1 < n1 and i2 < n2:
        if list1[i1] < list2[i2]:
            out.append(list1[i1])
            i1 += 1
        elif list2[i2] < list1[i1]:
            i2 += 1
        else:
            i1 += 1
            i2 += 1
    while i1 < n1:
        out.append(list1[i1])
        i1 += 1
    return out


#--  Queue  --------------------------------------------------------------------

##  A queue.  It uses a circular buffer.

class Queue (object):

    ##  Constructor.

    def __init__ (self, maxwaste=10):
        self.__buffer = []
        self.__head = 0
        self.__tail = 0
        self.__maxwaste = maxwaste

    ##  The number of elements.

    def __len__ (self):
        return self.__tail - self.__head

    ##  Whether the queue contains any elements.

    def __bool__ (self):
        return self.__tail > self.__head

    def __buffer_index (self, i):
        if isinstance(i, int):
            return self.__head + i
        elif isinstance(i, slice):
            if i.start: start = self.__head + i.start
            else: start = self.__head
            if i.stop: stop = self.__head + i.stop
            else: stop = self.__tail
            return slice(start, stop, i.step)
        else:
            raise IndexError('Not a valid index: %s' % repr(i))

    ##  Fetch the item at the given queue position.

    def __getitem__ (self, i):
        return self.__buffer.__getitem__(self.__buffer_index(i))

    ##  Set the item at the given queue position.

    def __setitem__ (self, i, v):
        self.__buffer.__setitem__(self.__buffer_index(i), v)

    ##  Add an element to the end of the queue.

    def write (self, elt):
        if self.__tail == len(self.__buffer):
            self.__buffer.append(elt)
        else:
            self.__buffer[self.__tail] = elt
        self.__tail += 1

    ##  Return the item at the head of the queue and advance the head.

    def read (self):
        if self.__head >= self.__tail:
            raise IndexError('Empty queue')
        elt = self.__buffer[self.__head]
        self.__head += 1
        if self.__head == self.__tail or \
                self.__maxwaste is not None and self.__head > self.__maxwaste:
            n = self.__tail - self.__head
            for i in range(n):
                self.__buffer[i] = self.__buffer[self.__head + i]
            self.__head = 0
            self.__tail = n
        return elt


#--  Iterables  ----------------------------------------------------------------

##  Returns the n-th item of iterable g, counting from 0, and counting from the
#   current position of the iterator's "read head."  For example:
#
#       >>> import itertools
#       >>> c = itertools.count(0)
#       >>> nth(c, 3)
#       3
#       >>> nth(c, 3)
#       7
#
#   The iterator I{c} generates the natural numbers, beginning with 0.  The
#   first call to C{nth} returns the fourth item, which is the number 3.
#   The second call begins where the first left off, and returns the
#   fourth item, which is the number 7.
#
#   Note that one can achieve the same functionality this way:
#
#       >>> itertools.islice(c, 3, 4).next()
#
#   One use of nth is to jump to problematic cases in a large
#   iteration.  An idiom for finding such cases in the first place is the
#   following:
#    
#       for i, x in enumerate(myiteration):
#           if isproblematic(x):
#               return i

def nth (iter, n):
    try:
        count = 0
        while count < n:
            next(iter)
            count += 1
        return next(iter)
    except StopIteration:
        return None

##  Returns a list containing the first n elements from the iteration.

def head (iter, n=5):
    return list(islice(iter, n))

##  Returns a list containing the last n elements from the iteration.

def tail (iter, n=5):
    out = []
    ptr = 0
    for elt in iter:
        if len(out) < n:
            out.append(elt)
        else:
            out[ptr] = elt
        ptr += 1
        if ptr >= n: ptr = 0

    if len(out) < n or ptr == 0:
        return out
    else:
        return out[ptr:] + out[:ptr]


##  A pager.
class _Pager (object):

    ##  Constructor.
    def __init__ (self, pagesize=40):
        ##  The page size, in lines.
        self.pagesize = pagesize

    ##  Call it.
    def __call__ (self, iter):
        for i,x in enumerate(iter):
            if i > 0 and i % self.pagesize == 0:
                if input() == 'q': break
            print(x)

##  Prints a "page" at a time and waits for space bar or 'q'.
more = _Pager()

##  The product of a list of numbers.

def product (nums):
    prod = 1
    for num in nums:
        prod *= num
    return prod

##  Counts up how many items are contained in
#   (or remain in) the given iterable.  It calls C{next()} repeatedly
#   until the iteration is "used up."  If the iterable is infinite, it
#   never returns.  It is defined as: python::
#
#       sum(1 for x in g)
#

def count (iter):
    return sum(1 for x in iter)


##  Creates a map whose keys are items in the given iterable, and whose value for
#   a given item is the frequency of occurrence of that item in the iteration.
#   All items are consumed.

def counts (iterable):
    dict = {}
    for item in iterable:
        if item in dict:
            dict[item] += 1
        else:
            dict[item] = 1
    return dict


#--  Cwd  ----------------------------------------------------------------------

##  To change the current directory temporarily.
#
#       with Cwd():
#           ...
#
#  On exit, undoes any chdir() in the body.

class Cwd (object):

    ##  @var wd
    #   The original working directory.

    ##  Enter.

    def __enter__ (self):
        self.wd = os.getcwd()

    ##  Exit.

    def __exit__ (self, t, v, tb):
        os.chdir(self.wd)


#--  file_size  ----------------------------------------------------------------

##  Returns the file size in bytes.

def file_size (fn):
    return os.stat(fn).st_size


#--  System calls  -------------------------------------------------------------

##  Make a synchronous call, raising an exception on failure.
#   If the call is unsuccessful, an exception is raised.
#   There is no return value.

def call (program, *args):
    value = os.spawnvp(os.P_WAIT, program, [program] + list(args))
    if value != 0:
        raise Exception("Program failed: value " + str(value) + ": " + program + " " + ' '.join(args))

##  Makes an asynchronous call, returning 0 on success and an error code on failure.

def launch (program, *args):
    return os.spawnvp(os.P_NOWAIT, program, [program] + list(args))


#--  Shell  --------------------------------------------------------------------

##  Prints output all at once, not incrementally.

def shell (cmd):
    print(subprocess.getoutput(cmd))

##  Unless silent=True, prints incrementally.
#   @arg value - '', 'v', 'vo', 'o'.
#   Unless 'v', signals an error for nonzero status.
#    - Returns (value, output) if 'vo'.
#    - Returns value if 'v'.
#    - Returns output if 'o'.

def run_command (com, *args, value='', silent=False, color=None):
    if color is None:
        return _run_command1(com, args, value, silent)
    else:
        with _stdout_color(color):
            return _run_command1(com, args, value, silent)

def _run_command1 (com, args, value, silent):
    if 'o' in value: output = bytearray()
    (pid, fd) = pty.fork()
    if pid == 0:
        os.execlp(com, com, *args)
    else:
        if not silent: os.write(1, b'\033[36m')
        while True:
            b = _read(fd, 64)
            if not b: break
            if not silent: os.write(1, strip_escapes(b))
            if 'o' in value: output.extend(b)
        if not silent: os.write(1, b'\033[39m')
        status = os.waitpid(pid, 0)[1]
        if not ('v' in value or status == 0):
            raise Exception('Executable error: %s' % status)
        if 'o' in value:
            output = output.decode('raw_unicode_escape')
        if value == 'vo': return (status, output)
        elif value == 'v': return status
        elif value == 'o': return output

def _read (fd, bufsize):
    b = b''
    try:
        b = os.read(fd, bufsize)
    except OSError:
        pass
    return b

##  Stdout color.
class _stdout_color (object):
    ##  Constructor.
    def __init__ (self, color):
        colors = {'red': b'\033[31m',
                  'green': b'\033[32m',
                  'yellow': b'\033[33m',
                  'blue': b'\033[34m',
                  'magenta': b'\033[35m',
                  'cyan': b'\033[36m'}
        ##  The escape code for the given color.
        self.color = colors[color]
    ##  Enter.
    def __enter__ (self):
        os.write(1, self.color)
    ##  Exit.
    def __exit__ (self, t, v, tb):
        os.write(1, b'\033[39m')


def _is_digit_or_semicolon (x):
    return (48 <= x <= 57 or x == 59)

def _is_letter (x):
    return (65 <= x <= 90 or 97 <= x <= 122)

# returns end point if looking at xterm escape sequence, -1 otherwise

def _escape_seq (b, i):
    if not (i < len(b) and b[i] == 27): return -1
    i += 1
    if not (i < len(b) and b[i] == 91): return i
    i += 1
    while i < len(b) and _is_digit_or_semicolon(b[i]): i += 1
    if i < len(b) and _is_letter(b[i]): i += 1
    return i

##  Strip xterm escape sequences, e.g. color changes.

def strip_escapes (b):
    out = None
    i = k = 0
    while k < len(b):
        j = _escape_seq(b,k)
        if j < 0:
            k += 1
        else:
            if out is None: out = bytearray(b[:k])
            else: out.extend(b[i:k])
            i = k = j
    if i < len(b) and out is not None:
        out.extend(b[i:])
    if out is None: return b
    else: return out


#--  Command line processing, v1  ----------------------------------------------

##  Deprecated.  Use shift instead.

class CommandLine (object):

    ##  Constructor.

    def __init__ (self, usage, nargs=None):
        self.__usage = usage
        ##  Arg vector.
        self.argv = sys.argv
        ##  Current position.
        self.i = 1
        ##  Command.
        self.arg0 = None
        ##  Number of arguments.
        self.nargs = nargs

    ##  Print usage and exit.
    def usage (self):
        sys.stderr.write('Usage: %s\n' % self.__usage)
        sys.exit(1)

    ##  Whether the current argument is a flag.
    def has_option (self):
        if len(self.argv) > self.i and self.argv[self.i][0] == '-':
            return True
        else:
            return False

    ##  Get the value for opt.
    def option (self, opt):
        if len(self.argv) <= self.i or self.argv[self.i][0] != '-':
            raise Exception('No option')
        key = self.argv[self.i]
        self.i += 1
        return key

    ##  Check whether the number of arguments is correct.
    def check_nargs (self):
        if self.arg0 is None:
            self.arg0 = self.i
            if self.nargs is None:
                self.nargs = len(self.argv) - self.arg0
            elif len(self.argv) - self.arg0 > self.nargs:
                self.usage()

    ##  Iterator method.
    def __next__ (self):
        self.check_nargs()
        t = self.i - self.arg0
        if t >= self.nargs:
            raise StopIteration
        if t < len(self.argv):
            arg = self.argv[t]
        else:
            arg = ''
        self.i += 1
        return arg

    ##  Get the i-th argument.
    def __getitem__ (self, i):
        self.check_nargs()
        if i < 0 or i >= self.nargs: raise IndexError
        t = self.arg0 + i
        if t < len(self.argv):
            return self.argv[t]
        else:
            return ''

    ##  Get the number of arguments.
    def __len__ (self):
        self.check_nargs()
        return self.nargs

    ##  Returns self.
    def __iter__ (self):
        return self


#--  Command line processing, v2  ----------------------------------------------

def _n_oblig_params (fnc):
    nparams = fnc.__code__.co_argcount
    nopt = len(fnc.__defaults__)
    return nparams - nopt

def _optional_params (fnc):
    nparams = fnc.__code__.co_argcount
    nopt = len(fnc.__defaults__)
    noblig = nparams - nopt
    names = fnc.__code__.co_varnames
    return names[noblig:nparams]

##  Deprecated.  Use shift instead.

def run_main_2 (main):
    if len(sys.argv) > 1 and sys.argv[1] == '-?': _print_usage(main)
    show_stack_trace = False
    kwargs = {}
    noblig = _n_oblig_params(main)
    i = 1 + noblig
    if i > len(sys.argv): _print_usage(main)
    while i < len(sys.argv):
        arg = sys.argv[i]
        i += 1
        if arg == '-!': show_stack_trace = True
        elif arg == '--': break
        else:
            k = arg.find('=')
            if k >= 0:
                key = arg[1:k]
                value = arg[k+1:]
            else:
                key = arg[1:]
                value = '1'
            if key in kwargs:
                print("Flag '-%s' multiply specified" % key, file=sys.stderr)
                sys.exit(1)
            kwargs[key] = value

    args = sys.argv[i:]
    try:
        value = main(*args, **kwargs)
        if value is not None:
            print(value)
        sys.exit(0)
    except Exception as e:
        if show_stack_trace:
            traceback.print_exc()
        else:
            print('ERROR:', e, file=sys.stderr)
        sys.exit(1)


#--  Command line processing, v3  ----------------------------------------------

##  Deprecated.  Use shift instead.

def run_main (main):
    show_stack_trace = False
    kwargs = {}
    i = 1
    while i < len(sys.argv) and sys.argv[i].startswith('-'):
        arg = sys.argv[i]
        i += 1
        if arg == '-?': _print_usage(main)
        elif arg == '-!': show_stack_trace = True
        elif arg == '--': break
        else:
            k = arg.find('=')
            if k >= 0:
                key = arg[1:k]
                value = arg[k+1:]
            else:
                key = arg[1:]
                value = '1'
            if key in kwargs:
                print("Flag '-%s' multiply specified" % key, file=sys.stderr)
                sys.exit(1)
            kwargs[key] = value

    args = sys.argv[i:]
    try:
        value = main(*args, **kwargs)
        if value is not None:
            print(value)
        sys.exit(0)
    except Exception as e:
        if show_stack_trace:
            traceback.print_exc()
        else:
            print('ERROR:', e, file=sys.stderr)
        sys.exit(1)

def _print_usage (f):
    progname = sys.argv[0]
    nargs = f.__code__.co_argcount
    defaults = f.__defaults__
    nopt = len(defaults)
    noblig = nargs - nopt
    allow_xs_positional = (f.__code__.co_flags & 0x04)
    allow_xs_keywords = (f.__code__.co_flags & 0x08)
    varnames = f.__code__.co_varnames
    oblig = varnames[:noblig]
    opt = varnames[noblig:nargs]
    words = [progname] + list(oblig)
    if opt: words.append('[%s]' % ' '.join(opt))
    print('USAGE:   ', ' '.join(words))
    if defaults:
        print('Defaults:')
        for i in range(nopt):
            print('    %-10s %s' % (opt[i], defaults[i]))
    print('Flags:')
    print('    Any arg can be provided as a flag in form -arg=value')
    print('    -arg  is the same as -arg=1')
    print('    -?    prints this usage message')
    print('    -!    causes a stack trace to be printed in case of error')
    print('    --    terminates flags; what follows are positional arguments')
    if f.__doc__:
        print()
        print(f.__doc__)
    sys.exit(1)


#--  Command line processing, v4  ----------------------------------------------

def _print_boilerplate ():
    print('Optional arguments may be specified in any of three ways:')
    print(' - include them among the positional arguments')
    print(' - in flag form, before the positional arguments')
    print(' - in keyword form, after the positional arguments')
    print()
    print('However, optional arguments that are specified as keyword-only')
    print('cannot be provided positionally.')
    print()
    print('Flags (precede positional arguments):')
    print('    -?         prints this usage message')
    print('    -!         causes a stack trace to be printed in case of error')
    print('    -ARG       value is 1')
    print('    --ARG      value is 1')
    print('    -ARG=VAL')
    print('    --ARG=VAL')
    print('    --         terminates flags')
    print()
    print('Keyword arguments have the form KEY=VAL and follow the positional')
    print('arguments.')


##  Dispatch table.

class _DispatchTable (object):

    ##  Constructor.

    def __init__ (self, table):
        ##  Contents.
        self.table = table
        
    ##  Get value.
    def __getitem__ (self, name):
        if name in self.table:
            return self.table[name]
        else:
            self.error('Unrecognized command: %s' % name)
        
    ##  Print usage and exit.
    def usage (self):
        print('Commands:')
        for name in sorted(self.table):
            print()
            f = _Function(name, self.table[name])
            f.print_description()
        print()
        _print_boilerplate()
        sys.exit(1)
        
    ##  Print error and usage and exit.
    def error (self, msg):
        print('**', msg, file=sys.stderr)
        self.usage()


##  A function.
class _Function (object):

    ##  Constructor.
    def __init__ (self, name, f):

        ##  The name.
        self.name = name

        ##  The python function.
        self.func = None

        ##  Whether it has a 'self' argument.
        self.selfarg = None

        ##  Number of positional parameters.
        self.npos = None

        ##  Number of obligatory parameters.
        self.nobl = None

        ##  Number of optional parameters.
        self.nopt = None

        ##  Number of keyword parameters.
        self.nkwo = None

        ##  Total number of arguments.
        self.nargs = None

        ##  Whether it has a '*args' parameter.
        self.star = None

        ##  Whether it has a '**kwargs' parameter.
        self.starstar = None

        ##  Names of parameters.
        self.names = None

        ##  Default values for parameters.
        self.defaults = None

        ##  Whether it accepts keyword arguments.
        self.keywords = None

        if hasattr(f, '__code__'):
            self.func = f
            self.selfarg = None
        elif hasattr(f, '__call__'):
            m = f.__call__
            if not (hasattr(m, '__self__') and hasattr(m, '__func__')):
                raise Exception('Not a recognized function type')
            self.func = f = m.__func__
            self.selfarg = m.__self__

        self.npos = f.__code__.co_argcount
        if f.__defaults__:
            self.nopt = len(f.__defaults__)
        else:
            self.nopt = 0
        self.nobl = self.npos - self.nopt
        self.nkwo = f.__code__.co_kwonlyargcount
        self.nargs = self.npos + self.nkwo
        self.star = bool(f.__code__.co_flags & 0x04)
        self.starstar = bool(f.__code__.co_flags & 0x08)

        self.names = f.__code__.co_varnames

        if self.selfarg:
            self.npos -= 1
            self.nobl -= 1
            self.nargs -= 1
            self.names = self.names[1:]

        self.defaults = []
        if f.__defaults__: self.defaults.extend(f.__defaults__)
        if self.nkwo:
            for name in self.names[self.npos:self.nargs]:
                self.defaults.append(f.__kwdefaults__[name])

        if self.starstar:
            self.keywords = True
        else:
            self.keywords = set(self.names[self.nobl : self.nargs])

    ##  Whether it accepts kw as a keyword argument.

    def accepts_keyword (self, kw):
        return self.keywords is True or kw in self.keywords

    ##  Print out a description.

    def print_description (self):
        args = ' '.join(self.names[:self.nobl])
        if self.nopt > 0:
            args = '%s [%s]' % (args, ' '.join(self.names[self.nobl:self.npos]))
        print(self.name, args)
        if self.star:
            print('    Additional positional arguments are allowed')
        if self.nkwo > 0:
            print('    Keyword only: ' + ' '.join(self.names[self.npos:self.nargs]))
        if self.defaults:
            print('    Defaults:')
            for i in range(self.nobl, self.nargs):
                print('        %-10s %s' % (self.names[i], self.defaults[i-self.nobl]))
        if self.starstar:
            print('    Additional keyword arguments are allowed')
        if self.func.__doc__:
            print()
            print(self.func.__doc__)

    ##  Print an error message, print usage, and exit.

    def error (self, msg):
        print('**', msg, file=sys.stderr)
        self.usage()
        
    ##  Print usage and exit.

    def usage (self):
        self.print_description()
        print()
        _print_boilerplate()
        sys.exit(1)

    ##  Call the function.

    def __call__ (self, args, kwargs, stack_trace):
        try:
            if self.selfarg: args = [self.selfarg] + args
            value = self.func(*args, **kwargs)
            if value is not None:
                print(value)
            sys.exit(0)
        except Exception as e:
            if stack_trace:
                traceback.print_exc()
            else:
                print('ERROR:', e, file=sys.stderr)
            sys.exit(1)


##  Dispatches either to a DispatchTable or to a Function.

class _Form (object):

    ##  Constructor.  Only one of 'table' or 'function' get set.
    def __init__ (self, main):

        ##  The DispatchTable.
        self.table = None
        ##  The Function.
        self.function = None
        ##  Positional arguments.
        self.args = None
        ##  Keyword arguments.
        self.kwargs = None
        ##  Whether to show a stack trace on error.
        self.stack_trace = None

        if isinstance(main, dict):
            self.table = _DispatchTable(main)
            self.function = None
        else:
            self.table = None
            self.function = _Function(sys.argv[0], main)
        self.args = []
        self.kwargs = {}
        self.stack_trace = False

    ##  The number of optional arguments.
    def n_optional_args (self):
        return self.function.nopt

    ##  The number of obligatory arguments.
    def n_obligatory_args (self):
        return self.function.nobl

    ##  Add arguments.
    def add_args (self, args):
        self.args.extend(args)

    ##  Add a keyword arg.
    def add_keyword_arg (self, key, value):
        if self.function.accepts_keyword(key):
            if key in self.kwargs:
                self.error('Keyword specified multiple times: %s' % key)
            self.kwargs[key] = value
        else:
            self.error('Unrecognized keyword: %s' % key)

    ##  Call the function on arguments and keyword arguments.
    def eval (self):
        self.function(self.args, self.kwargs, self.stack_trace)

    ##  Print an error message, print usage, and exit.
    def error (self, msg):
        if self.function: self.function.error(msg)
        else: self.table.error(msg)

    ##  Print usage and exit.
    def usage (self):
        if self.function: self.function.usage()
        else: self.table.usage()


def _isflag (i):
    return i < len(sys.argv) and sys.argv[i].startswith('-') and sys.argv[i] != '-'

def _isnonflag (i):
    return i < len(sys.argv) and ((not sys.argv[i].startswith('-')) or sys.argv[i] == '-')


##  Deprecated.  A command-line parser.
class _CommandLineParser (object):

    ##  Constructor.

    def __init__ (self):

        ##  Beginning of obligatory args.
        self.i = None
        ##  Beginning of optional args.
        self.j = None
        ##  Beginning of keyword args.
        self.k = None

    ##  Call it.
    def __call__ (self, main):
        form = _Form(main)
        self.i = 1
        while self.special_flag(form): pass
        if form.function is None: self.command(form)
        self.flags(form)
        self.obligatory_args(form)
        self.keyword_args(form)
        self.optional_args(form)
        return form

    ##  Whether a special flag has been provided (-? or -!).
    def special_flag (self, form):
        if self.i >= len(sys.argv): return False
        arg = sys.argv[self.i]
        if arg == '-!': form.stack_trace = True
        elif arg == '-?': form.usage()
        else: return False
        self.i += 1
        return True

    ##  Set the command.
    def command (self, form):
        self.i = 1
        if _isnonflag(self.i):
            name = sys.argv[self.i]
            com_name = '%s %s' % (sys.argv[0], name)
            self.i += 1
            form.function = _Function(name, form.table[name])
        else:
            form.error('No command provided')

    ##  Process flags.
    def flags (self, form):
        while _isflag(self.i):
            if not self.special_flag(form):
                arg = sys.argv[self.i]
                self.i += 1
                if arg == '--': break
                t = arg.find('=')
                if t < 0:
                    flag = arg[1:]
                    value = '1'
                else:
                    u = 1
                    if arg[u] == '-': u += 1
                    flag = arg[u:t]
                    value = arg[t+1:]
                form.add_keyword_arg(flag, value)

    ##  Process obligatory args.
    def obligatory_args (self, form):
        self.j = self.i + form.n_obligatory_args()
        if self.j > len(sys.argv):
            form.error('Not enough arguments provided')
        form.add_args(sys.argv[self.i:self.j])

    ##  Process keyword args.
    def keyword_args (self, form):
        self.k = len(sys.argv)
        while self.k > self.j:
            arg = sys.argv[self.k-1]
            t = arg.find('=')
            if t < 0: break
            self.k -= 1
            (key,value) = (arg[:t], arg[t+1:])
            form.add_keyword_arg(key, value)
        
    ##  Process optional args.
    def optional_args (self, form):
        if self.k - self.j > form.n_optional_args():
            form.error('Too many arguments provided')
        form.add_args(sys.argv[self.j:self.k])


_command_line = None

##  Deprecated.  Use shift instead.

def error (msg=None):
    global _command_line
    if _command_line is None:
        raise Exception('Cannot be called except in the context of run')
    _command_line.error(msg)

##  Deprecated.  Use shift instead.

def run (main):
    global _command_line
    p = _CommandLineParser()
    _command_line = p(main)
    _command_line.eval()


#--  Command line processing, v5  ----------------------------------------------

##  Process command-line arguments.

class Shift (object):

    ##  Constructor.  The argv should not include the command, only the arguments.

    def __init__ (self, argv=sys.argv, offset=1):
        self._usage = ''

        ##  The command line.
        self.argv = argv

        ##  Current pointer into argv.
        self.ac = 0

        self._initial_offset = offset

    ##  Set the usage message.

    def set_usage (self, msg):
        if len(self.argv) > 0 and self.argv[0] in ('-?', '--help'):
            print(msg)
            sys.exit(0)
        self._usage = msg

    ##  Print usage.

    def print_usage (self):
        if self._usage:
            print('USAGE:', file=sys.stderr)
            print(self._usage, file=sys.stderr)
        else:
            print('No usage information available', file=sys.stderr)

    ##  Begin processing.

    def __enter__ (self):
        self.ac = self._initial_offset
        return self

    ##  Calls done().

    def __exit__ (self, t, b, tb):
        if t is None:
            self.done()

    ##  Print out an error message, including usage, and quit.

    def error (self, msg):
        print('**', msg, file=sys.stderr)
        self.print_usage()
        sys.exit(1)

    ##  Whether any more arguments remain.

    def peek (self, targ=None):
        if targ is None:
            if self.ac < len(self.argv):
                return self.argv[self.ac]
        else:
            return (self.ac < len(self.argv) and self.argv[self.ac] == targ)

    ##  Whether the next argument is a flag.

    def isflag (self):
        return self.ac < len(self.argv) and self.argv[self.ac].startswith('-')

    ##  If the next argument is a flag, return it and advance.

    def flag (self):
        if self.isflag():
            return self()

    ##  Return the next argument and advance.

    def __call__ (self, targ=None):
        if targ is None:
            if self.ac >= len(self.argv):
                self.error('Too few arguments')
            arg = self.argv[self.ac]
            self.ac += 1
            return arg
        elif self.ac < len(self.argv) and self.argv[self.ac] == targ:
            self.ac += 1
            return True
        else:
            return False

    ##  Return the next argument and advance, if there is a next argument.

    def ifable (self):
        if self.ac < len(self.argv):
            arg = self.argv[self.ac]
            self.ac += 1
            return arg

    ##  Returns True just in case __call__ will succeed.

    def able (self):
        return self.ac < len(self.argv)

    ##  Whether or not we have processed all arguments.

    def isdone (self):
        return self.ac >= len(self.argv)

    ##  Return the remaining arguments as a list, and advance to the end.

    def rest (self):
        args = self.argv[self.ac:]
        self.ac = len(self.argv)
        return args
    
    ##  Check whether all arguments have been consumed.  Signal an error if not.

    def done (self):
        if self.ac != len(self.argv):
            self.error('Too many arguments')


##  An instance of Shift reading sys.argv[1:].
shift = Shift(sys.argv[1:])


#--  Timeout  ------------------------------------------------------------------

##  Exception used when a timeout occurs.

class TimedOut (Exception): pass

##  Runs a timer.

class Timeout (object):

    ##  Constructor.

    def __init__ (self, nsecs):

        ##  How long before the alarm goes off.
        self.nsecs = nsecs

        ##  The timer, in another thread, while running.
        self.timer = None

    ##  Enter.  Starts a timer in a thread.  If the timer goes off before
    #   it is canceled, it raises a TimedOut exception.

    def __enter__ (self):
        self.timer = threading.Timer(self.nsecs, self._alarm)

    def _alarm (self):
        raise TimedOut()

    ##  Exit.  Cancel the timer.  If TimedOut is raised, pass it through.

    def __exit__ (self, t, v, tb):
        self.timer.cancel()
        if t == TimedOut:
            return True


# class Timeout (object):
# 
#     def __init__ (self, nsecs, ontimeout=None):
#         self.nsecs = nsecs
#         self.ontimeout = None
# 
#     def __enter__ (self):
#         signal.signal(signal.SIGALRM, self._alarm)
#         signal.alarm(self.nsecs)
# 
#     def _alarm (self, signo, frame):
#         raise TimedOut()
# 
#     def __exit__ (self, t, v, tb):
#         signal.alarm(0)
#         signal.signal(signal.SIGALRM, signal.SIG_DFL)
#         if t == TimedOut:
#             return True

#  This works, but very heavyweight and clunky!!
#  Requires one to communicate with body via files or pipes!!
#
# class with_timeout (object):
# 
#     def __init__ (self, nsecs, fnc, *args, **kwargs):
#         self.childpid = None
#         self.timedout = False
# 
#         self.childpid = os.fork()
# 
#         # child
#         if self.childpid == 0:
#             fnc(*args, **kwargs)
#             os.kill(os.getpid(), SIGTERM)
# 
#         # parent
#         else:
#             timer = threading.Timer(nsecs, self._alarm)
#             timer.start()
#             (pid, status) = os.wait()
#             if not self.timedout:
#                 timer.cancel()
# 
#     def _alarm (self):
#         os.kill(self.childpid, SIGTERM)
#         self.timedout = True


#  Threading doesn't work.  Threads can't be interrupted, and even the
#  main thread doesn't always response to interrupt_main().
# 
# def _timer_goes_off ():
#     from seal.app.log import DEBUG
#     DEBUG('timer goes off')
#     interrupt_main()
# 
# class Timeout (object):
# 
#     def __init__ (self, nsecs, ontimeout=None):
#         self.timer = None
#         self.nsecs = nsecs
#         self.ontimeout = ontimeout
# 
#     def __enter__ (self):
#         self.timer = threading.Timer(self.nsecs, _timer_goes_off)
#         from seal.app.log import DEBUG
#         DEBUG('** starting timer, nsecs=', self.nsecs, 'thread=', repr(threading.current_thread()))
#         self.timer.start()
# 
#     def __exit__ (self, t, v, tb):
#         from seal.app.log import DEBUG
#         DEBUG('** cancelling timer', 't=', t)
#         self.timer.cancel()
#         if t == KeyboardInterrupt:
#             DEBUG('** got an interrupt')
#             if self.ontimeout is not None:
#                 self.ontimeout()
#             # suppress the exception
#             return True


#--  Elapsed Time  -------------------------------------------------------------

##  Prints out as elapsed time since it was created.

class Timer (object):

    ##  Constructor.

    def __init__ (self):

        ##  The start time.
        self.start = time()

    ##  Prints elapsed time.

    def __str__ (self):
        return elapsed_time_str(self.start, time())

##  Time difference, in human-readable form.

def elapsed_time_str (start, end):
    return timestr(end - start)

##  Readable string showing an amount of time.

def timestr (nsec):
    nhr = 0
    nmin = 0
    if nsec < 1:
        return '%.4f ms' % (nsec * 1000)
    if nsec >= 60:
        nmin = int(nsec / 60)
        nsec -= nmin * 60
        if nmin >= 60:
            nhr = int(nmin / 60)
            hstr = int(nhr)
            nmin -= nhr * 60
    intsec = int(nsec)
    fraction = nsec - intsec
    return '%d:%02d:%02d%s' % (nhr, nmin, intsec, ('%.4f' % fraction)[1:])


#--  Progress Monitor  ---------------------------------------------------------

##  A progress monitor.

class Progress (object):

    ##  Constructor.

    def __init__ (self, n):

        ##  How many ticks are expected in total.
        self.target = n

        ##  How many ticks have already taken place.
        self.count = 0

        ##  To keep track of elapsed time.
        self.timer = Timer()

    ##  Increment by n ticks (default 1).  Prints/updates a progress message.

    def __iadd__ (self, n=1):
        if self.count < self.target:
            self.count += n
            end = ' '
            if self.count >= self.target:
                self.count = self.target
                end = '\n'
            proportion_done = self.count/float(self.target)
            now = time()
            elapsed = now - self.timer.start
            est_total = elapsed/proportion_done
            print('\rProgress: %d/%d (%2.2f%%)' % (self.count, self.target, 100 * proportion_done),
                  'Time remaining: %s' % elapsed_time_str(elapsed, est_total),
                  end=end,
                  file=sys.stderr)
            sys.stderr.flush()
        return self


#--  Load module  --------------------------------------------------------------

##  Load a module, given a fully qualified name.

def load_module (name):
    names = name.split('.')
    module = file = path = None
    try:
        for name in names:
            (file, path, desc) = imp.find_module(name, path)
            module = imp.load_module(name, file, path, desc)
            if file is not None: file.close()
            if hasattr(module, '__path__'): path = module.__path__
    finally:
        if file is not None: file.close()
    return module

##  Import a class, given a fully qualified name.

def import_class (spec):
    i = spec.rfind('.')
    if i < 0: raise Exception('Need a fully qualified class name: %s' % spec)
    name = spec[i+1:]
    modname = spec[:i]
    module = importlib.import_module(modname)
    try:
        cls = module.__dict__[name]
    except KeyError:
        raise Exception('No class named %s in %s' % (name, modname))
    return cls

##  The fully qualified name for a given class.

def class_name (cls):
    return cls.__module__ + '.' + cls.__name__


#--  Manifest  -----------------------------------------------------------------
#
#  A manifest is a listing of the files in a directory tree.  The entries are of
#  form:
#
#      name relpath size [modtime] [hash]
#
#  Options.  By default, all are False:
#
#      symlinks=True:  Follow symlinks.  Signal an error for dangling symlinks
#                      or symlink chains.  If symlinks=False, the entry for a
#                      symlink has the target's name in place of size.
#
#      tmpfiles=True:  Include tmp files.  Tmp file patterns: *~ #*# tmp tmp.* *.tmp
#
#      downcase=True:  Downcase all names.  I.e., case-insensitive matching.
#
#      modtimes=True:  Include modtimes in the output.
#
#      hashes=True:    Include SHA5 hash values in the output.
#

# def manifest (dir, symlinks=False, tmpfiles=False, downcase=False, hashes=False):
#     return sorted(iter_tree(dir, symlinks, tmpfiles))
# 
# def iter_tree (dir, symlinks=False, tmpfiles=False, downcase=False, hashes=False):
#     names = os.listdir(dir)
#     for name in names:
#         fn = os.path.join(dir, name)
#         islink = False
#         size = None
#         modtime = None
#         hash = None
#         if os.path.islink(fn):
#             islink = True
#             tgt = os.readlink(fn)
#             if symlinks:
#                 if not os.path.exists(tgt):
#                     raise Exception('Dangling symlink: %s -> %s' % (fn, tgt))
#                 if os.path.islink(tgt):
#                     raise Exception('Symlink chain: %s -> %s' % (fn, tgt))
#                 fn = tgt
#                 islink = False
#             else:
#                 size = tgt
#         if not islink:
#             if os.path.isdir(fn):
#                 for entry in iter_tree(fn):
#                     yield entry
#                 continue
#             else:
#                 size = file_size(fn)
#                 


#--  Object  -------------------------------------------------------------------

##  A generic object.  One can set attributes as one pleases.
#   (The standard 'object' class does not allow one to set attributes.)

class Object (dict):

    ##  Get an attribute value.

    def __getattr__ (self, name):
        return self.__getitem__(name)

    ##  Set an attribute value.

    def __setattr__ (self, name, value):
        self.__setitem__(name, value)
