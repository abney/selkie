
``selkie.interp`` — Semantic interpretation
===========================================

.. testsetup::

   from selkie.expr import restart_variables
   restart_variables()

Steps in interpretation
-----------------------

The interpreter takes a parse tree as input and produces a
predicate-calculus expression as output.  There are multiple steps:

 * Metavariable replacement.  Replace the "``@``" metavariables in
   the semantic fragments in the parse tree.

 * Quantifier raising.  This transforms the parse tree, and also
   eliminates the "``!qs``" and "``!q``" directives in the
   semantic attachments.

 * Translation.  Fuse the semantic attachments, recursively, to
   produce an initial predicate-calculus expression.

 * Gap replacement.  Interpret the "``$g``" and "``!g=``"
   directives.

 * Macro replacement.  Replace macro calls with their
   definitions.

 * Standardize variables.  Make sure every variable-binding operator
   is associated with a unique variable.  This is necessary in order to
   avoid accidental capture of variables during lambda reduction.

 * Simplification (beta reduction).  Eliminate lambda applications.
   To be useful for reasoning, no lambda expressions should remain
   after simplification.

.. py:function:: replace_metavariables(e)
   
   Metavariables are used in grammars to stand in for variables.  A given
   grammar rule may be used several times in the course of parsing, and
   each time it is used, a new variable is created as instantiation of
   the metavariable.

   The symbol "``@``" represents a metavariable.  The function
   ``replace_metavariables()`` replaces all occurrences of
   "``@``" in a given expression with a new variable.
   
   >>> from selkie.expr import parse_expr
   >>> e = parse_expr('(lambda @ ($1 @ $2))')
   >>> from selkie.interp import replace_metavariables
   >>> vp = replace_metavariables(e)
   >>> vp
   (lambda _1 ($1 _1 $2))
   
   Note that, if we replace metavariables again, we get a different variable:
   
   >>> replace_metavariables(e)
   (lambda _2 ($1 _2 $2))

.. py:function:: tree_replace_metavariables(tree)

   Calls ``replace_metavariables()`` on the semantic expressions
   attached to each node in the tree.

.. py:function:: raise_quantifiers(tree)

   The function is ``raise_quantifiers()``.  First we create a tree to
   apply it to:
   
   >>> from selkie.data import ex
   >>> from selkie.parser import Parser
   >>> p = Parser(ex('sg0a'))
   >>> p('every cat chases a dog')
   [<Tree S ...>]
   >>> t = _[0]
   >>> from selkie.interp import tree_replace_metavariables
   >>> tree_replace_metavariables(t)
   >>> print(t)
   0   (S                     : (!qs ($2 $1))
   1      (NP[sg]                : (!q $1 _3 ($2 _3))
   2         (Det[sg] every)        : every
   3         (N[sg] cat))           : cat
   4      (VP[sg]                : (lambda _5 ($1 _5 $2))
   5         (V[sg,t,0] chases)     : chase
   6         (NP[sg]                : (!q $1 _4 ($2 _4))
   7            (Det[sg] a)            : some
   8            (N[sg] dog))))         : dog
   
   Now we call ``raise_quantifiers()``:
   
   >>> from selkie.interp import raise_quantifiers
   >>> print(raise_quantifiers(t))
   0   (NP[sg]                : ($1 _3 ($2 _3) $3)
   1      (Det[sg] every)        : every
   2      (N[sg] cat)            : cat
   3      (NP[sg]                : ($1 _4 ($2 _4) $3)
   4         (Det[sg] a)            : some
   5         (N[sg] dog)            : dog
   6         (S                     : ($2 $1)
   7            (NP[sg])               : _3
   8            (VP[sg]                : (lambda _5 ($1 _5 $2))
   9               (V[sg,t,0] chases)     : chase
   10              (NP[sg])))))           : _4

   Quantifier raising is discussed in greater detail in the next section.

.. py:function:: fuse(expr, subexprs)

   The ``fuse()`` function expands the variables "``$1``,"
   "``$2``," etc.  It is given an expression and a list of child
   translations.
   
   >>> from selkie.interp import fuse
   >>> fuse(vp, ['chase', 'Fido'])
   (lambda _1 (chase _1 Fido))

.. py:function:: translation(tree)

   The function ``translation()`` calls ``fuse()`` on each node of a
   tree, bottom-up, to convert the tree to a predicate calculus
   expression.
   
   >>> p('Fido barks')
   [<Tree S ...>]
   >>> t = _[0]
   >>> print(t)
   0   (S                   : (!qs ($2 $1))
   1      (NP[sg]              : $1
   2         (Name Fido))         : Fido
   3      (VP[sg]              : $1
   4         (V[sg,i,0] barks)))  : bark
   >>> from selkie.interp import translation
   >>> translation(t)
   (!qs (bark Fido))

