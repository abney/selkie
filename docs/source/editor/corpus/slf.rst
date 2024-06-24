
Selkie Language Format
======================

Selkie Language Format (SLF) is a lightweight specification for
linguistic corpora. It represents the logical structure of the corpus,
not the presentation in "pretty" human-consumable form. Indeed, we
make a fundamental distinction between **documentation** and
**annotation**. SLF is a format for annotation, not for documentation.

Media files, which include audio files, video files, and print-quality
page formats like PDF, constitute *documentation*,
and they are not included in an SLF file.
The SLF file can be viewed as stand-off annotation
representing the logical structure of their contents.

SLF files consist exclusively of plain ASCII text.
A typical workflow begins with documentary files, either recordings or
page displays such as PDF. Annotation, and SLF, begins when one 
identifies where target-language text occurs in the
documents, how it breaks down into sentences and individual word
forms, and where translations into a glossing language are provided.
Additional linguistic annotations may be added from that
point.

The SLF "file" is actually a directory, though it may of course be
reduced to a file by using zip. A corpus can also be converted to a
single-file JSON format ("itemizing") and back again ("deitemizing").

Components
----------

An SLF corpus contains four basic types of component: languages, texts,
lexicons, and romanizations. More precisely,
a corpus consists of **languages**, and a language consists of texts and
a lexicon. At the top level, a corpus also contains
a repository of romanizations.

There are three basic kinds of **text**: *simple texts* consist of sentences,
*aggregate texts* consist of other texts, and *empty texts* consist of
nothing; they serve as placeholders.

A simple text consists of sentences, optionally with translations.
A *sentence* consists of a sequence of forms, and a *form* is a particular
character sequence. (A character sequence that
differs in any way constitutes a distinct form.)
If the text is a transcript, the sentences may also contain time
points.

Forms consist of ASCII characters. For
scripts that are not well represented by ASCII characters, one may
think of the characters in the form as keystrokes in a
virtual keyboard. One hindrance for a linguist who works with many
languages is the necessity of finding and installing appropriate
system-specific software keyboards for every language. By
using "keystrokes" instead of Unicode characters, we eliminate that
complication.

A **romanization** represents the mapping from ASCII
"keystrokes" to Unicode characters. To avoid complexities that arise
if different texts use different romanizations, or if a text and the
lexicon use different romanizations, we associate a single
romanization with each language.

A **lexicon** is a table in which the keys are forms. The values are
*lexical entries*.

It is possible to designate multiple forms as
equivalent by choosing one as the *canonical form* and linking the
variant form(s) to it. That is used for spelling variation and spelling
errors, and may be used for dialectal or stylistic variation. (A
corpus represents a single linguistic variety, but one is free to
define that variety broadly.)

Forms may also be abstract, in at least two ways. (1) A sense
designator may be
added to an orthographic form to create a new sense-disambiguated form. The original
form represents the default sense. For example, "crane.1" may be used
to represent the machine, whereas "crane" represents the bird. Both
have the same orthographic form. (2) A form in the lexicon may
represent a morpheme, and there is no requirement that a morpheme be a
contiguous piece of text. For example, a consonant template "ktb"
is an acceptable morpheme.

Associated with a lexicon is also a *token index*, which maps forms to
the sentences in which they occur, for efficiency of access.
Like a lexicon, it is a table whose keys are forms;
but its values are lists of locations, where a
location is the pairing of a text ID and a sentence
number. Token indices are automatically generated.

Format Definition
-----------------

The main goal is simplicity. A corpus is represented as a (small)
hierarchy of directories, with structure as follows::

   corpus/
       langs             Language metadata
       roms/
           *romname*     Romanization
           ...
       *langid*/
           lexicon       Lexicon file
           index         Token index
           toc           Text metadata
           txt/
               *txtid*   Sentences
               ...
       ...

The corpus and its four major types of component are represented as follows.

 * A **corpus** is a directory containing a language-metadata file named
   'langs', a subdirectory 'roms' containing romanizations, and some
   number of language subdirectories. The names of language
   subdirectories are language IDs. The filenames 'langs' and
   'roms' cannot be mistaken for language IDs if one uses either
   ISO-639-3 or Glottolog codes.

 * A **language** is a subdirectory whose name is a language ID.
   It contains a lexicon, a table of
   contents named 'toc', and a subdirectory 'txt' containing texts.

 * A **lexicon** consists of two files: 'lexicon' and 'index'.

 * A **text** is a file whose name is the text ID. Each text also has
   metadata, which is contained in the 'toc' file. Some texts consist
   solely of metadata.

 * A **romanization** is a file that contains a mapping from ASCII
   characters to general Unicode characters.

