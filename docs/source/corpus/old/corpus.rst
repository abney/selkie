
Programmatic Interface to Corpus
================================

Selkie provides a programmatic interface to SLF corpora.
The directory structure of an SLF corpus is given in the first column
of the following. The second column gives an expression for accessing
the structural unit in question, assuming that *corpus* is a variable
containing the corpus as a whole, and the third column gives the type
of the object::

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

Recall from the description of the SLF format that
the individual files ('langs', 'lexicon', 'index', 'toc', and each of the roms
and simple texts) are called corpus *items*. The contents of the items
suffices to reconstruct the entire corpus.

Corpus
------

One loads a corpus using the Corpus constructor. Let us
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

The methods ``__iter__()``, ``__len__()``, ``keys()``, ``items()``, and ``values()`` are
also available and work as one would expect.
One can use the method ``new()`` to add a new language::

   >>> corpus.new('oji', 'Ojibwe')
   <Language oji Ojibwe>
   >>> list(corpus)
   ['deu', 'oji']
   
And one can delete a language using del::

   >>> del corpus['oji']
   >>> list(corpus)
   ['deu']

Language table
--------------

As indicated above, the corpus has a
``langs`` member, which is the list of languages::

   >>> print(corpus.langs)
   deu German

One may equally treat corpus.langs as a dict containing languages. In
fact, dict method calls placed on the corpus are simply dispatched to
corpus.langs (including ``new()`` as an honorary "dict method call").

Language
--------

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

Similarly, those properties may be modified, and the change is automatically
written to disk::

   >>> deu['name'] = 'Deutsch (German)'
   >>> deu['name']
   'Deutsch (German)'

(However, the key 'id' cannot be modified.)

Corresponding to the files in the language directory, a language has
attributes ``lexicon``, ``index``, ``toc``, and ``txt``::

   >>> deu.lexicon
   <Lexicon /deu/lexicon>
   >>> deu.index
   <TokenIndex /deu/index>
   >>> deu.toc
   <Toc /deu/toc>
   >>> deu.txt
   <TextTable deu>

Table of Contents
-----------------

A table of contents ('toc') is a table that maps text IDs to
metadata::

   >>> list(deu.toc)
   ['1', '2', '3']
   >>> deu.toc['1']
   <TextMetadata deu 1>

The toc prints out as a listing of IDs, types, and titles::

   >>> print(deu.toc)
   1 story Eine kleine Geschichte
   2 page  p1                    
   3 page  p2                    

One can add new texts to the toc::

   >>> deu.toc.new('4', ti='Der Taucher', ty='story')
   <TextMetadata deu 4>
   >>> print(deu.toc)
   1 story Eine kleine Geschichte
   2 page  p1                    
   3 page  p2                    
   4 story Der Taucher           

Text metadata behaves like a dict::

   >>> meta = deu.toc['1']
   >>> meta['ti']
   'Eine kleine Geschichte'
   >>> print(meta)
   id 1                     
   ty story                 
   ti Eine kleine Geschichte
   ch 2 3                   

Text table
----------

The 'txt' member has the same keys as the TOC (namely, text IDs), but
the values are text objects instead of metadata objects::

   >>> list(deu.txt)
   ['1', '2', '3', '4']
   >>> deu.txt['1']
   <Text 1>
   >>> deu.txt['2']
   <Text 2>

The same metadata dict that one access through 'toc' can also be accessed
from the text itself:

   >>> t1 = deu.txt['1']
   >>> t1.metadata()
   <TextMetadata deu 1>

Incidentally, the inverse method, from metadata to text, is also available::

   >>> meta.text()
   <Text 1>

The text has convenience methods to access most of the metadata items::

   >>> t1.textid()
   '1'
   >>> t1.text_type()
   'story'
   >>> t1.author()
   ''
   >>> t1.title()
   'Eine kleine Geschichte'

However, one cannot access metadata properties using square brackets
on a text. Square brackets applied to an aggregate text return its
children, and square brackets applied to a simple text returns its
sentences.

Hierarchical structure
----------------------

Texts form a hierarchical structure, represented by the ``children()`` and
``parent()`` methods of Text. One obtains the root of the hierarchy from
the language::

   >>> roots = deu.get_roots()
   >>> roots
   [<Text 1>, <Text 4>]
   
From there, one follows ``children()`` and ``parent()`` links::

   >>> roots[0].children()
   [<Text 2>, <Text 3>]
   >>> t2 = _[0]
   >>> t2.parent()
   <Text 1>

One can also use the method ``walk()`` to iterate over all descendants of
a text (including itself).

A text has methods that characterize its intuitive level in the
hierarchy. The largest aggregates are *collections*, which are
distinguished by having text type 'collection'. The largest
non-collections are *documents*. And the leaves of the hierarchy are
simple texts. Texts have methods to test those properties:
``is_collection()``, ``is_document()``, ``is_simple_text()``, and languages have
methods to fetch them::

   >>> deu.get_collections()
   []
   >>> deu.get_documents()
   [<Text 1>, <Text 4>]
   >>> deu.get_simple_texts()
   [<Text 2>, <Text 3>, <Text 4>]

Sentences and words
-------------------

A simple text behaves like a list of sentences::

   >>> t3 = deu.txt['3']
   >>> list(t3)
   [<Sentence 3.1 eines Tages begegnete der Schuster ...>, <Sentence 3.2 Ende>]

(Incidentally, if one accesses an aggregate like a list, the list
elements are the children.)