.. py:function:: replace_gaps(expr)

   The operator ``$g`` is the gap metavariable, and the operator
   ``!g=`` sets its value to a regular variable.  For example:
   
   >>> e = parse_expr('(lambda x (!g= x (chase Max $g)))')
   >>> e
   (lambda x (!g= x (chase Max $g)))
   >>> from selkie.interp import replace_gaps
   >>> replace_gaps(e)
   (lambda x (chase Max x))

.. py:class:: selkie.interp.Macros(fn)

   Macro replacement is done by calling an instance of ``Macros`` as a
   function.
   
   >>> from selkie.interp import Macros
   >>> defs = Macros(ex('sg0.defs'))
   >>> e = parse_expr('(every d (dog d) (some c (cat c) (chase c d)))')
   >>> e
   (every d (dog d) (some c (cat c) (chase c d)))
   >>> defs(e)
   (forall d (if (dog d) (exists c (and (cat c) (chase c d)))))

.. py:function:: standardize_variables(expr)

   The function ``standardize_variables()`` takes an expression and
   returns an equivalent expression in which every variable-binding
   operator binds a unique variable, distinct from each other and from
   all globally free variables.  For example:
   
   >>> e = parse_expr('(forall x ((lambda y (exists x (g x y z))) x))')
   >>> from selkie.interp import standardize_variables
   >>> standardize_variables(e)
   (forall _6 ((lambda _7 (exists _8 (g _8 _7 z))) _6))
   
   Note that lambda reduction assumes that variables have been
   standardized.  It does not call ``standardize_variables()``, but
   passing an expression to lambda reduction that has non-standardized
   variables can lead to incorrect results.

.. py:class:: selkie.interp.Symtab

   Both ``standardize_variables()`` and ``simplify()`` make
   use of symbol tables.  The class ``Symtab`` is a specialization of
   ``dict``.  It differs from ``dict`` in two ways.

    * It returns ``None`` for an undefined key (instead of signalling an error).
    * If ``None`` is assigned to a key as value, the key is deleted
      from the table.

.. py:function:: simplify(expr)

   Simplification involves replacing *lambda applications* (the
   application of a lambda expression to arguments) with a simplified
   form in which the arguments are substituted into the body of the
   lambda expression.

   For example,
   suppose that we translate "chases Max" as the lambda expression::
   
      (lambda x (chases x Max))
   
   Applying that to "Fido" gives us the lambda application::
   
      ((lambda x (chases x Max)) Fido)
   
   which simplifies, by beta reduction, to:
   
   >>> from selkie.interp import simplify
   >>> e = parse_expr('((lambda x (chases x Max)) Fido)')
   >>> simplify(e)
   (chases Fido Max)

   The implementation of simplification is discussed below in a
   separate section.

Quantifier raising
------------------

We do quantifier raising (QR) *before* converting the tree to a
predicate calculus expression.
To understand the motivation for doing QR before translation, consider
the following parse tree, for the sentence "every cat chases a dog"::

   (S                   : (!qs ($2 $1))
     (NP[sg]              : (!q $1 @ ($2 @))
       (Det[sg] every)      : every
       (N[sg] cat))         : cat
     (VP[sg]              : (lambda @ ($1 @ $2))
       (V[sg,t,0] chases)   : chase
       (NP[sg]              : (!q $1 @ ($2 @))
         (Det[sg] a)          : some
         (N[sg] dog))))       : dog

If we convert the tree to a predicate-calculus expression before doing
quantifier raising, we get::

   (!qs ((lambda _2 (chase _2 (!q some _3 (dog _3))))
         (!q every _1 (cat _1))))

After beta-reduction, we have::

   (!qs (chase (!q every _1 (cat _1))
               (!q some _3 (dog _3))))

The result is known as **quasi-logical form** (QLF).  It is not an
interpretable predicate-calculus expression, but will become one after
the quantifiers are raised to a scope position.

**Quantifier raising** maps from QLF to logical form (LF).  The
first step is to excise each quantifier, leaving its variable behind.
In this case, that leaves only::

   (chase _1 _3)

Then one wraps each quantifier in turn around the scope expression.
(The scope expression becomes an additional argument for the quantifier)::

   (every _1 (cat _1)
     (some _3 (dog _3)
       (chase _1 _3)))

(Note that we have dropped the ``!q`` and ``!qs`` operators in
the process.)

One observation that will become important is this: each quantifier
*must* have a distinct variable.  Consider what happens if the
quantifiers share the same variable::

   (!qs (chase (!q every _1 (cat _1))
               (!q some _1 (dog _1)))))

After raising, we have::

   (every _1 (cat _1)
     (some _1 (dog _1)
       (chase _1 _1)))

