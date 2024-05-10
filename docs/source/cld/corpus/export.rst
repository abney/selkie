
.. automodule:: selkie.cld.corpus.export

Export files
************

Import/Export
-------------

Items and containers
....................

For purposes of export and import, a corpus is treated as a set
of **content items,** of the following types:

 * **Language.**
   The language info file is a content item.

 * **Lexicon.**
   Settable lexical field values constitute independent
   information; they represent the content portion of the lexicon.
   Everything else is automatically computable, and represents
   administrative information.

 * **Text.**
   The information file, toc listing, original plaintext, translation,
   and media (media file, clips, transcript, new-sentence flags)
   represent contents.

 * **Romanization.**
   Romanizations are content items.

 * **Notebook.**  GLab notebooks are content items.

Each content item has an **ID** that consists of a *container name*
and a *local ID* that identifies it within the container.
Containers include languages,
the romanization registry, and GLab.  The name of a
container is unique within the corpus.  The name for a language is the
standard 3-letter ID, the name of the registry is roms,
and the name for GLab is glab.  (Uniqueness is guaranteed
because neither 'roms' nor 'glab' is a valid language name.)
An item's local ID is unique
within its container.  A local ID is not necessarily unique within the
corpus, but the combination of container name and local ID yields a
global ID that is unique.  The local ID for a GLab notebook combines
the user name and notebook number, e.g. abney-1.  (User
names are restricted to alphanumeric characters and underscore: see
UserList.)

Implementation
..............

An instance of Container represents a view of a directory as a named
container, and an instance of Item represents a view of either a
file or directory as an item.
Both Containers and Items may have **children,**
which are Items.  The **descendants** of a Container are computed
as the transitive closure of its children, and the descendants of an
Item are computed as the reflexive-transitive closure of its
children.

As a unit of export, an item is identified with a list of **kernel files.**
Two items may have overlapping sets of
descendants, but no two items have any kernel files in common.

The files constituting the kernels are as follows.  The C column
indicates whether the item may have children.

.. list-table::
   :widths: 4 4 1
   :header-rows: 1

 * - Item
   - Kernel Files
   - C
 * - Language
   - info
   - Y
 * - Lexicon
   - lexicon
   - N
 * - Text
   - orig, trans, media, clips, paras, transcript, toc
   - Y
 * - Romanization
   - rom
   - N
 * - Notebook
   - gn
   - N

The cld script
..............

The cld script is used for corpus management, including export and
import.  **Exporting** creates a serialized ASCII representation of
the items, or some subset of the items, of the
corpus.  **Importing** reads the serialized representation and
creates or appends to files in the corpus.

The list, export, and delete commands take a list of **selectors**
to indicate which items are to be included.  Possible selectors
are:

 * **Full name.**  A full name has the
   form *cn*/*id*, where *cn* is a container
   name and *id* is an item ID.  This selects the
   container *cn* and makes it current, and
   it selects the item whose ID is *id* within container *cn*.

 * **ID.**  If there is a current container *cn*, one may
   select an item in *cn* by specifying only its ID, without the
   prefix *cn*/.

 * **Container name.**  If the selector ends with a slash, or if
   it contains no slash and there is no current container, then the
   selector (sans slash) is taken to be a container name.
   The named
   container is selected and made current.  No items are selected
   within it.

In this way, processing the list of selectors yields a list of selected named
containers, and within each named container, a list of selected
items.  It is possible to select a container without selecting any
items in it.  In that case, the item wild-card is supplied, selecting
all items in the container.

The commands are **list, export, delete,** and **import.**
The first three accept a selection.

A language serves both as a Container and as an Item.  Hence we must
be able to distinguish between selecting a language as container
(which includes all its descendants) versus selecting the language as
item (just the info file, not the descendants).  The language name
denotes the container.  The item has name 'language' within
the container.

Export stream and import stream
...............................

The Item.com_export method receives an ExportStream as its first
argument.  The sole method of interest for ExportStream is
write_record.  It takes any number of arguments, and writes them to
the stream, separating them with tabs and terminating the line with a
newline.  (One should include neither tabs nor newlines in the call to
write_record.)  The first field should always be the record type; see
the tables above.

The method Item.start_block writes the 'I' record that starts
the item block.

A call to Item.com_import receives two arguments: an ImportStream and
a type, which is the second field of the 'I' record.  

Conflicts
.........

