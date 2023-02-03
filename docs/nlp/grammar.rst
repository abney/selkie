
``selkie.grammar`` — Constituent grammars
=========================================

Lexicon
-------

.. py:class:: selkie.grammar.Lexicon.Entry

   A lexical entry.  It consists of a word,
   a part of speech, and an optional semantic translation.
   
   >>> from selkie.features import C
   >>> from selkie.grammar import Lexicon
   >>> ent = Lexicon.Entry('dog', C('n'), 'DOG')
   >>> ent.word
   'dog'
   >>> ent.pos
   n
   >>> ent.sem
   'DOG'

.. py:class:: selkie.grammar.Lexicon

   A Lexicon consists of a set of lexical entries.

   .. py:method:: define(word, pos, [sem])

      The basic method.  It takes a
      word, a part of speech (category), and an optional semantic value.
      
      >>> lex = Lexicon()
      >>> lex.define('cat', C(['n','sg']))
      >>> print(lex)
      cat n[sg]
   
   .. py:method:: __getitem__(word)

      The lexicon can be accessed by word.  The value is a list of entries.
      
      >>> lex['cat']
      [<Entry cat n[sg]>]
      
      An error is signalled if the word is not present.
   
   .. py:method:: __len__()

      The length of the lexicon is the number of entries.
      
      >>> len(lex)
      1
   
   .. py:method:: __iter__()
   
      For purposes of iteration, the elements of a lexicon are entries.
      
      >>> list(lex)
      [<Entry cat n[sg]>]


Grammar
-------

.. py:class:: selkie.grammar.Rule(lhs, rhs, sem, symtab)

   Grammar rules are represented by instances of the class Rule.  A
   Rule has five attributes: ``lhs``, ``rhs``, ``bindings``,
   ``variables``, and ``sem``.  The ``lhs``
   is a single category, and the ``rhs`` is a list of categories.  The
   value for ``bindings`` is a list containing ``*``'s, one for each
   variable used in the rule.  The value for ``variables`` is a list of
   string representations for the variables, or ``None``.
   The value for ``sem`` is an expression.
   
   The constructor takes a lhs, rhs, sem, and a symbol table.  The symbol
   table is a dict that maps variable names to integers from 0 to the
   size of the table.  The symbol table is optional; if omitted,
   variables are anonymous.  The length of the bindings list is the size
   of the symbol table, if provided.  Otherwise, it is one greater than
   the largest numeric variable occurring in either the lhs or rhs.
   
   >>> from selkie.grammar import Rule
   >>> r = Rule('vp', ['v', 'np'], 'foo')
   >>> r.lhs
   'vp'
   >>> r.rhs
   ['v', 'np']
   >>> r.bindings
   []
   >>> r.sem
   'foo'

.. py:class:: selkie.grammar.Grammar

   The Grammar class has a similar structure to the Lexicon class.
   Internally, it maintains two indices.  A rule of form *X ->
   Y1 ... Yn* is indexed by *X* in the lefthand side index, and it
   is indexed by *Y1* in the righthand side index.
   
   .. py:method:: define(lhs, rhs, [sem, symtab])

      The basic method.  It takes a lhs, rhs, an optional
      semantic translation, and an optional symbol table.
      
      >>> from selkie.grammar import Grammar
      >>> g = Grammar()
      >>> g.define(C('s'), [C('np'), C('vp')])
      >>> g.define(C('vp'), [C('v'), C('np')])
      >>> print(g)
      Start: s
      <BLANKLINE>      
      Rules:
          [0] s -> np vp
          [1] vp -> v np
   
   .. py:attribute:: start
   
      The attribute ``start`` contains the start category.  It defaults to
      the lhs of the first rule defined.
      
      >>> g.start
      s
   
   .. py:method:: expansions(cat)
   
      Takes a string *X*
      and returns the list of rules of form *X -> Y1 ... Yn*.
      Note that the input is just a string, not a full category.
      
      >>> g.expansions('vp')
      [<vp -> v np>]
   
   .. py:method:: continuations(cat)

      Returns the list of rules whose righthand
      side begins with a given symbol.  For example:
      
      >>> g.continuations('v')
      [<vp -> v np>]
   
   .. py:attribute:: declarations
   
      The value of ``declarations`` is generally ``None``, unless the
      grammar is created by the grammar loader
      from a file that
      contains declarations.

   .. py:attribute:: lexicon

      The lexicon.


.. py:class:: GrammarLoader(fn)

   The ``GrammarLoader`` reads a grammar file.  Here is a simple
   example of the format.  This is the contents of ``ex('g9.g')``.
   In the section headers (e.g., "``% Features``"), the space
   following the percent sign is optional, and the capitalization of
   the section name does not matter::
   
      % Features
      nform = sg/pl
      vform = nform/ing
      trans = i/t
      bool = +/- default -
      % Categories
      S   []
      NP  [form:nform, wh:bool]
      VP  [form:vform]
      V   [form:vform, trans:trans]
      N   [form:nform]
      Det [form:nform]
      % Rules
      S -> NP[_f] VP[_f]
      NP[_f] -> Det[_f] N[_f]
      VP[_f] -> V[_f,i]
      VP[_f] -> V[_f,t] NP
      % Lexicon
      the Det
      a Det[sg]
      cat N[sg]
      dog N[sg]
      dogs N[pl]
      barks V[sg,i]
      chases V[sg,t]
   
   The grammar loader is called by the ``Grammar`` constructor when a
   filename is provided.  For example:
   
   >>> from seal.core.io import ex
   >>> g = Grammar(ex.g9)
   >>> print(g)
   Start: S
   <BLANKLINE>
   Rules:
       [0] S -> NP[_f,-] VP[_f]
       [1] NP[_f,-] -> Det[_f] N[_f]
       [2] VP[_f] -> V[_f,i]
       [3] VP[_f] -> V[_f,t] NP[pl/sg,-]
   <BLANKLINE>
   Lexicon:
       a Det[sg]
       barks V[sg,i]
       cat N[sg]
       chases V[sg,t]
       dog N[sg]
       dogs N[pl]
       the Det[pl/sg]
