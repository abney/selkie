
Introduction
============

Overview
--------

Panlex is a relational database representing lexical information for
the world's languages.  The information is drawn typically from
bilingual dictionaries.

Consider an illustrative (fake) entry:

   moo
      1. (n) A kind of flatbread.  eng:flatbread
      2. (n) Money.  eng:money
      3. (v) To crush.  eng:pancake

In panlex, each numbered subentry is a **lexeme**, and the dictionary
is simply a collection of lexemes:

   1. xyz:moo(n) eng:flatbread(n) - A kind of flatbread.
   2. xyz:moo(n) eng:money(n) - Money.
   3. xyz:moo(v) eng:pancake(v) - To crush.

A lexeme expressed using a particular word, such as "[3]xyz:moo(v)", is
a **word sense**.

A lexeme in Panlex typically contains two word senses, one in the
target language and one in the glossing language.
However, a lexeme in a multi-lingual dictionary contains one word sense
for each language of the dictionary.

Definitions and semantic fields are associated with lexemes, but parts
of speech and properties are intrinsic to word senses and may differ
between a target word and its gloss.

In more detail, the main data types are as follows.

 * A **dictionary** (which Panlex calls a "source" or "approver")
   consists of a list of lexemes, plus metadata.
   A dictionary is represented by a **dictionary ID (DID).**
   Dictionary metadata is given in the table ``ap``.

 * A **lexeme entry** (which Panlex calls a "meaning") is represented by
   a **lexeme ID (LXID).**  I use the term *lexeme*
   rather than *meaning* because the object in question is dictionary-specific.
   No attempt is made to identify
   sameness of meaning across dictionaries.
   The association between LXID and dictionary is given in
   the ``mn`` table.
   An LXID may also be associated with a definition, in the ``df``
   table, or with a semantic domain, in the ``dm`` table.

 * A **sense** (which Panlex calls a "denotation") is a word
   used to express a particular meaning: that is, a word paired with a
   lexeme.  A sense has a part of speech ("word class"), and may have properties.
   A sense is represented by
   a **sense ID (sid).**  The word and lexeme for
   a given SID are specified in the ``dn`` table.  The part of
   speech is given in the ``wc`` table.  The list of properties
   is given in the table ``md``.

 * An **expression** is a piece of text that is explicitly labeled with
   the language it is written in, like ``xyz:moo``.
   An expression is represented in the
   database by an **expression ID (EXID).**
   The ``ex`` table associates an EXID with a string and a language variety.

 * A **language variety** may be documented in multiple
   dictionaries, and a dictionary may document multiple language varieties.
   A language variety is represented by a **language variety ID (LVID).**
   The Panlex code for a language variety is of form ``abc-123``,
   consisting of a three-letter **ISO code** for the language and a
   three-digit **variety code.**  The association between LVIDs
   and DIDs is given in the ``av`` table.  The ISO code and
   variety code are given in the ``lv`` table.


Data types
----------

The data-type specifications used in the data tables are as follows.
The most important are:

 * *lvid* - Language variety
 * *did* - Dictionary
 * *lxid* - Lexeme
 * *sid* - Sense
 * *exid* - Expression

Supporting data types are as follows.
 * *bool* - t or f.
 * *num* - A number.
 * *str* - A string.
 * *char* - A Unicode code point.
 * *date* - A date.
 * *url* - A URL.
 * *iso* - A 3-letter ISO language code.
 * *vc* - A 3-digit Panlex variety code.
 * *lic2* - A 2-letter license code.
 * *fm* - A file format (?)


Language varieties
------------------

Languages are identified by 3-digit ISO codes.  A language variety is
a specialization.  The varieties of a given language are numbered from
0: ``eng0``, ``eng1``, etc.  There is also a numeric ID for each
language variety.  For example, variety 187 is ``eng0``.

