
Corpus Contents
***************

Simple texts
------------

CLD is organized around texts, which mediate between audio recordings
and the lexicon.  The basic item is a **column**
of tokenized text.  Structurally, a text column is a list
of sentences, optionally aligned with a translation that
is a list of the same length.  The translation can be viewed as a
second column, so that the container, called a **simple text,**
has the form of an array:
its first column is the original text, the second column is the
translation, and each row represents a sentence.  A simple text is
completely analogous to traditional facing-page format for text and
translation.

"Sentence" is to be understood loosely: **translation unit**
is a more accurate term.  Nothing hinges on its size or grammatical
status, only on it being a suitable unit for translation.

A sentence, in turn, is a list of word tokens.  Only word tokens matter;
punctuation
marks are not treated as separate tokens, but are attached to adjacent
words.  That is, each token is
optionally associated with leading and trailing punctuation
characters.  This approach is more intuitive for non-experts and
simplifies the correspondence between tokens and lexicon.

Intermediate between text and lexicon is interlinear glossed text
(IGT).  An IGT view shows a single sentence, partitioned into glossed
words corresponding to individual tokens.

Lexicon
-------

Central to CLD is a tight integration between texts and lexicon.
The character sequence making up a word token is called a **form.**
The class of *forms* is very inclusive; it includes not only
citation forms but also inflected forms, proper nouns, dialectal variants,
misspellings, and so on.  Anything that appears in a text is a form,
as is any element that a user introduces when analyzing a text, such as
bound morphemes or multi-word units.

The lexicon is a table whose keys are forms.  This, again, is a
much more inclusive conception than usual: inflected forms,
misspellings, and so on all have lexical entries.  For purposes of
printing a lexicon, there will be an ability to designate a subset of
entries as canonical entries, but that is not currently
implemented.

The lexicon is generated automatically from the texts.  It includes an
index of all sentences in which a given form occurs, to provide
backlinks from lexical entries to texts.  That is, from any entry in
the lexicon one may obtain a list of example sentences, which is the
same as a concordance.

The only way to enter a form into the lexicon is by including the form
in a text.
In particular, a traditional dictionary is conceived as just another text, one whose
"sentences" are single words.  If one enters a traditional dictionary
into CLD, one may enter the example sentences as a second text.
(Nothing prevents one from mixing headwords and example sentences in a
single text, but keeping them separate is probably more useful.)

Although one cannot manually enter a new form into the lexicon, one
can enter information into the lexical entry for an existing form.
There is a single lexical entry for each form,
independent of any particular occurrence of the form in text.
In the interest of keeping everything
intuitive for non-experts, the current lexical fields are very general and
simple.

First, to deal with misspellings, dialectal variants, orthographic
variants, and the like, one does not correct the original text.  Rather,
it is possible to indicate that one form is a **variant of** another form, which we may call the *canonical form.*
More generally, we define a *canonical form* to be any form that
does not have a *variant-of* link.
Backlinks are automatically created: if *A* is the canonical form of
*B*, then *B* is included in *A*'s list of **variants.**

A canonical form can be viewed as a conventional representative for an
equivalence class of forms.  Note that CLD chases *variant-of*
links to find the ultimate canonical form.  That is, if form *A* is a variant of form *B*, and form *B* is
a variant of form *C*, then the canonical form of *A* is actually *C*,
not *B*.  (If there is a cycle, it is broken arbitrarily, but the
software prevents the user from creating cycles under normal circumstances.)

A second relation is introduced for the relationship between an
inflected form and its lemma.  One may specify that a form
**consists of** one or more other forms, which are its *constituents.*
There is no requirement that the constituents exist independently in
texts; entirely new forms may be introduced in the *consists-of* field.
Nor are any assumptions made about how the constituents combine to create
the derived form.  It is possible that the derived form is simply the
concatenation of the constituents, or the constituents may be a stem
and infix, or a template and vowel sequence, or entirely abstract.
It is permissible for constituents to overlap, and it is permissible for the
list of constituents to be incomplete.  Whether the order of
constituents matters is also up to the user.

Again, backlinks are created automatically.  The field **derived-forms**
is automatically populated; if *B* is a constituent of *A*, then *A*
is a derived form of *B*.

The only other field currently supported is **gloss.**  This
provides the word-by-word gloss used in interlinear glossed text.

Typography and orthography
--------------------------

Text entry and display are areas in which there is a tension between
the desiderata of computational linguists and those of language speakers.
Desiderata for computational linguists include the following:

 * Since computational linguists are likely to work with many languages,
   including languages with which they have little familiarity, all
   functionality should be uniform across languages, and should in
   particular be available without the necessity of installing
   language-specific keyboards or the like.

 * CLD files should be easy to process, without recourse to
   special libraries (even libraries as broadly available as
   XML-processing libraries).  For this reason, tabular plaintext formats
   are used.

 * CLD files should be processable even using legacy
   text-processing tools such as grep and awk.  For this reason, we
   understand *plaintext* to mean *ASCII* plaintext.

