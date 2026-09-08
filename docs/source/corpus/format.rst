
File format
===========

*This is CLD format v27.*

Concrete example
----------------

Having a concrete example in mind will make it easier to discuss the
general definition. Here is an example of a file in CLD format::

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

Types
-----

A corpus consists of a set of **corpus objects** ("**cobs**", for
short), organized hierarchically. Conceptually, a cob has
**sub-cobs**, which are themselves cobs, and **properties**, which are strings. Cobs are
implemented simply as python dicts, whose (key, value) items represent
the properties and sub-cobs. An item (key, value) represents a
property if the value is a string, and it represents a child if the
value is another dict. The key is thought of as a name for the
property or sub-cob. For example, the following is a fragment of our
running example corpus::

   {...
    'sent.2': {
      'w': 'Ende',
      'tr': 'the end',
      'times': {
        't.0': '3.688200',
	't.1': '3.928300'}}}

Each key consists of a **type** and an optional **identifier**, separated
by a period. For example, 'lang.deu' is a key that consists of
the type 'lang' and the identifier 'deu', whereas 'lexicon' is a key
that consists of the type 'lexicon' and no identifier. The
following provides a complete list of types that take identifiers,
indicating what kind of identifier each takes:

+----------+----------------+-------------------------------------------+
| **Type** | **ID**         | **Descr**                                 |
+----------+----------------+-------------------------------------------+
| fg       | *form*         | Form gloss in alt glossing language       |
+----------+----------------+-------------------------------------------+
| form     | *form*         | A form                                    |
+----------+----------------+-------------------------------------------+
| lang     | *langid*       | A language                                |
+----------+----------------+-------------------------------------------+
| rom      | *romid*        | A romanization                            |
+----------+----------------+-------------------------------------------+
| sent     | *sentid*       | A sentence                                |
+----------+----------------+-------------------------------------------+
| sg       | *sentid*       | A sentence gloss in alt glossing language |
+----------+----------------+-------------------------------------------+
| t        | *int*          | A time                                    |
+----------+----------------+-------------------------------------------+
| trans    | *langid*       | An alt glossing language                  |
+----------+----------------+-------------------------------------------+
| text     | *textid*       | A text                                    |
+----------+----------------+-------------------------------------------+
| u        | *ASCII string* | A unicode string                          |
+----------+----------------+-------------------------------------------+
| xtext    | *textid*       | A text in an alt glossing language        |
+----------+----------------+-------------------------------------------+

The following is a
complete **signature**, listing all parent types and their attributes.

+----------+--------------------------------------------------+
| **Type** | **Attributes**                                   |
+----------+--------------------------------------------------+
| corp     | lang, rom                                        |
+----------+--------------------------------------------------+
| lang     | name, glot, iso3, userom, text, lexicon, trans   |
+----------+--------------------------------------------------+
| rom      |  u                                               |
+----------+--------------------------------------------------+
| text     | ty, ti, de, au, ch, pdf, audio, video, sent, xid |
+----------+--------------------------------------------------+
| lexicon  | form                                             |
+----------+--------------------------------------------------+
| trans    | xlexicon, xtext                                  |
+----------+--------------------------------------------------+
| sent     | w, tr, times                                     |
+----------+--------------------------------------------------+
| form     | fy, g, c, pp, cf, of                             |
+----------+--------------------------------------------------+
| xlexicon | fg                                               |
+----------+--------------------------------------------------+
| xtext    | sg                                               |
+----------+--------------------------------------------------+
| times    | t                                                |
+----------+--------------------------------------------------+

The type 'corp' never appears in a corpus file; it is included as a
name for the root of the hierarchy.

Values
------

The following tables describe the values associated with the keys of
each cob type.

**Lang**

+----------------+----------------------------------------------+
| name           | the language name (recommended)              |
+----------------+----------------------------------------------+
| glot           | the 8-character glottolog code (recommended) |
+----------------+----------------------------------------------+
| iso3           | the 3-character ISO code (optional)          |
+----------------+----------------------------------------------+
| userom         | a romid (optional)                           |
+----------------+----------------------------------------------+
| text.<textid>  | a cob of type 'text'                         |
+----------------+----------------------------------------------+
| trans.<langid> | a cob of type 'trans'                        |
+----------------+----------------------------------------------+
| lexicon        | a cob of type 'lexicon'                      |
+----------------+----------------------------------------------+

 * The value of e.g. 'trans.fra' is a trans object containing
   alternative glosses in French.