This is logically equivalent to::

   (some _1 (dog _1) (chase _1 _1))

which is not at all the correct interpretation.

Assuming that no rule explicitly creates multiple quantifiers that share a
variable, each quantifier in the initial translation will have a distinct
variable.  We need only assure that we do not create duplicates
anywhere along the line.

Now a dilemma arises concerning the ordering of quantifier raising
with respect to lambda reduction.  In the example just given, we did
lambda reduction first, but that can be problematic.  Specifically,
doing beta-reduction before quantifier raising can create
duplicate quantifiers.  Consider the example "some dog is a friendly slobberer."
The translation is::

   (!qs ((lambda _1 (and (friendly _1) (slobberer _1)))
         (!q some _2 (dog _2))))

After beta-reduction, we have::

   (!qs (and (friendly (!q some _2 (dog _2)))
             (slobberer (!q some _2 (dog _2)))))

Lambda reduction has duplicated the quantifier.  To avoid erroneous
interpretations, we have no choice but to rename one set of variables::

   (!qs (and (friendly (!q some _2 (dog _2)))
             (slobberer (!q some _3 (dog _3)))))

But now, after quantifier raising, we end up with the wrong meaning::

   (some _2 (dog _2)
     (some _3 (dog _3)
       (and (friendly _2)
            (slobberer _3))))

This says that there is a friendly dog, and there is a slobbering dog,
but it does not imply that they are one and the same dog.

The obvious conclusion is that we must do quantifier raising before
doing lambda reduction.  But a problem arises that way as well.
Consider the sentence "every cat chases a dog," with
translation::

   (!qs ((lambda _2 (chases _2 (!q some _3 (dog _3))))
         (!q every _1 (cat _1))))

When we raise quantifiers, they come out in the wrong order::

   (some _3 (dog _3)
       (every _1 (cat _1)
           ((lambda _2 (chases _2 _3)) _1)))

This is a less devastating problem: the sentence is in fact ambiguous,
and the interpretation we are getting is legitimate, but it is not the
preferred interpretation.

There is a third alternative, which is the one we adopt:
do quantifier raising
on the syntactic parse tree, before translation.
We again consider "every cat chases some dog."  After metavariable
instantiation, we have::

   (S                   : (!qs ($2 $1))
     (NP[sg]              : (!q $1 _1 ($2 _1))
       (Det[sg] every)      : every
       (N[sg] cat))         : cat
     (VP[sg]              : (lambda _2 ($1 _2 $2))
       (V[sg,t,0] chases)   : chase
       (NP[sg]              : (!q $1 _3 ($2 _3))
         (Det[sg] a)          : some
         (N[sg] dog))))       : dog

The procedure for doing quantifier raising is basically the same, but
we operate on the node plus semantic attachment, not just on the semantics.
First, we excise the quantifier nodes, leaving behind an empty node
whose translation is the variable.  The result is the body::

   (S                   : (!qs ($2 $1))
     (NP[sg])             : _1
     (VP[sg]              : (lambda _2 ($1 _2 $2))
       (V[sg,t,0] chases)   : chase
       (NP[sg])))           : _3

Then we wrap the quantifiers around the body.  Syntactically,
the body becomes an additional child node, and we add a corresponding additional
"$" variable to the translation.  We also
drop the "``!q``" and "``!qs``" markers::

   (NP[sg]              : ($1 _1 ($2 _1) $3)
     (Det[sg] every)      : every
     (N[sg] cat)          : cat
     (NP[sg]              : ($1 _3 ($2 _3) $3)
       (Det[sg] a)          : some
       (N[sg] dog)          : dog
       (S                   : ($2 $1)
         (NP[sg])             : _1
         (VP[sg]              : (lambda _2 ($1 _2 $2))
           (V[sg,t,0] chases)   : chase
           (NP[sg])))))         : _3

