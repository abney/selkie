
.. module:: selkie.io
   :synopsis: Input/output functionality

``selkie.io`` — Input/output functionality
==========================================

The ``selkie.io`` module contains functionality related to files and
directories.

Filenames
---------

Selkie uses the Path objects of pathlib: see
https://docs.python.org/3/library/pathlib.html and the temporary-file
facilities in tempfile (https://docs.python.org/3/library/tempfile.html).

.. py:function:: ispathlike(x)

   Returns True if *x* is something that can be passed to ``open()``.
   To be precise, it returns True just in case *x* is a string or
   implements the method ``__fspath__()``.

**Suffixes** — A filename suffix is defined to be the empty string if the filename
contains no dot, and the substring following the last dot, if it
contains a dot.  (In the case of a pathname, we limit attention to the
final pathname component.)

.. py:function:: get_suffix(fn)

   Takes a filename and returns the suffix (without dot), or ``''``, if there is no dot.

.. py:function:: strip_suffix(fn)

   Takes a filename and returns it without the suffix, if any.  The dot is also stripped.

.. py:function:: split_suffix(fn)

   Takes a filename and returns a pair (*f*, *s*) where *f* is the
   filename without the suffix (if any), and *s* is the suffix
   (without the dot).  If there is no suffix, *s* is the empty string.


Location
--------

A ``Location`` generalizes over local and remote files.  It may be
created from a string::

   >>> from selkie.io import Location
   >>> f1 = Location('abney@login.itd.umich.edu:scratch/foo')

It has three members: ``user``, ``host``, and ``pathname``::

   >>> f1.user
   'abney'
   >>> f1.host
   'login.itd.umich.edu'
   >>> f1.pathname
   'scratch/foo'

A local file has value ``None`` for ``user`` and ``host``::

   >>> f2 = Location('/tmp/foo')
   >>> f2.user is None and f2.host is None
   True
   >>> f2.pathname
   '/tmp/foo'

Alternatively, a ``Location`` may be created from ``user``, ``host``, and ``pathname``::

   >>> f3 = Location(host='login.itd.umich.edu', user='abney', pathname='scratch/bar')

Note that tilde is expanded, though this only works for local files::

   >>> from os.path import expanduser
   >>> f4 = Location('~/scratch/test')
   >>> f4.pathname == expanduser('~/scratch/test')
   True

There are several predefined locations:

.. list-table::

 * - ``Tmp``
   - The directory ``/tmp``.
 * - ``Dest``
   - The directory where Selkie is installed.
 * - ``Bin``
   - The ``bin`` subdirectory of ``Dest``.
 * - ``Examples``
   - The ``examples`` subdirectory of ``Dest``.
 * - ``Data``
   - The ``data`` subdirectory of ``Dest``.


.. py:class:: selkie.io.Location

   A ``Location`` instance has a collection of methods for ease of
   examining and manipulating the file.
   
   .. py:method:: join(s)

      Returns a new location with an added pathname component.
   
   .. py:method:: __div__(other)

      A synonym for ``join()``.
   
   .. py:method:: __add__(other)

      Adds a suffix.
   
   .. py:method:: is_remote()

      Whether the location is on a remote host.
   
   .. py:method:: to_filename()

      Returns the ``pathname``, but signals an error if not local.
   
   .. py:method:: parent()

      Location representing the parent directory.
   
   .. py:method:: name()

      The last component of the pathname.
   
   .. py:method:: split()

      Returns (parent directory, name).  The parent directory is a ``Location``.
   
   .. py:method:: exists()

      Whether the named file exists.
   
   .. py:method:: is_mounted()

      Mac-specific.  If the pathname begins with ``'/Volumes'``, it
      returns true just in case the toplevel directory under
      ``'/Volumes'`` exists.  If the pathname does not begin with
      ``'/Volumes'``, it always returns true.  Signals an error for a
      remote location.
   
   .. py:method:: islink()

      Whether the named file is a symbolic link.
   
   .. py:method:: isdir()

      Whether the named file is a directory.
   
   .. py:method:: size()

      Returns the file size.
   
   .. py:method:: modtime()

      Returns the file modtime, a float representing seconds since the epoch.
   
   .. py:method:: readable()

      Whether I can read it.  Optional arg ``forwhom`` may be ``'me'``
      (the default), ``'owner'``, ``'group'``, or ``'other'``.
   
   .. py:method:: writable()

      Whether I can write it.  Optional arg ``forwhom``
      may be ``'me'`` (the default), ``'owner'``, ``'group'``, or ``'other'``.
   
   .. py:method:: executable()

      Whether I can execute it.  Optional arg ``forwhom``
      may be ``'me'`` (the default), ``'owner'``, ``'group'``, or ``'other'``.
   
   .. py:method:: permit(a)

      Change the permissions to allow *a*, which is a
      string which may contain ``'r'``, ``'w'``, and ``'x'``.
      Optional second argument may be a string or list of strings, chosen from:
      ``'owner'``, ``'group'``, ``'other'``, ``'all'``, ``'me'``.
      Default: ``'me'``.
   
   .. py:method:: deny(a)

      Change the permissions to disallow *a*.  Same second
      argument as ``permit()``, but default is ``'all'``.
   
   .. py:method:: md5()

      Returns the MD5 hash (a string).  Prints a message
      unless ``silent=True`` is specified.
   
   .. py:method:: is_under(d)

      Whether or not *d* (a ``Location``) is an ancestor of this location.
   
   .. py:method:: open([mode, makedirs])

      With no arguments, open for reading.
      with mode ``'w'`` and makedirs=True,
      open for writing, doing ``mkdir -p`` on the parent.
   
   .. py:method:: tabular(*m*)

      The argument *m* is the mode for opening the
      file.  Keyword arguments ``encoding`` and ``separator`` are also
      accepted.  Should be called within a ``with`` clause.  If opened for
      reading, the file is an iterator over tuples of fields (strings), one
      per line.  If opened for writing, call its ``write()`` method; each
      argument is converted to a string and written as a field.  Default
      value for ``separator`` is tab.  Setting it to ``None`` causes any
      amount of whitespace to be a field separator, and trims leading and
      trailing whitespace.
   
   .. py:method:: read()

      Returns the contents of the file.  Takes keyword
      argument ``encoding``.  Value ``'bytes'`` causes the raw contents
      to be returned.
   
   .. py:method:: listdir()

      Returns an iteration over the names in this
      directory.  If it does not exist, returns an empty iteration.  If it
      exists but is not a directory, signals an error.</dd>
   
   .. py:method:: items()

      Like ``listdir()``, but returns pairs (``name``, ``loc``), where
      ``loc`` is the child ``Location``.
   
   .. py:method:: __call__()

      Calls ``os.system()`` on this file.  Returns ``True`` if the
      system call returns 0, ``False`` otherwise.
   
   A ``Location`` instance also provides the following system
   calls.  These can be disabled by setting ``DryRun = True``.
   
   .. py:method:: assure_parent()

      Create the parent directory if it does not exist.
   
   .. py:method:: make_directory()

      Create a directory.
   
   .. py:method:: copy_to(t)

      Copy this file to *t*.
   
   .. py:method:: copy_from(s)

      Copy *s* to this file.
   
   .. py:method:: move_to(t)

      Rename this file to *t*.
   
   .. py:method:: delete_file()

      Delete this file.
   
   .. py:method:: delete_directory()

      Delete this empty directory.
   
   .. py:method:: delete_hierarchy(s)

      Nothing will be
      deleted outside of the "sandbox" directory *s*.
   
   .. py:method:: make_writable()

      Change permission to writable.  If
      this is a directory, applies recursively, unless ``recurse=False``
      is specified.

Some examples::

   >>> from selkie.io import Tmp
   >>> Tmp/'my'
   /tmp/my
   >>> Tmp.join('my')
   /tmp/my
   >>> foo = Tmp/'my'/'foo'
   >>> foo + '.txt'
   /tmp/my/foo.txt
   >>> f1.is_remote()
   True
   >>> foo.is_remote()
   False
   >>> foo.parent()
   /tmp/my
   >>> isinstance(_, Location)
   True

The file ``make_repo_example`` in the ``Examples`` directory
is a shell script that creates a little example repository ``/tmp/my/foo``,
as well as the file ``/tmp/config`` and the empty directory ``/tmp/cp``.
Note that function call
takes precedence over division, making the parentheses necessary in
the second line::

   >>> from selkie.io import Examples
   >>> (Examples/'make_repo_example')()
   True
   >>> foo.exists()
   True
   >>> foo.isdir()
   True
   >>> file1 = foo/'bar'/'pkgex.pkg.sh'
   >>> file1
   /tmp/my/foo/bar/pkgex.pkg.sh
   >>> file1.exists()
   True
   >>> file1.size()
   161
   >>> file1.md5()
   Computing md5 hash for /tmp/my/foo/bar/pkgex.pkg.sh ... ok
   '69962bf31dd38a8e7f5ef9fc3858cc7c'

The following is an example of using ``tabular``::

   >>> with (Tmp/'config').tabular() as f:
   ...     for record in f:
   ...         print(record)
   ...
   ['repo', 'foo', '/tmp/my/foo', '/tmp/cp/foo', '/tmp/inst']
   ['active', 'foo', 'my.host.com:/home/me/foo']

Predefined locations
^^^^^^^^^^^^^^^^^^^^

The following variables name fixed directories:

Dest
   The destination directory in which Selkie is installed.

Bin
   The ``bin`` subdirectory.

Examples
   The ``examples`` subdirectory.

Data
   The ``data`` subdirectory.

Tmp
   The directory ``/tmp``.

As a convenience shorthand, ``L(*s*)`` creates a local Location with
pathname *s*.  One can use this to refer to the current working directory
``L('.')``, the parent directory ``L('..')``, and one's home
directory ``L('~')``.

Infiles and outfiles
--------------------

.. py:function:: infile(fn)

   The function ``infile()`` returns an input stream.::
   
      >>> from selkie.io import infile
      >>> from selkie.misc import as_ascii
      >>> [as_ascii(line) for line in infile(ex.text1.utf8)]
      ['f{e1} f{e1}{nl}', 'ki{014b} ko{014b}{nl}']
   
   Note that U+E1 is *a* with an acute, and U+014B is engma::
   
      >>> import unicodedata
      >>> unicodedata.name('\u00e1')
      'LATIN SMALL LETTER A WITH ACUTE'
      >>> unicodedata.name('\u014b')
      'LATIN SMALL LETTER ENG'
   
   In addition to accepting a string as filename, some cases are treated specially:
   
    * If the argument is ``'-'``, then the return value is ``sys.stdin``.
    * If the argument begins with letters (non-empty, only alphabetic)
      followed by a colon, it is interpreted as a URL.
    * If the argument is an open file whose mode begins with ``'r'``,
      or a ``StringIO`` instance, or an object with a ``readline()``
      method, it is passed through.
   
   Note that ``ex`` and its extensions, such as ``ex.text1``, are of
   type ``Fn``, which is a subclass of ``str``.
   
   To provide a string as contents, rather than filename, wrap it in ``StringIO``::
   
      >>> from io import StringIO
      >>> list(infile(StringIO('This is a test.\nOnly a test.\n')))
      ['This is a test.\n', 'Only a test.\n']

.. py:function:: outfile(fn)

   The function ``outfile()`` returns an output file::
   
      >>> from selkie.io import outfile, close, contents
      >>> fn = tmpfile()
      >>> f = outfile(fn)
      >>> print('Hello', file=f)
      >>> close(f)
      >>> contents(fn)
      'Hello\n'
   
   Regarding the argument to ``outfile()``, there are again some
   cases that are treated specially:
   
    * The filename ``Fn('-')`` represents ``sys.stdout``.
    * If the argument is omitted or is ``None``, output is accumulated as a string, which
      can be retrieved using ``getvalue()``.::
   
         >>> f = outfile()
         >>> f.write('hi there\n')
         9
         >>> f.write('bye\n')
         4
         >>> f.getvalue()
         'hi there\nbye\n'


Load and save functions
-----------------------

File Format
^^^^^^^^^^^

The `FileFormat` class takes a read and write function, and provides
`load()`, `parse()`, and `save()`.

.. py:class:: FileFormat

   .. py:method:: __init__([name], [read], [write], [encoding]):

      The argument *read* is the read function and *write* is the write
      function.  The read function is given an open stream, and should
      return a JSON object.  The write function is given a JSON object
      and a stream open for writing, and should write the object in
      the format that the read function expects.  If *encoding* is
      False, the read and write streams are opened in binary mode.
      Otherwise, *encoding* is passed to `open()`.

   .. py:method:: load(fn)

      Opens the named file, calls the read function on the open file,
      and returns the result.

   .. py:method:: parse(s)

      The argument *s* is the string contents of a file.  Wraps a
      string reader around *s* and calls the read function on it,
      returning the result.

   .. py:method:: save(x, fn):

      Opens *fn* for writing and calls the write function on *x* and
      the open file.

The following file formats are currently available:

.. py:data:: LineFormat

   The read function returns a list of the lines of the file.
   Carriage return and newline are stripped from each line.

.. py:data:: TabularFormat

   Each line of the file represents a record, with fields separated by
   tab.  The read function returns a list of records, where a record
   is a list of strings.

.. py:data:: KVIFormat

   The `read_kvi()` and `write_kvi()` functions are used.

.. py:data:: JsonFormat

   Reads and writes JSON format.

.. py:data:: BlockFormat

   Uses ``read_record_blocks()`` and ``write_record_blocks()``.


General
^^^^^^^

There is a series of paired "load" and "save" functions for
different kinds of contents.  They build on unicode input and output
streams, and inherit the same conventions regarding their filename
arguments.

Where it makes sense, there is also an "iter" function corresponding
to each "load" function.  The "iter" function returns a
generator, and the "load" function returns a list.  However, there is no
"iter" function corresponding to ``load_string()`` or ``load_dict()``.

Close unicode.
^^^^^^^^^^^^^^

The definitions of the "save" functions all have a similar outline::

   def save_x (x, filename=None):
       f = outfile(filename)
       ...
       return close(f)

The function ``close_unicode()`` will close the file *unless*
it is ``sys.stdout``.  If the file was created with no filename,
``close_unicode()`` gets the string contents before closing the
file, and its return value is the string contents.  Otherwise, the
return value is ``None``.

Strings
^^^^^^^

.. py:function:: load_string(fn)

   The function ``load_string()`` returns the entire contents of a
   file as a unicode string.::
   
      >>> from selkie.io import load_string
      >>> load_string(ex.text1)
      'This is a test.\nIt is only a test.\n'

.. py:function:: save_string(s, fn)

   The companion function ``save_string()`` does the opposite::
   
      >>> from selkie.io import save_string
      >>> fn = tmpfile()
      >>> save_string('f\u00e1\n', fn)

Lines
^^^^^

.. py:function:: load_lines(fn)

   The function ``load_lines()`` returns the
   lines of a file, *without* the trailing newline characters.::
   
      >>> from selkie.io import load_lines
      >>> load_lines(ex.text1)
      ['This is a test.', 'It is only a test.']

.. py:function:: iter_lines(fn)

   Returns a generator instead of a list.

.. py:function:: save_lines(lines, fn)

   The function ``save_lines()`` takes an iterator over strings.  Each
   becomes a line of the file.  Newline characters are added.::

      >>> from selkie.io import save_lines
      >>> fn = tmpfile()
      >>> save_lines(['foo', 'f\u00e1'], fn)
   
   One can then confirm the contents::

      >>> [as_ascii(line) for line in infile(fn)]
      ['foo{nl}', 'f{e1}{nl}']

Records
^^^^^^^

A **record** is a list (more generally, a sequence) of strings
representing field values.  On disk, each record is a line and
field values are separated by tabs.  A file containing such records is a
**tabular file**.

.. py:function:: load_records(fn)

   The function ``load_records()`` takes a filename and returns a list of records,
   representing the contents of the file.::

      >>> from selkie.io import load_records
      >>> load_records(ex.tab1.tab)
      [['foo', '42'], ['bar', '15']]
   
   Optionally, one can specify the field separator by providing the
   keyword argument ``separator``.  The default separator is tab.  A
   value of ``None`` means that any amount of whitespace constitutes a
   separator, and leading and trailing whitespace are ignored.

.. py:function:: iter_records(fn)

   There is also a function ``iter_records()`` that returns a
   generator instead of a list.  It takes the same ``separator``
   argument as ``load_records()`` does.
   In addition to the method ``next()``,
   which all generators support, the ``iter_records()`` generator also
   supports the method ``error()``, which takes an an error message and
   signals an error,
   indicating the filename and line number of the most recently read
   record.

.. py:function:: save_records(records, fn)

   The function ``save_records()`` takes an iterator over records
   and writes them to a file.::

      >>> from selkie.io import save_records
      >>> recs = [('1', 'hi'), ('2', 'lo'), ('3', 'bye')]
      >>> fn = tmpfile()
      >>> save_records(recs, fn)
      >>> load_records(fn)
      [['1', 'hi'], ['2', 'lo'], ['3', 'bye']]
   
   One can optionally specify the ``separator``.

Dict
^^^^

A dict is represented on disk as a tabular file with two columns: key
and value.

.. py:function:: load_dict(fn)

   The function ``load_dict()`` reads a dict from a tabular file.
   If there are duplicate keys in the file, only the last copy has any effect:
   earlier values get overwritten.::

      >>> from selkie.io import load_dict
      >>> d = load_dict(ex.tab1.tab)
      >>> sorted(d)
      ['bar', 'foo']
      >>> d['foo']
      '42'

.. py:function:: save_dict(d, fn)

   The function ``save_dict()`` takes a dict and writes it to a file.
   Keys and values must all be strings.

Nested dict
^^^^^^^^^^^

A nested dict is specified with dotted keys and values.  One or more
whitespace characters serve as separator between key and value.
For example, the following is the contents of ``ex.nivre.exp``::

   command selkie.dp.nivre
   dataset spa.orig
   features nivre-2007
   nulls True
   split.feature fpos.input.0
   split.cpt.s 0
   split.cpt.t 1
   split.cpt.d 2
   split.cpt.g 0.2
   split.cpt.c 0.5
   split.cpt.r 0
   split.cpt.e 1.0

The function ``load_nested_dict()`` creates a dict in which the
keys are ``'command'``, ``'dataset'``, ``'features'``, ``'nulls'``,
and ``'split'``.  The value for ``'split'`` is a subdict with
keys ``'feature'`` and ``'cpt'``, and within the subdict, the
value for ``'cpt'`` is a sub-subdict.

Paragraphs
^^^^^^^^^^

A paragraph is a maximal block of lines not containing an empty line.

.. py:function:: load_paragraphs(fn)

   The function ``load_paragraphs()`` reads a file and returns a list
   of paragraphs.::

      >>> from selkie.io import load_paragraphs
      >>> load_paragraphs(ex.par1.txt)
      ['This is\na test.\n', 'It is only\na test.\n']

.. py:function:: save_paragraphs(paras, fn)

   The function ``save_paragraphs()`` takes an iterator over
   paragraphs and writes each to the named file.  An empty line is written as
   a separator before each paragraph except the first.

Blocks
^^^^^^

A block is a contiguous sequence of non-empty lines.  Separators
between blocks consist of one or more empty lines.  A block is
represented as a list of lines; carriage return and newline are
stripped from the lines.

.. py:function:: iter_blocks(fn)

   The function ``iter_blocks()`` reads a file and generates a sequence of
   blocks.  

.. py:function:: load_blocks(fn)

   The function ``load_blocks()`` converts the generator to a list.::

      >>> from selkie.io import load_blocks
      >>> load_blocks(ex.par1.txt)
      [['This is', 'a test.'], ['It is only', 'a test.']]

.. py:function:: save_blocks(blocks, fn)

   The function ``save_blocks()`` takes an iterator over blocks (lists
   of lists of strings) and writes each to the named file.  An empty line
   is written as separator between each pair of blocks.

Record blocks
^^^^^^^^^^^^^

A record block is a contiguous sequence of non-empty records.  One or
more empty records (i.e., empty lines) separate record blocks.  A
record block is represented as a list of lists, each record being a
list of fields (strings).

Tokens
------

Files that contain something comparable to code---for example, grammar
files or files containing predicate-calculus expressions---are treated
as sequences of tokens.

Load, Iterate, Tokenize
^^^^^^^^^^^^^^^^^^^^^^^

A first step in processing natural-language text is to convert it to
tokens.
   
.. py:class:: Token

   .. py:attribute:: type
   
      The class ``Token`` is a specialization of ``str``.  It has an
      additional attribute ``type`` whose value is ``'word'``, ``'eof'``,
      or one of the six delimiter characters ``()[]{}``.
      No token whose type is ``'eof'`` is ever returned by the tokenizer, but
      it is used as an end-of-file sentinel.  Functions that test for types
      can also use the pseudo-type ``'any'`` which matches anything except
      ``'eof'``.
   
   .. py:attribute:: quotes

      Quoted strings are returned as independent tokens, but they are not
      distinguished in type from unquoted words: both quoted and unquoted strings
      have the type ``'word'``.  One can tell the difference, however, by
      examining the attribute ``.quotes``, whose value is either
      "'" or '&quot;' for a quoted string, and ``None``,
      for an unquoted string.  Backslash is an
      escape character inside of a quoted string, but nowhere else.

   .. py:attribute:: line

      The line number, the first line of the file being line 1.

   .. py:attribute:: offset

      The offset counted from the beginning of the line.

   .. py:method:: error(msg)

      Tokens support the method ``error()``, which takes an error message
      and raises an exception in which line and offset are included in the
      message.

   .. py:method:: warning(msg)

      Prints a warning instead of raising an exception.

.. py:function:: load_tokens(fn)

   The function ``load_tokens`` interprets a file (or string) as a list
   of tokens.  The default token definition is kept intentionally simple: quoted
   strings are recognized, the delimiters ``()[]{}`` are recognized as
   special characters, unquoted space separates tokens, and ``#``
   begins a comment.  (It is possible to customize the syntax: see
   Syntax below.)::

      >>> print(load_string(ex.tok1), end='')
      12 + foo(bar=42.0, baz="hi there")
      >>> from selkie.io import load_tokens
      >>> load_tokens(ex.tok1)
      ['12', '+', 'foo', '(', 'bar=42.0,', 'baz=', 'hi there', ')']
   
   In addition to tokens, the file may contain whitespace and comments,
   which are discarded.
   Whitespace is anything that is deemed to be whitespace
   by ``isspace()``.  Newlines are not treated specially.
   Comments begin with ``#`` and continue to the end of the
   line.

.. py:function:: iter_tokens(fn)

   The function ``iter_tokens()`` returns a tokenizer, which
   implements the standard ``next()`` method, but also provides
   finer-grained control.  See :py:class:`Tokenizer`.

.. py:function:: tokenize(s)

   The function ``tokenize(s)`` simply converts its input to a
   pseudo-file (using ``String.IO``) and calls ``iter_tokens()``.

.. py:class:: Tokenizer

   .. py:method:: token()

      First, one can peek at the next token
      using the ``token()`` method.::

         >>> from selkie.io import iter_tokens
         >>> toks = iter_tokens(ex.tok1)
         >>> toks.token()
         '12'
         >>> tok.type
         'word'
         >>> tok.line
         1
         >>> tok.offset
         0
   
      At the end of file, ``toks.token()`` will exist, but its type will be
      ``'eof'``.

   .. py:method:: has_next(typ)

      The method ``has_next()`` can be used to test the type of the next
      token, without consuming it.::

         >>> toks.has_next('word')
         True
         >>> toks.has_next('eof')
         False
      
      Calling ``has_next()`` with no argument is equivalent to calling it
      with the argument ``'any'``.::

         >>> toks.has_next('any')
         True
         >>> toks.has_next()
         True
      
      The ``has_next()`` method can also be used to test for a particular
      token string, by providing the keyword ``string``.  For example::

         >>> toks.has_next(string='12')
         True
      
      For a special-character token, the type and string are identical.::

         >>> next(toks)
         '12'
         >>> next(toks)
         '+'
         >>> next(toks)
         'foo'
         >>> toks.token()
         '('
         >>> toks.token().type
         '('
         >>> toks.has_next('(')
         True

   .. py:method:: __bool__()

      The boolean value of the iterator is ``True`` if there are any
      tokens remaining, and ``False`` if it is at EOF.::

         >>> bool(toks)
         True
         >>> notoks = iter_tokens(StringIO())
         >>> bool(notoks)
         False

   .. py:method:: accept(typ)
   
      The method ``accept()`` tests whether the next token has a given
      type; or, with the keyword ``string``, it tests for the identity of
      the next token.  If the next token satisfies the specification, it is
      consumed from the stream and returned.  If not, ``accept()`` returns
      ``None``.  For example,::

         >>> toks.accept('word')
         >>> toks.accept('(')
         '('
   
   .. py:method:: require(typ)
   
      The method ``require()`` is like ``accept()``, except that it
      signals an error if the specification is not satisfied.::

         >>> toks.token()
         'bar=42.0,'
         >>> toks.require(')')
         Traceback (most recent call last):
             ...
         Exception: [.../examples/tok1 line 1 char 9] Expecting ')'
         >>> toks.require('word')
         'bar=42.0,'
         >>> toks.token()
         'baz='
         >>> toks.require(string='baz=')
         'baz='
      
      Note that ``require()`` returns ``None`` if eof is required::

         >>> notoks.require('eof')
         >>>

Syntax
^^^^^^

The tokenizer can be configured by supplying a ``Syntax`` object.
For example::

   >>> from selkie.io import Syntax
   >>> syn = Syntax(special='()[]{}.,:=', eol=True)
   >>> out = load_tokens(ex.tok1, syntax=syn)
   >>> out[4:10]
   ['bar', '=', '42', '.', '0', ',']

The ``Syntax`` constructor takes the following keyword arguments.

 * ``special``.
   We distinguish between the "hard" special characters
   ``'&quot;#`` and the "soft" special characters ``()[]{}``.
   The choice of hard special characters cannot be modified, but one can
   supply a different set of soft special characters.  The value should
   be either a string (interpreted as a set of characters) or ``True``.  The value ``True`` means that all
   characters except alphanumerics are special.  (Underscore is
   considered to be an alphanumeric character.)
   If ``special`` is omitted, one gets the default soft special
   characters ``()[]{}``.

 * ``eol``.  If the value is ``True``, then
   newlines are returned as tokens.
   Only newlines at the end of non-empty lines are returned
   as tokens.  A line consisting solely of a comment is considered empty.
   The default value is ``False``, in which case newline is treated
   simply as whitespace.

 * ``comments``.  The value may be ``True`` (the default),
   something that is boolean false, or a string containing one or more
   characters that introduce comments.  A value of ``True`` is
   equivalent to ``'\#'``, and a boolean false value is equivalent to
   ``&quot;``.  Comments begin with any comment character and continue to
   the end of the line.

 * ``multi``.  The value should be ``None`` (the default) or a list of
    strings.  If strings are provided, the tokenizer recognizes them as
    multi-character specials.  For example, one might specify::

       multi=['->']

 * ``backslash``.  If the value is ``True`` (the default), then
   backslash escapes are recognized within quoted strings in the usual
   way.  If the value is ``False``, there is no way to enter a string
   that contains both a single quote and a double quote within its
   contents.

 * ``digits``.  If the value is ``True``, a word beginning with
   a digit contains only digits, and its type is ``'digit'``.  A
   minus sign followed by digits is also returned as a ``'digit'``.
   If the
   value is ``False`` (the default), digit characters are treated
   like any other word character.

 * ``stringtype``.  The value should be a string to be used as
   the type for quoted strings.  The default is ``'word'``.

 * ``mlstrings``.  If the value is ``True``, strings may extend
   over multiple lines.  Note: a multi-line string will contain just
   a single newline character at the end of each line, even if the input
   contains ``'\r\n'``.  If the value is ``False`` (the default),
   then an error is signalled if a string does not terminate before the
   end of the line.  

One can change syntax while scanning.  The scanner returned by
``iter_tokens()`` has methods ``push_syntax()`` and
``pop_syntax()``.  They may affect the value of methods like 
``has_next()`` or ``token()`` that look ahead in the input: the
lookahead token is rescanned after a change in syntax.

Writing tokens
^^^^^^^^^^^^^^

There is no ``save_tokens()`` function.  The token stream is
generally only an intermediate step in building a structured object
such as a grammar.  The convention used with grammars and trees is to
define a "loader" that can be used to scan a structured file,
and to write an object to a file in a scanable form.  The loader
generally has paired ``scan`` and ``unscan`` methods for each type
of expression in the format.

One piece of functionality is provided here as a convenience for
unscan methods.  Syntax instances have a method ``scanable_string()``
that produces a version of a string that can
be written to a file, and will produce the original string when
scanned in by ``iter_tokens()``, assuming that the same syntax is
in use.  Specifically,
``scanable_string()`` returns a quoted version of the string if it
contains a space or special character, and returns the string
unchanged otherwise.::

   >>> syn.scanable_string('foo')
   'foo'
   >>> syn.scanable_string('foo:bar')
   "'foo:bar'"

The function ``scanable_string`` uses the default syntax.::

   >>> from selkie.io import scanable_string
   >>> fn = tmpfile()
   >>> out = outfile(fn)
   >>> out.write(scanable_string('hi'))
   2
   >>> out.write(' ')
   1
   >>> out.write(scanable_string('x + y'))
   7
   >>> out.write(' ')
   1
   >>> out.write(scanable_string('oh \u306e!'))
   7
   >>> out.write('\n')
   1
   >>> out.close()
   >>> print(contents(fn), end='')
   hi 'x + y' 'oh \u306e!'
   >>> load_tokens(fn)
   ['hi', 'x + y', 'oh \u306e!']

Note: when writing non-word tokens, one should write them as they
are.  The ``scanable_string()`` method converts its input to
something that scans in as a *word* token.

.. _kvi:

Indented key-value format (KVI)
-------------------------------

Indented key-value (KVI) format is a format that is (almost) equivalent
to JSON but is syntactically less cluttered.  Impressionistically, it
is like markdown compared to XML.  Consider a file called ``foo.kvi``
with the following contents::

   # A comment
   lex |lexicon.lx
   texts []:
     {}:
       ti | Hi: My #|@\ "Adventures"
       pgs 238
     {}:
       au |J. Smith
       ti |Bar

The keyword ``[]:`` begins a list, with each element starting a new
line and at a consistent level of indentation.  ``{}:`` begins a dict.
A dict contains keys and values, with one key-value pair per line.  A
string value begins with ``|`` and goes to the end of the line.
Thus::

   >>> load_kvi('foo.kvi')
   {'lex': 'lexicon.lx',
    'texts': [{'ti': ' Hi: My #|@\\ "Adventures"', 'pgs': 238},
              {'au': 'J. Smith', 'ti': 'Bar'}]}

(The first text's value for "ti" illustrates that leading whitespace
and characters that are usually special are all preserved intact.)
   
The type of container (dict versus list) can actually be determined
from the types of the elements (key-value pairs versus bare values).
For that reason, one is permitted to use a plain colon in place of
either ``{}:`` or ``[]:``.  For example, the following is exactly
equivalent to the contents of ``foo.kvi`` given above::

   # A comment
   lex |lexicon.lx
   texts :
     :
       ti | Hi: My #|@\ "Adventures"
       pgs 238
     :
       au |J. Smith
       ti |Bar

.. py:function:: load_kvi(fn, json=False, **kwargs)

   Loads a KVI file and returns a dict or list.  If `json=True`, it
   makes sure that the return value is suitable input for `json.dump()`.
   The remaining keyword arguments are passed to ``open()``.

   In detail,
   a KVI file consists of *keys* and *values*.
   The following restrictions are imposed:
   
    * A key must begin with a letter (a character that satisfies ``isalpha()``).
    * A key may not contain embedded whitespace.
    * A value may not contain an embedded newline.
   
   Lines containing only whitespace or beginning with ``#`` (with
   optional leading whitespace) are ignored.
   
   Otherwise, each line of the file begins with indentation, followed either by a
   key-value pair (separated by whitespace), or just a value.
   Indentation consists exclusively of space characters.  Keys must begin
   with letters, and values never begin with letters, making it easy to
   distinguish between them.
   
   The interpretation of the value is determined by its form:
   
    * If the value begins with ``|``, it represents a string, consisting of all
      characters after the ``|``.  All characters are preserved as is.
      The only character that cannot occur in a string value is newline.
    * If the value begins ``/`` or ``.`` or ``~``, it is interpreted as a pathname.
      A legal pathname must be one of ``/`` ``.`` ``..`` ``~`` or must
      begin with one of ``/`` ``./`` ``../`` ``~/``.
      If the pathname begins with ``.``, it is interpreted relative to the
      directory in which the current file is located.
    * If the value begins with a digit, possibly preceded by ``+`` or ``-``, it must be
      parseable as a number.  If it contains ``.`` it is parsed as a
      float, and otherwise as an int.
    * ``:T`` and ``:F`` represent True and False.
    * ``-`` represents None.
    * ``{}`` is an empty dict, and ``{}:`` represents a dict whose key-value pairs come from the next line
      and subsequent lines at the same level of indentation, all of which
      must be key-value pairs.
    * ``[]`` is an empty list, and
      ``[]:`` is a list whose elements come from the next line and
      subsequent lines at the same level of indentation, all of which
      must be bare values.
    * ``:`` is equivalent to ``{}:``, if the next line is a key-value pair,
      and it is equivalent to ``[]:`` if the next line is a bare value.
   
   If the first line (excluding comments) is a key-value pair,
   the file as a whole is interpreted as a dict.  If the first line
   contains a bare value, the file is interpreted as a list.
   (Those are the only two possibilities.)

