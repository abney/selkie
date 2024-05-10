
Texts
*****

Data model
----------

A Text
is a shell that can represent several kinds of textual objects,
depending on its contents.  It is a specialization
of Structure, with six possible
members: audio, media, orig, toc, trans, xscript.
The kind of text is determined by which members are actually present.

.. list-table::
   :header-rows: 1

   * - If
     - Then it is:
   * - toc
     - A **complex text**: a
       document or document section.
   * - orig
     - A **written page**.
   * - media, [audio]
     - A **recording**, which is a **media page**.
   * - none of the above
     - An undifferentiated **stub**

It is invalid for a text directory to contain more than one of these
four files.

Complex texts
.............

Complex texts represent hierarchical structures whose leaves are
pages.

Written page
............

.. list-table::
  
   * - orig
     - TokenFile
   * - trans
     - Translation

Pages subsume both written pages and recordings.
A page may have a **plaintext** version and a **translation**.
The plaintext is always tokenized.
Together, plaintext and translation
constitute interlinear glossed text (IGT).

The method plaintext() returns a text's plaintext
representation.  For a written page, the plaintext
resides in orig and is represented by class TokenFile.
For recordings, the plaintext is derived from the transcript and is
represented by class TranslationUnits.

The translation resides in trans.

Recording (media page)
......................

.. list-table::
  
   * - media
     - MediaFile
   * - trans
     - Translation
   * - xscript
     - Transcription

Old-style audio page (deprecated):

.. list-table::

   * - audio
     - AudioDirectory (deprecated)
   * - trans
     - Translation

A recording may have a **transcription**.  If the media
subdirectory is present, the transcription is in a
separate xscript directory.  If audio is present
(deprecated), the transcription is audio/transcript.

The main difference between audio and media is that,
in the former case, the actual audio recording is stored in
the audio subdirectory.  In the case of media, the
actual audio or video file is stored in a central media directory.

The plaintext() for a recording is read-only.  It is derived
from the transcript, and is represented by class TranslationUnits.

Like a written page, a recording may also have a translation,
represented by the subdirectory trans.

Stub
....

A freshly-created text is a stub; it has no subdirectories.

Plaintext
---------

Plaintext file
..............

The Texts of a language describe a tree in which complex documents
supply the interior nodes and the leaf nodes are either written pages
or recordings.  (We set stubs aside since they are transitory.)  The
contents of written pages and recordings have a common representation
in the form of **plaintext**, optionally combined with a
translation.  The Text.plaintext() method returns the
plaintext representation of a textual leaf node.

A **plaintext file** provides the plaintext representation of a page.
A plaintext file is a piece of
tokenized, monolingual, target-language text that is of a suitable
size for editing and storage on disk as a single file.  Stripped to
its essence, a **monolingual corpus** is a list of plaintext files.

As we have seen, "plaintext file" does not name a class, but is represented by three
different classes that occur in four different contexts:

 * The orig member of a Text is a
   TokenFile; it represents a written page.

 * The transcript member of
   a Transcription is also a
   TokenFile.  It represents a sequence of text fragments, one for each
   small clip of a recording.

 * A TransTokenFile is not
   a specialization of TokenFile, but it behaves like a TokenFile.
   It presents a read-only **plaintext view** of a transcript in which the text
   fragments are stitched together into more natural sentence-like units.

 * TranslationUnits is an older, now deprecated, class that
   TransTokenFile replaces.

Segments and Tokens
...................

Conceptually, a plaintext file is a list of sentence-sized **segments**, and a
segment is a list of **tokens**.  Some of the tokens are
distinguished as **lexical tokens**, or word-form occurrences.
They are collected into the lexicon.

There is no hard-and-fast definition of what sized unit constitutes a "segment"
and what constitutes a "plaintext file".  For the sake of
responsiveness and incrementality, a plaintext file should be of
moderate size, ideally about the size of a page of printed text.  A
"segment" is any convenient subdivision for editing in a text box.
Segments also serve as **translation units**, in the sense of
the units of the plaintext file that align one-for-one
with units of the English translation.  The same units are used
for **interlinear glossed text (IGT)**.
Typically, segments are sentences, but they may be larger (for
example, paragraphs) or smaller (fragments).
It is important to distinguish them from **orthographic sentences,**
which are delimited by final punctuation, or **root clauses**,
which are the natural units for grammatical analysis.
How large the segments are, and how large the plaintext files are, is
ultimately up to the person that creates the text.

Segments are represented by the class TokenBlock.
A TokenFile behaves like a list of TokenBlocks, and a TokenBlock
behaves like a list of Tokens.

Indices
-------

Changes to texts are tracked in two central locations:

 * **TID table.**  Tracks the *location* of a text.
   Each Text is assigned a **text ID
   (TID)**, and the TID table maps TIDs to pathnames, to make it
   possible to find a text given its ID.

 * **Lexicon.**  Tracks the *contents* of a text.
   The tokens of the text are interned to create lexical entries, and
   references to the token locations are kept in the lexical
   entries.  A reference is represented by
   a **segment ID (SID)**;
   token locations are tracked at the granularity of the segment.

