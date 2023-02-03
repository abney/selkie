
``selkie.fsa`` — Finite-state automata
======================================

The module ``selkie.fsa`` provides finite-state automata, including
finite-state transducers.

Using automata
--------------

The most familiar representation of a finite-state automaton is the
state graph.  An example is given in the following figure:

.. image: ../figs/fig8.jpg
   :width: 200px

One can create this automaton manually, as follows.

>>> from selkie.fsa import DFsa
>>> a = DFsa()
>>> a.edge('1', '2', 'the')
<Edge 1 2 the>
>>> a.edge('2', '2', 'big')
<Edge 2 2 big>
>>> a.edge('2', '2', 'red')
<Edge 2 2 red>
>>> a.edge('2', '3', 'dog')
<Edge 2 3 dog>
>>> a.final_state('3')
>>> a.dump()
DFsa:
  ->0  [1]
    1  [2]
    2# [3]
    0 1 the
    1 1 big
    1 1 red
    1 2 dog

An automaton can be represented as a **transition matrix** that maps states and input
symbols to next states.  For the automaton just defined, the matrix
is:

.. list-table::

   * - 
     - ``the``
     - ``big``
     - ``red``
     - ``dog``
   * - 1
     - 2
     - 
     - 
     - 
   * - 2
     - 
     - 2
     - 2
     - 3
   * - 3
     - 
     - 
     - 
     - 

The automaton can be accessed like a matrix:

>>> a['1']['the']
<DFsa.State 2 [1]>
>>> a['2']['dog']
<DFsa.State 3 [2]>
>>> a['2']['the']
>>>

A row of the matrix is represented by a state, so one can access a
state by name using the same idiom:

>>> a['1']
<DFsa.State 1 [0]>

Final states are distinguished by their value
for the attribute ``is_final``:

>>> a['3'].is_final
True

The transition matrix is used to define the behavior of the automaton when given
a sequence of input symbols, as follows.
The automaton begins in the start state.  For each symbol in the input sequence in turn,
the new state of the automaton, given old state ``q`` and input
symbol ``sym``, is ``q[sym]``.
If at any point there is no next state,
the automaton **blocks**, and the input sequence is rejected.  At
the end of the input, the sequence is **accepted** if the state is a
final state, and rejected otherwise.  Here is the full definition of
the ``accepts`` method::
   
   def accepts (self, input):
       q = self.start
       for sym in input:
           q = q[sym]
           if q == None: return False
       return q.is_final

Here are some examples of the behavior of ``accepts``:

>>> a.accepts(['the', 'dog'])
True
>>> a.accepts(['the', 'cat'])
False
>>> a.accepts(['the', 'red', 'big', 'red', 'dog'])
True
>>> a.accepts(['the'])
False

The ``accepts`` method takes a sequence of symbols as
input.  Be sure to split a string representing a sentence.  A string
is treated as a sequence of characters, so::

   >>> a.accepts('the')

behaves as if it were::

   >>> a.accepts(['t', 'h', 'e'])


Fsa file format
---------------

An automaton can be stored in a file in
**fsa file format**.  The example file ``fsa1`` illustrates the format:

>>> from selkie.data import ex
>>> from selkie.io import contents
>>> print(contents(ex('fsa1')), end='')
1	2	the
2	2	big
2	2	red
2	3	dog
3

The fsa file format is an example of a **tabular format**.  The file consists
of **records** terminated by single newline characters, and each
record is separated into **fields** by single tab characters.  The
number of fields is one more than the number of tabs.  An empty field
is created by two tabs with nothing intervening, or by a tab at the
beginning or end of the line.

There are two kinds of records in an fsa file.  A record containing
three fields is an **edge** record, and represents one edge in the
graph.  A record containing one field is a **final-state**
record.  The initial state is identified as the state in the first
field of the first record (which may be either an edge or a
final-state record).

One can load the file simply by passing the filename to the ``DFsa``
constructor:

