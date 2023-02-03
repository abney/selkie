
``selkie.string`` — Strings
===========================

The code examples assume:

>>> import selkie.string as ss


ASCII representations
---------------------

.. py:function:: as_ascii(s)

   Returns a string containing only ASCII
   characters.  Define an "objectionable" character to be a
   non-printing character other than space, a non-ASCII
   character (code point 128 or higher), DEL, and left and right brace.
   If the input string contains no objectionable characters, it is returned unchanged.
   Otherwise, all objectionable characters are eliminated.  What they are
   replaced with depends on the value of the argument ``use.``
   If ``'names',`` Unicode character names are used.  If ``'hex',``
   hex codes are used.  If ``'alts',`` alternative single characters
   are used, where available, and deletion otherwise.  If None,
   objectionable characters are deleted.  The default is ``'hex'.``
   
   >>> ss.as_ascii('h\u00ff\n')
   'h{ff}{nl}'
   >>> ss.as_ascii('h\u00ff', use='names')
   'h{LATIN SMALL LETTER Y WITH DIAERESIS}'
   
   If the input is not a string, \verb|as_ascii()| calls ``str()`` on
   it.
   
   >>> ss.as_ascii(10)
   '10'

.. py:function:: ascii_chars(s)

   The function ``ascii_chars()`` is more aggressive and less flexible.
   It does "smart quote" and "smart dash" substitutions, and it replaces
   tab with space, vertical tab with newline, and form feed with
   newline.  All characters above code point U+00fe (~) are deleted, as
   are all characters with code point below U+0020 (space) except newline.
   Returns an iteration over characters.

.. py:function:: deaccent(s)

   Converts a Unicode string to ASCII in a
   lossy way.  It replaces characters in the Latin-1
   range with corresponding ASCII characters, where natural
   correspondences exist.  Characters without a natural ASCII counterpart
   are simply deleted.  ASCII control characters other than space, tab,
   newline, and carriage return are deleted.  The return value is an ASCII string.

.. py:function:: as_boolean(s)

   Converts the strings ``'True'`` and ``'False'`` to the
   corresponding boolean values.  Given anything else, it signals an
   error.

Unicode
-------

.. py:function:: unidescribe(s)

   Takes a string and prints out the details of the Unicode characters
   it contains.

   >>> ss.unidescribe('hi')
   0 0x68 LATIN SMALL LETTER H
   1 0x69 LATIN SMALL LETTER I

.. py:function:: utf8(s, fn)

   Writes string *s* to
   the file named *fn* in UTF-8 format.  It overwrites the file, if it
   already exists.  If no filename is given, the bytes of the UTF-8
   representation are printed out readably.


Miscellany
----------

.. py:function:: quoted(s)

   Takes a string and wraps double-quotes
   around it, escaping any internal double-quotes with backslashes.  It
   also doubles any internal backslashes, and replaces newline with
   backslash-en.

   >>> ss.quoted('L\u00ffc')
   '"Lÿc"'

   The return value is a string suitable for printing, or suitable for use in
   JSON.

.. py:function:: trim(w, s)

   It first calls ``as_ascii()`` on the string, and then it
   truncates it at the field width.

.. py:function:: dtstr(t)

   Takes a float representing seconds since the epoch, and returns a
   readable string representation.

   >>> ss.dtstr(1000000000)
   '2001-09-08 21:46:40'

.. py:function:: elapsed_time_string(t0, t1)

   *T0* and *t1* represent start time and end time
   in seconds.

   >>> ss.elapsed_time_str(10, 135)
   '0:02:05.0000'

.. py:function:: sizestr(sz)

   Takes an int representing a number of bytes
   and returns a string with three digits after the decimal, suffixed
   with B, KB, MB, GB, TB, or PB.

   >>> ss.sizestr(123456789)
   '123.457 MB'

.. py:function:: expand_envvars(s)

   Replace the pattern ``${VAR}`` with the value of the environment
   variable ``VAR``, wherever the pattern occurs in *s*.
