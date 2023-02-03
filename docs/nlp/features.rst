
``selkie.features`` — Non-recursive features
============================================

Atoms and AtomSets
------------------

To handle phenomena such as agreement and movement, we need to enrich
syntactic categories with features.  I take a limited approach, in
which only non-recursive features are permitted.

The values of features will be strings or sets of strings.
Sets of strings represent
nodes in a lattice, with ``None`` representing bottom and
the distinguished string ``'*'`` representing top.

The class ``AtomSet`` is used to represent a set of strings.  ``AtomSet`` is a
specialization of ``tuple``.  An atom set will not
work correctly unless its elements are lexicographically sorted; use
the function ``atomset()`` to create one.

>>> from selkie.features import atomset
>>> x = atomset(['sg', 'du', 'pl'])

Atom sets print out in notation that looks like this:

>>> x
du/pl/sg

The function ``atomset()`` returns a string instead of an ``AtomSet`` if
it is given a singleton list:

>>> atomset(['hi'])
'hi'

An atom set behaves like a sorted tuple of strings:

>>> len(x)
3
>>> x[0]
'du'
>>> x[2]
'sg'
>>> 'du' in x
True

The basic operation on atom sets is to take their **meet**, or
intersection.  This is done with the "``*``" operator.

>>> y = atomset(['du', 'pauc', 'pl'])
>>> x * y
du/pl

The meet operation is symmetric.

>>> y * x
du/pl

It also works with atoms as second argument.

>>> x * 'du'
'du'
>>> x * '*'
'*'
>>> x * 'foo'
>>> 

There is also a "join" operation (union):

>>> x + y
du/pauc/pl/sg
>>> x + 'foo'
du/foo/pl/sg
>>> x + '*'
'*'


Values
------

A general value is one of: ``'*'`` (top), an atom set, a string, or
``None`` (bottom).  Three functions are provided that handle general
values.

.. py:function:: meet(v1, v2)

   Returns the meet of two
   values.  The meet is the intersection, viewing the values as sets of atoms.

   >>> from selkie.features import meet
   >>> meet('du', x)
   'du'
   >>> meet('du', 'pl')
   >>> meet('*', x)
   du/pl/sg
   >>> meet(None, x)
   >>>

.. py:function:: join(v1, v2)

   Returns the join of two
   values.  The join is the union, viewing the values as sets of atoms.

   >>> from selkie.features import join
   >>> join('du', x)
   du/pl/sg
   >>> join('du', 'pl')
   du/pl
   >>> join('*', x)
   '*'
   >>> join(None, x)
   du/pl/sg

.. py:function:: subsumes(v1, v2)

   Tests whether
   one value subsumes another.  The subsuming value is more general: a
   superset, viewed as a set of atoms.

   >>> from selkie.features import subsumes
   >>> z = x + y
   >>> subsumes(z, x)
   True
   >>> subsumes(x, z)
   False
   >>> subsumes(x, x)
   True

.. py:class:: selkie.features.Category

   A category consists of a **type** (symbol) and a list
   of **features**.  An example is ``v[sg,i,0]``.
   Instead of using named attributes, we use positional attributes, and
   implement categories as tuples.
   For the example just given, the tuple is ``('v', 'sg', 'i', '0')``.
   
   More precisely, we define the class ``Category`` to be a
   specialization of ``tuple``, and we define the method
   ``__repr__()`` so that categories print out in the square-bracket
   format.
   
   >>> from selkie.features import Category
   >>> cat = Category(['np', x, 'fem'])
   >>> cat
   np[du/pl/sg,fem]
   
   A category can be accessed the same way one accesses a tuple:
   
   >>> cat[0]
   'np'
   >>> cat[1]
   du/pl/sg
   >>> len(cat)
   3
   
   The features by themselves can be accessed this way:
   
   >>> cat[1:]
   (du/pl/sg, 'fem')

Variables and bindings
----------------------

The categories in a rule may contain variables, in addition to
constant values.  An example of a rule with variables is the
following.  Variables are distinguished from constants by beginning
with an underscore::

   VP[_f] -> V[_f,i,0]

We permit variables *only* in categories in rules.  They may not
appear in categories in trees.

I use a representation for variables that maximizes simplicity.  When
digesting a rule, the variables are numbered as they are encountered, and
the variable number (starting from 0) represents the variable.  This
has the virtue that a set of bindings for a variable can simply be a
list, indexed by the variables.  For example, the rule::

   VP[_f] -> V[_f,i,_p] PP[_p]

is internally represented as::

   ('VP', 0) -> ('V', 0, 'i', 1) ('PP', 1)

If the variable ``_f`` has value ``'sg'`` and ``_p`` has value
``'to'``, then the bindings are represented by the list::

   ['sg', 'to']

