
``selkie.fst`` — Finite-state transducers
=========================================

Intro
-----

A finite-state transducer (FST) has an input alphabet *Σ1* and output
alphabet *Σ2*; a
set of states *Q*, one of which is the initial state, and some number of
which are final states; and a set of edges of form *(q1,α,β,q2)*
with *q1,q2 in Q*, *α in Σ1**, and *β in Σ2**.
An FST *T* defines a relation *R_T(α,β)* in
*Σ1* cross Σ2**.  Two FSTs are defined to be equivalent
just in case they define the same relation.

For a transducer, an *empty edge* is one labeled *ε:ε*.

**Rational transduction.**  A *transduction* is a
function from strings to sets of strings.  There is an obvious one-one
correspondence between string relations *R* and transductions *f_R*, where::

   fR(α) = {β | R(α,β)}.

A transduction computable by an FST is called a *rational transduction.*

**Rational function.**  A relation *R* is a function just in
case any input that *R* associates with an output, it associates
with a unique output.  We write *R(α)* for that unique output::

   R(α) = β if *R(α,β)*,
   undefined if *α* is not in the domain of *R*

An FST is *functional* if it computes a function.
A *rational function* is a function computed by some FST.
Note that a rational function is not a transduction: a rational
function maps strings to strings, whereas a transduction maps strings
to sets of strings.  But we have::

   fR(α) = R(α).


Derived FSAs
------------

**Underlying FSA.**  The *underlying FSA* of an FST
results from viewing edges *(q1,α,β,q2)* as FSA edges
labeled with symbol pairs: *(q1, α:β, q2)*.

**Projections.**  The *first projection* is the FSA
obtained by replacing transducer edges *(q1,α,β,q2)* with
FSA edges *(q1,α,q2)*.  The *second projection* keeps
*β* instead of *α*.

**Letter transducer.**
Note that edges of an FST are labeled with *strings,* not single symbols.
An FST whose edges are labeled with single symbols or ε
is called a *letter transducer.*  
Any FST can be converted to an equivalent letter transducer, by
replacing complex-string edges with sequences of letter edges.

**Empty-edge elimination.**
Empty edges *ε:ε* can be eliminated by applying the
ε-elimination algorithm to the underlying FSA.
Edges labeled *α:ε* or *ε:β* for nonempty
*α*, *β*, may still remain.


Basic operations on FSTs
------------------------

**Union.**  An FST computing the union of two FSTs *T1* and
*T2* can be constructed by creating a new initial state with empty
edges leading to the initial states of *T1* and *T2*.

**Inversion.**  Given an FST computing *T*, an FST computing
*T^{-1}* can be constructed by interchanging the input and output
labels on all edges.

**Composition.**  The *composition* *T1 compose T2* of
two transductions is the function that maps *α* to *T2(T1(α))*.
Given FSTs *T1* and *T2*, an FST *T3* that computes their composition can
be constructed as follows.  First, convert each FST to a letter
transducer and eliminate empty edges; let *T'1* and *T'2* be the results.
We now construct an FST *T3* representing the composition.
Its states are pairs *(q1,q2)* where *q1* is a state of *T'1* and
*q2* is a state of *T'2*.
We keep a to-do list of states needing expansion.
The initial state of *T3* pairs the initial state
of *T'1* with the initial state of *T'2*; it is the first entry in
the to-do list.  Then, until the to-do list is empty,
pop a state *(q1,q2)* off the to-do list and do the following, where
*a, b, c != ε*.

If *q1* and *q2* are both final states, add *(q1,q2)* to the list of
final states for *T3*.  
For every *c* such that
*(q1,a,c,r1)* is an edge of *T'1* and *(q2,c,b,r2)* is an edge of
*T'2*, intern state *(r1,r2)* and
add edge *((q1,q2), a,b,(r1,r2))*.
For every edge *(q1,a,ε,r1)* in *T'1*, intern state
*(r1,q2)* and add edge
*((q1,q2),a,ε,(r1,q2))*.
For every edge *(q2,ε,b,r2)* in *T'2*, intern state
*(q1,r2)* and add edge
*((q1,q2),ε,b,(q1,r2))*.

To intern a state, do nothing if it is already present.  Otherwise,
add it to *T3* and also add it to the to-do list.


The Fst class
-------------

