
Selkie command line
===================

Invoked as::

   $ python -m selkie COM ARG ...

One can generally substitute ``-`` for a filename to mean stdin/stdout.

The commands are:

 * ``get`` — Extract a range of lines from a file. Arguments:
   filename, start line number (counting from 0), end line number
   (counting from 0).

 * ``ud`` — Unicode dump. Prints each line of the file, followed by
   one line for each character, giving the hex code and description of
   the Unicode character.
