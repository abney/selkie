
``selkie.fs`` — File system convenience functions
=================================================

Creating directories
--------------------

``mkdir`` is imported from ``os``.  ``mkdirp`` is equivalent to
``mkdir -p``::

   >>> from selkie.fs import mkdirp
   >>> mkdirp('/tmp/foo')

The function ``need_parent`` can be used to assure that the parent
directory exists for a filename.  For example::

   >>> from selkie.fs import need_parent
   >>> need_parent('/tmp/foo/myfile')

is the same as ``mkdirp /tmp/foo``.

Navigation
----------

Examples::

   >>> from selkie.fs import pwd, cd, ls, lsl
   >>> cd('/tmp/foo')
   >>> ls()
   bar     baz     greet   text
   >>> pwd()
   '/private/tmp/foo'
   >>> lsl()
   total 16
   -rw-r--r--  1 spa  wheel  4 Oct 14 17:35 bar
   -rw-r--r--  1 spa  wheel  8 Oct 14 17:41 baz

The variations ``lsd``, ``lsld``, and ``lslt`` are also available.

with Cwd()
----------

.. py:class:: selkie.fs.Cwd

   The ``Cwd`` class protects against changes in working directory.
   On exit, it restores the working directory to what it was on entry::
      
      with Cwd():
          ...


Creating files: ``touch``, ``echo``, ``cat``
--------------------------------------------

One can use ``touch`` to create a new file::

   >>> cd('/tmp/foo')
   >>> touch('bar')

The function ``echo`` takes an optional second argument which is a
filename.  By default, the file is appended to, leaving any previous
contents intact::

   >>> echo('hi', '/tmp/greet')
   >>> echo('lo', '/tmp/greet')
   >>> cat('/tmp/greet')
   hi
   lo

One can prefix the filename with ``>`` or ``>>`` to
explicitly specify overwriting versus appending::

   >>> echo('boo', '>/tmp/bar')
   >>> cat('/tmp/bar')
   boo

The function ``cat`` behaves similarly.  With a single argument, it
prints to stdout, and given multiple arguments, it takes the last as
the output file name.  By default, the output file is created, but one
may specify appending by prefixing the filename with ``>>``::

   >>> cat('/tmp/greet', '/tmp/bar', '/tmp/baz')
   >>> cat('/tmp/baz')
   hi
   lo
   boo
   >>> cat('/tmp/bar', '/tmp/bar', '>1')
   boo
   boo


Examining files: ``more``, ``od``, ``wc``
-----------------------------------------

The function ``cat`` can also be used, of course.  The other
functions (``more``, ``od``, ``wc``) simply use ``os.system()``
to call the Unix executables.  The type of datum for ``od`` can be
specified using the ``type`` keyword.  Possible values are: ``a``
(named characters); ``c``; $is$ where $i$ is one of ``d``,
``o``, ``u``, ``x`` and $s$ (optional) is one of ``C``, ``S``, ``I``,
``L``, or a number of bytes; or ``f`` followed optionally by
``F``, ``D``, or ``L``::

   >>> od('bar')
   0000000    b   o   o  \n                                                
   0000004
   >>> od('bar', 'xC')
   0000000    62  6f  6f  0a                                                
   0000004
   >>> echo('this is a test', 'text')
   >>> echo('it is only a test', 'text')
   >>> wc('text')
          2       9      33 text


Copying: ``cp``, ``cpr``, ``mv``, ``ln``
----------------------------------------

The commands ``cp``, ``mv``, and ``ln`` behave as in the Unix shell.
The command ``cpr`` does a recursive copy.  An error is signalled if
the target already exists.  Symbolic links are copied as symbolic links.
Examples::

   >>> cp('bar', 'bar2')
   >>> ls()
   bar     bar2    baz
   >>> mv('bar2', 'bar3')
   >>> ls()
   bar     bar3    baz
   >>> ln('bar3', 'bar4')
   >>> cat('bar4')
   boo

Note that ``ln`` creates a symbolic link, not a hard link.  To
create a hard link, use ``link``.  (Both are imported from ``os``.
In ``os``, ``ln`` is called ``symlink``.)

Deletion: ``rm``, ``rmrf``, ``rmdir``
-------------------------------------

Examples::

   >>> rm('bar4')
   >>> ls()
   bar     bar3    baz
   >>> cd('..')
   >>> lsd('foo')
   foo
   >>> rmrf('foo')
   >>> lsd('foo')
   ls: foo: No such file or directory

Misc: ``sh``, ``pid``, ``launch``
---------------------------------

The functions ``sh`` and ``pid`` are just synonyms for
``os.system`` and ``os.getpid``.  The function ``launch``
calls the executable ``open``, which is Mac-specific.