In contrast, speakers of a language desire to enter and view texts
using customary orthography and typography.  There are a number of
ways in which customary conventions run athwart of the desiderata just
listed.

 * Most languages use character sets that include non-ASCII
   characters.

 * Many languages use language-specific **input methods**
   ("keyboards").  Chinese is a particularly complex example.

 * Languages differ in their tokenization conventions.  Some
   languages do not mark word breaks at all—Chinese is the obvious
   example.  Vietnamese uses spaces to mark syllable boundaries rather
   than word boundaries.  Most European languages use spaces as word
   separators but have complicating conventions, such as the use of
   hyphens or dashes without spaces.

 * In most European languages, capitalization is sometimes
   lexicographically significant (the proper noun *May* is
   lexicographically distinct from the verb *may*) and sometimes
   not (all words are capitalized sentence-initially).

In CLD, a language-general representation is used internally, but
language-specific customization is made available as an option where
practicable.  Let us use the term **language kit** loosely to
include all functionality that is specific to a given language.

The main language kit element is a **romanization,** which is a
mapping between an ASCII encoding (also known as a
*practical orthography*) and Unicode.  Romanized text consists
solely of ASCII characters.  (For example, the Arpabet may be viewed
as a romanization for a subset of the IPA.)
Romanized text is used internally to represent text
and forms, and may always be used for text entry.  One may think of a
romanization as a generic input method, in which the ASCII text
represents the keystrokes, and the mapping to Unicode gives the
resulting text.  In keeping with that analogy, when text is displayed,
it is always converted to Unicode, using the romanization.

Input methods are too complex and vary too much from language to
language to make it realistic to include them in CLD, but a user may
*optionally* use an input method installed in the operating
system when entering text.  Let us distinguish between
**romanized text entry,** in which keystrokes are interpreted as
ASCII characters in romanized text, and **native text entry,** in
which one uses an input method installed in the operating system.
One may optionally enable native text entry on a per-language
basis.

(One might expect CLD to automatically detect native
text entry by the presence of 
non-ASCII characters, but it is not possible to
automatically detect when a string consisting entirely of ASCII
characters is intended as Unicode text rather than romanized text, and
even a string intended as romanized text may contain non-ASCII
characters like so-called "smart quotes.")

To control the forms that appear in the lexicon, romanized text entry must
conform to the convention of using spaces uniformly for word
separation, even if that conflicts with language conventions.  When
entering romanized Chinese or Vietnamese text, one must include
spaces as word breaks.  In European languages, to distinguish hyphens from dashes,
one must use spaces with dashes.  (A hyphenated word is treated as a
single token; one may break it
into its constituents in the lexicon.)
One must use only lexicographically-significant capitalization:
sentence-initial words should not be capitalized.

**Word senses.**  One final issue that I include here,
though not properly a typographic or orthographic issue, is the
disambiguation of word senses.  During text entry, one may flag a word
as having a non-default sense by suffixing it with a
**sense number,** a period being used to separate the sense number
from the token proper.  CLD does not distinguish between polysemy and
homonymy, but each word sense has its own lexical entry.  I have found
it best to minimize the use of word senses, using them only
for the starkest homonym distinctions, but the facility may be used
as one sees fit.

One may use either a form with sense number or a form without sense number to
access the lexicon.  If a sense number is provided, one obtains a
single lexical entry, and if not, one obtains a list of entries all
sharing the same form.  In text, a form without a sense number is
treated as having sense 0, the default sense.

Recordings
----------

Tokenized text mediates between audio and lexicon.  We have discussed
the connection to the lexicon; let us turn to the connection between
text and audio recordings.

CLD assumes that an audio or audio-video file is given; *creating* recordings
is outside its purview.  For both practical and conceptual reasons,
media files are kept in a media directory separate from the
CLD texts and lexicons.

The practical reason is that an entire CLD
corpus is usually smaller than a single media file, and file
management (for example, under git) is simplified if one keeps such
disparately-sized files separate.  Also,
for the sake of portability, all CLD files apart from media use simple tabular
ASCII formats, and keeping them separate from binary files again
simplifies data management.

Conceptually, CLD files are viewed as **annotations** of audio
files, and experience suggests that stand-off annotation, rather than
integrated annotation, is more flexible and easier to manage.  Note
that this does not preclude texts that lack an audio representation,
but the most complete case is an audio recording connected to the
lexicon via a tokenized text.

