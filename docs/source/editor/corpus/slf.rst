
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
reduced to a file by using zip. A corpus can also be converted to a
single-file JSON format ("itemizing") and back again ("deitemizing").

Concepts
--------

A corpus consists of languages, and a language consists of a texts,
a lexicon, and an (automatically generated) index.

There are three basic kinds of text: *simple* texts consist of sentences,
*aggregate* texts consist of other texts, and *empty* texts consist of
nothing; they serve only as placeholders.

A simple text consists of sentences, optionally with translations.
A sentence consists of a sequence of forms, and a form is a particular
normalized Unicode character sequence. (Any alteration of the character sequence
produces a different form.)
If the text is a transcript, the sentences may also contain time
points.

A lexicon is a table in which the keys are forms.

It is possible to designate multiple forms as
equivalent by choosing one as the **canonical form** and linking the
variant form(s) to it. That is used for spelling variation and spelling
errors, and may be used for dialectal or stylistic variation. (A
corpus represents a single linguistic variety, but one is free to
define that variety inclusively.)

Forms may also be abstract, in at least two ways. (1) A sense
designator (conventionally, a period and some number of digits) may be
added to a form to create a new sense-disambiguated form. The original
form represents the default sense. (2) A form in the lexicon may
represent a morpheme, and there is no requirement that a morpheme be a
contiguous piece of text. For example, a consonant template 'ktb'
is an acceptable morpheme.

An index (of tokens) is also a table whose keys are forms;
but its values are lists of locations,
where a location is the pairing of a text ID and a sentence
number.

Format Definition
-----------------

The main goal is simplicity. A corpus is represented as a (small)
hierarchy of directories, with the following structure:

 * A **corpus** is a directory containing a metadata file named
   'langs', a subdirectory 'roms' containing romanizations, and some
   number of language subdirectories. The names of language
   subdirectories are language IDs. The filenames 'langs' and
   'roms' cannot be mistaken for language IDs if one uses either
   ISO-639-3 or Glottolog codes.

 * A **language** is a subdirectory whose name is a language ID.
   It contains a lexicon, a table of
   contents named 'toc', and a subdirectory 'txt' containing texts.

 * A **lexicon** consists of two files: 'lexicon' and 'index'.

 * A **text** is a file whose name is the text ID. Each text also has
   metadata, which is contained in the 'toc' file. Some texts consist
   solely of metadata.

All files are in a simple format in which a file consists of blocks of
lines separated by an empty line, and each line in a block
represents a key-value pair, separated at the first whitespace
character. For example::

   w aniin
   g hello

   w Debid ndizhnikaaz
   g my name is David