The class ``selkie.fst.Fst`` inherits from ``selkie.fsa.Fsa``.
An Fst can be created from a file.  The format is similar to the Fsa
format, except that there are two label columns instead of one.  For
example, here
are the contents of ``fst1``::

   1       2       the     d
   2       1               er
   1       3       big     gross
   3       1               e
   1       1       dog     Hund
   1

One can load it and examine it just as with an Fsa:

>>> from selkie.fst import Fst
>>> fst = Fst(ex('fst1'))
>>> fst.dump()
Fst:
  ->0# [1]
    1  [2]
    2  [3]
    0 0 dog : Hund
    0 1 the : d
    0 2 big : gross
    1 0 : er
    2 0 : e

One can call the transducer as a function.  The output is a list of
symbol sequences.

>>> fst(['the', 'big', 'dog'])
[['d', 'er', 'gross', 'e', 'Hund']]

.. py:class:: selkie.fst.Fst(init)

   A finite-state transducer.  Specializes selkie.fsa.Fsa.
   It overrides the implementations of *load()*, *accepts()*,
   *__iter__()*, *state_constructor()*, *typename()*.
   It changes the signature of *edge()*:

   .. py:method:: edge(src, dest, inlabel, outlabel)

      Create a new edge.
      *Inlabel* and *outlabel* are optional.

   It adds the following member and methods.

   .. py:attribute:: sigma

      The input vocabulary.

   .. py:method:: initialize_from(fsa)

      Initialize from an fsa.

   .. py:method:: inlabels()

      The set of input labels.  (Excludes epsilon.)

   .. py:method:: outlabels()

      The set of output labels.  (Excludes epsilon.)

   .. py:method:: __call__(input)

      One may optionally specify *trace=True*.  If one provides
      *cutoff* as a keyword argument, an error is signalled if the
      number of output strings produced exceeds the cutoff.
      Returns a list of strings.

   .. py:method:: vocabulary()

      Returns the set of labels.  One can specify *side='left'* to get
      just the left vocabulary, *side='right'* to get the right
      vocabulary, or *side='both'* (the default) to get the union.

   .. py:method:: globalize_wildcards(vocab)

      Creates a new FST.


.. py:class:: selkie.fst.Fst.State
    
   A state in an Fst, a specialization of Fsa.State.  Reimplements *typename()*
   Changes the signature of *edge()* and *__getitem__()*:

   .. py:method:: edge (self, dest, inlabel, outlabel)

      Add a new edge.  *Inlabel* and *outlabel* are optional and
      default to None.  One may alternatively copy the label from an
      old edge by providing the old edge as the value of keyword
      *label_from*.

   .. py:method:: __getitem__(inlabel)

      One specifies the *inlabel*, not the full label pair.
      Returns a list of states.

   Fst.State also adds the following methods:
   
   .. py:method:: advance(c)
   
      Returns a pair (r, out) where *r* is the next state, and *out* is
      the word whose last character was *c*.  Either *r* or *out* (or
      both) may be None.
   
      Signals an error if the automaton is not deterministic.

   .. py:method:: mentioned()

      Returns the set of non-wildcard input labels on the edges out of this state.


.. py:class:: selkie.fst.Fst.Edge(src, dst, inlabel, outlabel)
    
   Specializes Fsa.Edge.  *Inlabel* and *outlabel* are optional and
   default to None.  Reimplements *single_label()*, *label_pair()*,
   *__str__()*, *__repr__()*, and *write()*.
   The following members replace *label*:

   .. py:attribute:: inlabel

      Its input label.

   .. py:attribute:: outlabel

      Its output label.
    
   The meaning of the following changes:

   .. py:method:: is_epsilon()

      Only true if both the input and output labels are epsilon.

.. py:function:: from_list(lst, use_sink=False, eos='<eos>')

   The *lst* need only be an iterable.  Its elements ("words") should be
   fixed sequences, though, and the elements of the "words"
   ("characters") must be immutable and must support comparison.

   A graph is created in which common word prefixes always lead to the
   same state.  The graph is deterministic in the sense that q[c]
   returns either the empty list or a list of edges of length one.  

   If **use_sink** is False, the word is the outlabel of the edge whose
   inlabel is the word's last letter.  If True, the last-letter edge leads to a
   state that has an outgoing edge whose inlabel is **eos** and whose
   outlabel is the word.

   To use the fst::

      >>> q = fst.start
      >>> (r, out) = q.advance(c)

   When there is no transition, *r* is None.  When there is no
   output (yet), *out* is None.
