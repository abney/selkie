
File format
===========

*This is CLD format v29.*

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
        deu.eines
          pp ein -gen
          g of a(n)
        deu.ein
          g a(n)
        deu.-gen
          g (genitive case)
        deu.Schuster
          g cobbler

The indentation is optional; it makes the structure easier to see.

Types
-----

The corpus is read in as a nested dict, using :py:mod:`selkie.pyx.dct`.
The dicts are called **corpus objects** ("**cobs**", for
short). For example, the following is a fragment of the dict for our
running example corpus::

   {...
    'sent.2': {
      'w': 'Ende',
      'tr': 'the end',
      'times': {
        't.0': '3.688200',
	't.1': '3.928300'}}}

As usual, a dict associates **keys** with **values**.
If a key contains a period, the period divides the key into **prefix**
and **discriminator**. Otherwise, the entire key is considered to be the prefix.

If a key *K* has a sub-cob as value, then the prefix of *K* is treated
as a **parent type**, and it determines the
the legal prefixes (**attribute types**) for keys within the sub-cob.
For example, ``sent`` is considered to be parent type for the dict
that is the value of ``sent.2``, and the legal attribute types for a sent
are ``w``, ``tr``, and ``times``. In turn, ``times`` is the parent
type for its value (a dict), and the only legal attribute type is ``t``.

The following is a
complete **signature**, listing all parent types and their attribute
types. It also indicates what kind of discriminator the parent type
takes, if any.
(Note: the type ``corp`` never appears in a corpus file; it is included as a
name for the root of the hierarchy.)

+----------+-------------+--------------------------------------------------+
| **Type** | **Descrim** | **Attributes**                                   |
+----------+-------------+--------------------------------------------------+
| corp     |             | lang, rom                                        |
+----------+-------------+--------------------------------------------------+
| lang     | *langid*    | name, glot, iso3, userom, text, lexicon, trans   |
+----------+-------------+--------------------------------------------------+
| rom      | *romid*     | u                                                |
+----------+-------------+--------------------------------------------------+
| text     | *textid*    | ty, ti, de, au, ch, pdf, audio, video, sent, xid |
+----------+-------------+--------------------------------------------------+
| lexicon  |             | form                                             |
+----------+-------------+--------------------------------------------------+
| trans    | *langid*    | xlexicon, xtext                                  |
+----------+-------------+--------------------------------------------------+
| sent     | *sentid*    | w, tr, times                                     |
+----------+-------------+--------------------------------------------------+
| form     | *form*      | fy, g, c, pp, cf, of                             |
+----------+-------------+--------------------------------------------------+
| xlexicon | *langid*    | fg                                               |
+----------+-------------+--------------------------------------------------+
| xtext    | *langid*    | sg                                               |
+----------+-------------+--------------------------------------------------+
| times    |             | t                                                |
+----------+-------------+--------------------------------------------------+

Values
------

The following tables describe the values associated with the attributes of
each parent type. The second column again indicates the kind of discriminator.

**Lang**

+---------+----------+----------------------------------------------+
| name    |          | the language name (recommended)              |
+---------+----------+----------------------------------------------+
| glot    |          | the 8-character glottolog code (recommended) |
+---------+----------+----------------------------------------------+
| iso3    |          | the 3-character ISO code (optional)          |
+---------+----------+----------------------------------------------+
| userom  |          | a romid (optional)                           |
+---------+----------+----------------------------------------------+
| text    | *textid* | a cob of type 'text'                         |
+---------+----------+----------------------------------------------+
| trans   | *langid* | translations into *langid* (cob)             |
+---------+----------+----------------------------------------------+
| lexicon |          | a cob of type 'lexicon'                      |
+---------+----------+----------------------------------------------+

**Rom**

+---------+----------+----------------------------------------------+
| u       | *ASCII*  | Unicode string                               |
+---------+----------+----------------------------------------------+

**Text**

+---------+----------+----------------------------------------------+
| ty      |          | the type of text (book, page, etc)           |
+---------+----------+----------------------------------------------+
| ti      |          | title                                        |
+---------+----------+----------------------------------------------+
| de      |          | description                                  |
+---------+----------+----------------------------------------------+
| au      |          | author                                       |
+---------+----------+----------------------------------------------+
| ch      |          | children: space-separated textids            |
+---------+----------+----------------------------------------------+
| pdf     |          | pathname of a PDF file                       |
+---------+----------+----------------------------------------------+
| audio   |          | *fn* or *fn*:*start*:*end*                   |
+---------+----------+----------------------------------------------+
| video   |          | *fn* or *fn*:*start*:*end*                   |
+---------+----------+----------------------------------------------+
| xid     |          | an external identifier                       |
+---------+----------+----------------------------------------------+
| sent    | *sentid* | a cob of type 'sent'                         |
+---------+----------+----------------------------------------------+

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
