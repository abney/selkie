
.. automodule:: selkie.corpus.ops

Corpus operations — ``selkie.corpus.ops``
=========================================

.. py:function:: concordance(lang, form)

   Prints out a concordance of locations where *form* occurs. *Lang*
   should be a corpus object of type Language.

   By default, locations are included in which *form* occurs as a part
   of a token, not just where it occurs as an independent word. To
   limit printing to those location where *form* is an independent
   word, specify ``recurse=False``.
