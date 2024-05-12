
GLab — ``selkie.nlp.glab``
==========================

About GLab
----------

GLab is a language for talking about languages.
The seal.glab module
provides an interpreter, which may be called interactively::

   $ glab
   [glab]

Or it may be called on a file::

   $ glab -g test.gn
   | a
   a

A notebook-based web application is also provided with CLD.
It displays **notebooks** consisting of
alternating user-provided **expressions** of the GLab language
("inputs"), and the results of evaluating those expressions ("outputs").
The inputs are editable text blocks.  The outputs are not editable,
but are automatically updated whenever an input is editted.

Tutorial
--------

Start the interactive GLab interpreter simply by
typing ``glab``.

Variables and symbols
.....................

An atom represents a symbol.  It evaluates to itself::

   [glab] a
   a

Variables begin with underscore.  The operator ``:=`` is used to
set the value of a variable::

   [glab] _x := hi
   [glab] _x
   hi

Note that *operator* is a specialization of *symbol,* so any
"stray" operators that are not part
of a well-formed operator expression are treated as symbol literals::

   [glab] *
   <Op *>

Note that ``=`` is used for equality testing only, not assignment::

   [glab] _x = lo
   False
   [glab] _x
   hi

Sequences, strings, sets
........................

A sequence literal is marked with angle brackets.  The elements may be
separated by commas, though commas may be omitted if no ambiguity results.
(Commas are generally optional wherever they occur.)
Sequences evaluate to themselves::

   [glab] <hi, there>
   <hi, there>
   [glab] <hi there>
   <hi, there>

A double-quoted string
is interpreted as a sequence of symbols separated by whitespace.
A single-quoted string is interpreted as a sequence of characters::

   [glab] "hi there"
   <hi, there>
   [glab] 'hi'
   <h, i>

Braces introduce set literals::

   [glab] {a,b,c}
   {a, b, c}

Operator expressions
....................

Dot is used for concatenation::

   [glab] <a,b> . <c,d>
   <a, b, c, d>

The operator ``@`` is used for set membership::

   [glab] _S := {a,b,c,d,e}
   [glab] a @ _S
   True

Plus is used for set union::

   [glab] _S := {a,b,c}
   [glab] _S + {b,c,d}
   {a, b, c, d}

Expressions
...........

Examples::

   [glab] _s := {a,b,c}
   [glab] |_s|
   3
   [glab] |"dog"|
   1
   [glab] |'dog'|
   3
   [glab] _A = {'a', 'b c', 'c a'}
   [glab] {_x in _A where |_x| = 2}
   [glab] (_A x _B)
   [glab] (_A . _e_)
   [glab] _B := /a + e + i + o + u/
   [glab] _C := {a, e, i, o, u}
   [glab] _B = _C
   [glab] /g . o:e . o:e . s . e/
   [glab] {{0}}

Finite-state automata
.....................

The function ``new_fsa()`` creates an FSA and makes it current::

   [glab] _a1 := new_fsa()

The function ``E()`` adds an edge to the current FSA::

   [glab] E(1 the 2)
   [glab] E(2 big 3)
   [glab] E(2 red 3)
   [glab] E(3 cat 4)
   [glab] E(3 dog 4)

The function ``F()`` declares a state final::

   [glab] F(4)

One may call an FSA as a function to determine whether it accepts a
string::

   [glab] _a1
   (An FSA containing 4 states)
   [glab] _a1("the big cat")
   True

The function ``computation()`` prints out the computation.
[Currently buggy]::

   [glab] computation(_a1, "the big cat")

Debugging
.........

Debugging functions::

   [glab] trace(syntax)
   [glab] untrace(syntax)


Tutorial 2
----------

One uses GLab by creating **notebooks.**  A notebook consists of
**boxes** into which you type expressions to be evaluated.  The
result of evaluating the expression is shown immediately following it.
One can edit the contents of boxes, and all results will be
recomputed.  (The consequences of the edit will propagate throughout
the entire notebook, as necessary.)

The syntax follows the notation that we have used on the handouts as
closely as possible, though substitutions obviously must be made for
special characters.  The following provide a few examples.

Basics
......

Symbols evaluate to themselves::

   > a
   a

Sequences are enclosed in angle brackets, and sets in braces::

   > <c, o, o, l>
   <c, o, o, l>
   > {c, o, o, l}
   {c, l, o}

Note that the elements of sets are listed in alphabetic order.
Vertical bars represent size::

   > |<c, o, o, l>|
   4
   > |{c, o, o, l}|
   3

Since neither italics nor underlining are available, we distinguish
variables by starting them with underscore.  Here is how to set the value of a
variable::

   > _x := <d, o, g>

In this case, nothing is printed, but we can see the effects by typing
the variable as an expression.  A variable evaluates to its value::

   > _x
   <d, o, g>

If we type a variable whose value has not been set, we get an error::

   > _y
   ERROR: Unbound variable: _y

The assignment operator := can be read as "make equal to," and
should not be confused with the equality operator =, which tests
whether two things are equal.

   > _x = <c, a, t>
   False
   > _x
   <d, o, g>
   > {c, o, o, l} = {l, o, c, o}
   True

String and set operations
.........................

The period is used for concatenation.  It can be used with
strings or languages::

   > <c, a, t> . <f, i, s, h>
   <c, a, t, f, i, s, h>
   > {<p>, <t>} . {<a>, <i>}
   {<p, a>, <p, i>, <t, a>, <t, i>}

Plus is used for set union::

   > {a, b, c} + {b, c, d}
   {a, b, c, d}