.. py:function:: read_kvi(f)

   Just like ``load_kvi()``, except it takes an open file instead of a filename.

.. py:function:: save_kvi(x, fn)

   The object *x* must consist entirely of dicts, lists, strings,
   numbers, booleans, and None.  Any keyword arguments are passed to ``open()``.

.. py:function:: write_kvi(x, f)

   Just like ``save_kvi()``, except it takes an open file instead of a filename.


Formatting
----------

.. py:class:: Indenter

   .. py:method:: __init__(filename, encoding)

      The ``Indenter`` class provides a Unicode output file that does
      automatic indentation.  The constructor accepts ``filename`` and
      ``encoding`` arguments.  If they are not provided, the
      ``Indenter`` behaves like ``StringIO``::

         >>> from selkie.io import Indenter
         >>> out = Indenter()

   .. py:method:: begin_indent()
		  
      There is a prevailing indentation level, and indentation spaces are
      automatically inserted after each newline that is written to the
      formatter.  The level of indentation is increased
      using ``begin_indent()`` and decreased
      using ``end_indent()``.  It is initially zero::
   
         >>> out.write('hi there\n')
         >>> out.begin_indent()
         >>> out.write('foo\n')
         >>> out.begin_indent()
         >>> out.write('bar\n')
         >>> out.write('baz\n')
         >>> out.end_indent()
         >>> out.end_indent()

   .. py:method:: end_indent()

      Restore the previous level of indentation.

   .. py:method:: off()

      An indenter may be turned on and off.  When it is off, writing commands are
      accepted but generate no output.  The indenter is initially on.::

         >>> out.off()
         >>> out.write('invisible ink\n')
         >>> out.on()
         >>> out.write('blip\n')
         >>> print(out.getvalue(), end='')
         hi there
            foo
               bar
               baz
         blip

   .. py:method:: on()

      Turn output back on after it has been turned off.

