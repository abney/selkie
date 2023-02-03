
``selkie.gdev`` — Grammar development tool
==========================================

The usual way to run gdev is from the shell::

   $ python -m selkie.gdev

When it starts up, it prints out the usage message, followed by a
prompt (``>``).
The commands are as follows.

.. list-table::
   :widths: 1 6

   * - ``ls``
     - List the existing grammars.  It looks in the directories on
       its grammar path for files with suffix "``.g``."  The initial path
       includes the current directory, ``/cl/examples``, and ``/cl/data/eng``.
   * - ``r``
     - Reload the grammar and sentence files, and reparse.
   * - ``n``
     - Next: go forward one sentence.
   * - ``p``
     - Previous: go back one sentence.
   * - *number*
     - Go to the sentence with that number.
   * - *grammar*
     - Load the grammar.
   * - *expr*
     - Evaluate the given semantic expression in the model.
   * - *sent*
     - Parse and evaluate a temporary sentence.
   * - ``c``
     - Print the current sentence.  Discard the temporary sentence, if any.
   * - ``g``
     - Print the grammar.
   * - ``m``
     - Print the model.
   * - ``s``
     - Print the sentences.
   * - ``t``
     - Save the translations to ``NAME-trans.txt``
   * - ``h``
     - Print a help message.  Question mark or an empty command
       also cause the help message to be printed.
   * - ``trace``
     - Takes zero or more arguments, from the following list:
       ``on`` turns tracing on (the default), ``off`` turns tracing
       off, ``parse`` affects tracing of parse-tree construction,
       ``unif`` affects tracing of unifications, *number*
       specifies a particular rule to trace.  If both ``on`` and ``off``
       are specified, the one that comes later overrides the one that
       comes earlier.
   * - ``^D``
     - Quit.


.. py:class:: Dev

   When one calls ``seal.gdev`` from the shell, it instantiates the
   class ``Dev`` and calls its ``run()`` method.

   .. py:method:: run()
   
      Repeatedly reads a line from stdin and passes it to the
      ``com()`` method.

   .. py:method:: com(line)

      Execute a command line.

   Here is an example.  First we instantiate ``Dev``:
   
   >>> from selkie.gdev import Dev
   >>> d = Dev()
   
   Load grammar ``g9``, along with its example sentences:
   
   >>> d.com('g9')
   
   Show the sentences.  The numbers not in brackets indicate how many
   parses the grammar assigns to the sentence.
   
   >>> d.com('s')
   [0]   1  a cat barks
   [1]   0 *a dogs barks
   [2]   1  the cat chases the dog
   
   Show the parse tree(s) for the current sentence:
   
   >>> d.com('c')
   <BLANKLINE>
   [0]   a cat barks
   #Parses: 1
   Parse 0:
   0   (S
   1      (NP[sg,-]
   2         (Det[sg] a)
   3         (N[sg] cat))
   4      (VP[sg]
   5         (V[sg,i] barks)))

   When the command is the name of a grammar file, ``Dev`` expects two files to exist:
   ``NAME.g`` should contain a grammar, and
   ``NAME.sents`` should contain a list of sentences.
   Each line of the sentence file is considered to be a sentence, except
   that empty lines and lines beginning with ``#`` are ignored.
   Leading and trailing whitespace is ignored.  If the first
   non-whitespace character is ``*``, it indicates that the example is
   ungrammatical.  For example:
   
   >>> from selkie.data import ex
   >>> from selkie.io import contents
   >>> print(contents(ex('g9.sents')), end='')
    a cat barks
   *a dogs barks
    the cat chases the dog
   
   ``Dev`` creates a parser from the grammar file, and uses it to parse
   each of the sentences in the sentence file.  The predicted label is
   ``'OK'`` if the parser deems the sentence to be grammatical, and
   ``'*'`` if the parser rejects it.  The predicted labels are compared
   to the true labels, and the results are printed out.
