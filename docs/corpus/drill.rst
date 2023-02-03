
Drill
=====

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

