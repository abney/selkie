
``selkie.avs`` — Recursive feature structures
=============================================

The examples assume:

>>> from selkie.avs import *

``Selkie.features`` is much better for use in grammars.  They are not
recursive, but they are much more efficient.  ``Selkie.avs`` is an
implementation of fully recursive feature structures.  It
may be used for (one version of) semantic interpretation.

My current implementation is probably much too complicated.  I
should do a more traditional implementation in which there are
variables only when explicitly required (for re-entrancies and for
empty values), and in which an AVS is an AV list combined with a
symbol table.

Rationale
---------

We want to support both parsing and generation.  We associate an AV
*state* with each rule, which contains an AVS for the parent
node, and attribute paths indicating where to unify in each of the
children.

We wish to be use AVS's to represent semantic translations, which grow
as the sentence grows.  But to be efficient, we need to be able to
assure that the space and time involved in processing any single node
does not increase as the tree gets larger.

The approach we have taken is to copy pieces of structure in a lazy
fashion.  One can construct pathological cases in which the amount
that must be copied grows without bound, but most natural cases should
require copying only the upper reaches of the input structures.

Data structures
---------------

Here is an example of a typed attribute-value structure; let us call
it *A*::

   [<0>[foo hi]
    bar <1>[foo bye]
    baz <1>]

Our implemention is similar to the implementation of a
``Category``.  The atoms are either *variables* (the
angle-bracketed numbers in the example) or *constants* (strings).  As with
categories, we use the simple expedient of representing variables as
integers.  The variable 0 has special significance; it represents the
root of the structure.

We will at times be dealing with variables from multiple AVS's.
Typically one AVS will be the *local* AVS and the other is the
*foreign* AVS.  A particular numeric value *v* represents two
different variables: one a local variable and the other a foreign variable.

The bracketed structures are *AV lists*.
An AV list is a list of attribute-value pairs.  An attribute is
a string.  A value is an atom:
that is, either a constant or a variable.  For the sake of efficiency, we keep
attributes alphabetically sorted.

An AV list also keeps a pointer to the AVS that it belongs to.  The
variables in an AV list are local to its AVS.  An AV
list belonging to a foreign AVS is to be considered immutable.

An AVS is just a symbol table.  Since variables are ints, we can
represent the symbol table as a list.
Each value in the symbol table may be an atom, an AV list, or
None.  In the case where the value is another variable, we say
that the original variable has been *redirected*.  In the case
where the value is None, the variable is called a
*dangling variable*.
The numeric value -1 is special, and represents a value
that is temporarily unavailable.

The function ``parse_avs()`` can be used to
create AVS *A* from a string representation, as follows.

>>> avs1 = parse_avs('[foo hi; bar [foo bye]; baz = bar]')

The AVS prints in its string form:

>>> print(avs1)
[bar [foo bye]
 baz = bar
 foo hi]

The ``raw()`` method returns a string showing the internal structure.

>>> print(avs1.raw())
AVS 0:
    0 -> [bar:1, baz:1, foo:hi]
    1 -> [foo:bye]

To summarize, an attribute value or **atom** is one of:

 * a constant, or
 * a variable (foreign if the AV list is foreign).

A **variable value** is one of:

 * a constant,
 * a variable (local),
 * an AV list,
 * ``Top``, or
 * -1.

AVS unification
---------------
   
The basic operation on AVS's is unification, which essentially takes
the meet of two AVS's.
Let *B* be the following AVS::

   [<0>[bar <1>[cat <2>[meow <4>]]]
    baz <3>[dog <2>]]

AVS *B* is represented internally as::

   {0: [('bar', 1), ('baz', 3)],
    1: [('cat', 2)],
    2: [('meow', 4)],
    3: [('dog', 2)],
    4: None}

Lazy copying
------------

One use for AVS's is to represent semantic
interpretations, which grow as the sentence grows.  We would also like
to use unification interleaved with parsing and
generation operations.  This is especially important for generation,
where the AVS specifies what should be generated.  Hence we would like
an implementation of unification that is nondestructive, but only
copies a limited amount of structure no matter how large the AVS's
grow.

