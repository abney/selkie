
Tokenized text
**************

Tokenization
------------

Definition
..........

We use a simple whitespace-separated definition of *token.*
We strip off punctuation at the beginning and end of the token; what
remains is the **orthographic form.**  In addition, the
orthographic form may end with a **sense number** in the form of a
dot followed by one or more digits.

Hence, a token is conceptually the concatenation of four strings: leading
punctuation, the token proper, and trailing punctuation.  We classify
the token proper as a **word token** if it contains any alphabetic characters,
a **numeric token** if it contains digits but no alphabetic
characters, and a **miscellaneous token** otherwise.
For a word token, the ASCII string of the token proper is called an
**orthographic form.**  The orthographic form may subdivide into
word and sense number.

For example, consider the (nonsense) text::

   \`\`'ac, \$23 n\`a.1,'' 'ac,.

How this tokenizes depends on the romanization.  Let us assume a
romanization in which 'a represents &aacute;, \`a represents
&agrave;, and c, represents &ccedil;.  Then the tokenization is:

.. list-table::
   :header-rows: 1

   * - Type
     - Pre
     - Form
     - Post
   * - word
     - \`\`
     - 'ac,
     - 
   * - num
     - \$
     - 23
     - 
   * - word
     -
     - n\`a.1
     - ,''
   * - word
     -
     - 'ac,
     - .

Here the first column represents the token type, the
second column represents leading punctuation, the third contains
orthographic forms, and the fourth column
represents trailing punctuation.

The orthographic form n`a.1 subdivides into word n`a
and sense number 1.  Only word tokens may contain sense
numbers, and sense numbers are never obligatory.  A missing sense
number is equivalent to sense 0.

Token
.....

A **Token** instance has methods form, sense,
lpunc, rpunc, lexent, and unicode.
The value for unicode is provided by the romanization.  The
form does not include the sense number.  For a word token, the form
and sense number are used to find the entry in the lexicon (lexent);
non-word tokens have no lexent.

Annotation, whether of part of speech or word sense, is uniformly treated
via the sense number.  That
is, the sense division is maximally fine-grained.  A coarser-grained
distinction, such as part of speech, corresponds to a partition of the senses.
For example, fish.0 and fish.1 may both be noun senses,
whereas fish.2 and fish.3 are verb senses.

Limiting annotation to the addition of sense number allows one
to edit the annotated text as plain text.
One can edit the text in any plain-text editor, for example
rearranging words using cut and paste, and as long as orthographic
forms are not separated from their sense numbers, the annotation is
preserved.

Because a token without sense number is treated as having sense number 0,
unannotated text becomes a special case of annotated text.

Token file
----------

Sentences
.........

Tokenized text is represented by the class TokenFile, discussed below.
A token file consists of units that I will call **sentences,**
although the units are not necessarily actually sentences.
The defining feature of the units is that they are the units of
translation, hence a more accurate term
would be **translation unit.**  In
the code, the units are also sometimes called *paragraphs* or *segments.*
The class that represents them is TokenBlock.

Although sentences generally occur as elements in a token file, it is also
possible to create temporary sentences that are free-floating.

A token file behaves like a list of sentences, and a sentence's **index**
is its position in the list.  A sentence is also assigned a permanent
ID that is unique within the file.  IDs are assigned to sentences in
order of creation.  Because sentences may be
inserted, deleted, and reordered, a sentence's ID may well differ from
its index.

The sentence ID identifies the sentence uniquely only within its
file.  A sentence is uniquely identified within its language by its
**location,** which is a pair consisting of the text ID and the
sentence ID.  An ID is immutable and unique within its scope, but one
should not make any other assumptions.  In particular, a text ID is a
string but a sentence ID is an integer.

If *tf* is a token file, one may access a sentence either by
index or by ID::

   >>> s1 = tf[i]
   >>> s2 = tf.by_id(id)

One may create a new sentence by appending a string, which is
tokenized to create the sentence::

   >>> s3 = tf.append('foo bar baz')

It is assigned the next available ID and appended to the end of the file.

A sentence behaves like a list of Tokens::

   >>> token = s1[j]


PageEditor
----------

Pages and PageEditor
....................

A **page** is either a written page or a recording.  Viewed as a
page, a recording's content is its transcript, which always exists,
though it may be empty.  A page is represented by a Text instance,
since the page contents generally resides in multiple members of Text.
The original-language **plaintext** resides either in orig
or xscript, and the reference-language **translation** is
in trans.

A PageEditor
provides a UI view of a page.  The page resides in its file
member::

   >>> ped = app.follow('/langs/lang.oji/texts/text.3/toc/text.1/page')
   >>> ped
   <seal.cld.ui.page.PageEditor object at 0x...>
   >>> ped.file
   <Text langs/oji/texts/26/toc/14>
   >>> ped.file.title()
   'Lesson 8: Intransitive Inanimate Verbs'

The PageEditor constructor takes three arguments: the parent (of
class TextEditor), the text (of class Text), and
optionally the string 'nt' standing for "no translation."
The parent is accessible in the member __parent__, the text is
accessible in the member file, and whether or not a
translation should be included is recorded in the member
parallel::

   >>> ped.parallel
   True
   >>> tmp = app.follow('/langs/lang.oji/texts/text.3/toc/text.1/page.nt')
   >>> tmp.parallel
   False

Edit
....

The main view of a page is provided by the PageEditor.edit() method.
The displayed HTML page includes a number of links:

 * a 'Transcribe' button linking to xscript/edit
   or audio/edit, as appropriate.
   See Transcription.

 * ...

The home page is generated by the edit() method.
PlainTextPanel represents the central HTML element that displays
text with translation.
The PlainTextPanel contains javascript that may place a callback
to the PageEditor method edit_par().
It is described in the javascript section below.

Stub
....

Since this is a page, it has no toc.
If it also has no plaintext(), then it is a stub.

PlainTextPanel
--------------

PlainTextPanel widget
.....................

A PlainTextPanel is a widget.  The constructor takes four
arguments: the HTML page, the text's plaintext, the text's translation
(that is, the trans member), and a boolean parallel indicating whether
the translation should be displayed or not.
The panel renders as an H2 title "Text" followed by
a div that contains a table.  If parallel is true, there are
two columns in the table, with the
left column consisting of target-language paragraphs and the right column
consisting of English translations.  If parallel is false, the
right column is suppressed.

The div has ID textdiv.
The table has class ParallelText if there are two columns and
PlainText if there is only one.
Existing paragraphs are included in the generated HTML table.
New paragraphs are generated by javascript.

If the plaintext is of class TokenFile, it is editable.
Otherwise, the plaintext is a TranslationUnits object
representing a view of a transcript, in which case
it is read-only.

PlainTextPanel.js
.................

PlainTextPanel.js is activated by a call PlainTextPanel(*w,d*),
where *w* indicates whether the text is writable or not
and *d* indicates whether this text is derived from
an underlying transcription or not.
The PlainTextPanel instance contains the main control methods.

The script interacts with the server at five points.  Two of them are
merely buttons that cause a new page to be requested:

 * The "IGT" button visits the page igt.*i*/edit, where *i*
   is the current paragraph (row) number.

 * The "audio" button visits the page ../audio/tunit.*i*,
   where *i* is the current paragraph (row) number.

The remaining three points of interaction are ajax calls.  All are
calls to the same server-side method, namely, edit_par().
Each nominally applies to a single cell of the matrix.
In the callback, one specifies an operation and the text that the user entered.

 * The main interaction with the user is when the user enters a
   paragraph in the text box.  When 'enter' is pressed or 'commit'
   is clicked, a callback is placed.  The operation is 'insert' if this is a new
   paragraph and 'replace' if it is an old paragraph.

 * If the text box is empty when the user finishes, and the
   paragraph is not a new one, a callback is placed whose operation is
   'delete'.

 * If the user clicks the little 'X' button inside a box, a
   callback is placed with operation 'delete'.

The server-side method is edit_par(*op, i, j, s*).
As we have seen, *op* is one of 'insert', 'replace', or 'delete',
*i* is the paragraph (row) number and *j* is the column number (0 =
original, 1 = translation), and *s* is the (ASCII) text that the user
entered.  *S* is ignored if *op* is 'delete'.
The callback nominally applies to only one cell of the matrix: *j* is
required to be either '0' or '1'.
However, deletion affects the entire row,
and insertion is only permitted with *j* = '0', and causes an empty
translation cell to be inserted.
The argument *s* is the text that the user typed into the text box; it is
only meaningful for 'insert' and 'replace'.
In the cases where *s* is provided, the script
expects the server to send back an answer, which is the text in the
native orthography (Unicode) for display.

The calls are passed on to the PageWriter for the editor's page.
Specifically, an 'insert' call translates to insert_par(*s,i*);
an 'insert' call translates to set_orig(*i,s*)
if *j* is '0' and set_trans(*i,s*) if *j* is
'1'; and a 'delete' call translates to delete_par(*i*).
In addition, *s* is converted to Unicode, using the text's
romanization if *j* is '0' and the default romanization if *j*
is '1', and the Unicode is sent back to the script.

IGT
---

IGTEditor
.........

An IGTEditor displays a single tokenized text block with its
translation.  There are two panels: the left panel displays text and
translation, and the right panel displays lexical entries when one
clicks on tokens.  The right panel consists of a LexentViewer
element.

The edit() method generates the IGT editor page.  It explicitly
includes IGTEditor.css and IGTEditor.js.  The latter in
turn includes LexentViewer.js.  The editor page also includes
the script initialization IGTEditor(*p*,*t*) where *p* is the
paragraph index (as a string) and *t* is the token index (as a string)
or null.

LexentViewer
............

A LexentViewer constitutes the right panel in an IGT display.
It is a widget; its contents are generated by the LexentViewer.js
script.  The LexentViewer launches the script by placing the
call new LexentPanel(*v*,*l*), where *v* is the viewer URL,
e.g. 'edit.0;lexentViewer;', and *l* is the language URL,
e.g.::

   /cgi-bin/cldx/langs/lang.oji/

LexentPanel
...........

A LexentPanel is a Javascript object created on the client side.

The entry point is the creation of a LexentPanel, as described.