>>> a = DFsa(ex('fsa1'))
>>> a.dump()
DFsa:
  ->0  [1]
    1  [2]
    2# [3]
    0 1 the
    1 1 big
    1 1 red
    1 2 dog


More about states
-----------------

Note that state names are strings, not numbers.  One can
actually use anything one likes as state names, but state names read
from files are always strings, so we have used strings to now for
consistency's sake.  The automaton, viewed as a matrix, is accessed by
state name:

>>> a['3']
<DFsa.State 3 [2]>

In the printed representation of the state, the "3" is the state's
name, and the "2" in brackets is its **index**.  The automaton contains a
list of states, in order of creation, and the index is the position of
the state in that list:

>>> a.states
[<DFsa.State 1 [0]>, <DFsa.State 2 [1]>, <DFsa.State 3 [2]>]
>>> q = a.states[2]
>>> q
<DFsa.State 3 [2]>
>>> q.name
'3'
>>> q.index
2

Unlike ``edge`` and ``final_state`` methods, accessing a state by label does
not automatically create new states.  It signals an error if there is
no existing state with the given label:

>>> a['5']
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/cl/python/seal/fsa.py", line 137, in state
    return self.state_dict[label]
KeyError: '5'

Again, be careful not to confuse strings and numbers:

>>> a['2']
<DFsa.State 2 [1]>
>>> a[2]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/cl/python/seal/fsa.py", line 137, in state
    return self.state_dict[label]
KeyError: 2

To create a new nonfinal state, use the method ``state``.
It takes a name as argument, and
returns the state that has that name, creating a new state if
necessary.  Any
immutable object can be used as a label.

>>> a.state('6')
<DFsa.State 6 [3]>
>>> a.state('hi')
<DFsa.State hi [4]>
>>> a.state(2)
<DFsa.State 2 [5]>
>>> a.state(frozenset([1,2,4]))
<DFsa.State {1,2,4} [6]>
>>> for q in a.states: print(repr(q))
...
<DFsa.State 1 [0]>
<DFsa.State 2 [1]>
<DFsa.State 3 [2]>
<DFsa.State 6 [3]>
<DFsa.State hi [4]>
<DFsa.State 2 [5]>
<DFsa.State {1,2,4} [6]>

One can "clean up" the state names by calling the method ``rename_states``.
It sets each state name to be the string corresponding to the state's index:

>>> a.rename_states()
>>> a.states
[<DFsa.State 0 [0]>, <DFsa.State 1 [1]>, <DFsa.State 2 [2]>,
 <DFsa.State 3 [3]>, <DFsa.State 4 [4]>, <DFsa.State 5 [5]>,
 <DFsa.State 6 [6]>]
>>> a.states[0].name
'0'
>>> a.states[0].index
0

Nondeterministic automata
-------------------------

Suppose we wish to define an automaton that accepts any string of 0's
and 1's that ends in "01."  The easy way to do it is with the
automaton ``fsa2``, shown in the following figure.

.. image:: ../figs/fig9.jpg
   :width: 200px

It consumes 0's and 1's for a time, then nondeterministically
"guesses" that a given "0" is the next to last symbol in the
input.  If it guesses right, and if that "0" is immediately followed
by a "1," then the automaton arrives in a final state at the end of
the input, and the string is accepted.

Suppose that the string in fact ends in "01," but the automaton
guesses wrong.  The result is an alternative computation that ends in
failure.  Hence we must be more explicit about what it means for an
automaton to accept a string: it accepts an input string if there is
*any* valid computation that leads to success.  The existence of
alternative computations that end in failure is immaterial.

The previous automaton is **nondeterministic** because there are two
edges out of state "A" that are both labeled "0."  In general,
an automaton is nondeterministic if there is any state that has
multiple outgoing edges with the same label.

(Note that an
otherwise deterministic automaton that had, say, two edges labeled
"0" both of which go from state "A" to state "B" would satisfy
our definition of nondeterminism.  To keep the definition simple, we
indeed consider such an automaton to be nondeterministic, even though
the nondeterminism is in a sense spurious.)

