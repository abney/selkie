
Ethnologue language listing
***************************

Overview
--------

The database in selkie.data.langdb is compiled by merging data from
the *Ethnologue,* from the Library of Congress's official
ISO 639-2 database, and from Panlex.
It uses the iso-639-2 and iso-639-3 packages.

The database is called languages::

   >>> from selkie.data.langdb import languages

The information in languages exactly reflects the published
databases, with the following exceptions:

 * In the published databases, retired codes had no entry for scope
   or type, with the exception of one retired code, which had
   scope-type of IL (living language).  For the sake of
   uniformity, I have assigned all retired codes scope 'R' and
   type 'R'.

 * In the published databases, the names field was filled
   only if the language had multiple names, in which case names
   included the reference name.  For the sake of uniformity, names
   now always includes the reference name, and may be a singleton list
   containing only the reference name.  Inverted names have been
   treated similarly.

Language codes
--------------

Code sets
.........

The standard three-letter language codes are ISO 639-3 codes.  There
are several other code sets in the ISO 639 family.

 * ISO 639-1: These are the standard two-letter language codes.
   Only 184 languages have a 639-1 code.

 * ISO 639-2: These were created for librarians.  418 languages
   have a 639-2 code.  20 languages have two different 639-2 codes: 
   a "bibliographic" code (639-2/B) and a "terminological" code (639-2/T).
   The Library of Congress is the registration authority.

 * ISO 639-2/B: The bibliographic version of 639-2 codes.
   These do not always agree with 639-3.

 * ISO 639-2/T: The terminological version of 639-2 codes.  These
   constitute a subset of 639-3.

 * ISO 639-3: The standard three-letter language codes.  SIL is the
   registration authority.  These extend the 639-2/T codes to 8121 languages.

 * ISO 639-5: An extension to 639-2 to cover language groupings.
   The Library of Congress is the registration authority.

Access by code
..............

The database can be accessed by ISO-639-3 code to get a language::

   >>> print(languages['spa'])
   Code:      spa
   Code2B:    spa
   Code2T:    spa
   Code1:     es
   Type:      Living
   Scope:     Language
   RefName:   Spanish
   Name:      Spanish
   Varieties: 
   Dicts:     

The four codes listed are 639-3, 639-2/B, 639-2/T, and 639-1, in that order.

Language instances
------------------

Although one accesses languages as a table, one iterates over it
as a list of languages::

   >>> len(languages)
   8282
   >>> sum(1 for lang in languages if lang.code2b != lang.code2t)
   20

A language instance has the following members:

 * code —  The 639-3 language code (a string).

 * code2b —  The 639-2/B language code, or None.

 * code2t —  The 639-2/T language code, or None.

 * code1 —  The 639-1 language code, or None.

 * scope —  The value is 'I' for individual language,
   'M' for macrolanguage, 'S' for special code, and 'R'
   for retired codes.
   The special codes are used when one needs a code for something that is
   not actually a language.  They are 'mis' for an uncoded language, 'mul'
   when the thing to be coded contains multiple different languages, 'und'
   when the language is undetermined, and 'zxx' when the thing to
   be coded does not actually have linguistic content.

 * type —  The value is 'A' for an ancient language, 'C'
   for a constructed language, 'E' for an extinct language, 'H' 
   for an historical language, 'L' for a living language, 'S'
   for a special code, and 'R' for retired codes.

 * name —  The reference name for the language.

 * names —  All names for the language, including the reference name.

 * inv_names — Inverted names (like 'English, Old').

 * comment —  Comments.

 * parent —  The macrolanguage that this language belongs to,
   if any.

 * members —  The member languages, if this is a
   macrolanguage.

 * retirement —  None unless this is a retired code.  If this
   is a retired code, the value is an object with the following members:
   code repeats the language code, name repeats the name,
   reason is the retirement reason, date is the retirement
   date (a string), replacement is the new code this one was
   replaced with (if any), and split is an English string indicating
   which codes this one was split into (if any).  The retirement reasons
   are: 'C' for a code change, 'D' for deletion of a
   duplicate code, 'M' for the merger of multiple codes into a new
   code, 'S' for the splitting of one code into multiple codes, and
   'N' for deleting of a code that represents a non-existent
   language.  There is a value for replacement for the 'C',
   'D', and 'M' cases, and a a value for split for the
   'S' case.

 * varieties —  The varieties of this language, as identified by
   Panlex.  For details about varieties, see the chapter on Panlex.

Search
------

Normalization
.............

The methods named(), find() and search()
permit one to search for languages by name.
All three methods normalize both the language names and the search
key, as follows:

 * Letters are normalized to lower case.  I.e., search is
   case-insensitive::

      >>> languages.named('SPANISH')
      [<Living Language spa 'Spanish'>]

 * Anything in parentheses is ignored::

      >>> languages.named('wali')
      [<Living Language wll 'Wali (Sudan)'>, <Living Language wlx 'Wali (Ghana)'>]

 * Hyphens are treated like spaces::

      >>> languages.named('karkar yuri')
      [<Living Language yuj 'Karkar-Yuri'>]
      >>> languages.named('old-english')
      [<Historical Language ang 'Old English (ca. 450-1100)'>]

 * Accents are removed::

      >>> languages.named('yari')
      [<Retired Code Retired Code yri 'Yar\xed'>]

   Here the Unicode character U+ED represents *&iacute;* (letter *i*
   with an acute accent).

 * Everything that is not a letter is ignored in comparison::

      >>> languages.named('p!ao?')
      [<Living Language blk "Pa'o Karen">, <Retired Code Retired Code ppa 'Pao'>]


By name
.......

One can access languages by complete name.  Since names are sometimes
ambiguous, this returns a list::

   >>> languages.named('spanish')
   [<Living Language spa 'Spanish'>]
   >>> languages.named('pao')
   [<Living Language blk "Pa'o Karen">, <Retired Code Retired Code ppa 'Pao'>]

Note that the key need not be the
reference name: "Pa'O" is one of the alternate names for language
blk::

   >>> languages['blk'].names
   ["Pa'O", "Pa'o Karen"]
   >>> languages['blk'].name
   "Pa'o Karen"

By name part
............

The method named() does not find a language if one provides only
part of the name::

   >>> languages.named('chin')
   >>> languages.named('matu chin')
   [<Living Language hlt 'Matu Chin'>]

To find a language if one knows only part of the name, used the method
find()::

   >>> len(languages.find('chin'))
   33

By character sequence
.....................

The method find() looks for complete words in the name.
(Remember that hyphen is treated as a word separator.)  To find a
language given only a part of a word, use search()::

   >>> languages.search('ruman')
   [<Living Language rup 'Macedo-Romanian'>]
