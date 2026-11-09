
File format
===========

*This is CLD format v29.*

Concrete example
----------------

Having a concrete example in mind will make it easier to discuss the
general definition. Here is an example of a file in CLD format::

   corp.corp29
     lang.deu
       name German
       glot stan1295
       iso3 deu
       text.1
         ti Eine kleine Geschichte
         ty story
         ch 2 3
       text.2
         ti p1
         ty page
         sent.1
           w in einem kleinen Dorf am Fluss wohnte ein Schuster
           tr in a little village on a river there lived a cobbler
         sent.2
           w der Schuster war sehr arm
           tr the cobbler was very poor
       text.3
         ti p2
         ty page
         sent.1
           w eines Tages begegnete der Schuster einen Bettler
           tr one day the cobbler met a beggar
           times
             t.0 1.495800
             t.2 1.939400
             t.5 2.783300
             t.7 3.326900
         sent.2
           w Ende
           tr the end
           times
             t.0 3.688200
             t.1 3.928300
       lexicon
         form.eines
           pp ein -gen
           g of a(n)
         form.ein
           g a(n)
         form.-gen
           g (genitive case)
         form.Schuster
           g cobbler

The indentation is optional; it makes the structure easier to see.

The file is read into memory as a collection of nested dicts,
using :py:mod:`selkie.pyx.dct`. The result is just
like the result of reading a JSON file in which only dicts and strings
are used::

   {"corp.corp29":
      {"lang.deu":
         {"name": "German",
          "glot": "stan1295",
          "iso3": "deu",
          "text.1":
             {"ti": "Eine kleine Geschichte",
              "ty": "story",
              "ch": "2 3"},
           "text.2": { ... },
           ...}}}

Each of these dicts, other than the topmost one, is called a
**record**. Each represents a corpus object.
For example, the record ``{"name": "German", ...}`` represents a
language in the corpus.

Each record is the value of a **key**. That key names the object relative
to its parent, and is called the **object key**. For example, the
language object ``{"name": "German", ...}`` has key ``lang.deu``.

The following provides an illustrative code snippet:

>>> from selkie.data import ex
>>> from selkie.corpus.corpus import open_cld_file
>>> fi = open_cld_file(ex('corp29.cld'))
>>> corpus = fi.contents['corp.corp29']
>>> deu = corpus['lang.deu']
>>> text3 = deu['text.3']
>>> sent32 = text3['sent.2']
>>> sent32
{'w': 'Ende', 'tr': 'the end', 'times': {'t.0': '3.688200', 't.1': '3.928300'}}

The value of each of the variables ``corpus``, ``deu``, ``text3``, and
``sent32`` is a record representing a corpus object.

Record structure
----------------

A record can be uniquely identified within a corpus by its
**pathname**, which is the sequence of keys that leads to it. For
example, the record that was called ``sent32`` in the code snippet
above has the pathname::

   ("corp.corp29", "lang.deu", "text.3", "sent.2")

Each of these keys consists of an **attribute** and a **name**, joined by a
period. Not all keys contain a period: some keys, such ``iso3`` or
``lexicon``, consist only of an attribute.

The attributes in a pathname are predictable from the type of the
object that the pathname identifies. For example, a sentence always
has a pathname of form::

   ("corpus.{}", "lang.{}", "text.{}", "sent.{}")

where ``{}`` represents a wildcard to be filled by a name. Because of
the predictability of the attributes, we can equally well identify an
object by the name sequence alone (coupled with the object type).
The name sequence is called the **item ID**. For
example, ``sent32`` has item ID ``corp29.deu.3.2``. (Period is used
as a separator in item IDs.) Usually, we omit the corpus name, and use
the corpus-relative version ``deu.3.2``.

The object type also determines which attribute
types are legal within the record. In particular,
the legal attributes for a sentence are ``w``, ``tr``, and ``times``.
A ``times`` record, in turn, has only one legal attribute, namely, ``t``.

The following is a
complete **signature**, listing all record types and their
attributes. The second column gives an example of a name, for 
each record type whose key includes a name.

+----------+-------------+--------------------------------------------------+
| **Type** | **Name**    | **Attributes**                                   |
+----------+-------------+--------------------------------------------------+
| corp     | corp29      | lang, rom                                        |
+----------+-------------+--------------------------------------------------+
| lang     | oji         | name, glot, iso3, userom, text, lexicon, trans   |
+----------+-------------+--------------------------------------------------+
| rom      | gothic      | u                                                |
+----------+-------------+--------------------------------------------------+
| text     | 1           | ty, ti, de, au, ch, pdf, audio, video, sent, xid |
+----------+-------------+--------------------------------------------------+
| lexicon  |             | form                                             |
+----------+-------------+--------------------------------------------------+
| trans    | fra         | xlexicon, xtext                                  |
+----------+-------------+--------------------------------------------------+
| sent     | 1           | w, tr, times                                     |
+----------+-------------+--------------------------------------------------+
| form     | aanii       | fy, g, c, pp, cf, of                             |
+----------+-------------+--------------------------------------------------+
| xlexicon |             | fg                                               |
+----------+-------------+--------------------------------------------------+
| xtext    | 1           | sg                                               |
+----------+-------------+--------------------------------------------------+
| times    |             | t                                                |
+----------+-------------+--------------------------------------------------+

The following table gives the pathname template for
each object type, and an example of an item ID.
The corpus is omitted from pathname templates and item IDs.
The templates are written as lists of attributes. Attributes that are
not associated with names are bracketted.