A sentence behaves like a list of words::

   >>> sent = t3[0]
   >>> list(sent)
   ['eines', 'Tages', 'begegnete', 'der', 'Schuster', 'einen', 'Bettler']
   >>> sent[0]
   'eines'

In addition, a sentence has methods for accessing a list of
timestamps::

   >>> sent.timestamps()
   [(0, '1.4958'), (2, '1.9394'), (5, '2.7833'), (7, '3.3269')]

One can alternatively obtain a list of *spans*, which are triples
consisting of start time, end time, and a list of words::

   >>> for span in sent.spans():
   ...     print(span)
   ...
   ('1.4958', '1.9394', ['eines', 'Tages'])
   ('1.9394', '2.7833', ['begegnete', 'der', 'Schuster'])
   ('2.7833', '3.3269', ['einen', 'Bettler'])
   
Finally, if the sentence has a translation, the method ``gloss()``
returns it::

   >>> sent.gloss()
   'one day the cobbler met a beggar'

The words in a sentence appear to be strings, and *are* strings, but
they are more precisely instances of a specialization of str called
Token. They have some additional methods that str lacks. In
particular, each token has a location, which consists of the text ID
and the sentence number::

   >>> token = sent[4]
   >>> token
   'Schuster'
   >>> token.loc()
   <Loc 3.1.5>

A token also has a link to its lexical entry::

   >>> type(token.entry())
   <class 'selkie.corpus.core.Lexent'>

For convenience, one can access all methods of the lexical entry
directly from the token. We return to that point below, after
discussing lexical entries.

Lexicon
-------

In addition to accessing lexical entries via tokens, one can access
them from the Lexicon itself. The Lexicon behaves like a
dict whose keys are forms::

   >>> list(deu.lexicon)
   ['begegnete', 'Bettler', 'der', 'einen', 'eines', 'Schuster', 'Tag', 'Tages']
   >>> tages = deu.lexicon['Tages']
   >>> print(tages.table())
   id   Tages
   pp   Tag .gen

An entry, like a token, is a specialization of str:

   >>> tages
   'Tages'

But it has additional methods, like ``table()`` in the example above.
In particular, it has methods for accessing lexical attributes::

   >>> tages.form()
   'Tages'
   >>> tages.parts()
   ['Tag', '.gen']

The method ``form()`` actually just returns the lexent itself.
The value of ``parts()`` is also a list of lexents, not
merely a list of strings. For example::

   >>> tag = tages.parts()[0]
   >>> tag
   'Tag'
   >>> tag.gloss()
   'day'

The lexical attributes were listed in the discussion of SLF. The
method names are:

 * form
 * formtype
 * cat
 * parts
 * gloss
 * canonical
 * orthographic

The values of these lexical attributes can be set using the method
``set()``::

   >>> tages.set(cat='N', gloss="day's")
   >>> print(tages.table())
   id   Tages
   pp   Tag .gen
   c    N
   g    day's

In addition, there are two (automatically-generated) inverse
relations:

 * partof — inverse of parts
 * variants — inverse of canonical

For example::

   >>> sorted(tag.partof())
   ['Tag', 'Tages']

By default, the return set includes not only forms that the input is
an immediate part of, but the reflexive-transitive closure of that
relation. One can suppress the closure by specifying ``closure=False``::

   >>> tag.partof(closure=False)
   {'Tages'}

Finally, a lexical entry has a method ``sentences()`` that
accesses the token index to find all sentences in which this form occurs::

   >>> tages.sentences()
   {<Sentence 3.1 eines Tages begegnete der Schuster ...>}

The return list includes not only sentences in which the form appears
as an element, but also sentences in which the form appears as a part
of an element. For example, the word "Tag" never appears as
an independent word in our sentences, but it does appear as a part of
the word "Tages"::

   >>> tag.sentences()
   {<Sentence 3.1 eines Tages begegnete der Schuster ...>}

One can restrict the return value just to sentences in which the form
appears as an element by specifying ``recurse=False``::

   >>> tag.sentences(recurse=False)
   set()

(Note: ``sentences()`` either calls ``partof()`` or not; it is not
possible to specify that it should call ``partof(recurse=False)``.)

One can break down the operation of ``sentences()`` into
three steps. The method ``locations()`` returns a set of
locations::

   >>> tages.locations()
   {<Loc 3.1.2>}

(The method ``locations()`` also accepts ``recurse=False`` as an
option.) The method ``deref()`` of Language can then be used to go
from the locations to the tokens whose location is specified::

   >>> tokens = list(deu.deref(tages.locations()))
   >>> tokens
   ['Tages']

Then one can get the sentences that the tokens belong to::

   >>> tokens[0].sentence()
   <Sentence 3.1 eines Tages begegnete der Schuster ...>

Recall that we earlier set ``token`` to be one of the words of a
sentence. Tokens have a method ``entry()`` that returns their lexent,
though the token and lexent are not visibly different::

   >>> token.entry()
   'Schuster'
   >>> type(token)
   <class 'selkie.corpus.core.Token'>
   >>> type(token.entry())
   <class 'selkie.corpus.core.Lexent'>

For convenience, tokens have all the same methods as lexents. The
token versions simply dispatch to the lexent::

   >>> token.gloss()
   'cobbler'
   >>> print(token.table())
   id   Schuster
   g    cobbler

Thus, for practical purposes, one can think of a token simply as a
lexent with additional methods ``loc()`` and ``sentence()``.
