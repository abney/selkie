
``selkie.pretts`` — Converting text to bare words
=================================================

A "bare words" representation is intended to be a natural data format
for the boundary between the language system properly speaking and the
"media" system, meaning in particular speech versus writing.  A bare
words representation is intended to be neutral between spoken and
written language.  It consists only of words with no
orthographic or typographic modifications: no punctuation,
capitalization, abbreviations, arabic numbers, and so on.
It is the kind of representation that is typical output of a speech
recognizer, and it is suitable as input to a speech synthesizer.
It is also particularly suitable for lexical lookup and parsing.

One obtains bare words from conventional text by
tokenization and normalization.  Selkie.pretts provides the
normalization step.

.. py:class:: Normalizer(text)

   The text is represented as a single string.  The Normalizer
   instance behaves as an iteration containing normalized tokens.

The normalizer uses a table of abbreviations, which is
selkie/abbreviations in the selkie.data directory.