CLD provides the ability to transcribe an audio recording in
order to create the simple-text annotation.  The interface is intended
to be as simple and streamlined as possible.  Transcription consists
in marking the locations of units of interest, which are called
**snippets.**  Snippets are typically small, small enough that one
can transcribe them immediately after hearing them, without replaying them.  They may consist of
single words, a few short words, or even just a part of a word.

A **transcript** is a list of snippets.  A tokenized text called a
*transcribed-text column* is
automatically generated from a transcript by concatenating the
snippets, separated by spaces.  In the text, no distinction is made
between the spaces between snippets and any that occur within a
snippet.  The space between two snippets may be suppressed by flagging
the second snippet as a word continuation.  Sentence breaks are
introduced by flagging sentence-initial snippets.  

A transcribed-text column differs from an original-text column
in only two ways: the transcribed-text column is read-only, and its
sentences and tokens are linked to audio.

Complex texts and stubs
-----------------------

A text in CLD is actually a container for elements that can occur in
different combinations.  The elements we have already discussed are
the media file (more precisely, a pointer to the media file),
the transcript, the transcribed-text column, the original-text column, and the
translation.  A text is
defined to be a recording if it contains a media file.  A recording may, but
need not, also contain a transcript, which automatically generates a
transcribed-text column.  A recording may also contain a translation, which is aligned
with the transcribed-text column in the same way that a
translation is aligned with an original-text column.

A text is defined to be a simple text if it contains an
original-text column.  Recordings and simple texts are mutually
exclusive: an original-text column is not
permitted if a media file exists.

There is one additional element, namely, a **table of contents (TOC).**
A text that contains a TOC is a **complex text.**
The presence of a TOC excludes all other elements.
The TOC is a list of component texts.  Each component text has a
unique name, and may be accessed either by name or by position.

Finally, a newly created text contains no elements, and is called a
**stub.**  One may convert it to any of the other three text types
by adding a media file, original-text column, or TOC.

Languages and corpus
--------------------

For the sake of simplicity, texts in CLD are always monolingual.
Occasional foreign words that occur in otherwise monolingual text can
be treated as forms like any other and marked as non-native.
Parallel texts or other documents that contain passages in multiple
languages can be subdivided into multiple monolingual texts.  CLD does
not currently provide a way of aligning texts across languages.
These solutions may be awkward or unworkable for some documents, such
as texts that contain a great deal of code-switching; CLD is not the
appropriate tool for such documents.

As has already been discussed, central to CLD is the ability to cover
a wide variety of languages in a uniform fashion, so as to support
cross-linguistic study, and
particularly the aims of inductive general grammar.
Each language represents a sub-corpus.  Each contains a lexicon and a
list of texts.  Texts are organized in a hierarchy, with complex texts
as nonterminal nodes.  At the same time, each text has a unique ID
(that is, unique within the language), and there is an index that permits
direct access to texts by ID, as well as iteration over all texts.
There is a separate text index for each language.

Finally, at the highest level, languages are collected into a CLD **corpus.**
The corpus is the CLD application file.  It may range in size from a
single text to a full-blown universal corpus.

Permissions
-----------

For the web application,
there is a permissions system and user login support.
Each item has independent permissions.
Default permissions are inherited from the containing item: protecting
a language or complex text protects everything that it contains, as
well.

Permissions are granted to particular users to perform particular
actions.  The actions are read, write, and administer.
(Administration permission is needed in order to change an item's
permissions.)  One does not grant permission to perform an action
directly, but rather one assigns users to *roles:* owner,
editor, or reader.  An owner may perform any action, an editor may
read or write, and a reader may only read.

Roles may be assigned to
groups, in which case every member of the group inherits the granted
permissions.  There is no fundamental distinction between groups and
users: a group is simply a user that has members.

Permissions are only required in a multi-user context, which is to
say, within the web application.  When CLD is run as a desktop
application, the user is set to *_root_*, which automatically has
permission to perform any action.

Principles
----------

To summarize the principles guiding the design of CLD:

 * The primary goals are the production of large quantities of
   simple, uniform data across multiple languages, and supporting language
   self-study that complements immersion learning.

 * CLD does not aim to be all things to all users.  It
   does not aspire for print-quality page description or coverage
   of every conceivable type of text.  Other software already exists
   that serves the needs of producing archival-quality documents in
   which all details of grammatical and discourse structure are
   captured.

 * Simplicity, generality, and intuitiveness are paramount.

 * Equally important is robustness in the face of the variation
   that one encounters when documenting less well-studied languages.
   Using a *variant-of* field instead of insisting on
   orthographic regularity provides one example.

 * Constraints on the user are minimized.  The user is free to
   choose the orthography, or what constitutes a translation unit, or
   what sized snippets to use in transcription.