Ampersand is used for intersection::

   > {a, b, c} & {b, c, d}
   {b, c}

The "at" sign is used for set membership::

   > a @ {a, b, c}
   True

The special "variable" _e_ is used for
the empty string::

   > _e_
   <>
   > |_e_|
   0
   > <c, a, t> . _e_
   <c, a, t>

The special "variable" _0_ is used for the
empty set::

   > _0_
   {}
   > {a, b} + _0_
   {a, b}

I have put "variable" in scare quotes because these are actually
constants: GLab will not let you change their values.

Regular expressions
...................

Regular expressions are placed in slashes.
The basic regular-expression operators are '.' for
concatenation, '+' for union, and '\*' for Kleene star.
Parentheses may be used for grouping.

   > /(a+b).c/
   /(a+b).c/

Regular expressions display as
themselves, but they also represent languages::

   > _L := /(a+b).c/
   > <a, c> @ _L
   True
   > <a, b> @ _L
   False

The function *lang* enumerates the sentences of the
language::

   > lang(_L)
   [0] <b, c>
   [1] <a, c>

Variables may be used in regular expressions, provided that their
values have already been set::

   > _L2 := /_L . _L*/
   > lang(_L2, 3)
   [0] <b, c>
   [1] <b, c, b, c>
   [2] <b, c, b, c, b, c>
   ...

Notice that lang can be given a second argument, indicating how
many sentences to show.  (By default, it shows at most ten.)

Finite-state automata
.....................

One can also build up a finite-state automaton, by listing its edges.
First, one creates the automaton::

   > _A := new_fsa()
   > _A
   (An FSA containing 0 states)

Then one adds edges using the function E::

   > E(1, a, 2)
   > E(2, b, 2)

This creates an edge from state 1 to state 2 labeled "a" and
an edge from state 2 looping back to itself labeled "b."
The first state mentioned (here, state 1) becomes the start state.  To
mark final states, use the function F::

   > F(2)

To examine the automaton, use the function show::

   > show(_A)
   FSA:
     -> 1 a 2 (F)
        2 b 2 (F)

A listing of edges is given.  The start state is marked "->"
and final states are marked "(F)."

One can use the function L to get the language of an FSA::

   > <a, b> @ L(_A)
   True

Also, the function lang works with FSAs::

   > lang(_A, 3)
   [0] {\lt}a{\gt}\\
   [1] {\lt}a, b{\gt}\\
   [2] {\lt}a, b, b{\gt}\\
   ...

Transducers
...........

The colon operator is used to create input-output pairs::

   > a:b
   (a:b)

It can be used in regular expressions to define regular relations::

   > _R := /a:a . a:b*/}

A relation can be used like a function::

   > _R(<a, a, a>)
   {<a, b, b>}

The output is a set of strings, because in some cases there will be
more than one legal output string for a given input string.

The colon operator binds most tightly.  One can, however, apply the colon to
complex expressions by using grouping parentheses::

   > _R2 := /(a\*.b):(c.d)\*/
   > _R2(<a, a, a, b, b>)
   {<c, d, c, d>}

One can also use colon pairs in an automaton to create a finite-state
transducer.  In this case, only pairs of symbols may be used.  The
following is a nondeterministic automaton that requires its input to
end in ab, and deletes the ab::

   > _T := new_fsa()
   > E(1, a:a, 1)
   > E(1, b:b, 1)
   > E(1, a:_e_, 2)
   > E(2, b:_e_, 3)
   > F(3)