There is one other way in which an automaton may be nondeterministic.
It may contain **epsilon edges**.  The automaton ``ex('fsa2')``, shown in
the following figure, provides an example.

(fig1.pdf)

A (possibly) nondeterministic automaton is represented by the class
``Fsa``, rather than ``DFsa``.  For example, we may load 
``fsa1`` as an ``Fsa``, and add an edge to make it
nondeterministic:

>>> from selkie.fsa import NFsa
>>> a = NFsa(ex('fsa1'))
>>> a.edge('2', '3', 'red')
<Edge 2 3 red>
>>> a.dump()
NFsa:
  ->0  [1]
    1  [2]
    2# [3]
    0 1 the
    1 1 big
    1 1 red
    1 2 dog
    1 2 red

An edge is an ε-edge if its label, coerced to a boolean, is
``False``.  That is, the labels ``None``, ``''``, ``False``,
``0``, ``()``, etc., are all equivalent.  (The label ``'0'``,
however, is not boolean false.)
The label parameter for
the ``edge`` method defaults to ``None``, so one can also create an
ε-edge by omitting the label.

>>> a.edge('1', '2')
<Edge 1 2 None>
>>> a.dump()
NFsa:
  ->0  [1]
    1  [2]
    2# [3]
    0 1
    0 1 the
    1 1 big
    1 1 red
    1 2 dog
    1 2 red

If we try to add either kind of edge to a ``DFsa``, an error is signalled:

>>> d = DFsa(ex('fsa1'))
>>> d.edge('2', '3', 'red')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/cl/python/seal/fsa.py", line 103, in edge
    return src.edge(label, dest)
  File "/cl/python/seal/fsa.py", line 85, in edge
    raise Exception, 'Attempt to add multiple edges with same label'
Exception: Attempt to add multiple edges with same label
>>> d.edge('1', '2')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/cl/python/seal/fsa.py", line 103, in edge
    return src.edge(label, dest)
  File "/cl/python/seal/fsa.py", line 82, in edge
    if not label: raise Exception, 'Attempt to add empty edge'
Exception: Attempt to add empty edge

The next-state operation on an ``Fsa`` returns a list of states,
rather than a single state.  That is true even if there is only one
next state.

>>> a['2']['red']
[<Fsa.State 2 [1]>, <Fsa.State 3 [2]>]
>>> a['2']['big']
[<Fsa.State 2 [1]>]
>>> a['1']['']
[<Fsa.State 2 [1]>]
>>> a['1']['dog']
[]

Note that this operation does not automatically follow epsilon edges.
There is no version of the next-state operation that follows epsilon
edges.  Instead, one should convert the ``Fsa`` to a ``DFsa``.

>>> from selkie.fsa import determinize
>>> d = determinize(a)
>>> d.dump()
DFsa:
  ->0  [0]
    1  [1]
    2# [2]
    3# [3]
    0 1 big
    0 1 the
    0 2 dog
    0 3 red
    1 1 big
    1 2 dog
    1 3 red
    3 1 big
    3 2 dog
    3 3 red
>>> d.accepts(['red'])
True
>>> d.accepts(['red', 'dog'])
True
>>> d.accepts(['dog', 'red'])
False

Conversion to DFSA
------------------

The call ``determinize(a)``, given a nondeterministic automaton *a*,
produces an equivalent deterministic automaton.  If *a* is not
ε-free, ``determinize()`` will first call
``eliminate_epsilons()`` on it.

The call
``minimize(d)`` takes a deterministic automaton and creates an
equivalent automaton that is minimal, in the
sense that there is no other equivalent deterministic automaton that
has fewer states.

In this section, we examine these three main transformations:
ε-elimination, determinization, and minimization.

ε-Elimination
-------------

To convert a nondeterministic automaton to a deterministic automaton,
a preliminary step is the elimination of ε-edges.