In some cases, duplicate keys are allowed, and the file is
interpreted as a list of property-lists, and in other cases the file
is intepreted as a list of objects or maps (and duplicate keys are not allowed).
The following is the complete list of files:

 * **Langs**. There is a single corpus metadata file, with pathname 'corpus/langs'.
   It contains a map
   from language IDs to language entries. A language entry
   minimally has key ``name``.

 * **Lexicon**. Each language directory contains a file named 'lexicon'.
   It contains a list of lexical entries,
   and a lexical entry is an object
   with the following keys (all optional):

    * ``id`` — Form. No two lexical entries may have the same form.

    * ``ty`` - Type. Word, sense-disambiguated form of word, 
      inflected form of word, spelling variant,
      etc. It is permitted to have forms that appear only in the
      lexicon and not in texts; they may be used to represent
      dependent morphemes.

    * ``c`` - Category (part of speech). Connects the lexical entry
      to the grammar. May include morphological information.
   
    * ``pp`` - Parts. The value is a list of forms, representing
      (unordered) constituents of this form. No assumptions are
      made about how the form is related to the parts. In
      particular, the form need not be the concatenation of the
      parts.

    * ``g`` - The English translation.

    * ``cf`` - Canonical form. We deal with spelling variation,
      spelling errors, dialectal forms, etc., by mapping all
      variants to a canonical form. An entry for a variant form may
      not contain any keys except a 'cf' record and (optionally) a
      'type' record.

    * ``of`` — Orthographic form. Sense-disambiguated forms can use
      this field to indicate how the form is written in text.

 * **Index**. Each language directory also contains a file named 'index'.
   It contains a map from senses to lists of
   locations (where tokens occur). A location is a string consisting
   of a text ID and a sentence number, separated by a period.

 * **Toc**. Finally, each language directory contains a file name 'toc'.
   It contains a list of text metadata entries. A text
   metadata entry contains the following keys:

    * ``id`` — The text ID. This is the only required key. No two
      entries may have the same ID.

    * ``ty`` - E.g., collection, book, chapter, page, text,
      audio. Complex texts (collections, documents, document sections,
      and so on) consist of metadata but no text file.

    * ``ti`` — Title.

    * ``au`` — Author.

    * ``ch`` - Children. A list of text IDs. A text should either have a
      'ch' entry or a text file, but not both. A text that has a text
      file is simple, a text that has a 'ch' entry is aggregate, and a
      text that has neither is empty.

    * ``pdf`` - The pathname of a PDF file. If it is a relative
      pathname, it is interpreted relative to the directory that
      contains the SLF directory.

    * ``audio`` - The pathname of an audio file, or an object with keys
      'pathname', 'start', and 'end'.

    * ``video`` - The pathname of a video file, or an object with keys
      'pathname', 'start', 'and 'end'.

 * **Text files.** Each language directory contains a 'txt'
   subdirectory that in turn contains text files whose names are text
   IDs (numbers beginning with 1).
   A text file contains a list of segments that are generically called
   "sentences", though they may variously represent sentences,
   utterances, pause groups, or other similar-sized pieces of text.
   A sentence is an object with keys:

    * ``w`` - Words. The value is a string consisting of
      space-separated forms.

    * ``t`` — Timestamp. The value is a floating-point number
      representing seconds from the beginning of the audio.

    * ``g`` - Gloss. The translation into English.


Programmatic interface
----------------------

The structure of a corpus directory is as follows.
The second column gives an expression for accessing the structural
unit in question, assuming that *corpus* is a variable containing the
corpus as a whole, and the third column gives the type of the object::

   corpus/               corpus                        Corpus
       langs             corpus.langs                  LanguageTable
       roms/             corpus.roms                   RomRepository
           *romname*     corpus.roms[*romname*]        Rom
           ...
       *langid*/         corpus[*langid*]              Language
           lexicon       corpus[*langid*].lexicon      Lexicon
           index         corpus[*langid*].index        TokenIndex
           toc           corpus[*langid*].toc          MetadataTable
           txt/          corpus[*langid*].txt          TextTable
               *txtid*   corpus[*langid*].txt[*txtid]  Text
               ...
       ...

The individual files ('langs', 'lexicon', 'index', and each of the roms
and simple texts) are called corpus *items*. The contents of the items
suffices to reconstruct the entire corpus.

**Corpus**. One loads a corpus using the Corpus constructor. Let us
first create a temp directory to work in::

   >>> from tempfile import TemporaryDirectory
   >>> tmp = TemporaryDirectory()

And let us create a corpus by copying an example::

   >>> from selkie.data import ex
   >>> from shutil import copytree
   >>> from os.path import join
   >>> corpus_filename = join(tmp.name, 'corpus')
   >>> bool(copytree(ex('corp25.slf'), corpus_filename))
   True
   
Opening the corpus::

   >>> from selkie.corpus import Corpus
   >>> corpus = Corpus(corpus_filename)

A corpus behaves like a dict whose keys are language IDs::

   >>> list(corpus)
   ['deu']
   >>> corpus['deu']
   <Language deu German>

The methods __iter__(), __len__(), keys(), items(), and values() are
also available and work as one would expect.
One can use the method new() to add a new language::

   >>> corpus.new('oji', 'Ojibwe')
   <Language oji Ojibwe>
   >>> list(corpus)
   ['deu', 'oji']
   
And one can delete a language using del::

   >>> del corpus['oji']
   >>> list(corpus)
   ['deu']

**Language table.**
As indicated above, the corpus has a
``langs`` member, which is the list of languages::

   >>> print(corpus.langs)
   deu German

One may equally treat corpus.langs as a dict containing languages. In
fact, dict method calls placed on the corpus are simply dispatched to
corpus.langs. (The method new() is an honorary "dict method call".)

**Language.**
A language has an ID and a full name::

   >>> deu = corpus['deu']
   >>> deu.langid()
   'deu'
   >>> deu.fullname()
   'German'