The function rel shows the relation computed by the automaton::

   > rel(_T, 3)
   [0] ({\lt}a, b{\gt}:{\lt}{\gt})\\
   [1] ({\lt}b, a, b{\gt}:{\lt}b{\gt}\\
   [2] ({\lt}b, b, a, b{\gt}:{\lt}b, b{\gt}\\
   ...

The percent operator is used for transducer composition::

   > _T2 := _T % /(a:c + b:d)\*/
   > _T2(<a, a, b, a, b>)
   {<c, c, d>}

Another way of combining automata is to use variables within a regular
expression.  Variables whose values are automata may be used, in
addition to variables whose values are regular expressions::

   > _T3 := /_T . (_e_:c)/
   > _T3(<a, a, b>)
   {<a, c>}

Lax strings
...........

For convenience, GLab permits a certain lax notation for strings.
Strings contained in double quotes are interpreted as having
space-separated symbols, and strings contained in single quotes are
interpreted as having letters as symbols.

   > "the big dog"
   <the, big, dog>
   > 'dog'
   <d, o, g>

Example: morphology
...................

We now implement (part of) the morphology of Handout 11 as an extended example.
Let us begin by listing some transitive and intransitive verbs, broken
out into regular and irregular.

   > _vi_reg := /'bark' + 'jump'/
   > _vt_reg := /'chase' + 'like'/
   > _vi_irr := /'sleep' + 'dive'/
   > _vt_irr := /'catch' + 'see'/

To save some typing, we have used single-quoted strings instead of
e.g. "b.a.r.k."

A stem maps <V,i> or <V,t> to the spelling.
We define separate regular and irregular stems, then take their union::

   > _VStem_reg := /V:_e_ . (i:_vi_reg + t:_vt_reg)/
   > _VStem_irr := /V:_e_ . (i:_vi_irr + t:_vt_irr)/
   > _VStem := /_VStem_reg + _VStem_irr/
   > rel(_VStem)
   {}[0] (<V, t>:<s, e, e>)
   {}[1] (<V, t>:<c, h, a, s, e>)
   ...
   {}[7] (<V, i>:<j, u, m, p>)

To keep things small(ish), we will only do the base form and past tense.
The base form consists of just the stem::

   > _V_base := /_VStem .\ base:_e_/
   > rel(_V_base)
   [0] (<V, t, base>:<s, e, e>)
   [1] (<V, t, base>:<c, h, a, s, e>)
   ...
   [7] (<V, i, base>:<j, u, m, p>)

The regular past tense consists of stem plus *ed.*  The *e*
will disappear in some cases, so we will use a capital *E*::

   > _V_past_reg := /_VStem_reg .\ past:(E.d)/
   > rel(_V_past_reg)
   [0] (<V, t, past>:<c, h, a, s, e, E, d>)
   [1] (<V, t, past>:<l, i, k, e, E, d>)
   [2] (<V, i, past>:<b, a, r, k, E, d>)
   [3] (<V, i, past>:<j, u, m, p, E, d>)

For irregular past verbs, we first define the past-tense
transformation, then we compose it with the irregular stems::

   > _IrrPastTrf := /'catch':'caught' + 'see':'saw' + 'dive':'dove' + 'sleep':'slept'/
   > _V_past_irr := /(_VStem_irr \% _IrrPastTrf) . past:_e_/

We now define the "underlying" verb as the union of the forms::

   > _V0 := /_V_base + _V_past_reg + _V_past_irr/

The last piece we need is the transformation that deletes E
after e, and rewrites it to e otherwise.  This is most
easily specified by defining a transducer::

   > _orth := new_fsa()
   > E(1, e, 2)
   > E(1, E:e, 2)
   > E(1, _else_, 1)
   > E(2, E:_e_, 2)
   > E(2, e, 2)
   > E(2, _else_, 1)
   > F(1)
   > F(2)

Finally, we compose _V0 with _orth::

   > _V := _V0 \% _orth
   > rel(_V, 20)
   [0] (<V, i, past>:<j, u, m, p, e, d>)
   [1] (<V, i, past>:<b, a, r, k, e, d>)
   [2] (<V, t, past>:<l, i, k, e, d>)
   [3] (<V, t, past>:<c, h, a, s, e, d>)
   [4] (<V, i, base>:<s, l, e, e, p>)
   ...
   [14] (<V, t, past>:<c, a, u, g, h, t>)
   [15] (<V, t, past>:<s, a, w>)

Grammar
.......

Entering a rule::

   > S -> NP[_n] VP[_n]

The grammar actually distinguishes between grammatical rewrite rules
and lexical entries.  Entering lexical entries::

   > Fido <- NP[sg]
   > barks <- VP[sg]

Parsing
.......

Once a grammar is defined, one can parse sentences.  Remember the
difference between 'foo' (letters are symbols) and
"foo bar" (words are symbols)::

   > parse("Fido barks")
   0  (S
   1    (NP[sg] Fido)
   2    (VP[sg] barks))

What happens if there's no parse?  The grammar should not permit
"Fido bark" (why not?).  Though we do need to add the word "bark" first::

   > bark <- VP[pl]
   > parse("Fido bark")
   No Parse

   Best Fragments:
   NP[sg] Fido
   VP[pl] bark

   All Nodes:
   NP[sg] Fido
   VP[pl] bark

The parser tries to be helpful: if you *expected* the sentence
to parse, you'd like to know why it didn't, so the parser shows the
largest fragments that it was able to assemble.

Regression set
..............

In developing a grammar, it is good to have a **regression set**:
a set of examples marked as good or bad.  As you add rules to the
grammar, you want to make sure that you don't break things that were
working correctly before.  Breaking things can either meaning failing
to parse a sentence that is grammatical, or succeeding in parsing a
word-sequence that is ungrammatical::

   > good("Fido barks")
   > bad("Fido bark")
   > good("dogs bark")
   > bad("dogs barks")
   > results()
   :) good <Fido, barks>
   :)  bad <Fido, bark>
   \** good <dogs, bark>
   :)  bad <dogs, barks>

The mistake: "dogs" is missing.  Go back and insert it.

Debugging
.........

You can get information about what the parser is doing by turning on
tracing::

   > trace(parse)
   > parse("Fido barks")
   Add Node 0.NP[sg].1 Fido NP[sg]
   Add Edge (S -> 0.NP[sg].1 \* VP[X0] {sg})
   Add Node 1.VP[sg].2 barks VP[sg]
   Add Edge (S -> 0.NP[sg].1 1.VP[sg].2 \* {sg})
   Add Node 0.S.2 (S -> 0.NP[sg].1 1.VP[sg].2 \* {sg})
   
   0  (S
   1    (NP[sg] Fido)
   2    (VP[sg] barks))

An "edge" is a partially matched rule.  The \* shows how much
of the rule that has been matched.  "X0" represents a variable
as feature value; variables are numbered beginning with 0.
"{sg}" indicates the values for
variables.  In this rule there is only one variable, but rules may
contain multiple variables.

If you would like to see a listing of the grammar, there is a new_grammar
function that behaves rather like new_fsa.  Put it
at the beginning, before defining any rules::

   > _g := new_grammar()
   > S -> A A
   > a <- A
   > show(_g)
   Start: S
   
   Rules:
     [0] S -> A A
   
   Lexicon:
     a A

File inclusion
..............

As the grammar gets bigger, you may want to break it into multiple
notebooks to keep it more manageable.  You might put the grammar
proper in one notebook (say, notebook 1), and the lexicon in a second
notebook (say, notebook 2).  The contents of notebook 1 might look
like this::

   > S -> NP[_n] VP[_n]
   > NP[sg] -> Name
   > VP[_n] -> V[_n]