The method ``eliminate_epsilons`` does the following.
Each state in the old automaton is replaced by a
set of states, namely, those which can be reached crossing only
ε-edges.  That set of states is known as the
**epsilon closure** of the original state.  The method ``eclosure`` 
computes the epsilon closure of a state.  We illustrate with
``fsa3``.

>>> a = NFsa(ex('fsa3'))
>>> [q.name for q in sorted(a['1'].eclosure())]
['1', '2', '3', '4']
>>> [q.name for q in sorted(a['2'].eclosure())]
['2', '3', '4']
>>> [q.name for q in sorted(a['4'].eclosure())]
['4']

The function ``eliminate_epsilons`` creates a new automaton whose
states are the epsilon closures of the original states.  Its edges are
computed as follows.  If there is an edge from *i* to  on *x*
in the original automaton, and if *i'*
is any new state that has *i* in the set of original states that it
came from, and if *j'* is the ε-closure of *j*, then there is
an edge from *i'* to *j'* on *x* in the new automaton.
Here is the method definition::
   
   def eliminate_epsilons (self):
       if self.epsilon_free: return self
   
       new_fsa = self.__class__()
       table = []
   
       for q in self.states:
           if q.index != len(table): raise Exception("Bad index")
           table.append(new_fsa.state(frozenset(q.eclosure())))
   
       for q1 in new_fsa.states:
           for q in q1.name:
               for e in q.edges:
                   if not e.is_epsilon():
                       q1.edge(table[e.dest.index], e.label)
               if q.is_final:
                   q1.is_final = True
   
       return new_fsa

Here is an example of its use.  It renames states by default, but we
suppress that for this example.

>>> b = a.eliminate_epsilons(rename_states=False)
>>> b.dump()
NFsa:
  ->0  [{1,2,3,4}]
    1  [{2,3,4}]
    2# [{1,2,3,4,5}]
    0 1 big
    0 1 red
    0 1 the
    0 2 dog
    1 1 big
    1 1 red
    1 2 dog
    2 1 big
    2 1 red
    2 1 the
    2 2 dog

Incidentally, ``eliminate_epsilons`` immediately returns the original
automaton if it is already ε-free.  This is possible because
Fsas keep track of whether they are ε-free or not.
When an Fsa is created, it has no edges, hence is ε-free.
States record which fsa they belong to.  When an ε edge is
added to a state, the state flags its automaton as no longer being
ε-free.  This assumes that states and edges are never deleted
from an automaton, and states are never transplanted from one automaton to
another.

Determinization
---------------
    
.. py:function:: determinize(fsa)

   Determinizes an fsa.  Non-destructive.  Returns a DFsa.
   One may optionally specify *rename_states=True*.

The ``determinize`` function takes an fsa as input and produces
a DFSA as output.  It begins by applying ε-elimination to the
input fsa.  It constructs the new automaton as follows.

States *Q* of the new automaton are labeled
with sets of states from the old automaton.  For simplicity, we treat
*Q* as being a set of states from the old automaton.  We begin by adding the
state {*q*}, where *q* is start state of the old automaton.  Then we add edges to the
new state *Q*.  The outgoing edges
from *Q* take label *x* to state *R*
where *x*
is one of the input symbols and *R* is the set of old states *r* such
that there is an edge from *q* to *r* on *x*
in the old automaton for some *q* in *Q*.  A new state is final just in case it
contains an old state that is final.  Here is the complete function definition::
   
   def determinize (old_fsa, rename_states=True):
       old_fsa = old_fsa.eliminate_epsilons()
       new_fsa = DFsa()
       new_fsa.state(frozenset([old_fsa.start]))
       ndone = 0
   
       while ndone < len(new_fsa.states):
           q1 = new_fsa.states[ndone]
           ndone += 1
           table = {}
           for q in sorted(q1.name):
               for e in q.edges:
                   if e.label in table:
                       table[e.label].add(e.dest)
                   else:
                       table[e.label] = set([e.dest])
               if q.is_final: q1.is_final = True
           for (label, dests) in sorted(table.items()):
               q1.edge(new_fsa.state(frozenset(dests)), label)
   
       if rename_states: new_fsa.rename_states()
       return new_fsa

