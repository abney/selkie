
Conceptual
==========

General
-------

Language documentation and language description are closely related, but
distinct, activities. A **document** is a language recording of
some variety, whether audio, audio-visual, or printed. A primary
desideratum for a digital document is that it be a detailed, faithful
rendering of the original. Digital documents are typically media files
in formats such as WAV, MOV, or PDF.

By contrast, language description produces **annotations** of
documents, representing the linguistic
content of the document. Simplicity and generality of
representation are the primary desiderata; high-fidelity reproduction of the original form
is not a requirement.
A file format for linguistic annotation is defined, called CLD.

A collection of related documents is called a **corpus**, and
its annotation is a **corpus annotation**. However, one often uses
the term *corpus* indiscriminately for both. For many traditional
corpora, the distinction is not very meaningful, inasmuch as the
original documents no longer exist, and what survives is effectively
an annotation: it represents the content of the original, but is not
a faithful rendering of the original form. Indeed, given that
early documentary history lacks a clear delineation among copyists,
editors, and co-authors, the "original" document may even be pure
fiction: a convenient pretense to simplify a complex process of
genesis.

In *stand-off* annotation, the corpus annotation is kept
separate from the corpus that it annotates. Experience has shown this
to be a better practice than intermingling originals and annotation,
and CLD is designed for stand-off annotation.

Corpus objects
--------------

Briefly, a corpus annotation of the type defined here consists of a set of **languages**,
which consist of **texts**, which consist of **sentences**,
which consist of references to **words**. Words are structured
objects, and may be thought of as lexical entries. Indeed, the
collection of words for a given language is called a **lexicon**.

Each object is named by an **identifier**, which is a symbol in a
controlled vocabulary determined by the object type. For example, each
language is named by a language ID (langid), each text within a
language is identified by a text ID (textid), each sentence within a
text is identified by a sentence ID (sentid), and each word is
written in ASCII as a word **form**.

More precisely, an identifier is a string of
printable ASCII characters - no whitespace and no control
characters. IDs other than forms are more stringently
constrained: they must have the form of programming-language identifiers, meaning that
they may contain only letters, digits, and underscore, and must begin
with a letter or underscore.

Since the IDs are generally relative to some containing object - for
example, a sentence ID is relative to the containing text, and a text
ID is relative to the containing language - one generally requires
multiple identifiers to uniquely identify an object within the
corpus. For example, a particular sentence is identified by a triple
(*langid*, *textid*, *sentid*).

There are three types of supporting object. An **orthography**
maps forms (which are ASCII strings) to unicode for native display. A
**lexicon translation** and **text translations** are used if
one wishes to provide translations into languages other than the default
glossing language.

The following table summarizes.

+----------------+----------+------------------------+
| **Object**     | **Type** | **Unique ID**          |
+----------------+----------+------------------------+
| corpus         | corp     | -                      |
+----------------+----------+------------------------+
| language       | lang     | langid                 |
+----------------+----------+------------------------+
| text           | text     | langid, textid         |
+----------------+----------+------------------------+
| sentence       | sent     | langid, textid, sentid |
+----------------+----------+------------------------+
| word           | word     | langid, form           |
+----------------+----------+------------------------+
| lexicon        | lexicon  | langid                 |
+----------------+----------+------------------------+
| orthography    | orth     | orthid                 |
+----------------+----------+------------------------+
| lexicon trans. | xlexicon | langid, langid         |
+----------------+----------+------------------------+
| text trans.    | xtext    | langid, textid, langid |
+----------------+----------+------------------------+

Details
-------

**Corpus**. No corpus identifier is provided, because there is only ever one
corpus under discussion. Collections of corpora are outside the scope of the CLD format.

**Orthography**.
As discussed in the introduction, CLD is an annotation format, not a
documentation format. Word forms are explicitly intended to represent
linguistic distinctions, not conventional orthography. CLD follows
the standard practice in computational linguistics of undoing
sentence-initial capitalization, and treating punctuation marks as
separate tokens. Dialectal and spelling variation are generally
preserved, and a facility is provided for indicating that two forms
are spelling variants or dialectal variants of each other.

For convenience in dealing with collections that contain many different
languages, without requiring the user to install language-specific
keyboards or other software resources,
words are represented in *romanized* form, consisting
exclusively of printing ASCII characters. A romanized form should
absolutely not be thought of as a choice of standardized writing
system or standardized keyboard. Rather it represents a
corpus-specific way of typing a lexical form using an ASCII keyboard.

To produce text in conventional writing systems, one or more mappings
from the corpus romanization to Unicode strings may be provided. These
are called *orthographies*.

**Forms**.
Any variation in a word's character
sequence creates a distinction of form (and thus a distinct word type). One may define an
equivalence class of forms by choosing one of them as the canonical
representative, and mapping each of the others to it. The canonical
representative is known as the **canonical form** of the other
forms in the equivalence class.

**Texts**.
Texts represent the contents of documents. A one-one
correspondence between texts and documents is common, but not
required. One may well have a single videotape that contains multiple
unrelated recording sessions, in which case it is natural to represent
its contents as several different texts. Or one's recording of a long
story may be broken into several audio files. In that case, it is
natural to have a single text (representing the story) that
corresponds to multiple documents (the individual audio files).
More complicated situations are also possible, such as a movie file
digitized from a single videotape that contains two complete stories and
part of a third.

As already indicated, texts are not intended to
be faithful replicas of original documents.
Rather, they abstract away from most details of presentation to focus
exclusively on linguistic content.
The elimination of sentence-initial capitalization has already been
mentioned. To give another example,
one may choose to distinguish homographs by introducing non-standard
forms (say, with a numeric suffix, like ``cat.2``) to distinguish
the homographs.

**Lexicon**. A lexicon is
uniquely determined by its language - there is exactly one lexicon per
language. Every form that occurs in every text is automatically
included in the lexicon. It is permissible to include other forms
about which the user has information, even if they do not appear in
any text.

A lexicon maps forms to words. A word includes
linguistic information, such as part of
speech, and (for example) the canonical form, if the word form is not itself
canonical. Words also include morphological information in the
form of a list of the parts of the word. "Parts" is understood very
broadly. The parts are other forms, but there is no assumption
that concatenating the keystrokes of the parts' forms yields the form
of the composite word. Non-concatenative morphemes such
as Arabic roots or templates can freely be used. Morphemes may even be
entirely abstract.

Forms that represent bound, nonconcatenative, or abstract
morphemes obviously do not appear explicitly in printed documents. But
they also do not appear in corpus texts. Their occurrence at a
particular place in a text is, rather, implicit in the occurrence of a
form of which they are parts.