Alternatively, the properties listed in the 'langs' file can be
accessed by treating the language as a dict::

   >>> deu['id']
   'deu'
   >>> deu['name']
   'German'

Similarly, they may be modified, and the change is automatically
written to disk::

   >>> deu['name'] = 'Deutsch (German)'
   >>> deu['name']
   'Deutsch (German)'

Corresponding to the files in the language directory, a language has
attributes 'lexicon', 'index', 'toc', and 'txt'::

   >>> deu.lexicon
   <Lexicon deu>
   >>> deu.index
   <TokenIndex deu>
   >>> deu.toc
   <MetadataTable deu>
   >>> deu.txt
   <TextTable deu>

**Toc.**
A table of contents ('toc') is a table that maps text IDs to
metadata::

   >>> list(deu.toc)
   ['1', '2', '3']
   >>> deu.toc['1']
   <TextMetadata deu 1>

The toc prints out showing just IDs and titles::

   >>> print(deu.toc)
   1 story Eine kleine Geschichte
   2 page  p1                    
   3 page  p2                    

One can add new texts to the toc::



Text metadata behaves like a dict::

   >>> meta = deu.toc['1']
   >>> meta['ti']
   'Eine kleine Geschichte'
   >>> print(meta)
   id 1                     
   ty story                 
   ti Eine kleine Geschichte
   ch 2 3                   

**Text table.**
The 'txt' member has the same keys (text IDs), but the values are text objects::

   >>> list(deu.txt)
   ['1', '2', '3']
   >>> deu.txt['1']
   <Aggregate 1>
   >>> deu.txt['2']
   <SimpleText 2>

The same metadata dict that one access through 'toc' can also be accessed
from the text itself:

   >>> t1 = deu.txt['1']
   >>> t1.metadata()
   {'id': '1', 'ty': 'story', 'ti': 'Eine kleine Geschichte', 'ch': ('2', '3')}

Convenience methods are provided to access most of the metadata items::

   >>> t1.textid()
   '1'
   >>> t1.text_type()
   'story'
   >>> t1.author()
   ''
   >>> t1.title()
   'Eine kleine Geschichte'

**Hierarchical structure.**
Texts form a hierarchical structure, represented by the children() and
parent() methods of Text. One obtains the root of the hierarchy from
the language::

   >>> roots = deu.get_roots()
   >>> roots
   [<Aggregate 1>]
   
From there, one follows children() and parent() links::

   >>> roots[0].children()
   (<SimpleText 2>, <SimpleText 3>)
   >>> t2 = _[0]
   >>> t2.parent()
   <Aggregate 1>

One can also use the method walk() to iterate over all descendants of
a text (including itself).

A text has methods that characterize its intuitive level in the
hierarchy. The largest aggregates are *collections*, which are
distinguished by having text type 'collection'. The largest
non-collections are *documents*. And the leaves of the hierarchy are
simple texts. Texts have methods to test those properties:
is_collection(), is_document(), is_simple_text(), and languages have
methods to fetch them::

   >>> deu.get_collections()
   []
   >>> deu.get_documents()
   [<Aggregate 1>]
   >>> deu.get_simple_texts()
   [<SimpleText 2>, <SimpleText 3>]

**Sentences and words.**
A simple text behaves like a list of sentences::

   >>> t3 = deu.txt['3']
   >>> list(t3)
   [<Sentence 1 eines Tages begegnete der Schuster ...>, <Sentence 2 Ende>]

(Incidentally, if one accesses an aggregate like a list, the list
elements are the children.)

A sentence behaves like a list of words::

   >>> sent = t3[0]
   >>> list(sent)
   ['eines', 'Tages', 'begegnete', 'der', 'Schuster', 'einen', 'Bettler']
   >>> sent[0]
   'eines'

In addition, a sentence has methods for accessing a list of
timestamps, and a translation::

   >>> sent.timestamps()
   [(0, '1.4958'), (2, '1.9394'), (5, '2.7833'), (7, '3.3269')]
   >>> sent.translation()
   'one day the cobbler met a beggar'

API Documentation
-----------------