Here is an example of creating a category that contains a variable:

>>> v = Category(['V', 0, 'i', '0'])
>>> v
V[_0,i,0]
>>> v[0]
'V'
>>> v[1]
0
>>> v[3]
'0'

Note that variable ``0`` prints out as ``_0``.

Category unification
--------------------

Categories do not have to be identical to match.  Consider the following
example.

We begin with the node 1``V[sg,i,*]``2 at
the bottom center.  Note that "``*``"
is a wildcard: it matches any value.  After creating this node,
the parser performs the ``start`` action, which looks up
continuations of ``V[sg,i,*]``.  It finds the VP rule at the top left.  Written as
tuples, the rule categories and child-node category look like this::

   ('VP', 0) -> ('V', 0, 'i', 1) ('PP', 1)
   ('V', 'sg', 'i', '*')


The rule also contains bindings for the two variables.  Initially, both
values are wildcards: ``['*', '*']``.
Matching the child category against the first righthand side category
is called **unification**::

   ('V', 0, 'i', 1) * ('V', 'sg', 'i', '*')


This is equivalent to replacing the variables with their values, and
comparing each of the corresponding pairs of features.  If all pairs
match, a new set of bindings is created::

   ('V', '*', 'i', '*') * ('V', 'sg', 'i', '*')
   b[0] = '*' * 'sg'
   b[1] = '*' * '*'

Unification is a non-destructive process.  Its output is the new set
of bindings.  In this case::

   ['sg', '*']

The ``start`` operation creates the first edge: the oval at the
left end of the middle row.
The next step is to ``combine`` that edge with the second child.
We unify the category after the dot with the category of the second child::

   ('PP', 1) * ('PP', 'to')

which is::

   ('PP', '*') * ('PP', 'to')
   b[1] = '*' * 'to'

The unification succeeds, and the output is the set of bindings::

   ['sg', 'to']

The result of the ``combine`` operation is the new edge, with the
dot at the end.

Finally, we call the ``complete`` operation on the finished edge.
This creates a new node whose category is obtained by
**substituting** the edge bindings into the lefthand side category::

   ('VP', 0) * ['sg', 'to'] = ('VP', 'sg')


Category operations
-------------------

With this overview in mind, we turn to a more detailed consideration
of the implementation.  The most basic function is **meet**, which
we have already discussed.  It
combines two values *u* and *v*.  Specifically, if *u=v*, it returns
*u*, and if either *u* or *v* is the wildcard, it returns the other
one.  Otherwise, it fails (returns ``None``).

>>> n1 = Category(['n', 0, atomset(['du', 'pl'])])
>>> n1
n[_0,du/pl]
>>> n2 = Category(['n', 'fem', atomset(['sg', 'pauc', 'pl'])])
>>> n2
n[fem,pauc/pl/sg]
>>> meet(n1[2], n2[2])
'pl'
>>> meet(n1[2], '*')
du/pl
>>> meet(n1[2], None)

.. py:function:: unify(x, y, b)

   Takes two categories and a set of
   bindings, and returns a new set of bindings if the categories match,
   or ``None`` if they do not match.  Specifically:

    * Make a fresh copy of the bindings, so that updates to the
      bindings do not affect the original.
   
    * It fails if the types are different: i.e., if *x[0] != y[0]*.
   
    * Otherwise, it calls ``meet()`` on each element *u=x[i]* and *v=y[i]*, for *i>0*.
      If *u* is a variable, call it "the variable," and let *u*
      be its value: *u = b[u]*.
   
    * If *v* is a variable, signal an error
   
    * Let the new value be ``meet``*(u,v,b)*; fail if ``meet`` fails.
   
    * If there is a variable, store the new value back into *b*.
   
    * The return value is the new set of bindings, or ``None`` on failure.
   
   Example:

   >>> from selkie.features import unify
   >>> b = unify(n1, n2, ['*'])
   >>> b
   ['fem']

.. py:function:: subst(b, x)

   This function is used by
   ``complete()`` to create the category for a new node.  It
   returns a copy of the category (tuple) in which each variable is
   replaced with its value.

   >>> from selkie.features import subst
   >>> n1
   n[_0,du/pl]
   >>> subst(b, n1)
   n[fem,du/pl]


Declarations
------------

A ``Declarations`` object supports the following functionality:

 * Defining names for atom sets.  Top (``'*'``), bottom (``None``),
   the atoms, and all atomsets that can be formed from them, constitute
   the feature lattice.  Being able to name atom sets means that we can
   assign a name to any node in the lattice.  With the addition of
   defined names, we can think of feature names as **types**, the
   extension of a type being the set of atoms that it subsumes.

 * Defining the number of attributes that a category takes, along with
   their types and default values.  This permits us to use keyword
   feature specifications in addition to positional specifications.
   It is also useful for detecting errors in grammars, when an
   inappropriate value is assigned to an attribute.