+----------+------------------------+------------+
| **Type** | **PathTemplate**       | **ItemID** |
+----------+------------------------+------------+
| lang     | lang                   | oji        | 
+----------+------------------------+------------+
| rom      | rom                    | gothic     |
+----------+------------------------+------------+
| text     | lang text              | oji.1      |
+----------+------------------------+------------+
| lexicon  | lang [lexicon]         | oji        |
+----------+------------------------+------------+
| trans    | lang trans             | oji.fra    |
+----------+------------------------+------------+
| sent     | lang text sent         | oji.1.1    |
+----------+------------------------+------------+
| form     | lang [lexicon] form    | oji.aanii  |
+----------+------------------------+------------+
| xlexicon | lang trans [xlexicon]  | oji.fra    |
+----------+------------------------+------------+
| xtext    | lang trans xtext       | oji.fra.1  |
+----------+------------------------+------------+
| times    | lang text sent [times] | oji.1.1    |
+----------+------------------------+------------+

Values
------

The following tables describe the values associated with the attributes for
each record type. The second column gives an example of a name, for
attributes that are paired with names.

**Lang**

+----------+----------+----------------------------------------------+
| name     |          | the language name (recommended)              |
+----------+----------+----------------------------------------------+
| glot     |          | the 8-character glottolog code (recommended) |
+----------+----------+----------------------------------------------+
| iso3     |          | the 3-character ISO code (optional)          |
+----------+----------+----------------------------------------------+
| userom   |          | a romid (optional)                           |
+----------+----------+----------------------------------------------+
| text     | 1        | a text record                                |
+----------+----------+----------------------------------------------+
| trans    | fra      | translations into French (cob)               |
+----------+----------+----------------------------------------------+
| lexicon  |          | a lexicon record                             |
+----------+----------+----------------------------------------------+

**Rom**

+----------+----------+----------------------------------------------+
| u        | abcde    | Unicode string                               |
+----------+----------+----------------------------------------------+

**Text**

+----------+----------+----------------------------------------------+
| ty       |          | the type of text (book, page, etc)           |
+----------+----------+----------------------------------------------+
| ti       |          | title                                        |
+----------+----------+----------------------------------------------+
| de       |          | description                                  |
+----------+----------+----------------------------------------------+
| au       |          | author                                       |
+----------+----------+----------------------------------------------+
| ch       |          | children: space-separated textids            |
+----------+----------+----------------------------------------------+
| pdf      |          | pathname of a PDF file                       |
+----------+----------+----------------------------------------------+
| audio    |          | *fn* or *fn*:*start*:*end*                   |
+----------+----------+----------------------------------------------+
| video    |          | *fn* or *fn*:*start*:*end*                   |
+----------+----------+----------------------------------------------+
| xid      |          | an external identifier                       |
+----------+----------+----------------------------------------------+
| sent     | 1        | a sentence record                            |
+----------+----------+----------------------------------------------+

**Lexicon**

+----------+----------+----------------------------------------------+
| form     | aanii    | a form record                                |
+----------+----------+----------------------------------------------+

**Trans**

+----------+----------+----------------------------------------------+
| xlexicon |          | an xlexicon record                           |
+----------+----------+----------------------------------------------+
| xtext    | 1        | an xtext record                              |
+----------+----------+----------------------------------------------+

**Sent**

+----------+----------+----------------------------------------------+
| w        |          | space-seperated forms                        |
+----------+----------+----------------------------------------------+
| tr       |          | sentence translation                         |
+----------+----------+----------------------------------------------+
| times    |          | a times record                               |
+----------+----------+----------------------------------------------+

**Form**

+----------+----------+----------------------------------------------+
| ty       |          | the form type (word, inflected form, etc)    |
+----------+----------+----------------------------------------------+
| g        |          | gloss                                        |
+----------+----------+----------------------------------------------+
| c        |          | category (part of speech)                    |
+----------+----------+----------------------------------------------+
| pp       |          | parts                                        |
+----------+----------+----------------------------------------------+
| cf       |          | canonical form                               |
+----------+----------+----------------------------------------------+
| of       |          | orthographic form                            |
+----------+----------+----------------------------------------------+

 * The value for ``pp`` is a space-separated list of forms, representing unordered
   constituents of this word's form. No assumption is made about how
   parts are put together; in particular, it is not assumed that they are
   concatenated to create this word's form.

 * The property ``cf`` is used if this form is a spelling variant,
   dialectal variant, or the like. The canonical form is what it is a
   variant of.

 * The property ``of`` is used if this form represents a word
   sense. The orthographic form is the word of which it is a
   sense. For example, if the form ``cat.1`` represents the first
   sense of the word "cat", then ``cat.1`` has orthographic form
   ``cat``.

**XLexicon**

+----------+----------+----------------------------------------------+
| fg       | aanii    | word gloss                                   |
+----------+----------+----------------------------------------------+

**XText**

+----------+----------+----------------------------------------------+
| sg       | 1        | translation in the alt glossing language     |
+----------+----------+----------------------------------------------+

**Times**

+----------+----------+----------------------------------------------+
| t        | 1        | floating-point timestamp                     |
+----------+----------+----------------------------------------------+

 * Assigning value *f* to time *i* means that the boundary
   immediately preceding the *i*-th word (counting from zero) occurs
   *f* seconds from the beginning of the audio. To timestamp the right
   boundary of a word, insert a silent token ``<SIL>`` after it and
   timestamp the beginning of the silent token.

