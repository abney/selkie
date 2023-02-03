
``selkie.gen`` — Generation
===========================

*This is currently broken.*

Random generation from a feature grammar is a little tricky.  It is
not currently implemented, but the algorithm is described here.

To do random generation with feature grammars, we require both a
downward and upward pass, analogous to the upward chart-filling
step followed by the downward unwinding step in parsing.  In parsing,
we "enter" an expansion from the lower left corner (the first)
child, and proceed from child to child, finally "exiting" at the
top.  The "enter" steps involve unification of a node with a child
category, and the "exit" step involves instantiation of the lefthand
side category.  In generation, we enter from the top, unifying the
parent node with the lefthand side category.  

In random generation, we fully instantiate rules as we generate a
tree.  Full instantiation means eliminating not only variables but
also disjunctions, leaving a unique value for each attribute.  The
choice among disjuncts is made stochastically.

We begin by fully instantiating the start
category.  We create a root node for the start category, but leave the
children as yet unspecified.

Then, at each point, we have a parent node with a fully instantiated
category, and we find the rules that could expand it.
Rules are indexed by symbol in the grammar, not by complete
feature sets, so we must scan through a candidate list to determine
which ones actually match the given parent category.  The result of
each successful match is an updated symbol table.  We make a list of
the matching rules, and the symbol table for each.

We make a stochastic choice among the rules that match the parent
category.  We use the updated symbol table to fully instantiate each
righthand-side category in turn, keeping track of further symbol-table
updates as we go.  As we instantiate each child category, we create a
node possessing the category and insert it into the parent's child
array.  Then we recursively expand each child in turn.

It is possible for generation to fail.  For example, consider the
following little grammar.

S -> A[f ?x] B[f ?x];
S -> A[f ?x];
A[f 1] -> foo;
A[f 2] -> bar;
B[f 2] -> baz;


The ``f`` attribute ranges over ``1`` and ``2``; but if one
choose the first expansion for ``S``, then one must choose value
``2``.  If one happens to choose ``1``, though, the problem is
not detected until one attempts to generate a subtree from
``B[f 1]``.

Generation algorithm
--------------------

A **node** represents the results of generating from a pair
(*cat, sem*).  We may consider indexing nodes: a given node may
well be needed multiple times, because many choices of first
child may lead to the same requirements for the next child.
The calling state is recorded with the node.  If additional states
call for the same node, they will also be recorded as callers.

To expand the node, we find all rules whose lhs is consistent with
(*cat, sem*), and for each rule we create a new state.
The node is passed along as states are expanded.

A **state** is like a parser edge.  It represents a partial state of
generating from a given rule.  The first *i* children have been
generated.  Their categories have been merged into the current
bindings, and their semantics has been unified into the rule
semantics.

To advance a state, we substitute the current bindings into the
category of the next child, and we unify the appropriate sub-avs of
the current one with the semantics of the next child.  Then we
generate from that (*cat, sem*) pair.  The result is a list of
trees.  For each tree, we create a new state in which the tree
category is used to update the bindings, and the tree semantics is unified
into the semantics of the previous state to create the new state's semantics.

When a state has generated all children for its rule, a new tree is
created, whose category
comes from substituting the bindings into the rule lhs, and whose
semantics is the state's semantics.  That tree is passed back to the
node, which passes it to all of its callers.

We keep a stack of active states.  The discipline is depth-first, so
that we generate a complete tree as quickly as possible.

Example::

   >>> from selkie.data import ex
   >>> from selkie.grammar import Grammar
   >>> from selkie.parser import Parser
   >>> from selkie.gen import Generator
   >>> g = Grammar(ex('tinygen.g'))
   >>> p = Parser(g)
   >>> ts = p('fido barks')
   >>> print ts[0]
   0   (s              : [subj fido; type bark]
   1      (np             : fido
   2         (name fido))    : fido
   3      (vp             : [type bark]
   4         (vi barks)))    : [type bark]
   >>> sem = ts[0].sem
   >>> gen = Generator(g)
   >>> iter = gen(sem)
   >>> t = iter.next()
   >>> print t
   0   (s              : [subj fido; type bark]
   1      (np             : fido
   2         (name fido))    : fido
   3      (vp             : 6.0
   4         (vi barks)))    : [type bark]
