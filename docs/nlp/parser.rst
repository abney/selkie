
``selkie.parser`` — Constituent parser
======================================

Bottom-up chart parsing
-----------------------

In the particular implementation of bottom-up chart parsing that I
use, the basic data structure is the **Node,** which represents an
equivalence class of partial parse trees, identified by category,
start position, and end position.  Ambiguity arises when a Node
represents multiple parse trees.  The parser never creates more than
one Node with a given category, start, and end position.  Rather, a
single Node may have multiple **expansions.**

The **chart** is a dict that maps an (X,i,j) tuple (that is,
category X, start position i, end position j) to a Node.

The parser begins by creating one Node for each part of speech of each
word.  It matches a grammar rule by collecting a sequence of
children matching the right-hand side categories.  When all children
have been identified, a new Node is created as specified by the
left-hand side category.

The process of collecting children is broken into a sequence of steps
in which a partial match, representing a partial set of children, is
represented by an **Edge** object.  When a new Node (X,i,j) is
created, the grammar is accessed to find all rules whose first
right-hand side category is matched by X.  For each of those rules, an
Edge is created with one child, namely, the Node (X,i,j).  Edges are
indexed in an **edge table** by the end position of the last child
already collected.  The next child must start at that position.  When
a new Node is created, in addition to looking up grammar rules, the
edge table is also accessed to get existing Edges in which the new
Node matches the next right-hand side category of the Edge.  If there
is a match, the Edge and the new Node are **combined** to create a
new Edge, extended by one more child.

When an Edge is created that has all its children, a **complete**
operation is called to create a Node corresponding to the left-hand
side.

The parser proceeds word by word through
the sentence.  The *j*-th word spans positions *j-1* to *j*.
When processing the *j*-th word, all Nodes that *end* at
position *j* are created.  This guarantees systematicity.  The
main combinatory operation is the one that combines an incomplete Edge
with a new Node.  Any such combination involves an edge whose last
collected child ends at position *i* and a Node that
spans positions *i* to *j*.  The Node is created, and the
combination is done, at position *j*.  At that point, all Edges
with which the Node could ever be combined already exist in the edge
table, since they would have been created when their final child was
created, at position *i*.

Details of operation
--------------------

As mentioned, there are two different data objects, ``Node``
and ``Edge``, and two different indices: the **chart** and
the **edge table.**
Schematically, we write a node as
:math:`_iX_j` and an edge as
:math:`_iX \rightarrow\alpha\bullet_j\beta`.

There are four basic parsing operations:

 * ``Shift(j)``
   nodes for each part of speech of the word spanning (*j*-1, *j*).
 * ``Start(node)`` accesses the grammar to find rules of form
   :math:`X \rightarrow Y \beta\bullet`, where *Y* matches the node's category.
   It adds a new edge :math:`X\rightarrow{}_iY\bullet_j\beta` for each match.
 * ``Combine(node)`` accesses the edge table to find edges of form
   :math:`X\rightarrow{}_k\alpha\bullet_iY\beta`, where *i* is the
   node's start position and the node's category matches *Y*.
   For each successful match, a new Edge is created and added to the edge table.
 * ``Complete(edge)`` checks whether the edge has collected all
   children required by its rule.  If so, it creates a new Node
   corresponding to the left-hand side of the rule.

There are two supporting operations that stitch everything together:

 * ``Add_node(cat, expansion, i, j)``.  Create the
   node and put it in the chart, then call ``start()`` and ``combine()``.
 * ``Add_edge(edge)``.  If the edge has all its children,
   call ``complete()``.  Otherwise, store it in the edge table.

At the top level, the parser passes through the sentence,
calling ``shift()`` at each position in turn.  In principle, a
single call to shift causes a cascade of other actions.  However, for
the ease of debugging, the parser keeps a to-do list of "add node" and
"add edge" actions.  The method ``step()`` takes the next
specification from the to-do list and executes it, possibly adding new
actions to the to-do list.

After all words have been processed, an **unwind** operation looks
for an S node spanning the whole
sentence.  If found, it extracts a list of trees from it and returns
them.