``pprint``
^^^^^^^^^^

The function ``pprint()`` is pretty much a replacement for
``Indenter``, and usually more convenient.  It behaves like ``print()``,
except:

 * It does indenting.  Whenever it prints a newline, even embedded
   inside of an argument, it prints indentation.

 * It does not accept a ``file`` argument.  It prints only to
   ``sys.stdout``.  This is actually by design: otherwise it would
   break doctest or generally any tool that relies on redirecting
   ``sys.stdout``.

 * If one of its arguments has a ``__pprint__()`` method, that
   method is called instead of printing the argument in the usual way.
   The ``__pprint__()`` method is called with no arguments, and is
   expected to place recursive calls to ``pprint()``.

To be precise, ``pprint`` is actually not a function but a callable
object.  It provides the following additional methods:

.. py:class:: pprint

   .. py:method:: indent(n)

      The indentation amount, *n*, is optional; it
      defaults to 2.  This should be called in a "``with``" clause.
      An example::

         >>> from selkie.io import pprint
         >>> def ex1 ():
         ...     pprint('hi')
         ...     with pprint.indent():
         ...         pprint('lo', 'bob')
         ...         pprint('foo')
         ...
         >>> ex1()
         hi
           lo bob
           foo

   .. py:method:: br()

      A "soft" newline that does nothing at beginning of line.
      To be precise, it sets the break flag.  Just before printing a non-newline
      character, the break flag is checked.  If the break flag is set and
      the output is not currently at beginning of line, a new line is
      produced first along with the associated indentation.

    .. py:method:: now()

       Like ``__call__()``, but it immediately flushes the
       output after printing even if not at end of line.
    
    .. py:method:: start_indent(n)

       Increase the level of
       indentation.  It is better to use ``indent()``.
    
    .. py:method:: end_indent(n)

       Decrease the level of
       indentation.  It is better to use ``indent()``.

