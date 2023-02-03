
``selkie.expr`` — Predicate calculus
====================================

.. testsetup::

   from selkie.expr import restart_variables
   restart_variables()

The module ``selkie.expr``
contains the basic data structures for representing
predicate calculus expressions.  It is separate from
``selkie.interp`` (which contains the semantic interpreter),
because the grammar module requires ``parse_expr()``.

Variables and constants
-----------------------

.. py:class:: selkie.expr.Variable

   Expressions are composed of variables (``x``, ``y``) and constants
   (``forall``, ``if``, ``cat``).  We implement both as strings,
   but to distinguish them, we provide a subclass of ``str`` called
   ``Variable``, and define anything that is not an ``Expr`` or a
   ``Variable`` to be a constant.
   
   >>> from selkie.expr import Variable
   >>> e1 = 'x'
   >>> e2 = Variable('x')
   >>> e1
   'x'
   >>> e2
   x

.. py:function:: fresh_variable()

   One may create an "anonymous" variable by calling the function
   ``fresh_variable()``:
   
   >>> from selkie.expr import fresh_variable
   >>> fresh_variable()
   _1
   
   There is a global count of anonymous variables, and it is incremented
   each time an anonymous variable is created:
   
   >>> fresh_variable()
   _2


When we parse a predicate calculus expression, we require some convention for
distinguishing between constants and variables.  How do we
know that "x" should be converted to a ``Variable`` instance, but
"Fido" should be left as a string?  The Russell & Norvig text uses
the convention that variables are lowercase whereas names are
uppercase.  Prolog and other automated reasoners use the opposite
convention: variables are uppercase and names are lowercase.  The
convention I will adopt is that variables consist of a single letter,
such as "``x``" or "``P``," whereas names contain at least
two (or none).  To provide some
flexibility, a variable may optionally begin with underscore (which
does not count as a letter), and may optionally be suffixed with any
number of digits.  Hence the following are recognized as variables:
``_x``, ``x10``, ``_x10``; but not ``_Sk10`` (which
contains two letters).

.. py:function:: is_variable_symbol()

   The function ``is_variable_symbol()`` distinguishes constants from
   variables:
   
   >>> from selkie.expr import is_variable_symbol
   >>> is_variable_symbol('hi')
   False
   >>> is_variable_symbol('h1')
   True

   Note that anonymous variables have names like ``_1`` that
   are not recognized as variables by ``is_variable_symbol()``.  This is
   unproblematic: anonymous variables by definition never appear in
   string representations of expressions.


Predicate calculus expressions
------------------------------

Let us begin with a couple of examples of
predicate-calculus expressions.
We will represent them in Lisp format: Polish prefix
notation with obligatory grouping parentheses.
Operator symbols like "->" are replaced with names ("``if``")::

(forall x (if (cat x) (animal x)))
(exists y (and (cat y) (not (orange y))))
((lambda x (or (cat x) (dog x))) Max)

.. py:class:: selkie.expr.Expr

   In keeping with our philosophy of simplicity, we implement expressions
   as tuples.  An expression such as::
   
      (chases Fido (the cat))
   
   is implemented as::
   
      ('chases', 'Fido', ('the', 'cat'))
   
   For convenience of display, however, we use the same trick that we
   used for ``Category``: we define a class ``Expr`` that is a
   specialization of ``tuple``.
   
   >>> from selkie.expr import Expr
   >>> e = Expr(['chases', 'Fido', Expr(['the', 'cat'])])
   >>> e
   (chases Fido (the cat))
   
   The words (variables and constants) in an expression usually print out
   without quotes, as in the example just shown.  However, quotes are
   included if the word contains an embedded space.
   
   >>> Expr(['every', 'bird dog'])
   (every 'bird dog')

   .. py:method:: __str__()

      The ``__str__()`` method produces a pretty-printed
      form.  For example:
      
      >>> from selkie.expr import parse_expr
      >>> e = parse_expr('(if (forall x (loves x Fido)) (loves Fido Spot))')
      >>> print(e)
      (if (forall x
             (loves x Fido))
          (loves Fido Spot))

.. py:function:: parse_expr(s)

   The function ``parse_expr()`` that takes a string and
   converts it to an expression instance.  Here is an example:
   
   >>> parse_expr('(and (dog x) (friendly x))')
   (and (dog x) (friendly x))
   
   Expression parsing uses ``selkie.io.tokenize()`` for tokenization.  This
   means that the delimiters ``[]{}`` are treated as stand-alone
   tokens, and quoted strings are recognized as single tokens.
   
   >>> parse_expr('(x[y])')
   (x [ y ])
   >>> parse_expr('(hi"there")')
   (hi there)

.. py:function:: scan_expr(toks)

   The function ``parse_expr()`` dispatches to ``scan_expr()``,
   which scans a single expression from a token stream.
   
   >>> from selkie.io import tokenize
   >>> toks = tokenize('Fido (+ x y)')
   >>> from selkie.expr import scan_expr
   >>> scan_expr(toks)
   'Fido'
   >>> scan_expr(toks)
   (+ x y)

.. py:function:: load_exprs(fn)

   The function ``load_exprs()`` reads a file that contains
   expressions.
   
   >>> from selkie.data import ex
   >>> from selkie.expr import load_exprs
   >>> es = load_exprs(ex('cnf.expr'))
   >>> print(es[0])
   (forall x
      (if (forall y
             (if (animal y)
                 (loves x y)))
          (exists y
             (loves y x))))