+--------------------------------------------------------------------------+
| Table ?                                                                  |
+--------+--------+--------------------------------------------------------+
| ``lv`` | *lvid* | The language variety                                   |
+--------+--------+--------------------------------------------------------+
| ``lc`` | *iso*  | Its ISO language code                                  |
+--------+--------+--------------------------------------------------------+
| ``vc`` | *vc*   | Language-variety sequence number (from 0)              |
+--------+--------+--------------------------------------------------------+
| ``sy`` | *bool* | ?                                                      |
+--------+--------+--------------------------------------------------------+
| ``am`` | *bool* | ?                                                      |
+--------+--------+--------------------------------------------------------+
| ``ex`` | *exid* | The name of the variety                                |
+--------+--------+--------------------------------------------------------+

Names are usually given in
the variety (e.g., the name for German is given as "Deutsch."
But sometimes names are given in English.

Additional information about language varieties is given in tables
``cp`` and ``cu``.  I don't know what these tables contain,
possibly punctuation characters in the language.

+--------------------------------------------------------------------------+
| Table ``cp``                                                             |
+--------+--------+--------------------------------------------------------+
| ``lv`` | *lvid* | A language variety                                     |
+--------+--------+--------------------------------------------------------+
| ``c0`` | *char* | A code point                                           |
+--------+--------+--------------------------------------------------------+
| ``c1`` | *char* | A code point                                           |
+--------+--------+--------------------------------------------------------+

+---------------------------------------------------------------------------+
| Table ``cu``                                                              |
+---------+--------+--------------------------------------------------------+
| ``lv``  | *lvid* | A language variety                                     |
+---------+--------+--------------------------------------------------------+
| ``c0``  | *char* | A code point                                           |
+---------+--------+--------------------------------------------------------+
| ``c1``  | *char* | A code point                                           |
+---------+--------+--------------------------------------------------------+
| ``loc`` | ?      | ?                                                      |
+---------+--------+--------------------------------------------------------+
| ``vb``  | ?      |                                                        |
+---------+--------+--------------------------------------------------------+

Values for ``vb`` include ``pun``, ``priv``, ``aux``,
``cit:fin:pri``, ``cit:kom:pri``.

Dictionaries
------------

A dictionary contains a list of lexemes (see above).
Metadata information is contained in the table ``ap``.

+--------------------------------------------------------------------------+
| Table ``ap``                                                             |
+--------+--------+--------------------------------------------------------+
| ``ap`` | *did*  | The dictionary ID                                      |
+--------+--------+--------------------------------------------------------+
| ``dt`` | *date* | Registration date                                      |
+--------+--------+--------------------------------------------------------+
| ``tt`` | *str*  | A short identifier, e.g. ``eng-ciw:Weshki``            |
+--------+--------+--------------------------------------------------------+
| ``ur`` | *url*  | The URL                                                |
+--------+--------+--------------------------------------------------------+
| ``bn`` | *str*  | ISBN, perhaps?                                         |
+--------+--------+--------------------------------------------------------+
| ``au`` | *str*  | Author                                                 |
+--------+--------+--------------------------------------------------------+
| ``ti`` | *str*  | Title                                                  |
+--------+--------+--------------------------------------------------------+
| ``pb`` | *str*  | Publisher                                              |
+--------+--------+--------------------------------------------------------+
| ``yr`` | *str*  | Year of publication                                    |
+--------+--------+--------------------------------------------------------+
| ``uq`` | *num*  | Quality?                                               |
+--------+--------+--------------------------------------------------------+
| ``ui`` | *did*  | Appears to be the same as ``ap``                       |
+--------+--------+--------------------------------------------------------+
| ``ul`` | *str*  | Some kind of summary line                              |
+--------+--------+--------------------------------------------------------+
| ``li`` | *lic2* | An IP license code                                     |
+--------+--------+--------------------------------------------------------+
| ``ip`` | *str*  | An IP license statement                                |
+--------+--------+--------------------------------------------------------+
| ``co`` | *str*  | Company?                                               |
+--------+--------+--------------------------------------------------------+
| ``ad`` | *str*  | Email address                                          |
+--------+--------+--------------------------------------------------------+

A dictionary documents one or more language varieties.

+--------------------------------------------------------------------------+
| Table ``av``                                                             |
+--------+--------+--------------------------------------------------------+
| ``ap`` | *did*  | The dictionary                                         |
+--------+--------+--------------------------------------------------------+
| ``lv`` | *lvid* | A variety that it documents                            |
+--------+--------+--------------------------------------------------------+

The ``apli`` table appears to map 2-letter license codes to
3-letter codes.  I don't know what the codes mean.

+--------------------------------------------------------------------------+
| Table ``apli``                                                           |
+--------+--------+--------------------------------------------------------+
| ``id`` | *num*  | ID for the assignment (?)                              |
+--------+--------+--------------------------------------------------------+
| ``li`` | *lic2* | 2-letter code                                          |
+--------+--------+--------------------------------------------------------+
| ``pl`` | ?      | 3-letter code                                          |
+--------+--------+--------------------------------------------------------+

The table ``af`` appears to indicate the file format of the original
source for the dictionary.

+--------------------------------------------------------------------------+
| Table ``af``                                                             |
+--------+--------+--------------------------------------------------------+
| ``ap`` | *did*  | The dictionary                                         |
+--------+--------+--------------------------------------------------------+
| ``fm`` | *fm*   | The format                                             |
+--------+--------+--------------------------------------------------------+

Example values for format are ``html``,
``html-curl``, ``pdf-lock/encrypt``, ``txt``, ``txt-wb``,
``xml``, ``pdf-img``, and ``db``.

The ``fm`` table appears to contain information about "fm" codes.

+--------------------------------------------------------------------------+
| Table ``fm``                                                             |
+--------+--------+--------------------------------------------------------+
| ``fm`` | *fm*   | Format ID?                                             |
+--------+--------+--------------------------------------------------------+
| ``tt`` | *str*  | Dictionary name??                                      |
+--------+--------+--------------------------------------------------------+
| ``md`` | *str*  | ?                                                      |
+--------+--------+--------------------------------------------------------+

The table ``aped`` appears to contain Panlex processing information
for dictionaries.

+---------------------------------------------------------------------------+
| Table ``aped``                                                            |
+---------+--------+--------------------------------------------------------+
| ``ap``  | *did*  | The dictionary                                         |
+---------+--------+--------------------------------------------------------+
| ``q``   | *bool* | ?                                                      |
+---------+--------+--------------------------------------------------------+
| ``cx``  | *num*  | ?                                                      |
+---------+--------+--------------------------------------------------------+
| ``im``  | *bool* | ?                                                      |
+---------+--------+--------------------------------------------------------+
| ``re``  | *bool* | ?                                                      |
+---------+--------+--------------------------------------------------------+
| ``ed``  | ?      | ?                                                      |
+---------+--------+--------------------------------------------------------+
| ``fp``  | ?      | Short name?                                            |
+---------+--------+--------------------------------------------------------+
| ``etc`` | *str*  | What remains to be done?                               |
+---------+--------+--------------------------------------------------------+

The ``fp`` codes appear to indicate the documented
varieties and a one-word abbreviation of the title.  E.g., ``eng-ciw-Weshki``.

Lexemes
-------

A dictionary is a list of lexemes.  Panlex calls them "meanings."

+--------------------------------------------------------------------------+
| Table ``mn``                                                             |
+--------+--------+--------------------------------------------------------+
| ``mn`` | *lxid* | The lexical entry                                      |
+--------+--------+--------------------------------------------------------+
| ``ap`` | *did*  | The dictionary it belongs to                           |
+--------+--------+--------------------------------------------------------+

The ``df`` table appears to represent definitions or explanations.
Not all dictionaries have them.

+--------------------------------------------------------------------------+
| Table ``df``                                                             |
+--------+--------+--------------------------------------------------------+
| ``df`` | *num*  | The definition ID (?)                                  |
+--------+--------+--------------------------------------------------------+
| ``mn`` | *lxid* | The lexical entry                                      |
+--------+--------+--------------------------------------------------------+
| ``lv`` | *lvid* | The language variety of the definition text            |
+--------+--------+--------------------------------------------------------+
| ``tt`` | *str*  | The definition text                                    |
+--------+--------+--------------------------------------------------------+

The ``dm`` table appears to represent the semantic domain of an
entry.  Not all dictionaries include it.

+--------------------------------------------------------------------------+
| Table ``dm``                                                             |
+--------+--------+--------------------------------------------------------+
| ``dm`` | *num*  | The semantic domain ID (?)                             |
+--------+--------+--------------------------------------------------------+
| ``mn`` | *lxid* | The lexical entry                                      |
+--------+--------+--------------------------------------------------------+
| ``ex`` | *exid* | The name of the semantic domain                        |
+--------+--------+--------------------------------------------------------+

An additional table, ``mi``, also provides information about
lexemes.  I have not been able to determine what it
represents.  The values in the ``tt``
field are usually IDs of some sort, but occasionally English words.

+--------------------------------------------------------------------------+
| Table ``mi``                                                             |
+--------+--------+--------------------------------------------------------+
| ``mn`` | *lxid* | The lexical entry                                      |
+--------+--------+--------------------------------------------------------+
| ``tt`` | ?      | ?                                                      |
+--------+--------+--------------------------------------------------------+

Senses
------

A sense combines a lexeme with an a word (expression).

+--------------------------------------------------------------------------+
| Table ``dn``                                                             |
+--------+--------+--------------------------------------------------------+
| ``dn`` | *sid*  | The sense                                              |
+--------+--------+--------------------------------------------------------+
| ``mn`` | *lxid* | The lexeme it belongs to                               |
+--------+--------+--------------------------------------------------------+
| ``ex`` | *exid* | The contents                                           |
+--------+--------+--------------------------------------------------------+

A part of speech may be assigned to a sense.

+--------------------------------------------------------------------------+
| Table ``wc``                                                             |
+--------+--------+--------------------------------------------------------+
| ``wc`` | *num*  | An ID for the assignment?                              |
+--------+--------+--------------------------------------------------------+
| ``dn`` | *sid*  | The sense                                              |
+--------+--------+--------------------------------------------------------+
| ``ex`` | *exid* | The part of speech                                     |
+--------+--------+--------------------------------------------------------+

The ``wcex`` table is a convenience listing of the expressions
that are used as parts of speech.

+--------------------------------------------------------------------------+
| Table ``wcex``                                                           |
+--------+--------+--------------------------------------------------------+
| ``ex`` | *exid* | The part-of-speech expression                          |
+--------+--------+--------------------------------------------------------+
| ``tt`` | *str*  | The part-of-speech string                              |
+--------+--------+--------------------------------------------------------+

A sense may have properties (key-value pairs).  These are used
for declension classes, valency, etc.

+--------------------------------------------------------------------------+
| Table ``md``                                                             |
+--------+--------+--------------------------------------------------------+
| ``md`` | *num*  | An ID for the assignment?                              |
+--------+--------+--------------------------------------------------------+
| ``dn`` | *sid*  | The sense                                              |
+--------+--------+--------------------------------------------------------+
| ``vb`` | *str*  | The key                                                |
+--------+--------+--------------------------------------------------------+
| ``vl`` | *str*  | The value                                              |
+--------+--------+--------------------------------------------------------+

Expressions
-----------

Expressions are used not only for words in dictionaries but also for
parts of speech and dictionary names.
An expression is a word in a particular language variety.  It pairs a
string with a language-variety ID.

+--------------------------------------------------------------------------+
| Table ``ex``                                                             |
+--------+--------+--------------------------------------------------------+
| ``ex`` | *exid* | The expression                                         |
+--------+--------+--------------------------------------------------------+
| ``lv`` | *lvid* | Its language variety                                   |
+--------+--------+--------------------------------------------------------+
| ``tt`` | *str*  | Its string                                             |
+--------+--------+--------------------------------------------------------+
| ``td`` | *str*  | A "degraded text" version (lowercase letters + digits) |
+--------+--------+--------------------------------------------------------+
