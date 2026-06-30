
CLD Format (v27)
================

Concrete example
----------------

Beginning with a concrete example should make an abstract definition
more comprehensible::

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
          g one day the cobbler met a beggar
          times
            0 1.495800
            2 1.939400
            5 2.783300
            7 3.326900
        sent.2
          w Ende
          g the end
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

Description
-----------

The format is line-oriented. Leading and trailing whitespace is
insignificant. There are two sorts of line: a **node line**
contains no space character (after removing leading and trailing
whitespace), whereas an **attribute line** does contain a space
character. The first space character divides the attribute into *key*\/}
and *value*.

A node name consists of a *type* and, optionally, an ID,
separated by a period. For example, ``lang.deu`` is a node
name with type ``lang`` and ID ``deu``.
Each type has a **level** in a
hierarchical structure, corresponding to the amount of indentation in
the example given above. For example, ``lang`` is at level 0, ``text``
is at level 1, and ``sent`` is at level 2.

An attribute has no intrinsic level, but in context
the attribute's level is one greater than that of the most recent
preceding node line, which represents the node that possesses the
attribute.

In a CLD corpus, the node names and their levels are as follows.

+----------------+---+
| lang.<langid>  | 0 |
+----------------+---+
| rom.<romid>    | 0 |
+----------------+---+
| text.<textid>  | 1 |
+----------------+---+
| lexicon        | 1 |
+----------------+---+
| trans.<langid> | 1 |
+----------------+---+
| sent.<sentid>  | 2 |
+----------------+---+
| form.<form>    | 2 |
+----------------+---+
| xlexicon       | 2 |
+----------------+---+
| xtext.<textid> | 2 |
+----------------+---+
| times          | 3 |
+----------------+---+

When a file is loaded into memory, each node is
represented as a dict. The dict entries correspond to the children of
the node. If the child is a subnode, the key is the node name and the
value is a dict representing the subnode. If the child is a datum, the
key and value are the key and value of the datum.

For nodes of most types, there are constraints on
legal keys, as follows.

**Language**

+----------------+----------------------------------------------+
| name           | the language name (recommended)              |
+----------------+----------------------------------------------+
| glot           | the 8-character glottolog code (recommended) |
+----------------+----------------------------------------------+
| iso3           | the 3-character ISO code (optional)          |
+----------------+----------------------------------------------+
| rom            | a romid (optional)                           |
+----------------+----------------------------------------------+
| text.<textid>  | a text node                                  |
+----------------+----------------------------------------------+
| xtext.<textid> | an xtext node                                |
+----------------+----------------------------------------------+
| lexicon        | a lexicon node                               |
+----------------+----------------------------------------------+

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
| sent.<sentid>  | a sent node                                  |
+----------------+----------------------------------------------+

**Lexicon**

+----------------+----------------------------------------------+
| form.<form>    | a form node                                  |
+----------------+----------------------------------------------+

**Trans**

+----------------+----------------------------------------------+
| xlexicon       | an xlexicon node                             |
+----------------+----------------------------------------------+
| xtext.<textid> | an xtext node                                |
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

 * The attribute ``cf`` is used if this form is a spelling variant,
   dialectal variant, or the like. The canonical form is what it is a
   variant of.

 * The attribute ``of`` is used if this form represents a word
   sense. The orthographic form is the word of which it is a
   sense. For example, if the form ``cat.1`` represents the first
   sense of the word "cat", then ``cat.1`` has orthographic form
   ``cat``.

**XLexicon**

+----------------+----------------------------------------------+
| form.<form>    | word gloss                                   |
+----------------+----------------------------------------------+

**XText**

+----------------+----------------------------------------------+
| sent.<sentid>  | translation in the alt glossing language     |
+----------------+----------------------------------------------+

**Times**

+----------------+----------------------------------------------+
| idx.<int>      | floating-point timestamp                     |
+----------------+----------------------------------------------+

 * Assigning value *f* to index *i* means that the boundary
   immediately preceding the *i*-th word (counting from zero) occurs
   *f* seconds from the beginning of the audio. To timestamp the right
   boundary of a word, insert a silent token ``<SIL>`` after it and
   timestamp the beginning of the silent token.
