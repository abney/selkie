
``selkie.head`` — Head marking
==============================

The examples assume you have done:

>>> from selkie.head import *
>>> from selkie.tree import parse_tree, copy_tree

Head rules
----------

.. py:function:: mark_heads(tree, [rules])

   Destructively converts an unheaded
   tree into a headed tree.  Note that it is called for side effect; it
   does not return a value.

   >>> u = parse_tree('''(S (NP (DT the) (NN dog))
   ...                      (VP (VB chases)
   ...                          (NP (DT a) (NN cat))))''')
   >>> h = copy_tree(u)
   >>> mark_heads(h)
   >>> print(h)
   0    (S
   1       (NP
   2          (DT the)
   3          (NN:head dog))
   4       (VP:head
   5          (VB:head chases)
   6          (NP
   7             (DT a)
   8             (NN:head cat))))

   Nodes that already have heads are left unchanged: \verb|mark_heads()|
   only determines heads for headless nodes.

   Head-marking uses a set of head rules.  The function
   ``mark_heads()`` will accept a rule set as second argument.  By
   default, it uses ``DefaultHeadRules``.  These represent a modified
   version of the rules in Michael Collins's thesis.  The original rules
   are also available as ``CollinsMagermanRules``.

.. py:function:: find_head()

   This is the main function.
   It takes a node and indicates which of
   its children should be head.  The return value is the index of the
   predicted head node.

   >>> print(u)
   0    (S
   1       (NP
   2          (DT the)
   3          (NN dog))
   4       (VP
   5          (VB chases)
   6          (NP
   7             (DT a)
   8             (NN cat))))
   >>> find_head(u[0])
   1
   >>> find_head(u[4])
   0

   For debugging, one can turn tracing on:

   >>> find_head(u[4], trace=True)
   Rule <Rule VP 0>, found VB: h=0
   0

   One can print the head rules: ``print(DefaultHeadRules)``.


The Magerman-Collins head rules
-------------------------------

As mentioned above, the head-marking rules are an adaptation of the
Magerman-Collins rules, as given in Collins's dissertation [1], pp. 238 ff.
Collins adapts them from Magerman [1331].  The rules from Collins's
dissertation are listed in the following table.  Their use is best
explained with an example.  Suppose the parent node has category
``CONJP``.  The rule for ``CONJP`` has direction ``R`` and
child categories ``CC RB IN``.  One looks first for the rightmost
child with category ``CC``.  If none is found, look for the
rightmost child with category ``RB``.  If none is found, look for
the rightmost child with category ``IN``.  As a default, take
the rightmost child as head.

.. list-table::
   :widths: 2 1 5

   * - ADJP
     - L
     - NNS QP NN \$ ADVP JJ VBN VBG ADJP JJR
   * - 
     -
     - NP JJS DT FW RBR RBS SBAR RB
   * - ADVP
     - R
     - RB RBR RBS FW ADVP TO CD JJR JJ IN NP
   * - 
     - 
     - JJS NN
   * - CONJP
     - R
     - CC RB IN
   * - FRAG
     - R
     -
   * - INTJ
     - L
     -
   * - LST
     - R
     - LS :
   * - NAC
     - L
     - NN NNS NNP NNPS NP NAC EX \$ CD QP PRP
   * - 
     -
     - VBG JJ JJS JJR ADJP FW
   * - PP
     - R
     - IN TO VBG VBN RP FW
   * - PRN
     - L
     -
   * - PRT
     - R
     - RP
   * - QP
     - L
     - \$ IN NNS NN JJ RB DT CD NCD QP JJR JJS
   * - RRC
     - R
     - VP NP ADVP ADJP PP
   * - S
     - L
     - TO IN VP S SBAR ADJP UCP NP
   * - SBAR
     - L
     - WHNP WHPP WHADVP WHADJP IN DT S SQ
   * - 
     -
     - SINV SBAR FRAG
   * - SBARQ
     - L
     - SQ S SINV SBARQ FRAG
   * - SINV
     - L
     - VBZ VBD VBP VB MD VP S SINV ADJP NP
   * - SQ
     - L
     - VBZ VBD VBP VB MD VP SQ
   * - UCP
     - R
     -
   * - VP
     - L
     - TO VBD VBN MD VBZ VB VBG VBP VP ADJP
   * - 
     -
     - NN NNS NP
   * - WHADJP
     - L
     - CC WRB JJ ADJP
   * - WHADVP
     - R
     - CC WRB
   * - WHNP
     - L
     - WDT WP WP\$ WHADJP WHPP WHNP
   * - WHPP
     - R
     - IN TO FW

If the parent category is ``NP``, the following rules are used.  The
first one that matches determines the head.

 * The rightmost child that is a terminal node, if its category is
   ``POS``,
 * The rightmost child that is one of: {\tt NN NNP NNPS NNS NX POS JJR},
 * The leftmost child that is {\tt NP},
 * The rightmost child that is one of: {\tt \$ ADJP PRN},
 * The rightmost child that is {\tt CD},
 * The rightmost child that is one of: {\tt JJ JJS RB QP},
 * The rightmost child that is a terminal node.

These rules may fail if the parent category is not listed, or if an NP
contains no terminal node.  In either of those cases, Collins
specifies no action, but one presumably takes the rightmost child as head.

Finally, there is an adjustment rule that applies in the case of
coordination.

 * If the head is immediately preceded by {\tt CC}, and there is
   another child before the {\tt CC}, then that other child becomes head.

Decoordination
--------------

Head-marking is problematic in coordination structures, because, in
the usual view, all the coordinands have an equal claim to being head.
If desired, one can break the symmetry in coordination structures,
before head marking, by calling the function ``decoordinate()``.

.. py:function:: decoordinate(tree)

   Replaces all coordinate structures
   with single-headed structures, in which the first coordinand is left
   in place, but other coordinands are wrapped in a new adjunct node with
   category ``CO`` and role ``co``.
   The replacement is destructive.  Here is an example:
   
   >>> t = parse_tree('''(NP (N trains)
   ...                       (',' ',') (N planes)
   ...                       (',' ',') (CC and) (N autos))''')
   >>> decoordinate(t)
   >>> print(t)
   0    (NP
   1       (N trains)
   2       (CO:co
   3          (, ,)
   4          (N planes)
   5          (, ,)
   6          (CC and)
   7          (N:head autos)))