and the contents of notebook 2 might look like this::

   > Fido <- Name
   > barks <- V[sg]

The contents of the main notebook could then be::

   > include(1)
   > include(2)
   > parse("Fido barks")
   0  (S
   1    (NP[sg]
   2      (Name Fido))
   3    (VP[sg]
   4      (V[sg] barks)))

Note: the argument to include is the notebook *number,*
not the notebook title.  (The title may change, but the number never
changes.)  The notebook number is shown in square brackets preceding
the title, and is also shown in the second column in the notebook listing.

The GLab Language
-----------------

Syntax
......

An **atom** is one of the following:

 * An **operator**, as listed in the following table.  Example:
   ``+``.
 * A **variable**, which must begin with underscore.  Example: ``_a1``.
 * A **string** in single or double quotes.
   There is no significance to the choice between single quotes and double quotes, though the
   start and end quotes must of course match.  Example: ``'foo bar'``.
 * A **symbol** literal, which is any unquoted word that is not an
   operator or variable.  Example: ``a``.

The following table lists the operators, from highest (1) to lowest (5) precedence
classes.  Higher precedence operators "bind more tightly."  Operators
in the same precedence class group left to right.

.. list-table::

 * - 1
   - ``:``
   - Cross-product
 * - 2
   - ``*``
   - Kleene star (suffix operator)
 * - 3
   - ``.``
   - Concatenation
 * - 3
   - ``x``
   - Cross-product
 * - 4
   - ``+``
   - Addition
 * - 4
   - ``-``
   - Subtraction
 * - 4
   - ``\``
   - Set difference
 * - 5
   - ``=``
   - Equality
 * - 5
   - ``in``
   - Set membership

Note that there are two cross-product operators, differing only in
precedence.  That is intentional.  The colon operator is for letter
pairs in transductions, whereas the times operator forms the cross
product of longer strings.

Atoms are grouped into **expressions**.
The following are the expression types:

 1. **Infix expression.**  Two subexpressions with an infix operator between them,
    representing an operator expression with two operands.  Example:
    ``a.b``.
 2. **Postfix expression.**
    A subexpression followed by a postfix operator, representing an
    operator expression with one operand.  Example: ``a*``.
 3. **Size expression.**  A list of subexpressions in vertical bars.  Example: ``|{a,b}|``.
 4. **Function call.**  A symbol followed by a parenthesized list
    of subexpressions, separated optionally by commas.
    Example: ``f(_x, _y)``.
 5. **Category literal.**  A symbol followed by a bracketed list of subexpressions.
    Example: ``VP[sg]``.
 6. **Sequence literal.**  A list of subexpressions in angle brackets.
    Example: ``<c,a,t>``.
 7. **Set literal.**  A list of subexpressions in braces.
    Example: ``{a,b}``.
 8. **Language literal.**  A list of subexpressions in slashes.  Example: ``/a . b/``.

Semantically, expressions of types (1)-(4) represent functions
applied to arguments.  The remaining expression
types represent literal objects:
categories, sequences, sets, or languages.

A **command statement** consists of a **command** and some
number of argument expressions.

There are two types of
command statement:

 * **Prefix command statement.**  The first expression is a symbol representing a prefix
   command, as listed in the top half of the following table,
   and the remaining expressions in the line are its arguments.
 * **Infix command statement.**  The second expression is an infix command, as listed in the
   bottom half of the following table.  The first expression, along
   with the third and following expressions, represent arguments of the
   command.

Commands are designated symbols, as listed in the
following table.

+--------------------------------------------+
| **Prefix commands**                        |
+-------------+------------------------------+
| ``set``     | Set the value of a variable  |
+-------------+------------------------------+
| ``include`` | Include another notebook     |
+-------------+------------------------------+
| ``incr``    | Increment a variable         |
+-------------+------------------------------+
| ``show``    | Show the value of a variable |
+-------------+------------------------------+
| ``parse``   | Parse a sentence             |
+-------------+------------------------------+
| ``trace``   | Turn on tracing              |
+-------------+------------------------------+
| ``good``    | Mark a sentence as good      |
+-------------+------------------------------+
| ``bad``     | Mark a sentence as bad       |
+-------------+------------------------------+
| ``results`` | Show the results of parsing  |
+-------------+------------------------------+
| **Infix commands**                         |
+-------------+------------------------------+
| ``->``      | Define a grammar rule        |
+-------------+------------------------------+
| ``<-``      | Define a lexical entry       |
+-------------+------------------------------+
| ``=>``      | (I forget)                   |
+-------------+------------------------------+

At the highest level, a notebook consists of newline-terminated **lines.**
A line beginning with ``#`` is a **comment.**  The title of the
notebook must be the first line and begin with ``#T`` followed by a
space and the actual title.  Every other line is a **statement,**
which may be either a command statement or an expression.

List of constants
.................

The constants are:

 * ``_0_`` — the empty set
 * ``_e_`` — the empty string
 * ``_else_`` — used in FSTs
 * ``Top`` — the top of a lattice
 * ``Bottom`` — the bottom of a lattice

Global variables
................

The global variables are:

 * ``_fsa_`` - the current FSA/FST
 * ``_corpus_`` - the current corpus
 * ``*notebook-dir*`` - the current notebook directory
 * ``*output*`` - the current output stream
 * ``*trace*`` - a set of things to be traced

List of functions
.................