Tabular output
--------------

The function ``tabular()`` takes a table, represented as an iterator
over rows (lists), and produces a string representation with aligned
columns.  It converts the table to a list (infinite generators will
not work!) and sets the width of each column to the maximum width of
the string representation of any object in the column.::

   >>> from selkie.io import tabular
   >>> table = [['hi there', 42],
   ...          ['foo', 15],
   ...          ['elephants', 20]]
   >>> print(tabular(table))
   hi there  42
   foo       15
   elephants 20

Miscellany
----------

.. py:function:: srepr(x)

   The function ``srepr()`` returns the same as ``repr()`` except for
   dicts and sets.  In the case of dicts and sets, it prints the items or
   elements in sort order, so that the output is the same each time it is
   invoked.

.. py:function:: contents(fn)

   The function ``contents()`` returns the raw contents of a file.::

      >>> contents(ex.text1)
      'This is a test.\nIt is only a test.\n'

.. py:function:: tee(fn)

   The class ``tee`` is a file-like object that sends everything that
   is written to it both to a file and to stdout.::

      >>> import os
      >>> from selkie.sh import rmrf
      >>> if os.path.exists('/tmp/foo'): rmrf('/tmp/foo')
      >>> from selkie.io import tee
      >>> f = tee('/tmp/foo')
      >>> print('Hello', file=f)
      Hello
      >>> close(f)
      >>> contents('/tmp/foo')
      'Hello\n'
      </pre>
      >>> os.unlink('/tmp/foo')

