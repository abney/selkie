
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

The corpus is read in as a nested dict, using :py:mod:`selkie.pyx.dct`.
The dicts are called **corpus objects** ("**cobs**", for
short). For example:

>>> from selkie.data import ex
>>> from selkie.corpus.corpus import open_cld_file
>>> fi = open_cld_file(ex('corp29.cld'))
>>> corpus = fi.contents['corp.corp29']
>>> deu = corpus['lang.deu']
>>> text3 = deu['text.3']
>>> sent32 = text3['sent.2']
>>> sent32
{'w': 'Ende', 'tr': 'the end', 'times': {'t.0': '3.688200', 't.1': '3.928300'}}

As usual, a dict associates **keys** with **values**.
If a key contains a period, the period divides the key into an
**attribute type** and **discriminator**. Otherwise, the entire key is
considered to be the attribute type. If the value is another object
(rather than a string), the attribute type doubles as the object
type.

For example, the key ``sent.2`` divides into type ``sent`` and
discriminator ``2``, and ``sent`` is the type of the value, which is
an object.

The object type in turn determines which attribute
types are legal within the object. In particular,
the legal attribute types for a ``sent`` are ``w``, ``tr``, and ``times``.
A ``times`` object, in turn, has only one legal attribute type, namely, ``t``.

The following is a
complete **signature**, listing all cob types and their attribute
types. The second column gives an example of a discriminator for the cob type.

+----------+-------------+--------------------------------------------------+
| **Type** | **Discrim** | **Attributes**                                   |
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

To reach any give cob, one follows a path of keys.
Concatenating the discriminators along that path gives the **pathname**
for the object that one reaches. To identify an object within the
corpus, the corpus discriminator may be omitted. The resulting
relative pathname is called the **item ID**. 
The pairing of object type and item
ID uniquely identifies the object in the corpus.

The following table gives information about discriminators and
item IDs. For each object type, it gives the parent type, an example
of the parent item ID, an example of the object's discriminator, and
the resulting item ID for the object.

+----------+-----------+---------------+-------------+------------+
| **Type** | **PType** | **PItemID**   | **Discrim** | **ItemID** |
+----------+-----------+---------------+-------------+------------+
| lang     | corp      |               | oji         | oji        | 
+----------+-----------+---------------+-------------+------------+
| rom      | corp      |               | gothic      | gothic     |
+----------+-----------+---------------+-------------+------------+
| text     | lang      | oji           | 1           | oji.1      |
+----------+-----------+---------------+-------------+------------+
| lexicon  | lang      | oji           |             | oji        |
+----------+-----------+---------------+-------------+------------+
| trans    | lang      | oji           | fra         | oji.fra    |
+----------+-----------+---------------+-------------+------------+
| sent     | text      | oji.1         | 1           | oji.1.1    |
+----------+-----------+---------------+-------------+------------+
| form     | lexicon   | oji           | aanii       | oji.aanii  |
+----------+-----------+---------------+-------------+------------+
| xlexicon | trans     | oji.fra       |             | oji.fra    |
+----------+-----------+---------------+-------------+------------+
| xtext    | trans     | oji.fra       | 1           | oji.fra.1  |
+----------+-----------+---------------+-------------+------------+
| times    | sent      | oji.1.1       |             | oji.1.1    |
+----------+-----------+---------------+-------------+------------+

Values
------

The following tables describe the values associated with the attributes of
each object type. The second column gives an example of a discriminator for the attribute.

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
| text     | 1        | a cob of type 'text'                         |
+----------+----------+----------------------------------------------+
| trans    | fra      | translations into French (cob)               |
+----------+----------+----------------------------------------------+
| lexicon  |          | a cob of type 'lexicon'                      |
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
| sent     | 1        | a cob of type 'sent'                         |
+----------+----------+----------------------------------------------+

**Lexicon**

+----------+----------+----------------------------------------------+
| form     | aanii    | a cob of type 'form'                         |
+----------+----------+----------------------------------------------+

**Trans**

+----------+----------+----------------------------------------------+
| xlexicon |          | a cob of type 'xlexicon'                     |
+----------+----------+----------------------------------------------+
| xtext    | 1        | a cob of type 'xtext'                        |
+----------+----------+----------------------------------------------+

**Sent**

+----------+----------+----------------------------------------------+
| w        |          | space-seperated forms                        |
+----------+----------+----------------------------------------------+
| tr       |          | sentence translation                         |
+----------+----------+----------------------------------------------+
| times    |          | a 'times' cob                                |
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