When importing from a stream, an issue that arises is what to do when
the relpath given in the stream is already occupied by an item in the
corpus.  The answer depends on the item type and the value of the
**onconflict** import argument.

 * Lexicon: lexical entries are interned in the lexicon.  Lexical
   fields are included as long as they do not conflict with the current
   value.  If a conflict occurs, the onconflict argument indicates
   whether to 'reject' the stream value, 'override'
   the old value, reject and 'warn' the user, or signal
   an 'error'.

 * Rom: if the named romanization already exists,
   the onconflict argument determines what to do with the entire
   romanization.

 * Language: as for rom.

 * Text: regardless whether there is a conflict or not, a new text is
   allocated.

 * Notebook: same as for text.

Name mapping
............

In the case of texts and notebooks, during import a new item is always
allocated.  The relevant containers (language, glab) maintain a
mapping from stream-internal IDs to corpus IDs.  The intern_item
methods of the containers consult and update the table.

An complication arises in the case of texts.  Unlike with other items,
the position of a text in the corpus hierarchy is not uniquely determined by
its container name plus ID.  The information is encoded in two places in
the export stream.  A "relpath" entry is added to the text info file.
Toc items list their children in the textinfo file, which determines
not only the hierarchy but also the order.

.. automodule:: selkie.cld.corpus.export_file

Managing export files
---------------------

Export file format
..................

An export file conventionally has the file suffix 'ef'.
It is a tabular ASCII file; records are terminated with newline
and fields are separated by tabs.

The first field of each record contains the **record type,** which
determines the number and interpretation of the remaining fields.
The following table lists the record types, along with the
additional fields that a record of that type contains:

.. list-table::
   :header-rows: 1 5 5

 * - Record Type
   - Type
   - Additional Fields
 * - A
   - Media
   - media-suffix, user-name, filename
 * - A
   - Media
   - '__default__', media-suffix
 * - C
   - Snippet ("clip")
   - start, end, new-sentence-flag
 * - E
   - Translation ("English")
   - translation
 * - F
   - Lexical field name
   - index, long-name
 * - I
   - Start item
   - item-type, container-name, local-id, item-subtype, path
 * - L
   - Lexical entry
   - form, sense-number, lexical-field\*
 * - M
   - Metadata
   - attribute, value
 * - N
   - Notebook line
   - notebook-line
 * - P
   - Property
   - attribute, value
 * - R
   - Romanization record
   - romanized, unicode
 * - S
   - New translation unit
   -
 * - T
   - Token
   - form, sense-number, lpunc, rpunc

Records are grouped into **item blocks**.  An item block contains
all the information for a single item.
It begins with an 'I'
record and continues up to the next 'I' record or end of
file.  There are five types of item block, as follows:

 * Text —
   The item-type is 'text', the container-name is
   the language ID, the local-ID is numeric.  The item-subtype is one
   of: 'orig', 'media', 'toc', 'stub'.
   The path starts with the language ID, and gives the location of the
   text in the hierarchy of texts.
   The records that represent the contents of the text come in the
   following order:
   
    * 'P' records containing metadata.  The currently recognized
      attributes
      are: 'author', 'title', 'orthography', 'type', 'subtype'.
   
    * 'A' records identifying media files.
   
    * 'C' records giving snippet information.  Start and end are
      floating-point numbers representing time in seconds.
      New-sentence-flag is either 'True' or 'False'.
   
    * Mixed 'S' and 'T' records, representing tokenized text.  Each
      translation unit consists of an 'S' record followed by some number of
      'T' records, one for each token.
   
    * 'E' records, representing the translation.

   Not all texts have all blocks.  Only a media file has 'A' and 'C'
   records.  Media files and original texts both have 'S', 'T', and 'E'
   records.  The 'S' and 'T' records are obligatory for an original text.
   For a media file, they are optional, and represent the
   snippet contents, not translation units.  'E' records are always
   optional.  Texts of type 'toc' or 'stub' contain only 'P' records.

 * Lexicon —
   The item-type is 'lexicon', the
   container-name is the language ID, and the local-ID
   is 'lexicon'.  Item-subtype and path are empty.
   The contents consist of:

    * 'F' records containing field names.  Indices are sequential and
      begin at 0.
   
    * 'L' records containing lexical entries.  Each lexical field begins
      with *index* '=', followed immediately by the value.

 * Language —
   The item-type is 'language', the container-name is the
   language ID, the local-ID is 'language'.  Item-subtype and path
   are empty.  The contents consist of:

    * 'M' records, currently only a single record with attribute 'orthographies'.

 * Romanization —
   The item-type is 'rom', the container-name is 'roms', and the local-ID
   is the name of the romanization.  Item-subtype and path are empty.
   The contents consist of:

    * 'R' records.

 * Notebook - 
   The item-type is 'notebook', the container-name is 'glab', the
   local-ID has the form *user*/*number.*  The contents
   are:
   
    * 'N' records.  Everything after the first tab is one line from the
      original notebook file, unmodified.

