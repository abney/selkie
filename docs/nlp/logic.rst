
``selkie.logic`` — Automated reasoning
======================================

.. testsetup::

   from selkie.expr import restart_variables
   restart_variables()

The module ``selkie.logic`` provides a resolution-based theorem
prover.

Clausification
--------------

Reasoning is on the basis of **clauses**, but the output of parsing
and interpretation is predicate-calculus expressions.  Accordingly,
we must first convert a predicate calculus expression to
a set of clauses.

A clause is a set of literals, interpreted disjunctively.  For
example::

   +(dog Fido) +(cat Fido)

is a clause interpreted as "either Fido is a dog or Fido is a cat."
The components of a clause are **literals.**  A literal is a
**term** with a polarity.  A term is an expression containing only
variables, constants, and function application.

Both literals in the preceding example
were positive.  Here is an example with mixed polarities::

   -(human Socrates) +(mortal Socrates)

This represents "either Socrates is not human, or Socrates is
mortal," which is equivalent to "if Socrates is human, then Socrates
is mortal."

.. py:class:: Literal

   The class ``Literal`` represents a literal.  Its attributes are
   ``polarity`` and ``expr``.
   
   >>> from selkie.expr import parse_expr
   >>> from selkie.logic import Literal
   >>> lit1 = Literal(False, parse_expr('(human Socrates)'))
   >>> lit1
   -(human Socrates)
   >>> lit1.polarity
   False
   >>> lit1.expr
   (human Socrates)

.. py:class:: Clause

   One creates a clause from a list of literals.
   
   >>> lit2 = Literal(True, parse_expr('(mortal Socrates)'))
   >>> from selkie.logic import Clause
   >>> c = Clause([lit1, lit2])
   >>> print(c)
   1. -(human Socrates) +(mortal Socrates)

   .. py:attribute:: answer_literal

      A special literal whose predicate is ``_Ans``, meaning "this is
      the answer".

   .. py:attribute:: provenance

      A tuple (cl1, i, cl2, j), meaning that this clause was deduced
      by canceling the i-th literal of *cl1* against the j-th literal
      of *cl2*.

   .. py:attribute:: weight

      When deciding which clause to prioritize for processing, choose
      the one with the greatest weight.

Conversion to Clauses
---------------------

Let us consider an example that will illustrate the steps of conversion.
This states that every animal lover is loved by someone.

>>> from selkie.expr import load_exprs
>>> from selkie.data import ex
>>> orig = load_exprs(ex('cnf.expr'))[0]
>>> print(orig)
(forall x
   (if (forall y
          (if (animal y)
              (loves x y)))
       (exists y
          (loves y x))))

The conversion is effected by the following functions, applied in order.

.. py:function:: check_syntax(expr)

   The function ``check_syntax()`` checks that a predicate-calculus
   expression is well-formed.  It checks that variable-binding operators
   have variables where expected, and that all logical operators have the
   right number of arguments.
   
   >>> from selkie.logic import check_syntax
   >>> check_syntax(orig)
   >>> check_syntax(parse_expr('(forall Fido (woof))'))
   Traceback (most recent call last):
     File "<stdin>", line 1, in <module>
     File "/cl/python/selkie/logic.py", line 135, in check_syntax
       raise Exception, "Expecting variable in: " + str(expr)
   Exception: Expecting variable in: (forall Fido (woof))

.. py:function:: standardize_variables(expr)
   :noindex:

   In the expression ``orig``, there are two quantifiers that bind the variable *y*.
   After standardization, each quantifier binds a unique variable.
   
   >>> from selkie.interp import standardize_variables
   >>> e = standardize_variables(orig)
   >>> print(e)
   (forall _1
      (if (forall _2
             (if (animal _2)
                 (loves _1 _2)))
          (exists _3
             (loves _3 _1))))
   
   The function ``standardize_variables()`` is imported from the module
   ``selkie.interp``.  It is called in the production of an expression
   from a parse tree, but ``clausify()`` calls it for the sake of
   expressions that are not produced by the interpreter.