.. py:data:: null

    The object ``null`` can be used as a null stream.::

       >>> from selkie.io import null
       >>> print('Hello', file=null)
       >>>

.. py:class:: OutputList

   An ``OutputList`` is a specialization of ``list`` that
   behaves like an output stream.  That is, it implements
   a ``write()`` method.
   Strings not ending in newline constitute partial lines.  They
   are accumulated until a string ending with newline is written, at
   which point all partial lines to that point are concatenated, and the
   resulting line is appended to the list.  Trailing carriage returns and
   newlines are deleted.
   
   Here is an example::

      >>> from selkie.io import OutputList
      >>> output = OutputList()
      >>> print('Hello', [10,20], file=output)
      >>> print('Bye', file=output)
      >>> output
      ['Hello [10, 20]', 'Bye']
      >>> output[0]
      'Hello [10, 20]'
   
   Two cautions are in order.
   (1) Embedded newlines are not detected.  (2) If the last thing written
   to the list did not end in newline, it will not appear in the list.
   It can, however, be accessed as ``output.partial``.

.. py:function:: wget(url)

   The function ``wget()`` is a shorthand for
   ``urllib.urlretrieve()``.

.. py:function:: redirect()

   The function ``redirect()`` can be used in a with-clause to
   redirect output from sys.stdout to a file or string::

      >>> from selkie.io import redirect
      >>> with redirect():
      ...     pprint('Line 1')
      ...     with pprint.indent():
      ...         pprint('Line 2')
      ...
      >>> redirect.output
      'Line 1\n    Line 2\n'
   
   To redirect to a stream, provide it as argument to ``redirect()``.
   To open a file for output, provide a mode as second argument.
