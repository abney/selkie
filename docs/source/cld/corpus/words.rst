
Words
*****

General
-------

The original and primary aim of CLD is to support computational-linguistic study
of multiple languages simultaneously.  We would like all languages to
be both readable and writable for all users, but we do not wish to
require users to install hundreds of input methods on their computers,
nor can we make any assumptions about which input methods are already
installed, since there is no standard set across platforms.

One option is to define romanizations, which convert
ASCII key sequences (ASCII orthography or romanized text) to Unicode characters
(native orthography).  Character entry
is (or may be) entirely in ASCII, but display is (or may) use the
native script for the language.
There are actually at least three choices where orthography comes to play:
in text input, in text display, and in data
files.

The Universal Dependencies (UD) Treebank uses standard native orthography
(Unicode strings) in data files, and an interest in conforming to
it as an emerging standard gives us motivation to do likewise.
The main potential drawback is that producing romanized text for
editing involves inverting a romanization, and
romanizations are not guaranteed
to be invertible.  Nonetheless, it does seem natural to
expect the romanized version of a text to exist and to be unique, so we will
require that all romanizations we use are in fact invertible.

The UD documentation discusses tokenization, which converts
running plaintext to tokenized text.  Plaintext is
something of an artificial construct, however.  The more general
problem is conversion of arbitrary text documents
to tokenized text, a more difficult problem, and one that in our model
is part of document importing.

Our approach within CLD will be to be accommodating to those reading
texts, but require somewhat more of those entering texts.
Entering text is a more specialized action than reading it, so
expecting editors to have more specialized training
seems acceptable.
In particular, we expect texts to be entered in tokenized form, with
word boundaries explicitly indicated.
The main point of text entry is in the text boxes of the
PlainTextPanel.  We would like to give users a choice of whether
to use ASCII orthography or native orthography, but in either case,
we will assume that word boundaries are unambiguously marked.  When
entering Chinese, for example, spaces will be required between words,
even though that is not standard orthography.

The model we adopt for input and internal representation is the
following.  Text consists of a sequence of words.  Punctuation
marks are not treated as separate words, rather, associated
with each word is leading punctuation and trailing punctuation.
We will also allow the possibility of distinguishing otherwise
identical forms by the addition of a sense number.
The algorithm for taking input text provided by the user and
converting it to tokenized text is as follows:

 * Split the text at whitespace.  Each resulting unit contributes
   one word.

 * If the text is romanized, use the romanization to convert it to
   native (Unicode) orthography.

 * A *word character* is defined to be one whose Unicode
   category is letter (L), mark (M), number (N), or symbol (S).
   Non-word characters have category punctuation (P), control (C), or
   space (Z).  Characters before the first word character are leading
   punctuation and characters after the last word character are
   trailing punctuation.

 * If the remaining portion ends with a period followed by one or
   more digits, that is further stripped off as representing the
   sense number.

 * What remains is the word.  It is an error if it is empty.

That is the procedure for processing text coming from the user and
storing it in a tokenized-text file.  When the user edits existing
text (rather than entering new text), it must be converted from
tokenized format back to the plaintext format that is presented to the
user in a text box.  For that purpose, we must be able to invert the
romanization.

Multiple orthographies
----------------------

There may be multiple orthographies in use for a given language; for
example, Ojibwe may be written either with Latin letters or with
Canadian Syllabics.  Within the Latin orthography, there are
systematic variations.  For example, Kimewon uses *N* where
the standard orthography use *nh*, and he writes *k*, *t*, *p*
word-finally, even in cases where the standard orthography has *g*, *d*, *b*.
There are also dialectal differences, particularly on the question of
whether to write vowels that are silent due to syncope.

Sporadic spelling differences can be treated simply as variant forms.
The lexicon includes a facility for indicating the canonical form for any given
variant form and conversely getting the list of variant forms for any
given canonical form.  That approach becomes onerous for systematic
spelling differences.  We cannot simply use different romanizations,
however, because spelling variations are not generally invertible.
For example, it is not possible to (unambiguously) invert Kimewon's
orthographized word-final devoicing.

The approach we take is to adopt a single **canonical orthography**
but multiple **display orthographies**.  
We require those who enter text to cooperate in using a common orthography.  One
can then define a **respeller** to be a function that maps text in
the canonical orthography to a given display orthography.  (Having a
single canonical orthography makes the construction of respellers manageable.)
Unlike romanizations, respellers do not need to be bidirectional.

On the input side, we provide only two
options: direct entry of canonical orthography, or the use of a
default romanization, of which only one is defined for each language.
That is, we require those who enter text to
cooperate on a common romanization for the language.  

Access points
-------------

The basic unit of representation for tokenized text is the
TokenBlock, which represents a translation unit (sentence or
paragraph) in tokenized format.