.. py:function:: expand_query(expr)

   The next step is the replacement of
   question operators ``wh`` and
   ``yn`` with the answer predicate ``_Ans``.  Our running example
   does not illustrate this; we give different examples.  An
   example with the ``wh`` operator is:
   
   >>> wh = parse_expr('(wh x (criminal x))')
   
   This expands to:
   
   >>> from selkie.logic import expand_query
   >>> expand_query(wh)
   (forall x (if (criminal x) (_Ans x)))
   
   An example with the ``yn`` operator is:
   
   >>> yn = parse_expr('(yn (criminal West))')
   
   This expands to:
   
   >>> print(expand_query(yn))
   (and (if (criminal West)
            (_Ans yes))
        (if (not (criminal West))
            (_Ans no)))

.. py:function:: eliminate_implications(expr)

   We replace all
   occurrences of ``P <-> Q`` with ``(P -> Q) v (Q -> P)``, and then we
   replace all occurrences of ``P -> Q`` with ``-P v Q``.  Returning
   to our running example:
   
   >>> from selkie.logic import eliminate_implications
   >>> e = eliminate_implications(e)
   >>> print(e)
   (forall _1
      (or (not (forall _2
                  (or (not (animal _2))
                      (loves _1 _2))))
          (exists _3
             (loves _3 _1))))

.. py:function:: lower_negation(expr)

   An expression of form "not forall" becomes "exists not",
   "-(P & Q)" becomes "-P v -Q", etc.
   
   >>> from selkie.logic import lower_negation
   >>> e = lower_negation(e)
   >>> print(e)
   (forall _1
      (or (exists _2
             (and (animal _2)
                  (not (loves _1 _2))))
          (exists _3
             (loves _3 _1))))


.. py:function:: skolemize(e)

   Skolemization eliminates "exists" by introducing functions called
   Skolem functions.  One can think of a *Skolem term* involving the
   application of a Skolem function to a universally-bound variable as
   a unique description of a particular (anonymous) individual.  A
   fuller explanation is given in the next section.

   Applied to our running example, Skolemization produces the following:
   
   >>> from selkie.logic import skolemize
   >>> e = skolemize(e)
   >>> print(e)
   (or (and (animal (_Sk1 _1))
            (not (loves _1
                    (_Sk1 _1))))
       (loves (_Sk2 _1)
              _1))
   

.. py:function:: cnf(expr)

   The function ``cnf()`` distributes disjunctions over conjunctions,
   converting to conjunctive normal form.  The result is represented as a
   list of lists.  The outer list is a conjunction, and the inner lists
   are disjunctions.
   
   >>> from selkie.logic import cnf
   >>> e = cnf(e)
   >>> type(e)
   <class 'list'>
   >>> for d in e: print(d)
   ... 
   [(animal (_Sk1 _1)), (loves (_Sk2 _1) _1)]
   [(not (loves _1 (_Sk1 _1))), (loves (_Sk2 _1) _1)]

.. py:function:: clauses(lsts)

   The final step converts the list of lists to a list of clauses.  In
   the process, disjunctions and conjunctions containing "``True``" and
   "``False``" are simplified if possible, as are singleton
   disjunctions and conjunctions.  Also, the special operator ``_Ans``
   is recognized as marking the answer literal.
   
   >>> from selkie.logic import clauses
   >>> for c in clauses(e): print(c)
   ... 
   2. +(animal (_Sk1 _1)) +(loves (_Sk2 _1)
          _1)
   3. -(loves _1 (_Sk1 _1)) +(loves (_Sk2 _1) _1)
   
   The result is not immediately readable.  Here is how to make sense of it.
   First, ``_Sk2`` is one's best/only friend: the person who loves you, if
   anyone does.  Hence the first clause states that either your only
   friend loves you, or ``_Sk1`` is an animal.  That is, if your only
   friend does *not* love you, then ``_Sk1`` is an animal.
   The second clause states: if your only friend does not love you, then
   you do not love ``_Sk1``.
   Combining the two: if no one loves you, then there is an
   animal that you do not love.
   The counterpositive is: if you love every animal, then someone
   loves you.