All operations just described are methods of the class ``Parser``.
Here is an example of using Parser:

>>> from selkie.data import ex
>>> from selkie.parser import Parser
>>> p = Parser(ex('g1a'))
>>> ts = p('I book a flight in May', trace=True)
Add Node 0.NP.1 I NP
Add Edge (NP -> 0.NP.1 * PP {})
Add Edge (S -> 0.NP.1 * VP {})
Add Node 1.V.2 book V
Add Edge (VP -> 1.V.2 * NP {})
Add Node 1.N.2 book N
Add Node 2.Det.3 a Det
Add Edge (NP -> 2.Det.3 * N {})
Add Node 3.N.4 flight N
Add Edge (NP -> 2.Det.3 3.N.4 * {})
Add Node 2.NP.4 (NP -> 2.Det.3 3.N.4 * {})
Add Edge (NP -> 2.NP.4 * PP {})
Add Edge (S -> 2.NP.4 * VP {})
Add Edge (VP -> 1.V.2 2.NP.4 * {})
Add Node 1.VP.4 (VP -> 1.V.2 2.NP.4 * {})
Add Edge (VP -> 1.VP.4 * PP {})
Add Edge (S -> 0.NP.1 1.VP.4 * {})
Add Node 0.S.4 (S -> 0.NP.1 1.VP.4 * {})
Add Node 4.P.5 in P
Add Edge (PP -> 4.P.5 * NP {})
Add Node 5.NP.6 May NP
Add Edge (NP -> 5.NP.6 * PP {})
Add Edge (S -> 5.NP.6 * VP {})
Add Edge (PP -> 4.P.5 5.NP.6 * {})
Add Node 4.PP.6 (PP -> 4.P.5 5.NP.6 * {})
Add Edge (VP -> 1.VP.4 4.PP.6 * {})
Add Node 1.VP.6 (VP -> 1.VP.4 4.PP.6 * {})
Add Edge (VP -> 1.VP.6 * PP {})
Add Edge (S -> 0.NP.1 1.VP.6 * {})
Add Node 0.S.6 (S -> 0.NP.1 1.VP.6 * {})
Add Edge (NP -> 2.NP.4 4.PP.6 * {})
Add Node 2.NP.6 (NP -> 2.NP.4 4.PP.6 * {})
Add Edge (NP -> 2.NP.6 * PP {})
Add Edge (S -> 2.NP.6 * VP {})
Add Edge (VP -> 1.V.2 2.NP.6 * {})
Add Expansion 1.VP.6 (VP -> 1.V.2 2.NP.6 * {})
>>> for t in ts: print(t)
... 
0   (S
1      (NP I)
2      (VP
3         (VP
4            (V book)
5            (NP
6               (Det a)
7               (N flight)))
8         (PP
9            (P in)
10           (NP May))))
0   (S
1      (NP I)
2      (VP
3         (V book)
4         (NP
5            (NP
6               (Det a)
7               (N flight))
8            (PP
9               (P in)
10              (NP May)))))

You can confirm that the nodes and edges in the trace produced by the
parser correspond to the previous figure.

Top-down filtering (Earley parser)
----------------------------------

Top-down filtering is not implemented in the current parser, but I
describe the algorithm here for reference.

A dotted rule not only keeps track of children that have been
constructed, it also establishes expectations about what will come
next: if *Y* is the category after the dot, then only nodes of
category *Y*, or which might form the leading edge of a tree rooted in
*Y*, could ever be used to extend the dotted rule.

For example, consider position 1 in the chart.  The edges
whose dot is at position 1 are in the column above the first word.
There are two possible continuation categories: VP and PP.  They are
circled in the two edges in the first column.  Now consider the two
parts of speech for "book", whose start position is 1.  The category
V can be the first category in a VP, so it fits expectations.  But the
category N cannot be initial in either VP or PP, so it violates
expectations.

