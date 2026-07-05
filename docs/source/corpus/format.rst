
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
          g in a little village on a river there lived a cobbler
        sent.2
          w der Schuster war sehr arm
          g the cobbler was very poor
      text.3
        ti p2
        ty page
        sent.1
          w eines Tages begegnete der Schuster einen Bettler
          tr one day the cobbler met a beggar
          times
            0 1.495800
            2 1.939400
            5 2.783300
            7 3.326900
        sent.2
          w Ende
          tr the end
          times
            0 3.688200
            1 3.928300
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

Types
-----

A corpus consists of a set of **corpus objects** (**cobs**, for
short), organized hierarchically. A cob has **children**, which are
other cobs, and **properties**, which are strings.

Each cob and each property has a **name** (also called a *key*).
In memory, a cob is represented simply as a python dict, in which the keys are
the names of the cob's properties and children. The value associated
with an property name is the property's value (a string), and the
value associated with a child name is the child itself (a cob).

Each name consists of a **type** and an optional **identifier**, separated
by a period. For example, 'lang.deu' is a cob name that consists of
the type 'lang' and the identifier 'deu', whereas 'lexicon' is a cob
name that consists of the type 'lexicon' and no identifier. The
following provides a complete list of types that take identifiers,
indicating what kind of identifier each takes:

+----------+----------------+
| **Type** | **ID**         |
+----------+----------------+
| fg       | *form*         |
+----------+----------------+
| form     | *form*         |
+----------+----------------+
| idx      | *int*          |
+----------+----------------+
| lang     | *langid*       |
+----------+----------------+
| rom      | *romid*        |
+----------+----------------+
| sent     | *sentid*       |
+----------+----------------+
| sg       | *sentid*       |
+----------+----------------+
| trans    | *langid*       |
+----------+----------------+
| text     | *textid*       |
+----------+----------------+
| u        | *ASCII string* |
+----------+----------------+
| xtext    | *textid*       |
+----------+----------------+

Any given type occurs at only one place in the
hierarchy: each type has a unique **parent type**. The following is a
complete **signature**, listing all parent types and their child
types.

+----------+------------------------------------------------+
| **Type** | **Child types**                                |
+----------+------------------------------------------------+
| corpus   | lang, rom                                      |
+----------+------------------------------------------------+
| lang     | name, glot, iso3, userom, text, lexicon, trans |
+----------+------------------------------------------------+
| rom      |  u                                             |
+----------+------------------------------------------------+
| text     | ty, ti, de, au, ch, pdf, audio, video, sent    |
+----------+------------------------------------------------+
| lexicon  | form                                           |
+----------+------------------------------------------------+
| trans    | xlexicon, xtext                                |
+----------+------------------------------------------------+
| sent     | w, tr, times                                   |
+----------+------------------------------------------------+
| form     | fy, g, c, pp, cf, of                           |
+----------+------------------------------------------------+
| xlexicon | fg                                             |
+----------+------------------------------------------------+
| xtext    | sg                                             |
+----------+------------------------------------------------+
| times    | idx                                            |
+----------+------------------------------------------------+

The name 'corpus' never appears in a corpus file; it is included as a
name for the root of the hierarchy.

Each type also has a **level** in the hierarchy. To be precise, the
level of the root type, 'corpus', is 0, and every other type has a
level that is one greater than the level of its parent type.

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
| g              | sentence translation                         |
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

 * The value for ``pp`` is a list of forms, representing unordered
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

Because each type has a unique parent type, indentation is unnecessary
for reconstructing the structure. It is included
optionally for ease of reading. Each line is indented by
an amount corresponding to the level of the key type.