.. py:function:: clausify(expr)
   
   The function ``clausify()`` does the complete sequence of
   conversions from predicate-calculus expression to clause list.
   
   >>> from selkie.logic import clausify
   >>> for c in clausify(orig): print(c)
   ... 
   4. +(animal (_Sk3 _4)) +(loves (_Sk4 _4) _4)
   5. -(loves _4 (_Sk3 _4)) +(loves (_Sk4 _4) _4)


Skolemization
-------------

Skolemization is a technique for eliminating quantifiers; that is,
replacing existentially-bound variables with names, leaving all
remaining variables implicitly universally bound.

We begin with two observations.  First,
it is common in mathematics for free variables to be interpreted as
universally bound.  For example::

   x + y = y + x

may be interpreted as::

   forall x forall y [x + y = y + x]

The second observation is that names
might be interpreted as existentially bound variables.
For example, consider "Fido is a dog.  Fido barks.  Fido does not like any cat."
We might treat this as::

   exists Fido [
       dog(Fido) & barks(Fido) & forall c [
           cat(c) -> -likes(Fido,c)
       ]
   ]

Note that the "name existential" *must* take wide scope
over "real" quantifiers: we do not want a different Fido for each cat.

We can use these observations to eliminate (some) quantifiers.
Consider "a cat chases every dog"::

   exists c [
       cat(c) & forall d [
           dog(d) -> chases(c,d)
       ]
   ]

We can turn *c* into a name, and allow "forall d" to be implicit::

   cat(C) & [ dog(d) -> chases(C,d) ]

Now of course there is a second reading for the sentence::

   forall d [
       dog(d) -> exists c [
           cat(c) & chases(c,d)
       ]
   ]

In this reading, there is a different cat for each dog.
That is, the cat *C* is **a function of** *d*::

   dog(d) -> cat(C(d)) & chases(C(d), d)

This is the key idea of Skolemization.

The general rule is this:
we replace each existentially bound variable *y* with a **Skolem function**
:math:`Y(x_1,\ldots,x_n)`,
where :math:`x_1,\ldots,x_n` are the universals that have wider scope than *y*.
Then we can delete quantifiers.  All remaining variables are
interpreted as universally bound.


Resolution theorem proving
--------------------------

Let us consider some common rules of inference.
The first is modus ponens, which takes the following form::

   forall x [human(x) -> mortal(x)]
   human(Socrates)
   ----------------
   mortal(Socrates)


The second is modus tolens::

   forall x [human(x) -> mortal(x)]
   -mortal(Zeus)
   ----------------
   -human(Zeus)

A third is reasoning by case::

   murderer(Jeeves) v murderer(Smith)
   -murderer(Jeeves)
   -----------------
   murderer(Smith)

All of these rules of inference (and many others) have a common form,
which becomes even more explicit if we express them in
**conjunctive normal form** (CNF).  In CNF, expressions are
transformed to a conjunction of disjunctions, and variables are
understood as universally bound::

   forall x [P(x) -> Q(x)] -> -P(x) v Q(x)

In CNF, modus ponens has the form::

   -P(x) v Q(x)
   P(a)
   ------------
   Q(a)

Modus tolens::

   -P(x) v Q(x)
   -Q(a)
   ------------
   -P(a)

Reasoning by case::

   P(a) v Q(a)
   -P(a)
   ------------
   Q(a)

All three are special cases of **resolution**::

   +- P(α) v Q<sub>1</sub> v ... v Q<sub>m</sub>
   -+ P(β) v R<sub>1</sub> v ... v R<sub>n</sub>
   ----------------------------------------------
   Q'<sub>1</sub> v ... v Q'<sub>m</sub> v R'<sub>1</sub> v ... v R'<sub>n</sub>

Here, α and β need not be identical, but do need to be
**unifiable**.  The **unifier**
is the set of variable assignments that make them identical.  E.g.,
the unifier of *x* and Socrates is: *x* = Socrates.
Q'<sub>i</sub> comes from Q<sub>i</sub> by **substituting** the unifier.
E.g., substituting (x = Socrates) into mortal(x)
yields mortal(Socrates).
The *Q*'s and *R*'s may be positive or negated, and
the order of disjuncts is irrelevant.

