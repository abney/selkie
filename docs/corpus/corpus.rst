
``selkie.corpus`` — Simple text corpus
======================================

.. toctree::
   :titlesonly:

   drill

Introduction
------------

The logical structure is intentionally simple.  A corpus consists of
languages, and a language consists of texts and a lexicon.  We
distinguish between *text* and *aggregate*.  A
text is essentially just a list of sentence-sized units called
*segments*.  An aggregate has hierarchical structure, terminating in
texts.  We further distinguish between *collections* and *documents*.
A *document* is a maximal item that is not a collection.  (Documents
may either be single texts or themselves aggregates.)

Languages are identified by *language IDs* (langids).
The set of language IDs is not rigidly specified, though
ISO 639-3 codes are typical.

Texts and documents are identified by *text IDs*.  They are arbitrary
strings; typical is simply to number them sequentially.

The segments of a text are generically called *sentences*, though they
may represent sentences, utterances, pause groups, or similar
sentence-sized units.  Segment-by-segment translations (into a
glossing language) may be provided.

For texts that originate as audio recordings, the text is called
a *transcription*, which is a tabular file with one record for every
couple of seconds of speech, called a *snippet*.  The file contains four fields:
start time and end time (in seconds), an indication of whether this
snippet begins a new segment (``S``) or not (``-``), and the text of
the snippet.

Dividing a segment at whitespace yields *tokens*.  A token is an
occurrence of a *form*.

On disk, a corpus is a directory with the following internal structure:
 * ``rom`` — Subdirectory containing romanizations.
 * ``lgid.lg`` — Subdirectory representing the language with the
   given ID.

    * ``orig`` — Subdirectory containing original documents.  These
      are for convenience only; no assumptions are made about format.
    * ``toc`` — A file containing text metadata and documents.
    * ``txt`` — A subdirectory containing texts in files ``textid.txt``.
    * ``xs`` — A subdirectory containing audio transcriptions in files
      ``textid.xs``.
    * ``lexicon.lx`` — A file containing properties of lexical entries.
    * ``lexicon.ldx`` — An index file mapping forms to lists of token locations.

Hierarchical interface
----------------------

One loads a corpus using the Corpus constructor.  The corpus has a
``langs`` member, which is a list of languages::

   >>> from selkie.corpus import Corpus
   >>> from selkie.data import ex
   >>> corpus = Corpus(ex('corp25.lgc'))
   >>> print(corpus.langs)
   deu German

One can fetch a language by accessing langs as a dict::

   >>> deu = corpus.langs['deu']
   >>> deu.langid
   'deu'
   >>> deu.name
   'German'

The ``toc`` member is a dict containing **items** (texts, documents, and
collections).  It is loaded the first time it is accessed.  The
metadata for each item is loaded at the same time::

   >>> print(deu.toc)
   1 story Eine kleine Geschichte
   2 page  p1
   3 page  p2
   >>> len(deu.toc)
   3
   >>> t1 = deu.toc['1']
   >>> print(t1.meta)
   lang        <Language deu German>
   textid      1
   text_type   story
   descr
   author
   title       Eine kleine Geschichte
   orthography None
   child_names ('2', '3')
   catalog_id  None
   audio       None
   >>> t1.title
   'Eine kleine Geschichte'

Subsets of interest are the documents (maximal items that are not
collections) and the texts::

   >>> deu.get_documents()
   [<Aggregate 1>]
   >>> deu.get_texts()
   [<Text 2>, <Text 3>]

An aggregate behaves as a list of children, a text behaves as a
list of sentences, and a sentence behaves like a list of words::

   >>> list(t1)
   [<Text 2>, <Text 3>, <Aggregate 4>, <Text 9>]
   >>> t2 = t1[0]
   >>> list(t2)
   [<S in einem kleinen Dorf am Fluss wohnte ein Schuster>,
    <S der Schuster war sehr arm>]
   >>> s = t2[0]
   >>> s[0]
   'in'

REST interface
--------------

Alternatively, one can create a REST interface to the corpus::

   >>> from selkie.corpus import RESTCorpus
   >>> corpus = RESTCorpus(corpus_filename)

The corpus can be accessed like a dict, or using the methods GET, PUT,
and DELETE.  (If an object is read-only, then only GET is available.)
The valid paths are as follows.  All entities are represented in JSON
format.

.. list-table::
   :widths: 1 3

   * - ``/toc/lgid``
     - Read-only.  Returns the toc file for the given language as a
       list of text metadata objects.
   * - ``/toc/lgid/textid``
     - Read-write.  Returns the metadata for a given text.  This is a
       dict with keys ``textid``, ``text_type``, ``author``,
       ``title``, ``orthography``, ``filename``, and ``children``.


Corpus and Language
-------------------

.. autoclass:: selkie.corpus.Corpus
   :members:

.. autoclass:: selkie.corpus.Language
   :members:


Utility functions and classes
-----------------------------

.. py:function:: counts(items)

   Returns a dict mapping the item types to their counts in the
   iteration *items*.  Items must be hashable.

.. py:class:: Records

   A Records instance represents the contents of a file whose lines
   are to be interpreted as tab-separated records.  It is not
   necessary to wrap Records in "with".  For example::

      >>> recs = Records('foo.tab')
      >>> for (x, y) in recs: ...
   
   One may report errors with line numbers by calling the methods
   ``warn()`` or ``error()``.

.. py:class:: RecordGroups

   Represents the contents of a file that consists of tabular
   records that are separated into groups by empty lines.