To illustrate the behavior of ``determinize``, we use ``fsa2``.
(The automaton ``b`` of the previous example is already deterministic.)

>>> a = NFsa(ex('fsa2'))
>>> b = determinize(a, rename_states=False)
>>> b.dump()
DFsa:
  ->0  [{A}]
    1  [{A,B}]
    2# [{A,C}]
    0 0 1
    0 1 0
    1 1 0
    1 2 1
    2 0 1
    2 1 0

Minimization
------------

.. py:function:: minimize(fsa)

   Minimize an automaton.  Non-destructive.

Within every equivalence class of automata (an equivalence class
being the set of automata that generate a given language), there is a
unique minimal automaton, in the sense of an automaton with the fewest
states.  The minimization algorithm finds that automaton for any given
deterministic automaton.

In a deterministic automaton, a given string *x* maps a state *q* to a
unique state δ*(q,x).  We define the **language of a state**
*q* to be the set of strings that take *q* to a final state; that is,
the set of strings *x* such that δ*(q,x) is a final state.  By
this definition, the language of the automaton is obviously equal to
the language of its start state.

We define two states to be **equivalent** if they have the same
language.  Two states have the same language *L* just in case
every string *x* either takes both states to a final state (in which case
*x* is in *L*) or takes both to a nonfinal state (in which
case *x* is not in *L*).
To avoid having a special case for blocking, we add a special "sink"
state ⊥.  For any state *q* and input symbol *w* such that *q*[*w*]
is undefined, we define *q*[*w*] = ⊥.  In particular, ⊥[*w*] =
⊥ for all input symbols *w*.  Once a string leads to ⊥, it
stays there.  Moreover, ⊥ is nonfinal, so any string that leads
to ⊥ is rejected.

Two states are **distinguished** by a string *x* just in case *x*
takes one of the states to a final state, and the other state to a
nonfinal state.  The idea of the algorithm is to systematically find
distinguishable state pairs, which we call **incompatible pairs**.
When all incompatible state pairs
have been identified, all remaining state pairs involve equivalent
states.

Systematicity is achieved by recursing on string length.  We first
identify all state pairs that are distinguished by strings of length
zero.  There is only one string of length zero, the empty string, and
it distinguishes a state pair only if one of the states is final and
the other is nonfinal.

Then we recurse.  Assume that we know all state pairs that are
distinguished by strings of length <= *n*.  We will identify any
additional state pairs that are distinguished by strings of length
*n*.

Consider an input symbol *w*, and states *q* and *r* with

*q*[*w*] = *s*
*r*[*w*] = *t*.

If *q* and *r* are equivalent, then clearly *s* and
*t* are equivalent.  Namely, *q* and *r* being equivalent means that
every string *x* = *wy* takes *q* and *r* to the same kind of state
(final or nonfinal); hence every string *y* takes *s* and *t* to the
same kind of state.
Hence if *st* is an incompatible pair,
then *qr* must be.  If we propagate incompatibility in this way, we
will eventually identify every incompatible pair.  When the
propagation peters out, any remaining pair is equivalent.

We will illustrate using automaton ``fsa4``, shown in the following figure.

(fig10.pdf = \Archive/2007-A/ling441/figs/fig3.pdf)

The states of this automaton intuitively represent the most two
recently encountered input symbols, and the automaton is in a final
state only if the last two symbols were "01."  That is, the
automaton is equivalent to ``fsa2``.  The following figure shows the
same automaton with single-letter state names, which will be more
convenient for illustrating minimization.

