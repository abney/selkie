
from math import inf
from itertools import islice
from collections.abc import Sequence


#--  Lists  --------------------------------------------------------------------

def as_list (x):
    '''
    Converts x to a list.

     * None becomes the empty list.
     * Tuples, sets, frozensets, ranges, dicts, and iterables are passed to list().
       (An iterable is anything with method ``__next__()``.)
     * Anything else is wrapped in a (single-element) list.

    '''
    if x is None: return []
    elif isinstance(x, list): return x
    elif isinstance(x, (tuple, set, frozenset, range, dict)): return list(x)
    elif hasattr(x, '__next__'): return list(x)
    else: return [x]


def single (x):
    '''
    Takes an iterable and returns its sole element.
    Signals an error if the iterable does not contain exactly one element.
    '''
    it = iter(x)
    first = next(it)
    try:
        next(it)
        raise Exception('Multiple items in iterator')
    except StopIteration:
        return first


def repeatable (x):
    '''
    The return value is something that has method ``__iter__()``.
    
     * If *x* is None: returns the empty list.
     * If *x* already has method ``__iter__()``, it is returned.
     * If *x* has method ``__next__()``, then ``iter(x)`` is returned.
     * Otherwise an error is signalled.

    '''
    if x == None: return []
    elif hasattr(x, '__iter__'): return x
    elif hasattr(x, '__next__'): return iter(x)
    else: raise Exception('Does not appear to be iterable: %s' % repr(x))


def concat (lists):
    '''
    Concatenates multiple lists.
    '''
    out = []
    for list in lists:
        out.extend(list)
    return out


def unique (elts):
    '''
    Eliminates duplicates from a list.  Otherwise preserves order.
    '''
    out = []
    for elt in elts:
        if elt not in out:
            out.append(elt)
    return out


def cross_product (lists):
    '''
    Cross product.
    '''
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
    '''
    One optionally provides a loss function when instantiating EditDistance.
    The loss function should take two items and return 0 if they are identical
    and a number greater than 0 if not. The default is 0-1 loss.
    An instance of EditDistance is a function that returns the edit distance
    between two sequences.
    '''

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

def uniq (sortedlst):
    '''
    Eliminates duplicates, assuming that the list is sorted.
    '''
    out = []
    for elt in sortedlst:
        if len(out) == 0 or elt != out[-1]:
            out.append(elt)
    return out


def intersect (list1, list2):
    '''
    Intersects two sorted lists.  Unpredictable results if the lists are not
    sorted.
    '''
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


def union (list1, list2):
    '''
    Takes the union of two sorted lists.  Unpredictable results if the lists
    are not sorted.
    '''
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


def difference (list1, list2):
    '''
    Returns the set difference of two sorted lists.  Unpredictable results if
    the lists are not sorted.
    '''
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

class Queue (object):
    '''
    A queue.  It uses a circular buffer.
    The ``write()`` method adds an object to the end of the queue.
    The ``read()`` method takes an object from the head of the queue.
    '''

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



#--  Index  --------------------------------------------------------------------

class Index (dict):
    '''
    A specialization of dict in which keys are associated with lists of values
    instead of single values. Setting a value actually appends it to the list
    values. The method ``add()`` is available as a synonym. The method
    ``count(key)`` returns the number of values for the given key, and
    ``delete(key,val)`` deletes one of the values, leaving the others in place.
    '''
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


#--  Iterables  ----------------------------------------------------------------

def nth (iter, n):
    '''
    Returns the n-th item of iterable g, counting from 0, and counting from the
    current position of the iterator's "read head."  For example:

    >>> from selkie.pyx.seq import nth
    >>> import itertools
    >>> c = itertools.count(0)
    >>> nth(c, 3)
    3
    >>> nth(c, 3)
    7

    The iterator I{c} generates the natural numbers, beginning with 0.  The
    first call to C{nth} returns the fourth item, which is the number 3.
    The second call begins where the first left off, and returns the
    fourth item, which is the number 7.

    Note that one can achieve the same functionality this way:

    >>> c = itertools.count(0)
    >>> next(itertools.islice(c, 3, 4))
    3

    One use of nth is to jump to problematic cases in a large
    iteration.  An idiom for finding such cases in the first place is the
    following::

        for (i, x) in enumerate(myiteration):
            if isproblematic(x):
                return i

    '''
    try:
        count = 0
        while count < n:
            next(iter)
            count += 1
        return next(iter)
    except StopIteration:
        return None


def head (iter, n=5):
    '''
    Returns a list containing the first *n* elements from the iteration.
    '''
    return list(islice(iter, n))


def tail (iter, n=5):
    '''
    Returns a list containing the last *n* elements from the iteration.
    '''
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


def product (nums):
    '''
    The product of a list of numbers.
    '''
    prod = 1
    for num in nums:
        prod *= num
    return prod


def count (iter):
    '''
    Counts up how many items are contained in
    (or remain in) the given iterable.
    '''
    return sum(1 for x in iter)


def counts (iterable):
    '''
    Creates a map whose keys are items in the given iterable, and whose value for
    a given item is the frequency of occurrence of that item in the iteration.
    All items are consumed.
    '''
    dict = {}
    for item in iterable:
        if item in dict:
            dict[item] += 1
        else:
            dict[item] = 1
    return dict


#--  ListWrapper, MapWrapper  --------------------------------------------------

class LazyList (Sequence):
    '''
    An abstract class. Its ``__init__()`` method requires an iterable. Elements
    will be fetched from the iterable only on demand, so one should be cautious about
    changing the underlying element source during the lifetime of the LazyList.
    '''

    def __init__ (self, iterable):
        self.__expanded = []
        self.__iter = iter(iterable)

    def __iter__ (self):
        return LazyListIterator(self)

    def _fully_expanded (self):
        return self.__iter is None
    
    def _advance (self):
        if self._fully_expanded():
            raise IndexError('list index out of range')
        try:
            self.__expanded.append(next(self.__iter))
        except StopIteration:
            self.__iter = None

    def __getitem__ (self, i):
        while len(self.__expanded) <= i:
            self._advance()
        return self.__expanded[i]

    def __len__ (self):
        while not self._fully_expanded():
            self._advance()
        return self.__expanded.__len__()

    def __repr__ (self):
        if self._fully_expanded():
            return repr(self.__expanded)
        else:
            with StringIO() as f:
                f.write('[')
                first = True
                for item in self.__expanded:
                    if first: first = False
                    else: f.write(', ')
                    f.write(repr(item))
                if not self._fully_expanded():
                    f.write(', ...')
                f.write(']')
                return f.getvalue()