Functions have a minimum number of arguments, a maximum number of
arguments, and a flag indicating whether or not they take the symtab
as a hidden argument (ENV), in order to get the values of global
variables.  A few of the functions have types associated
with their parameters; that is not indicated in the table.
All functions are built-in, in the sense that
their implementation is provided by a Python function.

 * ``=>(*things)`` — Expand
 * ``apply(fsa,x,ENV)`` — Applies an FSA to an input
 * ``bad(s,ENV)`` — Marks a sentence as bad
 * ``abs(x)`` — Absolute value of number, or size of a container
 * ``accepts(fsa,seq)`` — Whether or not an FSA accepts a sequence
 * ``check(x,ENV)`` — Check something
 * ``compose(fst1,fst2,ENV)`` — Compose FSTs
 * ``computation(fsa,seq)`` — Show the computation of an FSA on a sequence
 * ``concat(*fsas)`` — Concatenate FSAs
 * ``cross(*fsts)`` — Take the cross product of FSTs.
 * ``E(src,dst,lab,[olab],ENV)`` — Add an edge to the current FSA.
 * ``equals(x,y)`` — Equality
 * ``ex(s,ENV)`` — Add a sentence to the list of examples.
 * ``exp(x,y)`` — Take x to the y
 * ``F(q,ENV)`` — Declare state q final, in the current FSA
 * ``first(x)`` — Return the first element
 * ``fsa(*edges)`` — Create an FSA.
 * ``good(s,ENV)`` — Declare a sentence to be good.
 * ``gt(x,y)`` — Greater than
 * ``include(s,ENV)`` — Include the notebook with the given name,
   searching in the current notebook directory. 
 * ``incr(x,amt)`` — Increment x by an amt
 * ``intersection(x,y)`` — Intersect two sets
 * ``io(x,y)`` — Not sure
 * ``islang(x)`` — Whether x is something that can be used as a language
 * ``ismember(x,y)`` — Whether x is a member of y
 * ``isstring(x)`` — Whether x is a string
 * ``L(x)`` — Convert x to a language
 * ``lang(x,ENV)`` — Print the language
 * ``lt(x,y)`` — Whether x is less than y
 * ``makecat(*ftrs)`` — Turn a set of features into a category
 * ``minus(x,y)`` — Subtraction
 * ``new_fsa(ENV)`` — Start a new FSA
 * ``new_grammar(ENV)`` — Start a new grammar
 * ``new_union(ENV)`` — Start a new union
 * ``pair(x,y)`` — Create a pair
 * ``parse(s,ENV)`` — Parse a sentence
 * ``plus(x,y)`` — Addition
 * ``rel(fst,[n],ENV)`` — List [at most *n* tuples from] the relation computed by an FST
 * ``results(ENV)`` — Run regression tests
 * ``seq(*elts)`` — Create a sequence
 * ``set(*elts)`` — Create a set
 * ``show(x,ENV)`` — Print details
 * ``size(x)`` — The size of a container
 * ``start(ENV)`` — Get the start symbol
 * ``trace(what,ENV)`` — Turn tracing on
 * ``type(x)`` — The type of x
 * ``untrace(what,ENV)`` — Turn tracing off

List of macros
..............

A genuine macro is a function that
suppresses evaluation of its arguments and constructs a new expression
that is evaluated in the place of the macro expression.  GLab does not
support genuine macros, but it does permit functions to suppress
evaluation of some or all of their arguments.

 * ``makelexent(w,pos,ENV)`` — Evaluates pos but not w.
 * ``makerule(*cats,ENV)`` — Cats are not evaluated.
 * ``new(type,ENV)`` — Type is not evaluated.  May set a global variable.
 * ``regex(x,ENV)`` — x is not evaluated.
 * ``quote(x)`` — Suppresses evaluation.
 * ``setvalue(var,val,ENV)`` — Neither argument is evaluated.

List of setters
...............

A "setter" is a function that can be placed on the left-hand side of
an assignment.  There is only one: ``start(fsa) = q`` expands into
Python as ``set_start(fsa,q)``.

GLab Implementation
-------------------

Command-line invocation
.......................

GLab will use the current working directory as its working directory.
If you create a notebook, it will be placed in a subdirectory whose
name is your user name.  The subdirectory will be automatically
created, if necessary.  To launch GLab::

   $ python -m seal.glab

To use it, visit ``http://localhost:8000/``.

WSGI web application
....................

To run GLab under a web server (e.g., Apache) as a WSGI application,
create a file ``glab.wsgi`` along the lines of the following::

   import site
   site.addsitedir('/home/me/mypython/lib/python2.6/site-packages')
   import seal.glab
   application = seal.glab.make_application('/home/me/myglabdir')

The WSGI script must have permissions 744.

This assumes that ``/home/me/mypython`` was created using
virtualenv::

   $ python virtualenv.py mypthon

and that Seal was installed in ``mypython``.

CGI web application
...................

To run GLab as a CGI script, create a file called e.g. ``glab`` in
the ``cgi-bin`` directory, with contents along the lines of the following::

   #!/home/me/mypython/bin/python
   import site
   site.addsitedir('/home/me/seal-0.11.x/python')
   import seal.glab
   application = seal.glab.make_application('/home/me/myglabdir')
   from wsgiref.handlers import CGIHandler
   CGIHandler().run(application)

The CGI script should have permissions 744.

Batch mode
..........

The first line of a ``.gl`` file is a notebook name prefixed with
``#T``, and each subsequent line is a glab statement.
For example, ``ex.notebook.gl`` contains::

   #T My Notebook
   set _x <a,b,c>
   _x . <b,a>