A declaration consists of two pieces: a feature table and a category table.

.. py:class:: FeatureTable

   Contains named features, including both atoms and
   features that name sets of atoms.  Each feature may be assigned a
   default value.

   .. py:method:: define(name, def, dflt)

      The basic FeatureTable method.  It takes the name
      to define, its definition, and a default value.  The default value
      must be subsumed by the definition.
   
      >>> from selkie.features import FeatureTable
      >>> ftab = FeatureTable()
      >>> ftab.define('vform', atomset(['sg', 'pl', 'ing']), 'sg')
      >>> print(ftab)
      Features:
          <Feature vform ing/pl/sg sg>
   
   .. py:method:: __getitem__(name)

      One can access the FeatureTable as one accesses a dict.
      
      >>> ftab['vform']
      <Feature vform ing/pl/sg sg>
      
      The value is an object of type ``Feature``.  It has ``name``,
      ``value``, and ``dflt`` attributes.
      
      >>> vform = ftab['vform']
      >>> vform.name
      'vform'
      >>> vform.value
      ing/pl/sg
      >>> vform.dflt
      'sg'
   
   .. py:method:: intern(name)
   
      Also accesses the FeatureTable, but records the name as
      an atom, if it is not already present in the table.
      
      >>> ftab.intern('sg')
      'sg'
      >>> print(ftab)
      Features:
          <Feature sg sg sg>
          <Feature vform ing/pl/sg sg>


.. py:class:: CategoryTable

   Contains categories, associated with information
   about the number of features they take, and type restrictions.
   Default values come from the type restrictions.

   .. py:method:: define(cat, params)

      The main method.  It takes the category name and a
      list of ``Parameter`` instances.  A ``Parameter`` consists of a
      name (string) and a type (of class ``Feature``).
      
      >>> from selkie.features import CategoryTable, Parameter
      >>> ctab = CategoryTable()
      >>> ctab.define('vp', [Parameter('form', vform)])
      >>> print(ctab)
      Categories:
          <Entry vp[form:vform]>
      
   .. py:method:: __getitem__(cat)

      A category table is a specialization of dict.  The values are of type
      ``CategoryTable.Entry``.
      
      >>> ent = ctab['vp']
      >>> ent.name
      'vp'
      >>> ent.params
      [form:vform]
      >>> ent.params[0].name
      'form'
      >>> ent.params[0].type
      <Feature vform ing/pl/sg sg>
   
.. py:class:: Declarations(ftab, ctab)

   A ``Declarations`` instance combines a feature table and a category
   table.  If the feature table and category table are not provided,
   empty ones will be created.
   
   .. py:attribute:: features

      A FeatureTable.

   .. py:attribute:: categories

      A CategoryTable.
      
   Examples:

   >>> from selkie.features import Declarations
   >>> decls = Declarations(ftab, ctab)
   >>> decls.features == ftab
   True
   >>> decls.categories == ctab
   True
   >>> print(decls)
   Features:
       <Feature sg sg sg>
       <Feature vform ing/pl/sg sg>
   <BLANKLINE>
   Categories:
       <Entry vp[form:vform]>
   
   .. py:method:: scan_category(stream)
   
      Scans a category from a token stream.  See
      :py:func:`scan_category` below.

   .. py:method:: unscan_category(cat, stream)
   
      Identical to the ``unscan_category()`` function.


Scanning
--------

.. py:function:: scan_category(stream)

   Scans a category from a token
   stream.  It uses a syntax in which the only special characters are ``[:/,]``.
   It restores the original syntax after scanning.
   
   >>> from io import StringIO
   >>> from seal.core.io import iter_tokens
   >>> tokens = iter_tokens(StringIO('np[{},a/b] {hi}'))
   >>> from selkie.features import scan_category
   >>> scan_category(tokens)
   np[{},a/b]
   >>> next(tokens)
   '{'

   The ``Declarations.scan_category()``
   method allows one to use defined features and keyword features.

.. py:function:: write_category(cat, out)

   Writes a category to an
   outfile in a format that will be correctly scanned.
   This is actually used by the ``__repr__()`` method of ``Category``.

   >>> cat = Category(['np', 'hi', atomset(['/', ','])])
   >>> cat
   np[hi,','/'/']

   The ``__repr__()`` method essentially does the following:
   
   >>> from io import StringIO
   >>> from selkie.features import write_category
   >>> with StringIO() as f:
   ...     write_category(cat, f)
   ...     s = f.getvalue()
   ...
   >>> s
   "np[hi,','/'/']"