Consider also the edge :math:`_2\mbox{S}\rightarrow\mbox{NP}\bullet_4\mbox{VP}`.  If we
subsequently find a VP and use the completed edge to construct an S,
the start position of the S node will be position 2.  The only edge
with the dot at position 2 is the one above "book".  It expects an
NP, not an S; nor can S be the initial category in an NP.
Accordingly, we can filter out the S edge immediately.

In short, we can use expectations to avoid creating the nodes and
edges marked with an "X" in the chart.  In cases where
(unlike here) the nodes and edges in question spawn significant
downstream construction, a lot of work can be saved by filtering them
out immediately.

In the original Earley algorithm, one works top-down from
expectations.  For example, we expect a VP at position 1, and there is
a rule :math:`\mbox{VP}\rightarrow\mbox{V}\;\mbox{NP}`; hence we would install an edge
:math:`_1\mbox{VP}\rightarrow\bullet_1\mbox{V}\;\mbox{NP}` in the chart, spanning no material, but
indicating that a V will also satisfy expectations.

Instead of installing these edges in the chart, an alternative is to
precompute a table called the **left corner table** giving all
predictions that follow from a symbol following the dot.  For
``g1``:

.. list-table::

   * - S 
     - S, NP, Det 
   * - NP
     - NP, Det 
   * - VP
     - VP, V 
   * - PP
     - PP, P 
   * - Det
     - Det 
   * - N
     - N 
   * - P
     - P

We use predictions to filter at two points:

In ``shift``, do not install a part of speech unless it is predicted
In ``bu_predict``, do not create edge :math:`_iX\rightarrow Y\bullet_j\beta` unless *X* is predicted.

Here is a recursive definition for ``lc-predicts()``.  For all
categories *X*:

 1. *X* lc-predicts *X*
 2. If *X* lc-predicts *Y*, and there is a rule :math:`Y\rightarrow Z\beta`, then *X* lc-predicts *Z*

Note that this definition is very similar to some of the relations
involved in the conversion to CNF.  The discussion here can readily be
applied to those relations as well.

The relation "lc-predicts" can be thought of as a collection
of pairs (X,Y) such that *X* lc-predicts *Y*.
We build a table that takes pairs (X,Y) and returns true or
false, depending on whether the pair is present in the table.
We can use a python ``set`` containing pairs to implement it.
Consider:

>>> pairs = set()
>>> ('S','NP') in pairs
False
>>> pairs.add(('S','NP'))
>>> ('S','NP') in pairs
True

We initialize the table using the base clause (1) above: for every category
in the grammar, add pair (X,X).
Then every time we add a new pair (Y,Z), clause (2) comes into play.  Namely, we
then look for all rules :math:`X\rightarrow Y\beta`, and for each, we
recursively add the pair (X, Y).  Note that the rules
:math:`X\rightarrow Y\beta` are the **continuations** of *Y* in a Grammar.
Before adding a pair (X,Y), however, we should check whether
it is already present.  If so, we do nothing.

In short, we define a class **LCTable** that has the following
methods.

 * **LCTable(g)**.  Store the grammar as ``t.grammar``,
   set ``t.pairs`` to the empty set, then cycle through the
   categories *X* of the grammar, calling ``add_pair(X,X)`` on each.
 * **add_pair(Y,Z)**.  First, it checks whether (Y,Z) is
   already present in the set of pairs.  If so, it does
   nothing.  If not, it adds the pair to the set, then cycles through
   the continuations :math:`X\rightarrow Y\beta`, recursively calling
   ``addPair(X,Z)`` for each.  Note that the recursion will
   eventually be terminated, even if there is a cycle in the grammar:
   eventually, we will encounter pairs that have already been added.
 * **predicts(X,Y)**.  Takes an expected category *X*, and
   returns ``True`` if *X* lc-predicts *Y*, otherwise ``False``.
   This is what we use after the table has been completed.

Finally, the class ``earley.Parser`` is a modification of
``chart.Parser`` that adds top-down filtering.  It uses an LC table
to implement a method ``is_expected()`` that determines
whether a given category is expected at a given position or not, and
it modifies the ``shift()`` and ``bu_predict()`` methods to
test whether a node or edge is expected, before installing it in the
chart.
