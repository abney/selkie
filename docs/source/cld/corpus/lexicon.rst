
Lexicon
*******

Lexical entry
-------------

Description
...........

I define **form** very broadly to include
(inflected) word forms as they appear in text; their
stems, roots, and affixes; dialectal variants; spelling
variants and outright misspellings; and so on.  The lexicon includes
an entry for each, not just for traditional headwords.

I actually use the term **lexical entry** for what would be a
numbered sense within a traditional entry.  That is, a form maps to a
list of LexicalEntry objects, and the sense number is the index of the
LexicalEntry in that list.

One may alternatively view a lexicon as mapping a **lexid,** which
is a form paired with a sense number, to a LexicalEntry.  Lexids are
represented as strings; a dot separates the form and sense number.  A
form standing alone is equivalent to a lexid with sense number 0.

A lexical entry is a mapping from **lexical fields** to values.
The lexical fields include part
of speech, semantics, morphological analysis, and the like.
A lexical field is a structured object, but it is
immutable and suitable for use as key in a mapping.  The lexical field
includes information about the type of value that is expected.

In addition, a lexical entry contains a list of **parids**
representing the locations where tokens of the lexid occur.
A parid is the
pairing of a textid with a paragraph number, separated
by a dot.

Finally, a lexical entry contains two back-links.  The first is a
simple back-link to the lexicon itself.  The second is
the **index** of the lexical entry within an ordered list of
all lexical entries, which is also part of the lexicon.

In short, the members of LexicalEntry are: form, sense, fields, refs,
lexicon, and index.

Lexical fields
..............

There are currently only a few lexical fields.  The **gloss** is an
English rendering of the meaning.  The value of **components** is a
list of lexids representing parts of the form.  The components
typically represent a morphological decomposition but they can
represent any sort of decomposition.  The field **derived forms**
is automatically generated as the inverse of *components.*
If *c* is a component of *f,* then *f* is a derived
form of *c.*

Forms that are dialectal variants, spelling variants, misspellings, or
the like, have a **canonical form.**  The inverse of
*canonical form* is **variants;** it is also automatically
generated.  Finally, a variant form (one that has a non-null canonical
form) has a **variety,** which is a string indicating what kind of
variant it is: what dialect it belongs to, or what orthographical
tradition, or its status as a spelling error.

There is a fixed list of lexical fields.  Each lexical field contains
the following information:

 * Its **name**.

 * A two-letter **abbreviation** of the name.

 * Which lexical field is its **inverse**, if any.  Inverseness is
   reflexive: if *f* has inverse *g,* then *g* has
   inverse *f.*

 * Whether it is **settable.**  Automatically-generated inverses
   are not settable; all other fields are settable.

 * The **type** of the value.  The possible types are String, XRef
   (a single lexid), or XRefs (a list of lexids).  The type provides a
   method to parse a string representation into a value, and a
   method to convert a value into a string representation.

 * Its **index** in the list of lexical fields.

Lexicon
--------
A Lexicon has three content members:

 * _lexents - a list of LexicalEntries.  Different senses of
   a form are separate LexicalEntry instances on the list.

 * _table - a dict whose keys are forms.  The value for a
   form is a list of LexicalEntries, where the sense number equals the
   index in the list.  That is, _table[form][sno] is a LexicalEntry.

 * _indices - a LexicalIndices instance.  It contains three indices,
   one that maps forms to similar forms, one that maps gloss words to
   similar gloss words, and one that maps gloss words to lexical
   entries.

Similarity
----------

Editor
------

Concordance
-----------