Segment-level changes
.....................

Changes to plaintext files need to be propagated to the lexicon.  The lexicon
includes every word form that occurs in a plaintext, and keeps a list
of references to the SIDs where tokens of each
word form occur.  Whenever a plaintext file is edited, references need to
be added and deleted.  When the last reference to a word is
deleted, its lexical entry is deleted as well.

The use of SIDs assumes that a TID identifies a unique plaintext.  The
presence of both transcript and plaintext view break that assumption.
The transcript/view separation makes things
tricky in another way, as well.  When going from the lexical entry for
a form to places where
the form occurs, it is most natural to refer to the plaintext view,
not to the fragments in the transcript.  However, the plaintext view is
read-only; it is the transcript that is edited.

Our solution is this.  All lexical updates triggered by edits to plaintext
go through
the TokenBlock
methods set_contents() and delete_contents().  We
let the transcript be represented by a standard
TokenFile, with the
consequence that the references to the tokens of a recording are at
the granularity of fragments.

The trick is in going from a lexical reference back to a TextBlock.
A SID combines a TID with the sequence number for a TokenBlock.  Both
the transcript and plaintext view of a recording share the same TID.
Dereferencing a SID is done by
Language.deref_parid().
It dereferences the TID to the value
of *text*.plaintext(), which is not the transcript, but
the plaintext view.  The "misdirection" is not actually a problem, as
long as we arrange that the sequence number for a transcript fragment leads us
to the correct TokenBlock in the plaintext view.

To find the TokenBlock with a given sequence number, TransTokenFiles (and TokenFiles)
contain a table that maps sequence numbers to
TextBlocks.  Nothing prevents us from mapping multiple sequence numbers
to the same TextBlock.  When initializing a TransTokenFile from a
transcript, we concatenate multiple fragments to form a given
TokenBlock.  We simply index the TokenBlock under all of the
fragment sequence numbers.  This has the consequence that the
TokenBlock's sequence number is not uniquely defined, but read-only
TokenBlocks have no internally-recorded SID, so there is no need for
uniqueness.

Text-level changes
..................

To modify the number and arrangement of nodes in the hierarchy of
Texts, one uses the methods
of TocWriter listed in
the table below: new_child() to create a
node, delete_child() to delete a node,
and transfer_children() to change the parent of one or more
nodes.

A TextType object
provides TocWriter with a single point of contact for updating the TID
table and lexicon.  There is a separate TextType for each language, returned by the
text_type() method of Language.
The text-change methods of TocWriter, and the TextType or
TextTypeWriter methods that they call, are shown in the
following table.  I include the load() method of Toc as well,
since it also calls TextType methods.

.. list-table::
   :header-rows: 1

   * - Toc[Writer]
     - TextType
     - TextTypeWriter
   * - load()
     - get_class(), check_item()
     -
   * - new_child()
     - get_class()
     - allocate()
   * - delete_child()
     - descendants()
     - deleting()
   * - transfer_children()
     - to_list(), descendants()
     - moved()

Updates to the TID table are performed by ItemType, which TextType
inherits from.  In particular, allocate() creates a new entry
in the ID table, deleting() removes an entry,
and moved() updates an entry.

TextType adds a call to LexiconWriter.
If the text contains a TokenFile,
deleting() calls the delete_contents()
method of each block in the TokenFile.  The other two
hierarchy-changing methods
do not affect the lexicon.  In particular, new_child()
always creates an empty text, and transfer_children() changes the
pathnames but not the TIDs of the moved texts.

Examples
--------


Editor
------

Visiting a text in the UI returns a
TextEditor.
After instantiating the app::

   >>> e6 = app.follow('/langs/lang.oji/texts/text.6')
   >>> e6
   <seal.cld.ui.text.TextEditor object at 0x...>

A TextEditor is little more than a dispatcher.  The Text
is found in the file member::

   >>> e6.file
   <Text langs/oji/texts/30>

The home page '' of the editor is represented by the
root() method, which returns a redirect to 'toc/' if the toc
exists::

   >>> e6.file.ls()
   _meta   _perm   toc
   >>> e6.file.toc.exists()
   True
   >>> e6.root()
   <Redirect 'toc/'>

Otherwise, root() returns a redirect to 'page/'::

   >>> e7 = app.follow('/langs/lang.oji/texts/text.7')
   >>> e7.file.ls()
   _meta   _perm   media   xscript
   >>> e7.file.toc.exists()
   False
   >>> e7.root()
   <Redirect 'page/'>

The redirects are handled by the toc() method and the
page() method.  The former returns a TocEditor
editting the text's toc, and the
latter returns a PageEditor editing the text itself::

   >>> e6.toc()
   <seal.cld.ui.toc.TocEditor object at 0x...>
   >>> e7.page()
   <seal.cld.ui.page.PageEditor object at 0x...>

Stub texts are also handled by PageEditor.


Toc
---

Data model
..........

A Toc is essentially
just a list of component Texts.

User view
.........

TocEditor