The corpus is built on top of a VDisk that associates Files with
names. First, the disk is wrapped in a BatchDisk, which collects a
list of modified items for saving as a batch.
And the Files are wrapped in Items, which apply a Format to the
File, store the resulting contents, and manage edits. After
editing the contents, one calls the item's 'modified()' method, which
adds the item to the BatchDisk's list. Edits may be done in a
'with' clause applied to the BatchDisk. On exit, all modified items
are saved. (Outside a 'with' clause, modified() causes an immediate
save.)

Classes that specialize CorpusItem have a 'format' member that is used
to instantiate items. That is, the item class determines the file format.

The only caching is the creation of backlinks. The Toc and the Lexicon
both have backlinks. Each has a backlinks() method, which instantiates
an appropriate backlinks object the first time it is called. When
an item that has backlinks is flagged as modified(), its cached value
for backlinks is cleared.

The Corpus maintains a cache that maps item names to items. When a new
item is visited, one must provide its type.

.. py:class:: BatchDisk

   Wraps a VDisk and adds the hold() and modified() methods.
   Call hold() in a 'with' clause to hold saves until the 'with'
   clause is ended.
   
   Although not included here, Item does implement __hash__() and
   __cmp__(), permitting Items to be used in sets or as keys for
   dicts. Two Items with the same name are equal.

   .. py:attribute:: root

      The pathname corresponding to the root of the disk.

   .. py:method:: __getitem__(name)

      Passed through to the VDisk.      
            
   .. py:method:: hold()

      Creates a "hold" object for use in a 'with' clause. When the
      clause ends, the object notifies this BatchDisk. The BatchDisk
      keeps a count of active holds. When the last one ends, all
      modified items are saved.

.. py:class:: Item(disk, name, fmt)

   An Item is created on a BatchDisk (*disk*) and is identified by a
   *name* that is unique to it. *Fmt* is applied to the File to get
   the contents of the item.

   .. py:attribute:: debug

      A class attribute that can be set True to cause messages to
      print whenever items are read or written.

   .. py:method:: disk()

      Returns the BatchDisk.

   .. py:method:: item_name()

      Returns the item name.

   .. py:method:: contents()

      Returns the object read from the formatted File. One may modify
      it, but changes will not be saved unless one calls
      modified().

   .. py:method:: modified()

      Notifies the BatchDisk that this Item is modified. If there is a
      hold on the disk, the Item goes into a set of modified
      items. Since it is a set, calling modified() multiple times has
      no effect after the first time. When the hold is released, or
      immediately, if there is no hold, the disk saves the Item,
      calling the store() method of the underlying File.

.. py:class:: CorpusItem(corpus, item_name)

   A specialization of Item for use in a Corpus. The Item is created
   on the disk in the corpus, and its format is determined by the
   class of the Item. (Each specialization of CorpusItem is associated
   with a format.)

   .. py:attribute:: format

      This is a class attribute that must be provided by any
      specialization. The Item class determines the file format for
      its instances.

   .. py:method:: corpus()

      Returns the corpus.

.. py:class:: Corpus(root)

   *Root* is a pathname. It may begin with '~'.

   A Corpus wraps a BatchDisk. It has its own mapping from item names
   to Items. (In addition, the corpus its self is the value of the
   name '/'.)

   .. py:method:: disk()

      Returns the BatchDisk.

   .. py:method:: filename()

      Returns the root filename.

   .. py:method:: item(name)

      Returns the item with the given *name*, if it exists. Signals an
      error otherwise.

   .. py:method:: intern(name, cls)

      Returns the item with the given *name*. If it does not already
      exist, it instantiates it as an instance of *cls* and adds it to
      the mapping.
        
   .. py:attribute:: langs

      This attribute is a synonym for the item '/langs', which is a
      LanguageTable. It is a lazy attribute: it is created the first
      time it is accessed.

   .. py:attribute:: roms

      The value is a RomTable. It is not interned in the item table,
      since it is a subdirectory, not an item. Note that accessing
      'roms' twice returns two different objects, but they behave
      identically.

   .. py:method:: __getitem__(name)

      The same as .langs[name].

   .. py:method:: get(name)

      The same as .langs.get(name).

   .. py:method:: __iter__()

      Iterates over the languages.

   .. py:method:: __len__ (self):

      The number of languages.

   .. py:method:: languages()

      Iterates over the languages.

   .. py:method:: language(name)

      Same as get(name).

   .. py:method:: new_language(langid, fullname)

      Same as .langs.new(langid, fullname).