We distinguish between the *conceptual components* of a corpus and its *items*.
An **item** corresponds to a single data file, that is, a leaf in
the schematic hierarchy given above, of which there are six.
They correspond to six item types, each with a
distinct item-name pattern, as follows::

   /langs                 Language metadata
   /roms/*romname*        Romanization
   /*langid*/lexicon      Lexicon file
   /*langid*/index        Token index
   /*langid*/toc          Text metadata
   /*langid*/txt/*txtid*  Sentences

To be clear about the differences between conceptual components and items:

 * The corpus corresponds to a directory, not an item.

 * A language corresponds to a directory and also to an entry in the
   language-metadata item.

 * A lexicon encompasses two items: the lexicon proper and the token
   index.

 * A text corresponds to an entry in the text-metadata item. A simple
   text (but not an aggregate or empty text) also corresponds to a text
   item, containing sentences.

All item files are in a simple format consisting of blocks of
lines separated by an empty line, where each line in a block
represents a key-value pair, separated at the first group of whitespace
characters. For example::

   w aniin
   g hello

   w Debid ndizhnikaaz
   g my name is David

In this example, there are two blocks. The keys are "w" and "g", the values being
the rest of the lines. Values (but not keys) may contain internal
whitespace.

In some cases, duplicate keys are allowed, and the file is
interpreted as a list of property-lists, and in other cases the file
is intepreted as a list of objects or maps (and duplicate keys are not allowed).

The following is the complete list of item types:

 * **Langs**. The corpus directory contains a language-metadata file named 'langs'.
   It contains a map
   from language IDs to language entries. A language entry
   minimally has key ``name``.

 * **Lexicon**. Each language directory contains a file named 'lexicon'.
   It contains a list of lexical entries,
   and a lexical entry is an object
   with the following keys (all optional):

    * ``id`` — Form. No two lexical entries may have the same form.

    * ``ty`` — Type. Word, sense-disambiguated form of word, 
      inflected form of word, spelling variant,
      etc. It is permitted to have forms that appear only in the
      lexicon and not in texts; they may be used to represent
      dependent morphemes.

    * ``c`` — Category (part of speech). Connects the lexical entry
      to the grammar. May include morphological information.
   
    * ``pp`` — Parts. The value is a list of forms, representing
      (unordered) constituents of this form. No assumptions are
      made about how the form is related to the parts. In
      particular, the form need not be the concatenation of the
      parts.

    * ``g`` — The English translation.

    * ``cf`` — Canonical form. We deal with spelling variation,
      spelling errors, dialectal forms, etc., by mapping all
      variants to a canonical form. An entry for a variant form may
      not contain any keys except a 'cf' record and (optionally) a
      'type' record.

    * ``of`` — Orthographic form. Sense-disambiguated forms can use
      this field to indicate how the form is written in text.

 * **Index**. Each language directory also contains a file named 'index'.
   It contains a map from senses to lists of
   locations (where tokens occur). A location is a string consisting
   of a text ID and a sentence number, separated by a period.

 * **Toc**. Finally, each language directory contains a file name 'toc'.
   It contains a list of text metadata entries. A text
   metadata entry contains the following keys:

    * ``id`` — The text ID. This is the only required key. No two
      entries may have the same ID.

    * ``ty`` — E.g., collection, book, chapter, page, text,
      audio. Complex texts (collections, documents, document sections,
      and so on) consist of metadata but no text file.

    * ``ti`` — Title.

    * ``au`` — Author.

    * ``ch`` — Children. A list of text IDs. A text should either have a
      'ch' entry or a text file, but not both. A text that has a text
      file is simple, a text that has a 'ch' entry is aggregate, and a
      text that has neither is empty.

    * ``pdf`` — The pathname of a PDF file. If it is a relative
      pathname, it is interpreted relative to the directory that
      contains the SLF directory.

    * ``audio`` — The pathname of an audio file, or an object with keys
      'pathname', 'start', and 'end'.

    * ``video`` — The pathname of a video file, or an object with keys
      'pathname', 'start', 'and 'end'.

 * **Text files.** Each language directory contains a 'txt'
   subdirectory that in turn contains text files whose names are text
   IDs (numbers beginning with 1).
   A text file contains a list of segments that are generically called
   "sentences", though they may variously represent sentences,
   utterances, pause groups, or other similar-sized pieces of text.
   A sentence is an object with keys:

    * ``w`` — Words. The value is a string consisting of
      space-separated forms.

    * ``t`` — Timestamp. The value is a floating-point number
      representing seconds from the beginning of the audio.

    * ``g`` — Gloss. The translation into English.

 * **Romanization files.** In a romanization file, the keys are ASCII
   character sequences and the values are Unicode character
   sequences. Non-ASCII Unicode characters may be represented as
   escape sequences of form \(codepoint codepoint ...\). For example,
   the following is one line from the Salish romanization file::

      Q'w Q\(0313 02b7)

   (The character U+0313 is an apostrophe written above the preceding
   letter, representing glottalization, and U+02b7 is a raised "w",
   representing labialization.)
