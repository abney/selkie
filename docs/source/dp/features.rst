
Features — selkie.nlp.dp.features
*********************************

Compile
-------

The main function is compile(), which takes a set of feature
specifications (a string) and produces a function that maps
configurations to instances::

   >>> from seal import ex
   >>> from seal.dep import conll_sents
   >>> from seal.data import dep
   >>> from seal.dp.parser import computation, supervised_oracle
   
   >>> s = next(conll_sents(ex.depsent1))
   >>> comp = computation(s, supervised_oracle)
   
   >>> from seal.dp.features import *
   >>> cfgs = [cfg for (cfg,_,_) in comp]
   >>> f = compile('fpos stack 0, fpos input 0')
   >>> f(cfgs[0])
   [('fpos.input.0', 'pron')]
   >>> f(cfgs[1])
   [('fpos.stack.0', 'pron'), ('fpos.input.0', 'vb')]

By default, features with a null value are suppressed.  One can change
this behavior by passing ``nulls=True`` to compile()::

   >>> f = compile('fpos stack 0, fpos input 0', nulls=True)
   >>> f(cfgs[0])
   [('fpos.stack.0', 'null'), ('fpos.input.0', 'pron')]

Format
------

Feature specifications are built up from accessor functions such as
'fpos' and 'stack'.  The simplest specifications are of the
form 'stack 0' or 'input 2', in which the argument is a
number.  Only the functions 'stack' and 'input' may be used in
this way.  All other functions take a subexpression as argument.
The available functions are:
form,
lemma,
cpos,
fpos,
morph,
govr,
role,
lc,
rc,
ls,
rs.
Multiple feature specifications may be separated either by comma or
newline.

Load
----

One can alternatively load feature specifications from a file.

The function load() simply calls compile() on the contents
of the file.  The function compile() first splits the input text
into feature specs.  Feature specs may be separated either by commas
or newlines::

   >>> from seal.dp.features import specs
   >>> sps = specs('form input 0, fpos input 0, role lc input 0')
   >>> sps
   ['form input 0', 'fpos input 0', 'role lc input 0']

The specs are then used to create a FunctionList object, which
in turn uses _compile1() to turn each spec into a
function.

The function _compile1() takes a spec consisting of a
sequence of words, like ['role', 'lc', 'input', '0'].  The first
word is the *operator*.  The operators 'stack' and 'input'
are nonrecursive; they take the next word (which must be the last
word) as argument.  For example::

   _compile1(['input', '0'])

converts the '0' to an int and returns the function::

   lambda cfg: cfg.input(0)

The other operators are recursive.  For example, if the first word is 'lc', the
remainder of the spec is passed to _compile1() to
obtain a function *f*, and the return value is::

   lambda cfg: cfg.lc(f(cfg))

The result is always a function that takes a configuration as input
and returns a string or None.
