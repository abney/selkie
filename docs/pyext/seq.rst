
.. :py:module:: selkie.seq

``selkie.seq`` — Sequences and iterators
========================================

List-producing functions
------------------------


The functions ``as_list()``, ``repeatable()``, ``concat()``, ``unique()``,
and ``cross_product()`` produce lists as output.

**As list.**
The function ``as_list()`` converts any item *x* to a list.

If *x* is ``None``, it returns the empty list.
If *x* is a list, it returns *x* itself.
If *x* is a sequence, it returns ``list(*x*)``.
If *x* is has attribute "``next``," it takes *x* to be a
generator and returns ``list(*x*)``.
Otherwise, it returns ``[*x*]``.


**Repeatable.**
A generator can only be used once, whereas iterables such as lists,
tuples, sets, and dicts can be iterated over multiple times.
The function ``repeatable()`` converts a generator into a list, but
leaves other iterables alone.  It coerces ``None`` to the empty
list, but otherwise signals an error if its input is not an iterable.
It assumes that any object with a ``next`` attribute is a generator,
and any object with an ``__iter__``
attribute is an iterable.

**Unique.**
The function ``unique()`` takes a list as input and produces a list
with all duplicates removed.  The list does not need to be sorted, nor
do duplicates need to be adjacent to each other.  The algorithm is
naive (quadratic), so it is only appropriate for short lists.

>>> from selkie.seq import unique
>>> unique([4, 2, 4, 1, 2])
[4, 2, 1]

**Cross product.**
The function ``cross_product()`` takes a single argument, a list of
lists, and produces the cross product of those lists as output.

>>> from selkie.seq import cross_product
>>> cross_product([['a', 'b'], [1, 2], [42]])
[('a', 1, 42), ('a', 2, 42), ('b', 1, 42), ('b', 2, 42)]


Sorted lists
------------


The functions ``intersect``, ``union``, and ``difference``
expect sorted lists as input.  Their behavior is unpredictable if they
are given unsorted lists.

>>> from selkie.seq import intersect, union, difference
>>> x = [1,3,5,6,7]
>>> y = [2,3,4,7,8]
>>> intersect(x,y)
[3, 7]
>>> union(x,y)
[1, 2, 3, 4, 5, 6, 7, 8]
>>> difference(x,y)
[1, 5, 6]
>>> difference(y,x)
[2, 4, 8]


Queue
-----

A ``Queue`` is a first-in first-out queue.  The method ``write()``
inserts an element at the tail of the queue, and ``read()`` removes
and returns the element at the head of the queue.

It is implemented as a buffer with head and tail pointers.  Initially
the buffer is empty.  If the tail is at the end of the buffer, new
elements are appended to the buffer and the buffer grows.
When the queue is empty, the head and tail are reset to 0.

Space in the buffer before the head is "wasted" space.  If the
wasted space exceeds a threshold (``maxwaste``), the contents of the
queue are relocated so that the head is 0.  One can specify ``maxwaste``
when creating the queue; by default it is 10.  Setting ``maxwaste``
to ``None`` prevents the
contents from being relocated (though the head and tail will still be
reset to 0 if the queue becomes empty).

The elements in the queue can be accessed and set by index.

Edit distance
-------------

Edit distance works with sequences generally, not just strings.
To create and use an edit distance function:

>>> from selkie.seq import EditDistance
>>> distance = EditDistance()
>>> distance('testy', 'tezt')
2

By default, it uses the function ``simple_distance()``, which
imposes a cost of 1 for each insertion, substitution, or deletion.
One can provide a new cost function when instantiating
EditDistance.  A cost function should take two arguments, *x*
and *y*, representing a deletion if *y* is None, and
insertion if *x* is None, and a substitution, if neither is
None.  The return value should be a number, possibly math.inf.

Generators
----------

The following functions are provided that relate to generators:
``chain()``,
``nth()``, ``head()``, ``tail()``, ``more()``,
``product()``, ``count()``, and ``counts()``.

For the purpose of illustration, let us define a little generator:

>>> def pots ():
...     for i in range(11):
...         yield 2**i
... 
>>> list(pots())
[1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]

**Chain.**
The function ``chain()`` is imported from ``itertools``.
It concatenates multiple generators.

**Nth.**
The function ``nth()`` returns a particular item from an iterator.

>>> from selkie.seq import nth
>>> nth(pots(), 2)
4

Remember that an iterable is consumed as one iterates through it.  In
the example just given, we created a new generator by calling ``pots()``.
If we use its value, though, we need to be careful:

>>> iter = pots()
>>> nth(iter, 2)
4
>>> list(iter)
[8, 16, 32, 64, 128, 256, 512, 1024]

Note that ``nth()`` consumed the first three items.
One use of ``nth`` is to jump to problematic cases in a large
iteration.  An idiom for finding such cases in the first place is the
following::

   for i, x in enumerate(myiteration):
       if isproblematic(x):
           return i

**Head, tail.**
The functions ``head()`` and ``tail()`` are also provided for
inspecting parts of a large iterable.

>>> from selkie.seq import head, tail
>>> head(pots())
[1, 2, 4, 8, 16]
>>> tail(pots())
[64, 128, 256, 512, 1024]

An optional argument specifies how many items one would like to have:

>>> head(pots(), 3)
[1, 2, 4]
>>> tail(pots(), 3)
[256, 512, 1024]

A more general function is ``islice``, from the standard
``itertools`` module.

>>> from itertools import islice
>>> list(islice(pots(), 2, 5))
[4, 8, 16]

**More.**
The function ``more()`` calls ``print`` on each item in turn,
pausing after a pageful of items has been displayed.  Hitting return
causes another page to be displayed, and hitting 'q' then enter causes
``more()`` to quit.

One can adjust the pagesize by setting ``more.pagesize``.  For
example::

   >>> more.pagesize = 4
   >>> more(pots())
   1
   2
   4
   8
   q

**Product.**
The function ``product()`` is analogous to ``sum()``.  It takes an
iterable containing numbers, and returns the product of the numbers.

**Count.**
The function ``count()`` is analogous to ``len()``, except that it
works for generators as well as lists and other iterables.

>>> from selkie.seq import count
>>> count(pots())
11

Note that ``count`` is unrelated to ``itertools.count()``.  The
latter returns an infinite iterator that generates the natural
numbers.

**Counts.**
The function ``counts()`` creates a table of counts of occurrences.

>>> from selkie.seq import counts
>>> tab = counts('abracadabra')
>>> sorted(tab.items())
[('a', 5), ('b', 2), ('c', 1), ('d', 1), ('r', 2)]

