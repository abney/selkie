
Wiktionary — ``selkie.data.wiktionary``
=======================================

Using the command line::

   $ python -m selkie.data.wiktionary xlangs DUMPFILE LANGFILE
   $ python -m selkie.data.wiktionary xdicts DUMPFILE TGTLANGFILE OUTDIR

Using the API::

   >>> dump_fn = '~/scratch/ling780/enwiktionary-20230201-pages-articles.xml.bz2'
   >>> from selkie.data.wiktionary import WiktDump
   >>> wikt = WiktDump(dump_fn)
   >>> arts = wikt.articles()
   >>> art = next(arts)
   >>> while ':' in art.title:
   ...     art = next(arts)

An example of a raw article::

   >>> art.orig
   {'title': 'dictionary',
    'ns': '0',
    ...
    'text': '{{also|Dictionary}}\n==English==\n{{was wotd|2022|December|12}}...'}

Parsed version::

   >>> level_1_section = art.parsed()
   >>> [k for (k,v) in level_1_section]
   ['__pre__', 'English']
   >>> level_2_section = level_1_section[1][1]
   >>> [k for (k,v) in level_2_section]
   ['__pre__',
    'Alternative forms',
    'Etymology',
    'Pronunciation',
    'Noun',
    'Verb',
    'Further reading',
    'Anagrams']

..
   Loading entries from a language file:


API
---

.. py:class:: WiktDump

   Represents a wiktionary dump file from
   ``https://dumps.wikimedia.org/enwiktionary``.

   .. py:method:: __init__(dump_fn)

      Sets the members ``dump_fn``, ``prefix``, and ``parse``.  The *dump_fn* may
      start with '~'.  It should end with '-pages-articles.xml.bz2'.
      The *prefix* is everything before that.  The *parse* member is
      an instance of Parser.

   .. py:method:: raw_articles()

      Opens the bz2 file.  The first line is expected to be
      '<mediawiki ...>', and is discarded.  Next there should be a
      '<siteinfo>' element, which is also discarded.

      After that, the function ``selkie.pyx.xml.lines_to_items`` is used to convert
      the input to XML parsed into dictionary format.  (See lines_to_items.)

      The elements in the iteration are expected to have tag 'page';
      otherwise an error is signalled.  The return value is an
      iteration over elements, each element represented as a dict.

   .. py:method:: articles()

      Calls ``raw_articles()`` and calls ``WiktArticle(art)`` on each
      raw article.  Returns an iteration over WiktArticles.

   .. py:method:: find(title)

      Iterates over the ``articles()`` and returns the first one whose
      title is *title*.

   .. py:method:: extract_language_names(tgtfn)

      Writes *tgtfn*.  Iterates over the ``articles()``, skipping any
      whose title contains a colon.  In the remaining articles, all
      level-2 headings are language names.  Extracts them and writes
      them to *tgtfn*, one per line, eliminating duplicates.

   .. py:method:: extract_dicts(tgtlangs_fn, tgtdir)

      Reads the names of the target languages from the file
      *tgtlangs_fn*.  Creates *tgtdir* and writes one file per
      language in that directory.  The filename is the language name.
      It processes each wiktionary page into **entries**, one for each
      level-2 heading.  Each Entry is pickled to the corresponding
      language file.


.. py:class:: WiktArticle

   .. py:attribute:: wikt

      The WiktDump object.

   .. py:attribute:: orig

      The original (raw) article, a dict.

   .. py:attribute:: title

      The title.  The value of orig['title'], or if that does not
      exist, the empty string.

   .. py:attribute:: markdown

      The contents.  The value of orig['revision']['text'], or if that
      does not exist, the empty string.

   .. py:method:: parsed()

      The parsed version is computed the first time that parsed() is
      called.  The WiktDump parser is called on the markdown.  See Parser.
      The output is a ParsedArticle.


.. py:class:: ParsedArticle

   .. py:attribute:: orig

      The original WiktArticle.

   .. py:attribute:: items

      A list of pairs; the output of parsing.  Values are either item
      lists (recursively) or strings or Markdown.

   .. py:method:: entries()

      The toplevel items have level-2 headings as keys, which are
      language names.  This wraps each value as an Entry and yields
      it.  (But if the title contains a colon, the empty iteration is
      returned.)


.. py:class:: Entry
      
   .. py:attribute:: word

      The lemma.

   .. py:attribute:: lang

      The language name.

   .. py:attribute:: items

      The contents.


.. py:class:: Parser

   .. py:method:: __call__(md)

      The input is markdown.  It is split into lines, and then
      recursively split wherever there are headers.  The result is
      in **recursive item format**.  An *element* is a list of
      *items*, and an *item* is a (key, value) pair, where the *key*
      is either a header or '__pre__' (for material preceding the
      first header), and the *value* is either a Markdown object or an
      *element* (recursively).

      The initial parse produces a list of items whose key is either
      '__pre__' or a level-1 header.  In the return from __call__(),
      that is reduced to an iteration over items whose key is either
      '__pre__' or '__H1__' (with the level-1 header as value) or a
      level-2 header.  In principle, there might also be items whose
      key is '__md__' (for stray markdown), though only if an article
      is ill-formed.

      The final outcome is an iteration over **level-2 items**, which
      are pairs (level-2-header, level-2-section).  A level-2-section,
      in turn, is a list of pairs (level-3-header, level-3-section),
      and so on.