It is interpreted as follows::

   >>> from selkie.data import ex
   >>> from selkie.cld.glab.eval import interpret_file
   >>> interpret_file(ex('notebook.gl'), show_syntax=True)
   | #T My Notebook
   | _x := <a,b,c>
   : setvalue(_x, seq(a, b, c))
   | _x . <b,a>
   : concat(_x, seq(b, a))
   <a, b, c, b, a>

The original line of text is echoed with ``|`` as prompt, and
the parsed expression is echoed with ``:`` as prompt.  Then any
return value or error is printed.

By default, echo is on, meaning that each statement and value is
printed.  It also means that errors are printed instead of terminating
processing.  Echo can be turned off by providing
``echo=False``.  In that case, the only printing is what is
explicitly done with ``show`` statements, and any exceptions
immediately terminate processing.

Parsing
-------

Tokenization
............

The function ``tokenize()`` takes a string and returns an iteration
containing tokens.  
Tokenize assumes that its input represents a
single line of input.  If any newlines happen to be present, they are
treated like spaces.
The tokens in the iteration are instances
of ``Token``, which is a specialization
of ``str``.  
A Token has a member ``type`` giving its token type,
and members ``filename``, ``line``, and ``offset``,
indicating exactly where the token occurred.  String tokens also have
member ``quotes`` indicating the quote character::

   >>> for tok in tokenize('_a1 = foo("hi\\tbye")\n_a1+s'):
   ...     print('{:6} {}'.format(tok.type, repr(tok)))
   ...
   word   '_a1'
   =      '='
   word   'foo'
   (      '('
   string 'hi\\tbye'
   )      ')'
   word   '_a1'
   +      '+'
   word   's'

In detail, the kinds of token are as follows:

 * **Word.**  A maximal sequence of word characters
   (alphanumerics plus underscore).  The value
   for ``tok.type`` is ``'word'``.
 * **String.**  Surrounded by paired single quotes or
   double quotes.  The value for ``tok.type`` is ``'string'``,
   and the value for ``tok.quotes`` is either a single quote or a
   double quote character.
 * **Special.**  The type of a special token is the token itself.
   There are two cases:

    - **Multi-character special.**  One
      of: ``->``, ``<-``, ``=>``,
      ``:=``, ``@<``, ``@>``.
    - **Single-character special.**  Any single character that is not
      a word character or whitespace.

Whitespace is not returned as a token, but it
does separate words.  Backslash is never interpreted as an escape
character; it is treated like any other punctuation character.

Grouping
........

After tokenization, pairs of grouping characters are mated to create a
syntactic skeleton.  After grouping, the atoms are still tokens
(words, strings, or specials), but complex expressions belong to the
following classes, which are subclasses of ``tuple``:

 * ``BracketExpr`` — ``[...]`` (paired square brackets)
 * ``ParenExpr`` — ``(...)`` (paired parentheses)
 * ``BraceExpr`` — ``{...}`` (paired braces)
 * ``SeqExpr`` — ``<...>`` (paired angle brackets)
 * ``AbsExpr`` — ``|...|`` (paired vertical bars)
 * ``ToplevelExpr`` — wrapped around the expression as a whole

Example::

   >>> exp = group(tokenize('g.[f, {a,b}]'))
   >>> pprint(exp)
   ToplevelExpr {
       g
       .
       BracketExpr {
           f
           ,
           BraceExpr {
               a
               ,
               b
           }
       }
   }

Normalization
.............

The function ``normalize()`` takes the output of grouping and
converts it into a fully parsed expression.  It processes the skeletal
expression recursively, bottoming out with the tokens.

The auxiliary function ``normalize_token()`` handles the individual
tokens.  It replaces the atoms with atoms of the following types,
which are specializations of ``str``:

 * ``Var`` — a variable.  Created from ``word`` tokens that begin with
   underscore.

 * ``Symbol`` — a symbol.  Created from ``word`` tokens
   that do not begin with underscore.  Also, quoted strings are
   converted to sequences of symbols.

 * ``Op`` — an operator.  Created from specials.
   There is a table of operators that is used to do the conversion.  If
   the token is not in the table, a ``SyntaxError`` is signalled.

 * ``SeqExpr`` — Quoted strings are shorthands for angle-bracket
   expressions.  A double-quoted string is split at
   whitespace, and a single-quoted string is exploded into its
   characters.  The resulting list is converted to a
   ``SeqExpr`` containing ``Symbol`` instances.

A complex expression (produced by grouping) is normalized as follows.
First, each of the elements is normalized.
Then the function ``op_parse()``, which does
operator-precedence parsing, is called on the
normalized elements.  Finally, commas are deleted.  (They serve as
lowest-precedence separators, if present.)
Associated with each operator is a function name, and the combination
of the operator with its arguments is replaced by a ``Funcall``
expression:

 * ``Funcall`` — represents a function and its arguments

Function calls of the usual sort are also recognized and replaced with
``Funcall`` expressions.  The arguments may be surrounded either by
parentheses or by square brackets::

   >>> g = group(tokenize('''_x := {"a b".'!?'}'''))
   >>> pprint(g)
   ToplevelExpr {
       _x
       :=
       BraceExpr {
           a b
           .
           !?
       }
   }
   >>> n = normalize(g)
   >>> pprint(n)
   ToplevelExpr {
       Funcall {
           setvalue
           Var _x
           BraceExpr {
               Funcall {
                   concat
                   SeqExpr {
                       Symbol a
                       Symbol b
                   }
                   SeqExpr {
                       Funcall {
                           sym
                           33
                       }
                       Funcall {
                           sym
                           63
                       }
                   }
               }
           }
       }
   }

