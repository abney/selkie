
.. py:module:: selkie.newio

``selkie.newio`` — New I/O
==========================

Files
-----

The newio module defines a class of File objects that are associated with
read/writeable locations.  The function ``File()`` creates one::

   >>> f = File('/tmp/foo')

A File can be thought of as a view of the characters on disk as an
iteration over objects, known as **elements** of the File.  The Files
returned by ``File`` contain lines (a line being a string terminated
with a newline character), but other Files may have other element
types.

There are two broad classes of File: **iterable Files** and **singleton Files.**
An iterable File behaves as a two-way mapping from characters on disk
to an iteration over elements.  A single-element File maps between
characters on disk and a single element.

To read an iterable file, one simply iterates over it.  To
write it, one uses the method ``store()``.  The argument to
``store()`` may be anything that behaves as an iteration over elements.

   >>> f.store(['foo\tbar\n', 'baz\n', '  a\t1\n', '  b\t2\n'])
   >>> list(f)
   ['foo\tbar\n', 'baz\n', '  a\t1\n', '  b\t2\n']

To read a singleton file, one calls the method ``load()``.  An example
is given below, in the section on Singleton File Formats.

.. py:function:: File(filename)

   Returns an object that inherits from ``BaseFile``.
   Optional arguments are ``encoding``, ``binary``, ``format``, and ``contents``.
   *Binary* is boolean.  If *format* is provided, it is called on the
   file after opening it, and the result is returned.  The keyword
   *contents* is used to specify that the given string is to be
   interpreted as file contents rather than filename.  It is an error
   to provide both *filename* and *contents*.

.. py:class:: BaseFile

   .. py:method:: __iter__()

      Must be implemented by specializations.  Returns an iteration
      over the elements of the file.

   .. py:method:: store(contents)

      Must be implemented by specializations.  Saves *contents* to the
      file.  *Contents* should be an iteration over elements.

   .. py:method:: load()

      Iterates over the file and returns the results as a list of
      elements.

   .. py:method:: save(contents)

      A synonym for ``store(contents)``.

.. py:class:: SingletonFile

   Inherits from BaseFile.

   .. py:method:: load()

      Must be implemented by specializations.  Returns a single
      element.

   .. py:method:: save(contents)

      Must be implemented by specializations.  *Contents* should be a
      single element.

   .. py:method:: __iter__()

      Returns an iteration that contains just one element.

   .. py:method:: store(contents)

      A synonym for ``save(contents)``.


Formats
-------

One may create Files from other Files using a File Format.  A File
Format is associated with elements of type *T*, for some choice of
*T*.  The Format contains a ``read`` function that converts an iteration over
lines into an iteration over elements of type *T*, and a ``render``
function that takes anything that can be treated as an iteration over
elements of type *T*, and converts it to an iteration over lines.
Applying the format to a line-based File yields a File over elements
of type *T*.  For example::

   >>> f = Nested(File('/tmp/foo'))
   >>> list(f)
   ['foo\tbar', 'baz', ['a\t1', 'b\t2']]

(Nested lists are lists that contain a mix of strings and Nested
lists.)

File formats implicitly call ``File()`` if given an argument that is
not already a ``BaseFile``:

   >>> f = Nested('/tmp/foo')

.. py:class:: FormattedFile

   A specialization of ``BaseFile`` that is produced by applying a
   ``FileFormat`` to a file.  It contains a base file and a
   format.  Iterating over it applies the format's ``read`` function
   to the base file.  Saving *contents* to it applies the format's
   ``render`` function to *contents* and then stores the resulting lines
   in the base file.


.. py:class:: FileFormat

   A file format defines *elements* of a certain sort.

   .. py:attribute:: read

      The value is a function that takes an iteration over lines and
      returns an iteration over the elements.  Note
      that this is a *member* whose value is a function; it is not a
      bound method.

   .. py:attribute:: render

      The value is a function that is the inverse of ``read()``.  It
      takes an iteration over elements and returns an
      iteration over lines.

   .. py:method:: __call__(f)

      Apply to *f*, which is an instance of ``BaseFile``.  The return
      value is a ``FormattedFile``.


Iterable File Formats
---------------------

.. py:data:: Lines

   A file format whose elements are lines.  Its ``read`` and
   ``render`` functions are both identity functions.

.. py:data:: Records

   A file format whose elements are *records*.  A record is a list
   of strings corresponding to the tab-separated fields of a line.

.. py:data:: Tabular

   A synonym for ``Records``.

.. py:data:: Blocks

   A file format whose elements are *blocks*.  A block is a list of
   records, corresponding to groups of lines separated by empty
   lines.  Multiple empty lines represent a single separator.  That
   is, blocks cannot be empty.

.. py:data:: Dicts

   A file format whose elements are *dicts*.  The file contents are
   treated as blocks, and it is expected that each record contains
   exactly two fields (key and value); thus a block corresponds to a
   dict.

.. py:data:: ILines

   A file format whose elements are *indented lines*.  An indented
   line is a pair (*indent*, *line*), in which *indent* is an int
   indicating the number of leading spaces, and *line* is the contents
   of the line without the leading spaces and without terminating
   return/newline.

.. py:data:: Nested

   A file format whose elements are *nested blocks*.  A nested block
   is a list of contiguous lines at the same level of indentation.
   Leading spaces and terminating return/newline have been removed.
   A nested block also contains sublists representing nested blocks at
   deeper levels of indentation.



Singleton File Formats
----------------------

A singleton file uses the methods
``load()`` and ``save()`` instead of ``__iter__()`` and ``store()``::

   >>> NestedDict('/tmp/foo').load()
   {'foo': 'bar', 'baz': {'a': '1', 'b': '2'}}

Note that ``load()`` returns a single element.  The method
``__iter__()`` returns an iteration containing just that one element.


.. py:class:: LoadableFile

   A specialization of ``SingletonFile`` that is produced by applying a
   ``LoadableFormat`` to a file.  It is like ``FormattedFile``, except
   that ``load()`` and ``save()`` are taken to be basic.  The file is
   assumed to contain a single object, returned by ``load()``.
   ``__iter__()`` yields the value of ``load()``.


.. py:class:: LoadableFormat

   Like ``FileFormat``, except that its ``read()`` method should
   return (and its ``render()`` method accept) a single object, not an
   iteration.

.. py:data:: NestedDict

   A format for a file containing a *nested dict*.  A nested dict is
   like a nested block, except that lines are parsed into key-value
   pairs separated by a whitespace character and the value is a dict
   rather than a list.  A subdict at a deeper level of indentation
   must be preceded by a line containing a key but no value.