The approach we take is to allow a variable's value to be a foreign AV
list, but to copy a variable into the working AVS whenever we need to
change its value.  We keep a temporary *import table* for the
working AVS, containing entries of form::

   (avs, u): v

meaning that variable *u* of AVS *avs* has been imported as
variable *v* of the working AVS.

Importing a variable *v* means that every reference to *v* in the
original AVS must be replaced.  That is, every AV list containing a
reference to *v* must be imported into the working AVS.  We can find
such AV lists by keeping track of the *parents* of a variable,
defining *u* to be a parent of *v* just in case *u*'s value is an AV
list containing a reference to *v*.

Importing an AV list may cause us to import additional variables.
Each AV list belongs to a particular AVS, and each variable in the AV
list is a local variable with respect to that AVS.  When we import the
AV list, we must replace its variables with variables that are local
to the working AVS.

Let us consider an example.  Suppose we wish to create an AV list
containing a reference to variable 2 of *B*.  To do so, we need to
import (B,2).  If we import (B,2), we must also import its
parents and the parents' values.  There are two parents: (B,1) and
(B,3).  Their values contain references to (B,2) that will need to
be replaced, but no new variables.  However, we must also import the
parent of (B,1) and the parent of (B,3) - they have the same
parent, namely, (B,0).  Assume that the working
AVS already has one entry, so that we start with local variable 1.
Here are the resulting import table entries::

   (B,2): 1
   (B,1): 2
   (B,3): 3
   (B,0): 4

Further, we add the following entries to the working AVS:

   1: *B* [('meow', 4)]
   2: [('cat', 1)]
   3: [('dog', 1)]
   4: [('bar', 2), ('baz', 3)]

Notice that the value of variable 1 is the foreign AV list, belong to
AVS *B*.  When we access the value, the result will be a *foreign variable*
represented by the pair (B,4).

Normalization
-------------

**Dereferencing**.
Dereferencing consists
in chasing a chain of redirects until we arrive at a variable whose value is
something other than another variable.  An error is signalled if -1
is encountered.  If the value is a constant,
the result of dereferencing is the constant.  Otherwise, the result is
the variable itself.  In short, the possible return values are:

 * constant, constant
 * v, avlist
 * v,* None

The first value is the dereferenced atom, and the second is its
value.  A constant's value is the constant itself.  A dereferenced
variable's value is an AV list or None.

In our example, both variables have AV lists as values, so
dereferencing has no effect.

The unification algorithm
-------------------------

We begin by creating a new, empty AVS to hold the result of
unification.  The two input AVS's are not to be modified.
We will consider the unification of *A* and *B*.  The initial task is
to unify (A,0) with (B,0).  We first import both foreign
variables, then we unify the resulting local variables.

**Unifying atoms**.
The first step in unifying two atoms is to dereference each.
After dereferencing, each argument is each either a constant, a variable
naming an AV list, or a *dangling variable* whose value is {\tt None}.

 * If both atoms are one and the same object, we are done.  Return the atom.
 * Else if either argument is a dangling variable, redirect the
   dangling variable to the other atom and return the other atom.
 * Else if either value is a constant, unification fails.
 * Otherwise, we have two AV lists.
   Redirect the second variable to the first, and set the value of the
   first to the result of unifying the lists.  While unifying the two
   substructures, the value of the first variable is set to -1,
   representing "unavailable".  If -1 is encountered when
   dereferencing a variable, we have detected a cycle in the structure,
   and unification fails.

**Unifing AV lists**.
The first step in unifying two AV lists is to make sure that both are
local.  If either belongs to a foreign AVS, import it into the local AVS.
Then one iterates through the two (local) AV lists together,
constructing a new output list.  Recall
that the attributes are alphabetically sorted.  If the alphabetically
next key appears in only one of the lists, copy it and its value
unmodified into the output list.  If it appears in both lists, unify
the values, and copy the attribute along with the result of unification into
the output list.  The values in an AV list are atoms (either variables
or constants), and we have already discussed the unification of atoms.