Propagation goes "backwards" along edges: incompatibility between 
*q*[*w*] and *r*[*w*] implies incompatibility between *q* and *r*.
Hence we construct an **incompatibility table** of "reverse edges."  The table is indexed
by state and input symbol, and entry *(s,w)* contains all source
states *q* such that *q*[*w*] = *s*.  Here is the table for ``fsa4``::
   
       0    1
   a
   b  a
   c  bce
   d       bce
   e  dfg
   f       dfg
   g       a

For example, there is an edge from *c* to *d* on 1,
hence the entry "*c*" in the cell (*d*,1).

Here is how we use the incompatibility table.  Suppose we determine that *d* and *f*
are incompatible.  Then we compare the rows for *d* and *f*::
   
   d      bce
   f      dfg

Any states *q* and *r* in the same column are such that *q[w] = s* and
*r[w] = t*, where *s = d* and *t = f* or the other way around.  In
short, since *d* and *f* are incompatible, it follows that *q* and *r*
are incompatible.  In particular, we propagate incompatibility to the
following pairs: *bd, bf, bg, cd, cf, cg, ed, ef, eg*.

The incompatibility table is implemented as the class ``Incompatibility``.
Here is an example of its use.  Note that states are represented by
their index.

>>> a = DFsa(ex('fsa4'))
>>> from selkie.fsa import Incompatibility
>>> t = Incompatibility(a)
>>> a['d']
<DFsa.State d [4]>
>>> a['f']
<DFsa.State f [6]>
>>> from seal.nlp.fsa import pair
>>> p = pair(4,6)
>>> for newp in t.propagate(p): print(newp)
... 
(2, 1)
(3, 2)
(5, 2)
(4, 1)
(4, 3)
(5, 4)
(6, 1)
(6, 3)
(6, 5)

Now we use the incompatibility table to compute a list of compatible
pairs.  We use two data structures: a map from state pairs to
"compatible" or "incompatible", and
a "todo" list of the incompatible pairs that
have been discovered but not yet used for propagation.  Initially,
all pairs are marked as compatible and the todo list is empty.  Then we
systematically go through pairs consisting of one final state and one
nonfinal state, mark each as incompatible, and add them to the todo list.
Here is the result of initialization on our example:

>>> from selkie.fsa import Minimizer
>>> m = Minimizer(DFsa(ex('fsa4')))
>>> m.itab.dump()
0 : {} {}
1 : {0} {}
2 : {} {0}
3 : {1,3,5} {}
4 : {} {1,3,5}
5 : {2,4,6} {}
6 : {} {2,4,6}
7 : {7} {7}
>>> m.todo
[(7, 4), (4, 0), (4, 1), (4, 2), (4, 3), (5, 4), (6, 4)]

The next step is propagation.
One takes a pair from the todo list, and one uses the incompatibility
table to propagate to new pairs.  For each new pair, one checks whether it has been
previously encountered.  If so, it is discarded, but if not, it is
added to the table of known pairs as well as to the todo list.
The process ends when the todo list is exhausted.

Here is the trace of the computation for our example.  We initialize
with final-nonfinal pairs::

   da, db, dc, ed, fd, gd

Then we begin propagating.  Most pairs propagate nothing; here are the
exceptions, noting only the new pairs::
   
   fd: fb, fc, fe, gb, gc, ge
   gd: ba, ca, ea

After that, no futher propagation is possible.

>>> m.propagate()
>>> m.marked.dump()
(1, 0) True
(2, 0) None
(2, 1) True
(3, 0) True
(3, 1) None
(3, 2) True
(4, 0) True
(4, 1) True
(4, 2) True
(4, 3) True
(5, 0) True
(5, 1) None
(5, 2) True
(5, 3) None
(5, 4) True
(6, 0) None
(6, 1) True
(6, 2) None
(6, 3) True
(6, 4) True
(6, 5) True

When the final list of incompatible pairs has been computed, every
pair not on the list is equivalent.  One creates a mapping from old
states to new states, such that equivalent old states get mapped to
the same new state.  That mapping is used to copy edges from the old
automaton to the new automaton, as well as final-state information.

