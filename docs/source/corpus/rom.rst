
``selkie.rom`` — Romanizations
==============================

Definition
----------

A **romanization** defines ASCII key sequences for entering
non-ASCII characters.  It can be thought of as a keyboard for entering
a non-roman script, or as an orthography.
For example, using the Salish romanization, one can
type ``l**x@c'`` to obtain the character sequence ƛ̣̓xəc̓.

In CLD, text stored in files is stored in romanized (ASCII) form.
It is easiest if we can associate a unique romanization with a given
language.  That is problematic in cases where different orthographies
are in use.  For example, Ojibwe is sometimes written using Canadian
syllabics.  We probably want to convert such texts to the "standard"
orthography before analyzing them.  The alternative is to treat
alternative orthographies as introducing variant forms of all words,
not an attractive option.

We store the romanizations in the toplevel directory ``roms``.
We need to be able to specify a separate registry.

Usage
-----

Romanizations provide one-way codecs: they can be used to
decode ASCII byte sequences, producing Unicode strings as output.  The
reverse mappings are not currently provided.

The romanizations currently defined are: ``'gothic'``, ``'gothic-student'``,
and ``'salish'``.
They are enabled when seal.nlp.rom is imported.
One uses them as one uses any decoder.  For example:

>>> import selkie.rom
>>> s = b'c*a'.decode('salish')
>>> from selkie.string import unidescribe
>>> unidescribe(s)
0 0x10d LATIN SMALL LETTER C WITH CARON
1 0x61 LATIN SMALL LETTER A

The string prints out as "ča."

There is also a ``decode()`` function:

>>> from selkie.rom import decode
>>> s2 = decode("a'tho:", 'gothic-student')
>>> unidescribe(s2)
0 0xe1 LATIN SMALL LETTER A WITH ACUTE
1 0xfe LATIN SMALL LETTER THORN
2 0x6f LATIN SMALL LETTER O
3 0x304 COMBINING MACRON

To convert the output to an ascii string containing HTML entities of
form ``&#dddd;`` for non-ascii characters:

>>> from selkie.rom import to_html
>>> to_html(s2)
b'&#225;&#254;o&#772;'

Decoder
-------

A Decoder applies a romanization.  It is similar to the reader
for a codec, but it maps text to text, not bytes to text.

The romanization behaves as a dict mapping strings to strings.  It is
interpreted as a prefix code.  At any point in the input
stream, the longest matching key is used to determine the output string
at that point.

If no key matches, the unicoder checks whether the next thing in
the input stream is one of the directives in the following table.  The first
thirteen are identical to escapes allowed in Python.
The symbol *d* represents any
octal digit (0-7), and *h* represents any hex digit (0-7, a-f, A-F).

.. list-table::

   * - \*newline*
     - A backslash followed by newline produces no output.
   * - \\
     - A literal backslash.
   * - \a
     - ASCII bell, U+0007.
   * - \b
     - ASCII backspace, U+0008.
   * - \f
     - ASCII formfeed, U+000C.
   * - \n
     - ASCII newline (line feed), U+000A.
   * - \r
     - ASCII carriage return, U+000D.
   * - \t
     - ASCII tab, U+0009.
   * - \v
     - ASCII vertical tab, U+000B.
   * - \*ddd*
     - The Unicode character whose codepoint, in octal,
       is *ddd.*  One to three digits may be given; the longest
       match will be taken up to three digits.
   * - \x*hh*
     - The Unicode character U+00*hh.*  Exactly two
       hex digits must be provided.
   * - \u*hhhh*
     - The Unicode character U+*hhhh.*  Exactly
       four hex digits must be provided.
       The named codepoint is inserted.
   * - \U*hhhhhhhh*
     - The codepoint U+*hhhhhhhh* is inserted.
       Exactly eight hex digits must be provided.
   * - \.*name*
     - *Name* consists of any mix of letters, digits,
       and underscore.  The longest match is taken.  To force a shorter
       match, when the next intended character is a letter, digit, or underscore,
       one may terminate the name with ``\.`` (backslash period).
       The unicoder switches to the named romanization.
   * - \[*name*
     - The unicoder switches to the named
       romanization, but pushes the old one on the stack.
   * - \]
     - The unicoder pops the previous romanization off the
       stack and resumes using it.
   * - \.
     - Produces no output, can be used to terminate
       *name* or *ddd.*

If the next thing in the input is not one of the romanization's keys,
and not one of the directives in the table, then
a single character is copied unmodified to the output.

A ``.rom`` file is loaded using ``load_dict()``
of ``seal.io``.  Keys may not be null.

To get Unicode characters into the value part of a .rom file, use numeric
escapes and pass it through Unicoder.

The function ``decoder`` produces a decoder for a given romanization,
and the function ``reader`` produces an input stream.

In Javascript, the coder
accepts strings or single characters via ``append()``.
The input must consist of seven-bit ASCII, so characters and code
points are the same.  There 
is no one-one correspondence between input characters and output characters, and in
some cases, lookahead is required to determine what the output sequence should be.
If the output sequence is still ambiguous, but no further input remains, one can
force all pending output to be produced by calling ``flush()``.

Defining a new romanization
---------------------------

TODO


Catalog
-------

To get a list of the defined romanizations:

>>> from selkie.rom import default_registry
>>> list(default_registry)
['korean', 'otw-webkamigad', 'salish', 'gothic', 'gothic-student', 'otw-jones']

To get the romanization itself, access the registry like a dict:

>>> salish = default_registry['salish']

The file in which the romanization resides is ``salish.filename``.
Calling ``print(salish)`` prints its contents.  One can also use
``salish.items()`` to get an iteration over the pairs, and
``salish.print_graph()`` to see the finite-state graph.

API
---

.. py:function:: load_rom(fn)

   Opens the file in binary mode.  Returns an iteration over (key,
   value) pairs.  The values are not expanded.

.. class:: Romanization

   .. py:method:: __init__([name], [fn])

      Initialize.  If *fn* is provided, `load_rom()` is used to read
      it, and the values are decoded.
      
   .. py:attribute:: name

      The name.

   .. py:attribute:: filename

      The filename.

   .. py:attribute:: start

      The start state.

   .. py:method:: __setitem__(k, v)

      Add a new association.

   .. py:method:: items()

      Calls `load_rom()` on its filename and returns the resulting
      iteration.

   .. py:method:: __str__()

      Prints the contents of the file.

   .. py:method:: print_graph()

      Prints out the state graph.

   .. py:method:: match(input, i=0)

      Finds the longest match in *input* beginning at index *i*.  The
      return value is a pair (j, value).

   .. py:method:: decode(input, output=None, errors='strict')

      Creates a Decoder from itself and calls it on *input* and *output*.