Let us consider a simple example of reasoning by resolution.
The knowledge base consists of two clauses::

   1. -(human x) +(mortal x)
   2. +(human Socrates)

Each clause is understood disjunctively.  For example, clause 1 states
that either *x* is not human, or *x* is mortal.  (That is equivalent
to: if *x* is human, then *x* is mortal.)  The knowledge base asserts
the conjunction of the clauses.

To answer the query "is Socrates mortal," we try to prove that Socrates
is mortal.  To do that, we assume that Socrates is *not* mortal,
and deduce a contradiction.
That is, we adopt the assumption::

   -(mortal Socrates)

This resolves with clause 1, with *x* = Socrates, yielding::

   -(human Socrates)

This in turn contradicts clause 2.  Resolving with clause 2
yields the empty clause, which represents a contradiction.

Now let us consider the query "who is mortal."
Assume that no one is mortal, and try to deduce a
contradiction::

   -(mortal y)

This resolves with clause 1, with *x* = *y*, yielding::

   -(human y)

This resolves with clause 2, with *y* = Socrates, yielding the
empty clause.

That proves that someone is mortal, but it does not answer the
question of *who* is mortal.
To do so, we add an "answer literal" to our assumption::

   -(mortal y) ; +(_Ans y)

This can be read as "if *y* is mortal, then *y* is the answer."
Any substitutions of values for variables apply to the answer literal
as to the other literals, but the answer literal is otherwise treated
as an annotation rather than a contentful literal.  One does not use
the answer literal for resolution, and the proof is complete when only
the answer literal remains.

The above assumption resolves with clause 1, yielding::

   -(human y) ; +(_Ans y)

This in turn resolves with clause 2, yielding::

   ; +(_Ans Socrates)

At this point the proof is complete: there are no content literals left.
The answer is: Socrates.

Now let us consider a more complex example.
The following sentences are input to the parser::

   every American who sells a weapon to a hostile country is a criminal
   West sells Nono every missile that Nono owns
   every enemy of America is a hostile country
   every missile is a weapon
   Nono owns a missile
   West is an American
   Nono is an enemy of America
   who is a criminal

The interpreter converts them to the following predicate calculus
expressions.  This is the contents of the file ``crime.kb``::

   (forall x7
     (if (and (American x7)
              (exists x1
                (and (weapon x1)
                     (exists x3
                       (and (and (hostile x3) (country x3))
                            (sell x7 x1 x3))))))
         (criminal x7)))</p>

   (forall x11
     (if (and (missile x11) (own Nono x11))
         (sell West x11 Nono)))</p>

   (forall x14
     (if (enemy x14 America)
         (and (hostile x14) (country x14))))</p>

   (forall x16 (if (missile x16) (weapon x16)))</p>

   (exists x17 (and (missile x17) (own Nono x17)))</p>

   (American West)</p>

   (enemy Nono America)