For our example, the compatible pairs are::

   cb, eb, ec, fa, ga, gf

We go through these pairs, assigning new-state indices to the members
of each, so that the members of a pair both receive the same index.
The pair *cb* causes us to create a new index (0) and assign it to
both *b* and *c*.  The pair *eb* causes us to assign that
index to *e*, and the pair *ec* causes no new assignments, but is
campatible with previous assignments.  The pair *fa* causes a
new index (1) to be created; it is further assigned to *g* when we
encounter *ga.*  The result is::

   a  b  c  e  f  g
   1  0  0  0  1  1

In Python:

>>> m.create_map()
>>> m.state_map
[0, 1, 0, 1, 2, 1, 0]

We then create new indices for any old states that have not yet been
assigned an index.  In this case, only *d* remains.  The new automaton
has three states.  State 0 corresponds to old states *b, c, e;*
state 1 corresponds to old states *a, f, g;* and state 3
corresponds to old state *d.*

>>> out = m.create_newfsa()
>>> out.dump()
DFsa:
  ->0  [0]
    1  [1]
    2# [2]
    0 0 1
    0 1 0
    1 1 0
    1 2 1
    2 0 1
    2 1 0

For the table where we keep track of
state-pair compatibility, and for the mapping from state pairs to new
states, an upper triangular matrix (UTM) provides an efficient data structure.
It consists of an array with as many cells as state pairs (namely,
*n(n-1)* for *n* the number of states), and a pair *(i,j)* of state
indices maps to the array location:

   :math:`[ i(i-1) / 2 ] + j.`

It is assumed that :math:`i > j`.

Here is why that calculation of array location maps every index pair to
a unique array location.
The order of pairs is:

   :math:`(1,0), (2,0), (2,1), (3,0), (3,1), (3,2), \ldots`

There is one pair with *i* = 1, two pairs with *i*
= 2, and so on.  Hence there are zero pairs that precede (1,0), one
pair that precedes (2,0), 1+2 pairs that precede (3,0), and so on.
In general, there are 1+2+...+n = n(n+1)/2 pairs that precede
(n+1,0).  The array location is equal to the number of preceding
pairs in the enumeration.

The Fsa class
-------------

The inheritance hierarchy is:

 * Fsa
    * NFsa
       * SimpleFsa
    * DFsa

.. py:class:: selkie.fsa.Fsa(init)
	      
   This is an abstract state, providing common code for
   specializations.  The main method that is required from
   specialization is *accepts()*.

   If *init* is pathlike, it is interpreted as a pathname and loaded.
   Otherwise, the method initialize_from(init) must be defined.  (Used
   by some specializations.)

   .. py:attribute:: state_dict

      The states, a dict.

   .. py:attribute:: states

      The states as a list.

   .. py:attribute:: start

      The start state.  It is initially None, but is automatically set
      to the first state created, when a state is created.

   .. py:attribute:: epsilon_free

      A flag indicating whether the fsa is epsilon-free.

   .. py:method:: state_constructor(name)

      Create a state.  A specialization of Fsa generally has its own
      specialization of State.

   .. py:method:: edge(src, dest, label)

      Create an edge.  *Label* is optional and defaults to None.

      One may optionally provide an old edge instead of a label, by
      using the keyword argument *label_from* instead of
      *label*.  The edge's *single_label()* method is called to get the label.
      (Fst edges also work, provided that their inlabel equals their
      outlabel; otherwise an error is signalled.)

   .. py:method:: edges()

      Iterate over all edges of all states.

   .. py:method:: labels()

      Returns a set containing all edge labels.

   .. py:method:: final_state(name)

      Whether or not the state with the given name is final.

   .. py:method:: load(fn)

      Load from a file.

   .. py:method:: __len__()

      The number of states.

   .. py:method:: __getitem__(name)

      Returns an existing state.  Error if no state exists with the given name.

   .. py:method:: state(name)

      If a state with the given name exists, returns it.  Otherwise adds a new
      state to the automaton and returns it.

   .. py:method:: rename_states()

      Change the state names to be the state indices as strings.
      Destructive.

   .. py:method:: typename()

      Returns a pretty version of the class name.

   .. py:method:: __iter__()

      Iterates over generated strings.  May be an infinite iteration.

   .. py:method:: dump(file)

      Dump the contents.  *file* may be omitted or None, in which case
      it prints to stdout.
    
   .. py:method:: eliminate_epsilons()

      Eliminate epsilon edges.  
      Works for Fst, too.
      Not destructive; creates a new automaton.

      The specification *rename_states=True*
      may optionally be provided, in which case the new automaton's
      *rename_states()* method is called.