Here are a few points to note:

 * The double-quoted string ``"a b"`` is treated as
   consisting of whitespace-separated symbols, whereas the single-quote
   string ``'!?'`` is treated as consisting of
   single-character symbols.
 * The non-word symbols ``!`` and ``?``
   are replaced with calls to the function ``sym``.
 * The operators have been replaced with function names: for
   example, ``:=`` has been replaced
   with ``setvalue``.  A table of operators is given below,
   after we discuss operator-precedence parsing.

Operator-precedence parsing
...........................

Operator-precedence parsing does the real work of normalization.
The operator-precedence parser works as follows.
The input sequence consists of the contents of a single group
expression, and consists of tokens and subexpressions.  Each element
is assigned one or more categories, as follows:

 * A comma token has category ``,``.
 * An operator has two categories: ``O`` (operator) and the
   syntactic type of the operator, which is either ``I`` (infix) or
   ``S`` (suffix).
 * A ``Funcall`` created by reducing an infinite-arity infix
   operator has categories ``L`` (list) and ``A`` (argument).
 * A ``ParenExpr`` has category ``P`` (parenthesized expression).
 * A ``BracketExpr`` has category ``P``.
 * A ``Symbol`` has categories ``A`` (argument) and ``Y``
   (function symbol)
 * Everything else has category ``A`` (argument).