The corresponding CNF clauses are shown when we call the solver::

   >>> from logic import solve
   >>> solve('(wh x (criminal x))', 'crime.kb', trace=True)</p>
   <BLANKLINE>
   KB
   1. -(American _1) -(weapon _2) -(hostile _3) -(country _3)
      -(sell _1 _2 _3) +(criminal _1)
   2. -(missile _4) -(own Nono _4) +(sell West _4 Nono)
   3. -(enemy _5 America) +(hostile _5)
   4. -(enemy _5 America) +(country _5)
   5. -(missile _6) +(weapon _6)
   6. +(missile _Sk1)
   7. +(own Nono _Sk1)
   8. +(American West)
   9. +(enemy Nono America)</p>
   <BLANKLINE>
   USABLE</p>
   <BLANKLINE>
   SOS
   10. [0] -(criminal _8) ; +(_Ans _8)</p>
   <BLANKLINE>
   Resolve 10.1 + 1.6
   12. [8] -(American _9) -(weapon _10) -(hostile _11) -(country _11)
           -(sell _9 _10 _11) ; +(_Ans _9)</p>
   <BLANKLINE>
   Resolve 12.1 + 8.1
   14. [6] -(weapon _12) -(hostile _13) -(country _13)
           -(sell West _12 _13) ; +(_Ans West)</p>
   <BLANKLINE>
   Resolve 14.1 + 5.2
   16. [6] -(missile _14) -(hostile _15) -(country _15)
           -(sell West _14 _15) ; +(_Ans West) </p>
   <BLANKLINE>
   Resolve 16.1 + 6.1
   18. [4] -(hostile _16) -(country _16) -(sell West _Sk1 _16)
           ; +(_Ans West)</p>
   <BLANKLINE>
   Resolve 18.1 + 3.2
   20. [4] -(enemy _17 America) -(country _17) -(sell West _Sk1 _17)
           ; +(_Ans West)</p>
   <BLANKLINE>
   Resolve 20.1 + 9.1
   22. [2] -(country Nono) -(sell West _Sk1 Nono) ; +(_Ans West) </p>
   <BLANKLINE>
   Resolve 22.1 + 4.2
   24. [2] -(enemy Nono America) -(sell West _Sk1 Nono) ; +(_Ans West)</p>
   <BLANKLINE>
   Resolve 24.1 + 9.1
   26. [1] -(sell West _Sk1 Nono) ; +(_Ans West)</p>
   <BLANKLINE>
   Resolve 26.1 + 2.3
   28. [2] -(missile _Sk1) -(own Nono _Sk1) ; +(_Ans West)</p>
   <BLANKLINE>
   Resolve 28.1 + 6.1
   30. [1] -(own Nono _Sk1) ; +(_Ans West)</p>
   <BLANKLINE>
   Resolve 30.1 + 7.1
   32. [0] ; +(_Ans West)</p>
   <BLANKLINE>
   Resolve 32.
   ANSWER 32.  ; +(_Ans West)