NFsa and DFsa
-------------

.. py:class:: selkie.fsa.NFsa

   A non-deterministic fsa.  Specializes Fsa, adding just one method:

   .. py:method:: accepts(seq)

      Returns a boolean indicating whether it accepts the given sequence
      of symbols.  One may optionally provide *trace=True*.

.. py:class:: selkie.fsa.SimpleFsa

   An NFsa in which state names equal their indices.  It needs no
   state_dict to map state names to states.  Overrides the definitions
   of methods *__getitem__()* and *state()*, and its implementation of
   rename_states() signals an error.



.. py:class:: selkie.fsa.DFsa

   A deterministic fsa.  Has its own State class.
   The methods *typename()*, *state_constructor()*, and *accepts()* are overridden.


State and Edge classes
----------------------

.. py:class:: selkie.fsa.Fsa.State(name)
    
   Also used by NFsa and SimpleFsa.

   .. py:attribute:: name

      The value is provided by the constructor.

   .. py:attribute:: edges

      The list of outgoing edges, initially [].

   .. py:attribute:: is_final

      Whether this is a final state, initially False.

   .. py:attribute:: index

      Initially None.

   .. py:attribute:: fsa

      The fsa that this state belongs to.  Initially None.
    
   .. py:method:: typename()

      A string representing a readable version of the class name.

   .. py:method:: __lt__(other)

      Comparison is by string representation (using str()).

   .. py:method:: __eq__(other)    

      Comparison is by string representation (using str()).

   .. py:method:: __hash__()

      The hash value of the name.
    
   .. py:method:: edge(dest, label)

      Creates and adds a new edge, unless an edge to the given *dest*
      state with the given *label* already exists, in which case it is
      re-used.  Return value is the (new) edge.

      Boolean false labels match even if they are not ==.

   .. py:method:: __getitem__(label)

      Returns the edge(s) with the given label.  Boolean false labels
      match even if they are not ==.

   .. py:method:: eclosure()
    
      Compute the epsilon-closure of this state.
      This works for Fsts, too.
    
   .. py:method:: __str__()

      Converts the name to a string.  If the name is a set, the
      elements are sorted so that the string value is uniquely
      determined.

.. py:class:: selkie.fsa.Fsa.Edge(src, dst, label)

   *label* is optional; defaults to None.

   .. py:attribute:: source

      The state that the edge comes from.

   .. py:attribute:: dest

      The state that the edge goes to.

   .. py:attribute:: label

      The edge label.
    
   .. py:method:: is_epsilon()

      Whether this is an epsilon edge.  An epsilon edge is one whose label
      is boolean false.

   .. py:method:: single_label()

      Return the label.  This is the same as the label member, for an
      Fsa.Edge, but not for an Fst.Edge.

   .. py:method:: label_pair()

      Return a pair consisting of the label twice.
    
   .. py:method:: write(out)

      Write it to an output stream.

.. py:class:: selkie.fsa.DFsa.State

   A state in a deterministic FSA.  (DFsas do not override Fsa.Edge, though.)

   .. py:method:: __getitem__(label)

      Returns a single state, or None.
    
   .. py:method:: edge(dest, label)

      Add a new edge.  *Label* is optional and defaults to None.
      *Label* may not be boolean false (no empty edges).
