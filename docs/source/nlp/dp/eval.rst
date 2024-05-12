
Evaluation — ``selkie.nlp.dp.eval``
***********************************

The following functions are in the module selkie.nlp.dp.eval::

   >>> from selkie.dp.eval import *
   >>> from selkie import ex
   >>> from selkie.dep import conll_sents

evaluate
--------

This is the main function.  It takes a parser, a list of sentences
with gold pgovrs and proles, and prints out evaluation information.
The parser should place its output in the govr and role slots, not
pgovr and prole.  One may specify ``excludepunc=False`` to count
punctuation tokens.  (They are ignored by default.)  One may provide
``output=`` *stream* to specify
an output stream other than stdout::

   >>> evaluate(parser, sents)

ispunc
------

The function ispunc() returns True if all the characters
in the given string have a Unicode category beginning with "P"::

   >>> ispunc('.')
   True
   >>> ispunc('Dr.')
   False

eval_sent
---------

The function eval_sent() evaluates a single sentence.  Its
arguments are *pred* and *truth*.  It considers the govrs
and roles of the predicted sentence, but the pgovrs and proles of the
true sentence.  (A projective dependency parser can produce
non-projective output if it ever fails to attach a word, so the output
of even a projective dependency parser is stored in the govr/role
slots rather than the pgovr/prole slots.)

The outputs are *las*, *uas*, *la*, *n*, where *las* is the
number of words that have the correct govr and role, *uas* is
the number of words that have the correct govr, *la* is the
number of words that have the correct role, and *n* is the
number of words.  Nota bene: these are counts, not proportions.
Note also that *n* will be less than the length of the
sentence.  The length of the sentence includes the root token
(position 0), which is never included in *n*.
Also, by default, punctuation tokens are ignored.
(One can cause them to be counted by specifying ``excludepunc=False``::

   >>> pred = next(conll_sents(ex.depsent3_pred))
   >>> gold = next(conll_sents(ex.depsent3_gold))
   >>> eval_sent(pred, gold)
   (2, 3, 2, 4)
   >>> eval_sent(pred, gold, excludepunc=False)
   (3, 4, 3, 5)

compare
-------

The function compare() prints out a detailed comparison of a
predicted and a gold sentence::

   >>> compare(pred, gold)
   1   This G R 2 subj 2 subj   
   2   is   G R 0 mv   0 mv     
   3   a        2 pt   4 det    
   4   test G   2 obj  2 prednom
   5 * .        2 obj  2 prednom
   
   LAS: 2 4 0.5 
   UAS: 3 4 0.75
   LA:  2 4 0.5

Punctuation tokens are marked with '\*' in the second column.
Tokens marked 'G' contribute to the UAS score, tokens marked
'R' contribute to the LA score, and tokens marked
'G R' contribute to the LAS score.