Only after quantifier raising do we fuse the semantic attachments.
The result is::

   (every _1 (cat _1)
     (some _3 (dog _3)
       ((lambda _2 (chase _2 _3)) _1)

Now beta-reduction is safe.

Incidentally, there is an independent motivation for this approach.  Scope preferences
often care about the particular English word used.  For example, "each" and
"every" differ not in meaning, but in that "each" prefers wide
scope and "every" prefers narrow scope.


Simplification
--------------

Simplification involves applying **beta reduction** to each
lambda-expression application in the expression.
The general form of a lambda application is::

   ((``lambda`` *params body*) *args*). 

Consider the example::
   
   ((lambda x (chases x Max)) Fido)

In this case, *params* is ``[x]`` (a
single-element list), *body* is
``(chases x Max)``, and *args* is ``[Fido]`` (also a
single-element list).
In beta reduction, all occurrences of the parameters in the body are
replaced with the corresponding arguments, yielding a simpler
expression that is equivalent to the original.  In this case (as we
have already seen), the result is::

   (chases Fido Max)

Here are some more examples.

>>> e = parse_expr('''((lambda (x y) (knows (mother y) x))
...                    Fido
...                    (the cat))''')
>>> simplify(e)
(knows (mother (the cat)) Fido)
>>> e = parse_expr('''((lambda x (and (friendly x) (slobberer x)))
...                    Fido)''')
>>> simplify(e)
(and (friendly Fido) (slobberer Fido))

Beta reduction can be defined as follows::

   (λ x.t)s = t[x→s]

where ``t[x→s]`` means the expression *t* with all free
occurrences of *x* replaced by *s*.  The result may be another lambda
application, in which case it is necessary to reduce again.

Substitution is defined more precisely as follows:

 1. ``x[x→r] = r``
 2. ``y[x→r] = y``
 3. ``(ts)[x→r] = (t[x→r])(s[x→r])``
 4. ``(λ x.t)[x→r] = λ x.t``
 5. ``(λ y.t)[x→r] = λ y.t[x→r]``

Here, *x* and *y* are (distinct) variables; *r*, *s*, and *t* are
(possibly complex) terms.

There is one caveat: in rule (5), the
variable *y* must not occur free in *r*.  If it did, it would be
invalidly captured by the lambda.  This is true for variable-binding
operators more generally: the substitution::

   forall y.t[x→r]

would also be invalid if *y* occurs free in *r*.

We can prevent this happening by
first renaming all variables involved in variable-binding expressions, so that
every variable-binding operator has its own unique variable.  (The standard term
for this renaming is *alpha conversion.*)
Incidentally, doing so makes (d) moot.

It is possible to construct pathological expressions for which
beta-reduction never returns.  Consider::

   (λ x.xx)(λ x.xx)

We apply the substitution ``[x→λ x.xx]`` to the term
*xx*, with the result::

   (λ x.xx)(λ x.xx)

That is, we are right back where we started, and repeated reductions
will never terminate.

The current implementation does not attempt to prevent this.

.. py:function:: beta_reduce(expr, env)

   *Expr* must be a lambda application of form ((lambda params body) args).
   For convenience, we permit *params* to be either a Variable
   or a list of Variables.  If it is a Variable, treat it as a singleton list.

   Reduce each of the arguments using the current environment.
   Add the substitution param→arg to the environment,
   for each parameter-argument pair.  The value for the parameter is the
   argument after reduction.
   Reduce the body using the new substitution and return the result.

The function ``beta_reduce()`` assumes that variables have
already been standardized.  We combine substitution and
reduction into a single
pass through an expression.  I.e., while applying a substitution to an
expression, if the expression happens to be a lambda application, we
reduce it, adding bindings to the substitution.  We assume that
variables have already been standardized.
The combined process can be summed up as follows::

   x[x→r|α] = r
   y[α] = y if *y* has no value in α
   ((λ x.t)s)[α] = t[x→s[α]|α]
   (ts)[α] = (t[α])(s[α])
   (λ y.t)[α] = λ y.t[α]

In detail, ``simplify(expr)`` is defined as follows.

 * If ``expr`` is a bound variable, return its value.  If it is
   a free variable, return the variable itself.

 * If ``expr`` is a constant (i.e., not an ``Expr``), return it.

 * If ``expr`` is a lambda application, return ``beta_reduce(expr)``.

 * If ``expr`` is headed by a variable-binding operator,
   return a new expression consisting of operator, parameter list, and
   the reduced body.

 * Otherwise, return a new expression consisting of the reductions of
   all elements ``expr``.

However, if the return value is itself a lambda application, reduce it
repeatedly until we obtain something that is not a lambda application.

Here is an example.

>>> e = parse_expr('((lambda (x y) (foo (bar y) x)) (mother jack) (father jill))')
>>> simplify(e)
(foo (bar (father jill)) (mother jack))

Here is a somewhat trickier example.

>>> e = parse_expr('''((lambda (P x) (P x))
...                    (lambda y (forall z (f y z)))
...                    Fido)''')
>>> simplify(e)
(forall z (f Fido z))

The interpreter
---------------

The interpreter is created from a grammar file name.  It creates and
stores a parser for the grammar.

>>> from selkie.interp import Interpreter
>>> interp = Interpreter(ex('sg1a'))

It behaves as a function.  It takes a sentence as input, parses it,
and interprets it.  The return value is a list of predicate-calculus
expressions, one for each parse tree.

>>> interp('every cat chases a dog')
[(forall _22 (if (cat _22) (exists _23 (and (dog _23) (chase _22 _23)))))]

One can see the results of each step of processing by providing the
keyword argument ``trace=True``.