In outline, then, the prover goes through the following steps.

 * Clausification.  Convert the predicate calculus expressions to KB clauses.
 * Convert the question to a clause to be *disproved.*
 * The question becomes the first **active** clause ("SOS" = "set
   of support").  The KB clauses are the initial **usable** clauses.
 * Resolve the smallest active clause *C* against a usable clause,
   where possible, yielding new clause *D*.  (We still need to discuss
   unification.)
 * Move *C* to the usable list.  Add new clause *D* to the active list.
 * Keep going until you reach a contradiction.

Knowledge Base
--------------

The input to the prover is a knowledge base.

.. class:: KB

   The class ``KB`` represents a knowledge base, consisting of a list
   of clauses.  It may be loaded from a file:
   
   >>> from selkie.logic import KB
   >>> kb = KB(ex('curiosity.kb'))
   >>> print(kb)
   6. +(animal (_Sk5 _7)) +(love (_Sk6 _7) _7)
   7. -(love _7 (_Sk5 _7)) +(love (_Sk6 _7) _7)
   8. -(animal _11) -(kill _10 _11) -(love _12 _10)
   9. -(animal _13) +(love Jack _13)
   10. +(kill Jack Tuna) +(kill Curiosity Tuna)
   11. +(cat Tuna)
   12. -(cat _14) +(animal _14)

Unification
-----------

Two literals are **unifiable** if they can be made identical by some
choice of assignment of values to variables.  The relevant choice of
values for variables is called the **unifier**.  Let us start with
some examples::

   (a) (knows john  x  )  x = jane  OK
       (knows john jane)
   
   (b) (knows john  x  )  x = bill  OK
       (knows  y   bill)  y = john
   
   (c) (knows john      x    )  x = (mother y)  OK
       (knows y    (mother y))  y = john

.. py:function:: unify(expr1, expr2, substs)

   Unify *expr1* and *expr2*, storing the unifier in *substs*, which
   should be an empty, freshly-created dict.

We confirm that the implementation behaves as intended:

>>> from selkie.logic import unify
>>> def test (e1, e2):
...     d = {}
...     try:
...         unify(parse_expr(e1), parse_expr(e2), d)
...         for key in sorted(d):
...             print(key, '->', d[key])
...     except:
...         print('Failure')
>>> test('(knows john x)', '(knows john jane)')
x -> jane
>>> test('(knows john x)', '(knows y bill)')
x -> bill
y -> john
>>> test('(knows john x)', '(knows y (mother y))')
x -> (mother y)
y -> john

There is one subtlety that arises.  It should be possible to
substitute the unifier for the variables that it binds, and leave no
occurrences of those variables.  The way this can fail to be true is
if there is a cyclic dependency among variables.  For example::

   (d) (knows      x     (mother x))  x = (mother y)  FAIL
       (knows (mother y)      y    )  y = (mother x)

In this case, substitution essentially never terminates; or saying it
another way, substituting the unifier would create infinite literals.
Unification should fail in this case.  To recognize these examples, we
must check whether there a variable-value chain leading
from any variable *x* back to *x* again.
That is known as the **occurs check.**

>>> test('(knows x (mother x))', '(knows y (mother y))')
Failure

Standardizing apart
-------------------

Unification constitutes the central step of resolution: we combine two
clauses if there is a pair of literals whose polarity is opposite but
whose contents are unifiable.  By setting values of variables, we
unification affects all literals in both clauses.  We copy all
remaining literals of both clauses to create a new clause, and then we
do ``revert()`` to undo all changes.

For safety, we also change all the variables to new variables, in the
newly created clause.  This is called **standardizing apart.**

The function ``standardize_apart()`` replaces all variables in a
clause with
new variables.  It optionally accepts a symbol table, in which the
values of bound variables are used when creating the new clause.

>>> from selkie.logic import standardize_apart
>>> print(standardize_apart(kb[2]))
13. -(animal _15) -(kill _16 _15) -(love _17 _16)

Let us consider an example.  We create clauses for "every human is
mortal" and "Socrates is human":

>>> from selkie.logic import parse_clause
>>> c1 = parse_clause('-(human x) +(mortal x)')
>>> c2 = parse_clause('+(human Socrates)')

Now we unify the expressions in the "mortal" literals.

>>> symtab = {}
>>> c1.literals[0].expr
(human x)
>>> c2.literals[0].expr
(human Socrates)
>>> unify(c1.literals[0].expr, c2.literals[0].expr, symtab)

The unifier is ``x = Socrates``:

>>> symtab
{x: 'Socrates'}

We copy clause 1, in the context of the unifier:

>>> c3 = standardize_apart(c1, symtab)
>>> print(c3)
16. -(human Socrates) +(mortal Socrates)

That is, we have deduced that Socrates is mortal if he is human.

Resolution
----------

.. py:function:: resolve(cl1, i, cl2, j)

   The function ``resolve`` implements resolution.

   >>> from selkie.logic import resolve
   >>> print(resolve(c1, 0, c2, 0))
   18. +(mortal Socrates) 14.1+15.1

   ``Resolve`` takes four arguments: *c1, i, c2, j,*
   and it resolves the *i*-th literal of *c1* with the *j*-th
   literal of *c2.*

.. py:function:: factor(cl)

   There is also a function ``factor``, which derives new clauses from
   a single input clause by identifying pairs of literals that can be
   unified.  For example, if everyone loves Harvey or else Mary loves
   everyone, we can conclude that Mary loves Harvey.
   
   >>> c = parse_clause('+(loves x Harvey) +(loves Mary y)')
   >>> from selkie.logic import factor
   >>> out = factor(c)
   >>> print(out[0])
   21. +(loves Mary Harvey) 19.1+19.2

The combination of resolution and factoring yields a inferentially
complete theorem prover.

Prover
------

.. class:: Prover(kb)

   The prover encapsulates a KB.  It also creates a resolver internally.
   
   >>> from selkie.logic import Prover
   >>> prover = Prover(ex('curiosity.kb'))
   
   The argument may either be a KB object or a filename that is passed to
   the ``KB()`` constructor.
   
   The prover behaves as a function
   that takes a query and answers it using the KB.
   
   >>> prover('(wh x (kill x Tuna))')
   ['Curiosity']
   
   The prover accepts two keyword arguments: ``trace`` and
   ``maxsteps``.  By default, ``maxsteps`` is 200.  The "curiosity"
   proof requires 19 steps, though the search for additional solutions
   continues beyond 200.
