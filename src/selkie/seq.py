
from math import inf
from itertools import islice


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

def dups (items):
    counts = {}
    for item in items:
        if item in counts:
            if counts[item] == 1:
                yield item
            counts[item] += 1
        else:
            counts[item] = 1
