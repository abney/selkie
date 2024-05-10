      
Language-learning support
=========================

A Course is a sequenced
list of lessons.  A **lesson** is a list of lexical entries.
A **selection** is also a list of lexical entries; it may be either
a lesson or an ad hoc list, e.g., a list of review items drawn at
random or based on user history.
It would be easiest for the user if there is a single course for
each language.  We will need web pages for editing lessons and courses.

To run a drill, we first construct a selection, then we
present the selected items one at a time, and for each, get a response
from the user and display feedback.
It will be simplest if there is a single web page displaying the
feedback from the previous item, followed by the presentation of the next item.  That
means all state is kept in the server.

As a first approximation, user state consists in the list of lessons
completed, the current selection, the current position in the
selection, and a digest of user history.

Drill
-----

The drill pool is represented by a collection, which is viewed as a
list of vocabularies.  Let us call vocabularies "units" and words in
the vocabulary "items".

Each item ``x`` has a refresh duration ``x.d`` and a last visit time
``x.t``.  The numeric values of durations are in a table ``dur``; the
actual refresh duration is ``dur[x.d]``.

The target time for repeating item ``x`` is ``T = x.t + dur[x.d]``.
An item is overdue by ``now - T``, if that is positive.

We maintain a heap of visited items sorted by their target time, and
we have a pointer to the next unvisited unit.

Drilling is done by batch.  If the item at the top of the heap is due
(``T <= now``), the batch is formed by taking the top 20 items, or all
the items that are due, if there are less than 20.  If the top item is
not yet due, a new unit is started, and the unit point is advanced.
Each item in the new unit is assigned ``x.d = 0``.

The batch is shuffled, and then each item is presented in turn.  If
the answer is correct, do ``x.d += 1``, and if not, do ``x.d = 0``.
In either case, set ``x.t = now``.

What needs to be persistent is the next-unit pointer and the values of
``x.d`` and ``x.t`` for every visited item.