The parser passes through the element sequence, applying the following
rules.  The pattern is a sequence of categories, and the action is
taken if the first *n* words have the categories given.  To "reduce"
means to remove the indicated elements and replace them with a ``Funcall``
headed by the operator's equivalent function, destructively changing
the sequence of elements.

 * If ``AIAO``, then compare the precedence of the two operators
   (``I`` and ``O``).  If the second has higher precedence,
   temporarily shift two elements to the right.  Otherwise, reduce the
   first three elements.
 * If ``LAO``, do the same, but if a reduction is done, it
   consists in adding the A to the L's argument list.
 * If ``AIAP``, then temporarily shift two elements to the
   right.  (The ``AP`` may be a function call, and function call
   has highest precedence.  **[Shouldn't this be AIYP?]**
 * If ``LAP``, then temporarily shift one element to the
   right.
 * If ``AIA``, then reduce the first three elements and
   terminate the most recent shift, if any.
 * If ``LA``, then add the A to the L's argument list and
   terminate the most recent shift, if any.
 * If ``YP``, then reduce the first two elements and
   terminate the most recent shift, if any.
 * If ``AS``, then reduce the first two elements and
   terminate the most recent shift, if any.
 * If none of the above rules apply, then cancel any temporary
   shifts, advance one element to the right, and restart.

Digesting
.........

The function ``digest()`` simplifies the syntax by replacing all
expressions, including complex literals, with ``Funcall`` objects.
In particular, the expressions introduced by grouping that have not
been previously eliminated are eliminated now:

 * ``BracketExpr`` — Brackets that are not recognized as part of a
   function call are grouping brackets.  If there is only one sub-expression, it is
   returned.  Otherwise an error is signalled.
 * ``ParenExpr`` — Parentheses that are not recognized as part of a
   function call are grouping parentheses.  If there is only one sub-expression, it is
   returned.  Otherwise an error is signalled.
 * ``BraceExpr`` — The return is a ``Funcall`` whose function is
   ``set`` and whose arguments are the ``BraceExpr``.
 * ``SeqExpr`` — The return is a ``Funcall`` whose function is
   ``seq`` and whose arguments are the ``SeqExpr``.
 * ``AbsExpr`` — The return is a ``Funcall`` whose function is
   ``abs`` and whose arguments are the ``AbsExpr``.
 * ``ToplevelExpr`` — If there is only one sub-expression, it is
   returned.  Otherwise an error is signalled.

Example::

   >>> print(digest(n))
   setvalue(_x, set(concat(seq(a, b), seq(sym(33), sym(63)))))

In the final result, the expression tree consists only of the
following types: ``Funcall``, ``Var``, ``Symbol``, ``int``.

Parsing
.......

The function ``parse()`` performs the sequence of steps just
discussed: tokenization, grouping, normalization, and digesting::

   >>> expr = parse('_x := {&lt;a>.&lt;b>}')
   >>> print(expr)
   setvalue(_x, set(concat(seq(a), seq(b))))

List of Operators
.................

The following is the complete list of operators, along with their
precedence and the corresponding function
name.  Infinite arity is represented by ``...``.  The comma is
"inert" in the sense that it never actually combines with arguments;
it is only used as a separator.  Since commas
are deleted after operator-precedence parsing, there is also no
corresponding function.

.. list-table::
   :header-rows: 1

 * - Op
   - Prec
   - Function
 * - x ``:`` y
   - 7
   - ``pair``
 * - x ``^`` y
   - 6
   - ``exp``
 * - x ``*``
   - 5
   - ``star``
 * - x ``.`` y
   - 4
   - ``concat``
 * - a ``x`` b
   - 4
   - ``cross``
 * - x ``&`` y
   - 4
   - ``intersection``
 * - x ``+`` y
   - 3
   - ``plus``
 * - x ``-`` y
   - 3
   - ``minus``
 * - x ``\`` y
   - 3
   - ``setdiff``
 * - x ``%`` y
   - 3
   - ``compose``
 * - x ``=`` y
   - 2
   - ``equals``
 * - x ``@`` y
   - 2
   - ``ismember``
 * - x ``@<`` y
   - 2
   - ``lt``
 * - x ``@>`` y
   - 2
   - ``gt``
 * - x ``:=`` y
   - 1
   - ``setvalue``
 * - x ``->`` ...
   - 1
   - ``makerule``
 * - x ``<-`` ...
   - 1
   - ``makelexent``
 * - ``,``
   - 0
   -

Evaluation
----------

Overview
........

There are four interrelated functions: ``evaluate()``,
``apply()``, ``symeval()``, and ``setvalue()``.  All take an
``env`` argument, which is simply a dict mapping names to values.
Variables, constants, and function names are all included in ``env``.
They are easy to tell apart because variables begin with underscore,
constants are nonalphabetic, and function names are alphabetic.  The
user can only change the values of variables.

Of those four functions, the only one of any complexity is
``apply()``.  It takes a function name and an argument list.  It
goes through the following steps:

 * The function name is looked up in the environment to get the actual
   function ``f``.  An error is signalled if the name is not
   found, or if its value is not a function.  It is also permissible for
   the function "name" to be an actual ``Function``
   object, in which case no lookup is done.
 * Checks are done to make sure that the argument list
   includes at least ``f.min_narg`` arguments, but not more than ``f.max_narg``
   arguments.  (The latter may have the value ``Unlimited``.)
 * Each argument is evaluated, unless ``f.eval`` exists
   and has the value ``False`` for the argument position in question.
 * If ``f.types`` exists, the types of the arguments are checked.
 * If ``f.envarg`` is ``True``, the environment itself is
   added to the argument list as a new final argument.
 * ``f.implementation`` is called on the argument list, and the
   result is returned.

To get an environment populated with the standard functions, call ``Environment()``::

   >>> env = Environment()
   >>> expr = parse('_x := {<a>.<b>}')
   >>> print(evaluate(expr, env))
   None
   >>> env['_x']
   {<a, b>}

Interpreter
...........

**Evaluator.**
An ``Evaluator`` instance behaves like a function with an internal
environment.  It
can be used to evaluate a sequence of statements::

   >>> e = Evaluator()
   >>> e('_x := <a,b,c>')
   >>> e('_x')
   <a, b, c>

When initialized, it uses ``Environment()`` to create an environment,
and each time it is called it uses ``parse()`` to turn the string
into an expression and ``evaluate()`` to evaluate it in the environment.

**Interpreter.**
An ``Interpreter`` also evaluates statements.  Unlike an Evaluator,
it traps exceptions and captures the output of commands that do direct
printing, like ``show``.  It also echoes the input statements, and
if created with the setting ``show_syntax=True``, it
also echoes the parsed version of each input line (for debugging).
The return value is a string containing all output::

   >>> i = Interpreter(echo=True)
   >>> i('_x := <d,o,g>')
   '| _x := <d,o,g>\n'
   >>> i('_x')
   '| _x\n<d, o, g>\n'
   >>> i('_y')
   '| _y\nERROR: Unbound variable: _y\n'

It can either be called with a single string (as in the examples just
shown), or with an iteration over strings, such as an open file::

   >>> with open(ex.notebook.gl) as file:
   ...     print(i(file), end='')
   ...
   | #T My Notebook
   | _x := <a,b,c>
   | _x . <b,a>
   <a, b, c, b, a>

The Interpreter calls two lower-level functions:

interpret_file(file,output,env)
   *File* may be a filename or an iterator over strings (e.g., an open file).
   The strings are parsed as input lines and evaluated.  Processing
   continues even if an exception is encountered.  All output is
   trapped and returned at the end as a string.

parse_file(strs)
   This is used by ``interpret_file()`` to parse the
   input.  It takes an iterator over strings as input, and returns an
   iterator over triples, one for each input line.  If the input line is
   empty or a comment, the triple is (None, None, *line*).
   If there is an error during parsing, the triple is (None,
   *excep*, *line*).  Otherwise, the triple is (*expr*,
   None, *line*).

Customization
-------------

Adding an operator
..................

The operators are listed in ``_operators``.  The key is the
operator, and the value is a ``makeop`` expression.  The arguments
to ``makeop`` are: the operator string (identical to the key), the
precedence, the syntactic type (``I`` for infix or ``S`` for
suffix), and the name of the GLab function that the operator should be
replaced with.  A named GLab function is a ``Function`` object that
is the value of a key in the environment symtab; the key is the
function's name.

To add a multi-character operator, one must also add the operator to the list of
multi-character specials in the definition of ``_syntax``.

Adding a function
.................

Add an entry to the environment symtab whose value is a ``Function``
object.  The arguments to the ``Function`` constructor are as
follows:

 * ``imp`` — a Python function that implements the GLab function.
 * ``min_nargs`` — the minimum number of arguments
   that ``imp`` requires.
 * ``max_nargs`` — the maximum number of arguments
   that ``imp`` accepts.  ``None`` means that ``imp`` is declared
   ``*args``.
 * ``types`` — a list giving the required types for the first *n*
   arguments, where *n* is the length of ``types``.
 * ``eval`` — a list of booleans indicating which arguments should
   be evaluated.  If None (the default), all arguments are evaluated.
 * ``envarg`` — whether or not the Environment should be provided
   as a keyword argument.  The default is False.

One must also define a Python function to serve as the
implementation.  It will receive only positional arguments, with the
exception of the keyword argument ``env``, if ``envarg`` is True.
Note that Python permits one to declare a function that accepts a variable
number of positional arguments as well as an ``env`` keyword argument::

   def foo (*args, env=None): ...