**Rom**

+----------------+----------------------------------------------+
| u.<ASCII>      | Unicode string                               |
+----------------+----------------------------------------------+

**Text**

+----------------+----------------------------------------------+
| ty             | the type of text (book, page, etc)           |
+----------------+----------------------------------------------+
| ti             | title                                        |
+----------------+----------------------------------------------+
| de             | description                                  |
+----------------+----------------------------------------------+
| au             | author                                       |
+----------------+----------------------------------------------+
| ch             | children: space-separated textids            |
+----------------+----------------------------------------------+
| pdf            | pathname of a PDF file                       |
+----------------+----------------------------------------------+
| audio          | *fn* or *fn*:*start*:*end*                   |
+----------------+----------------------------------------------+
| video          | *fn* or *fn*:*start*:*end*                   |
+----------------+----------------------------------------------+
| xid            | an external identifier                       |
+----------------+----------------------------------------------+
| sent.<sentid>  | a cob of type 'sent'                         |
+----------------+----------------------------------------------+

**Lexicon**

+----------------+----------------------------------------------+
| form.<form>    | a cob of type 'form'                         |
+----------------+----------------------------------------------+

**Trans**

+----------------+----------------------------------------------+
| xlexicon       | a cob of type 'xlexicon'                     |
+----------------+----------------------------------------------+
| xtext.<textid> | a cob of type 'xtext'                        |
+----------------+----------------------------------------------+

**Sent**

+----------------+----------------------------------------------+
| w              | space-seperated forms                        |
+----------------+----------------------------------------------+
| tr             | sentence translation                         |
+----------------+----------------------------------------------+
| times          | a times node                                 |
+----------------+----------------------------------------------+

**Form**

+----------------+----------------------------------------------+
| ty             | the form type (word, inflected form, etc)    |
+----------------+----------------------------------------------+
| g              | gloss                                        |
+----------------+----------------------------------------------+
| c              | category (part of speech)                    |
+----------------+----------------------------------------------+
| pp             | parts                                        |
+----------------+----------------------------------------------+
| cf             | canonical form                               |
+----------------+----------------------------------------------+
| of             | orthographic form                            |
+----------------+----------------------------------------------+

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

+----------------+----------------------------------------------+
| fg.<form>      | word gloss                                   |
+----------------+----------------------------------------------+

**XText**

+----------------+----------------------------------------------+
| sg.<sentid>    | translation in the alt glossing language     |
+----------------+----------------------------------------------+

**Times**

+----------------+----------------------------------------------+
| t.<int>        | floating-point timestamp                     |
+----------------+----------------------------------------------+

 * Assigning value *f* to time *i* means that the boundary
   immediately preceding the *i*-th word (counting from zero) occurs
   *f* seconds from the beginning of the audio. To timestamp the right
   boundary of a word, insert a silent token ``<SIL>`` after it and
   timestamp the beginning of the silent token.

File format
-----------

The file format is line-oriented. Leading and trailing whitespace is
insignificant. There are two sorts of line: a **cob line**
contains no space characters (after removing leading and trailing
whitespace), whereas an **property line** does contain at least one space
character. The first space character divides the property line into
the **property name** and **property value**.

The lines of the file correspond exactly to the key-value pairs of the
cobs, viewed as python dicts. A subordinate cob produces a line with a
key (the cob name) but no value. In lieu of a value, the
key-value pairs of the subordinate cob are enumerated recursively, producing
additional lines.

Indentation is ignored when reconstructing the structure; its only
purpose is for ease of reading. Each line is attached to the most
recent object for which its key is valid. (See the table of attributes
above.)

Corpus files are represented by the class ``File``. It provides
convenience methods for loading and saving files, and reading to and
writing from open streams. Otherwise, it behaves like a proxy for its
root cob.

The file format is explicitly represented by a ``Format`` object,
which provides two methods. The method ``decode()`` takes a string and
converts it to a python dict representing the root cob, and the
method ``encode()`` does the reverse computation.
The format that we have been considering is called CLD format. There
is also an alternative JSON format, whose decoder is just ``json.loads()`` and
whose encoder is just ``json.dumps()``.