Example
-------

Let us consider the algorithm applied to our example.  The first step
is merging, resulting in the structure ??.

**Unify 0 and 2**.
We now unify the variables 0 and 2.  Both have AV lists as values, so dereferencing
has no effect.  Redirect 2 to 0, and set the value of 0 temporarily to
-1::

   0: -1
   2: 0

Now we unify the original values of 0 and 2, namely,
['bar', 1, 'baz', 1, 'foo', 'hi'] and ['bar', 3, 'baz', 5].
Only the first list has a
value for ``foo``, so that goes unmodified into the result.  The
values for ``bar`` are 1 and 3, and the values for ``baz`` are 1
and 5.  Hence we have two recursive unifications to perform.

**Unify 1 and 3**.
The values for 1 and 3 are ['foo', 'bye'] and
['cat', 4].  There are no common attributes, so the output is
simply the concatenation of the two lists.  Variable 3 is redirected
to 1, and the output is stored in 1::

   1: {\tt ['cat', 4, 'foo', 'bye']}
   3: 1

**Unify 1 and 5**.
Now we unify 1 and 5.  Variable 5 is redirected to 1 and 1 is
temporarily set to -1::

   1: -1
   5: 1

The values to be unified are ['cat', 4, 'foo', 'bye']
and ['dog', 4].  There are no shared attributes, so the
unification is again simply the concatenation of the lists.  It is
stored in 1::

   1: ['cat', 4, 'dog', 4, 'foo', 'bye']

**Finish unifying 0 and 2**.
We have now completed the two recursive calls.  The value for
``bar`` is set to 1, and the value for ``baz`` is also set to 1.
The output list is stored in 0.  The final outcome is::

   0: ['bar', 1, 'baz', 1, 'foo', 'hi']
   1: ['cat', 4, 'dog', 4, 'foo', 'bye']
   2: 0
   3: 1
   4: ['meow', 6]
   5: 1
   6: None

Packing
-------

To make future unifications a little more efficient, we may
*pack* the result.  We first propagate "reachability" from
variables to the variables mentioned in their values, starting from
variable 0.  The result is::

   [True, True, False, False, True, False, True]

That is, variables 0, 1, 4, and 6 are reachable.  Then
we define replacement variables by numbering the reachable variables.
The result is::

   [0, 1, False, False, 2, False, 3]

Finally, we create a reduced symbol table, in which all variables have
been replaced with their new numbers.

   0: ['bar', 1, 'baz', 1, 'foo', 'hi']
   1: ['cat', 2, 'dog', 2, 'foo', 'bye']
   2: ['meow', 3]
   3: None

This last step can be destructive, as long as we are sure to copy all
AV lists from *both* of the original input structures when we do
the initial merge.

In Python
---------

Create the second AVS:

>>> avs2 = parse_avs('[bar [cat [meow []]]; baz [dog = bar.cat]]')
>>> print(avs2)
[bar [cat [meow []]]
 baz [dog = bar.cat]]
>>> print(avs2.raw())
AVS 1:
    0 -> [bar:1, baz:4]
    1 -> [cat:2]
    2 -> [meow:3]
    3 -> Top
    4 -> [dog:2]

Unify:

>>> avs3 = unify(avs1, avs2)
>>> print(avs3)
[bar [cat [meow []]
      dog = bar.cat
      foo bye]
 baz = bar
 foo hi]

AV state
--------

An AV state represents an intermediate state during the construction
of the AVS for a node with children.  The second argument to
``parse_avstate()`` is the number of children:

>>> s = '[subj $1 [foo hi; bar [foo bye]; baz = subj.bar]]'
>>> q = parse_avstate(s, 2)
>>> print(q)
(AvState . * subj - : [subj [bar [foo bye]; baz = subj.bar; foo hi]])

The method ``extend()`` is given the AVS for the next child in
line.

>>> q2 = q.extend(avs2)
>>> print(q2)
(AvState . subj * - : [subj [bar [cat [meow []]; dog = subj.bar.cat;
foo bye]; baz = subj.bar; foo hi]])

