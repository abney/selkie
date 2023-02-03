
``selkie.textgrid`` — Praat textgrid
====================================

Interface
---------

.. py:class:: TextGrid(fn)

   The class ``TextGrid`` represents a Praat text grid.
   The argument *fn* is optional.  If provided, it
   is a pathname that is passed to ``load()``.  One may also provide
   encoding as a keyword argument.  (Note that recent versions of
   Praat write UTF-16 files rather than the standard UTF-8.)

   >>> from selkie.data import ex
   >>> from selkie.textgrid import TextGrid
   >>> grid = TextGrid(ex('northwind.TextGrid'), encoding='utf16')

   A TextGrid has the following members:
   
   .. py:attribute:: xmin

      The start time of the span covered by the grid.

   .. py:attribute:: xmax

      The end time.

   .. py:attribute:: tiers

      A list of ``Tier`` instances.
   
   In addition, a ``TextGrid`` provides the following methods:
   
   .. py:method:: load(fn)

      Load the contents from filename *fn*.

   .. py:method:: save(fn)

      Save it to a file with filename *fn*.

   .. py:method:: __len__()

      The number of tiers.

   .. py:method:: __getitem__(idx)

      If *idx* is an integer, returns the tier at that position.
      If *idx* is a pair (i, j), returns the *j*-th element of the *i*-th tier.

   .. py:method:: __delitem__(i)

      Delete the *i*-th tier.

   .. py:method:: add_tier(type, name)

      Add a new tier with the given type and name.
      The type should be either ``'IntervalTier'`` or ``'TextTier'``.

   .. py:method:: clone()

      Creates a new copy of the text grid.  The tiers are
      *not* copied.  One should be sure to clone any of the tiers
      that one wishes to modify, e.g.:
   
      >>> grid[1] = grid[1].clone()

.. py:class:: Tier

   A ``Tier`` is created by calling the ``TextGrid`` method ``add_tier()``.
   Although not currently enforced, the following members should be
   treated as read-only.
   
   .. py:attribute:: type

      Either ``'IntervalTier'`` or ``'TextTier'``.

   .. py:attribute:: dtype

      The actual type of the elements, which is either
      ``Interval`` or ``Point``.

   .. py:attribute:: name

      The name.

   .. py:attribute:: xmin

      Inherited from the ``TextGrid``.

   .. py:attribute:: xmax

      Inherited from the ``TextGrid``.

   .. py:attribute:: contents

      A list of elements, which are either ``Intervals``
      or ``Points``.

   .. py:attribute:: symtab

      If the tier has been converted to an array, this will
      contain the symbol table used.  It maps strings to ints.
   
   A ``Tier`` also provides the following methods:
   
   .. py:attribute:: __len__()

      The number of elements in the tier.

   .. py:attribute:: __getitem__(i)

      The *i*-th element.

   .. py:attribute:: x()

      The last time point covered by an element in the
      contents.  A freshly-created tier is empty, and the value is xmin.  As
      elements are added to the tier, the value is the xmax of the most
      recently added element.

   .. py:attribute:: add(*args, **kwargs)

      Add an element to the tier.  The arguments are passed to the element constructor.

   .. py:attribute:: array()

      Returns a time series, that is, a two-column matrix in
      which the first column is a time point and the second column contains
      symbol codes.  The symbol table used to convert strings to symbol codes
      is stored in member ``symtab``.  There is one row for each element
      in the tier.  The time points are obtained by calling ``center()``
      on each element, and the symbol codes are obtained by calling ``symbol()``.

   .. py:attribute:: clone()

      Creates an identical but independent copy of the
      tier.  All elements are also copied.


.. py:class:: Interval

   In general, one only creates an ``Interval`` by calling the ``add()``
   method of a ``Tier``.  One should provide the keyword arguments ``text``
   and ``xmax``.

   An ``Interval`` has the following members, which should be
   considered read-only.
   
   .. py:attribute:: tier

      The tier that it belongs to.

   .. py:attribute:: xmin

      Its start time.

   .. py:attribute xmax

      Its end time.

   .. py:attribute text

      A string.
   
   The following methods are provided:
   
   .. py:method:: string()

      Returns the text.

   .. py:method:: center()

      Returns the mean of ``xmin`` and ``xmax``.

   .. py:method:: symbol(tab)

      Returns the result of interning the text in the
      symbol table *tab*.
   
.. py:class:: Point

   In general, one only creates a ``Point`` by calling the ``add()``
   method of a ``Tier``.  One should provide the keyword arguments
   ``number`` and ``mark``.

   A ``Point`` has the following members, which should be considered read-only:
    
   .. py:attribute:: tier

      The tier that it belongs to.

   .. py:attribute:: number

      The time (a float).

   .. py:attribute:: mark

      A string.

   .. py:attribute:: string()

      Returns the mark.

   .. py:attribute:: center()

      Returns the time.

   .. py:attribute:: symbol(tab)

      Interns the mark in the symbol table *tab* and
      returns the resulting code.
