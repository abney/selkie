
.. automodule:: selkie.corpus

Selkie Language Format — ``selkie.corpus``
==========================================

Selkie Language Format (SLF) is a lightweight specification for
linguistic corpora. It represents the logical structure of the corpus,
not the presentation in "pretty" human-consumable form. An analogy can
be drawn to web pages, in which HTML represents the logical structure
and CSS represents the presentation.

Media files, which include audio files, video files, and print-quality page formats like PDF, are
considered to be presentational. They are not included in an SLF file,
though they obviously constitute an important part of language
documentation. The SLF file can be viewed as stand-off annotation
representing the logical structure of their contents. The distinction between media
files and annotation also aligns roughly with the distinction between
documentation and description. If we identify media with documentation
and annotation (SLF) with description, then we do treat e.g. translation
as part of description rather than documentation, but that is not
entirely unreasonable.

The SLF "file" is actually a directory, though it may of course be
reduced to a file by using zip.

Concepts
--------

A corpus consists of languages, and a language consists of a texts,
a lexicon, and an (automatically generated) index.

A text consists of sentences (possibly with translations), and a
sentence consists of a sequence of forms with (optional) sense
numbers. The lack of an explicit sense number is the same as sense 0.
If the text is a transcript, the sentences may also contain time
points.

A lexicon is a table in which a key is a form plus a sense
number. A **form** is a Unicode string representing a concrete word shape or a
piece of a word. It is possible to designate multiple forms as
equivalent by choosing one as the **canonical form** and linking the
variant form(s) to it. That is used for spelling variation and spelling
errors, and may be used for dialectal or stylistic variation. (A
corpus represents a single linguistic variety, but one is free to
define that variety inclusively.)

An index (of word forms) is also a table whose keys are form plus
sense number; but its values are lists of locations,
where a location is the pairing of a text ID and a sentence
number.

Definition
----------

The main goal is simplicity. A corpus is represented as a (small)
hierarchy of directories, with the following structure:

 * A **corpus** is a directory containing a metadata file named
   'langs', a subdirectory 'roms' containing romanizations, and some
   number of language subdirectories. The names of language
   subdirectories are language IDs; neither of the names 'langs' nor
   'roms' are valid language IDs either in ISO-639-3 or Glottolog.

 * A **language** is a subdirectory whose name is a language ID.
   It contains a lexicon, a table of
   contents named 'toc', and a subdirectory 'txt' containing texts.

 * A **lexicon** consists of two files: 'lexicon' and 'index'.

 * A **text** is a file whose name is the text ID. Each text also has
   metadata, which is contained in the 'toc' file. Some texts consist
   solely of metadata.

Files are in JSON format. I use the terms "object" and "map"
interchangeably.

 * The corpus metadata file is named 'langs'. It contains a map
   from language IDs to language entries. A language entry
   minimally has key ``name``.

 * The file 'lexicon' contains a map from forms to form entries.
   A form entry is a list of sense entries, and a sense entry is an object
   with the following keys (all optional):

    * ``type`` - Word, inflected form of word, spelling variant,
      etc. It is permitted to have forms that appear only in the
      lexicon and not in texts; they may be used to represent
      dependent morphemes.

    * ``pos`` - Part of speech. Connects the lexical entry
      to the grammar. May include morphological information.
   
    * ``parts`` - The value is a list of senses, representing
      (unordered) constituents of this form. No assumptions are
      made about how the form is related to the parts. In
      particular, the form need not be the concatenation of the
      parts.

    * ``gloss`` - The English translation.

    * ``cf`` - Canonical form. We deal with spelling variation,
      spelling errors, dialectal forms, etc., by mapping all
      variants to a canonical form. An entry for a variant form may
      not contain any keys except a 'cf' record and (optionally) a
      'type' record.

 * The file 'index' contains a map from senses to lists of
   locations (where tokens occur). A location is a string consisting
   of a text ID and a sentence number, separated by '.' (period).

 * The 'toc' file contains a map from text IDs to text metadata. Text
   metadata is an object containing the following keys (all optional):

    * ``type`` - E.g., collection, book, chapter, page, text,
      audio. Complex texts (collections, documents, document sections,
      and so on) consist of metadata but no text file.

    * ``title``

    * ``author``

    * ``parts`` - A list of text IDs. A text should either have a
      'parts' entry or a text file, but not both.

    * ``pdf`` - The pathname of a PDF file. If it is a relative
      pathname, it is interpreted relative to the directory that
      contains the SLF directory.

    * ``audio`` - The pathname of an audio file, or an object with keys
      'pathname', 'start', and 'end'.

    * ``video`` - The pathname of a video file, or an object with keys
      'pathname', 'start', 'and 'end'.

 * A text file contains a list of segments that are generically called
   "sentences", though they may variously represent sentences,
   utterances, pause groups, or other similar-size pieces of text.
   A sentence is an object with keys:

    * ``text`` - The value may be either a string or a list containing
      a mix of strings, positive numbers representing timestamps, and
      negative numbers representing sense numbers. A sense number
      applies to the immediately preceding form.

    * ``gloss`` - The translation into English.

   A sentence is tokenized by dividing the strings at whitespace. The
   result is a sequence consisting of a mix of forms, timestamps, and
   sense numbers.


Hierarchical interface
----------------------

**Corpus**. One loads a corpus using the Corpus constructor.  The corpus has a
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
