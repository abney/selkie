
Version and config
==================

There are two items in the toplevel selkie module, outside of all
submodules.

 * ``selkie.__version__`` is a string giving version information (major.minor.patch).

 * ``selkie.config`` is a dict that is loaded from the Selkie
   configuration file. If the environment variable ``SELKIE_CONFIG`` is
   set, it will be used as the configuration file pathname. Otherwise,
   the pathname is ``~/.selkie.json``. The contents are in standard JSON
   format. They must be enclosed in braces, which is to say, they must
   define a dict.

   Various pieces of Selkie's functionality make use of settings in
   ``selkie.config.`` Each is documented separately.

Command line
------------

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
