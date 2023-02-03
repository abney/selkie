
``selkie.tok`` — Tokenizer for Latin scripts
============================================

Usage
-----

.. py:function:: tokenized(s)

   The main function is ``tokenized()``, which takes a text (string) and returns a
   list of tokens.
   
   >>> from selkie.tok import tokenized
   >>> t = tokenized('"Hi, @#!"\nsaid  42-J.\n')
   >>> t[:4]
   [<word '"Hi,'>, <punct '@#!"'>, <word 'said'>, <number '42'>]

   The return value is a list of Token instances.

.. py:class:: selkie.tok.Token

   .. py:method:: type()

      The value is one of: ``'word'``, ``'number'``, ``'hyphen'``, or ``'punct'``.
      (Internally, the tokenizer also creates ``'space'`` and
      ``'newline'`` tokens, but they are not returned.  Newlines are
      implicit in the line numbers, and spaces can be reconstructed from the
      column numbers.)

   .. py:method:: string()

      The original characters.

   .. py:method:: line()

      The line number (from 1).

   .. py:method:: column()

      The column number (from 0).

   .. py:method:: endcolumn()

      The ending column number (exclusive).

   .. py:method:: start()

      The character offset (from 0, inclusive).

   .. py:method:: end()

      Ending character offset (exclusive).

   For example:

   >>> t[5].string()
   'J.'
   >>> t[5].line()
   2
   >>> t[5].column()
   9

   One can compute the space between two adjacent tokens by subtracting
   the endcolumn of the first from the column of the second:

   >>> t[5].column() - t[4].endcolumn()
   0
   >>> t[2].string()
   'said'
   >>> t[3].column() - t[2].endcolumn()
   2

   This is legitimate only if the two tokens are on the same line.

Algorithm
---------

To be robust to OCR errors, tokens typically mix alphanumeric and
punctuation characters.  The only exception is that a non-peripheral
hyphen will break a token into two pieces.
The definition in detail is as follows:

 * *Whitespace* is a sequence of one or more characters that
   satisfy ``isspace()``.

 * A *hyphen* is a sequence of one or more hyphen characters.  It
   is *peripheral* if it is preceded or followed by whitespace
   or by the beginning or end of the text.
   It is *embedded* if it is not peripheral.

 * A *separator* is whitespace or an embedded hyphen.  Note that a
   peripheral hyphen is not a separator, and will be included as part of
   another token.

 * A *regular token* is a maximal sequence of
   non-separators.  Its type is ``word`` if it contains any letters,
   ``number`` if it contains digits but no letters, and ``punct``
   if it contains neither letters nor digits.

 * A *token* is either a regular token or an embedded hyphen.

The tokenizer returns a sequence of tokens.  Note that whitespace is
discarded.  However, the tokenizer does keep track of line numbers;
each token has line number as an attribute.
