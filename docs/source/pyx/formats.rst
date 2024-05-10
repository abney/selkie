
Formatted Files — ``selkie.pyx.formats``
****************************************

.. automodule:: selkie.pyx.formats

Files
-----

Selkie defines a class of File objects that are associated with
read/writeable locations.  The function ``File()`` creates one::

   >>> from selkie.pyx.formats import File
   >>> f = File('/tmp/foo')

Conceptually, a File is a named location containing a sequence of
**elements**.  The ``File`` function returns Files whose elements are
newline-terminated lines, but other Files may have different element
types.

A File has two basic methods: ``__iter__()`` returns an iteration over
the elements of the File, and ``store()`` takes an iterable containing
elements and replaces the existing contents with them::

   >>> f.store(['foo bar\n', 'baz\n', '  a 1\n', '  b 2\n'])
   >>> list(f)
   ['foo bar\n', 'baz\n', '  a 1\n', '  b 2\n']

One can also write elements one at a time as follows::

   >>> f2 = File('/tmp/foo2')
   >>> with f2.writer() as write:
   ...     write('foo\n')
   ...     write('bar\n')
   ...

One can view the contents of the File by printing it::

   >>> print(f, end='')
   foo bar
   baz
     a 1
     b 2

..
   Commented Out
   Singles
   -------
   
   A Single is a File-like object that contains exactly one element,
   rather than an iteration over elements.  Its methods are ``load()``
   and ``save()`` instead of ``__iter__()`` and ``store()``.
   For example::
   
   #   >>> f = Single(NestedDicts('/tmp/foo2'))
   #   >>> f.load()
   #   {'foo': 'bar', 'baz': {'a': '1', 'b': '2'}}
   
   
   Objects
   -------
   
   An Object, like a Single, has ``load()`` and ``save()`` methods.  In
   addition:
   
    * It implements accessor and setter methods, and the setter
      methods automatically call ``save()``.
   
    * It can be edited in a ``with`` block, and a single ``save()`` is
      done at the end of the block, instead of after each edit.
   
   .. py:class:: selkie.newio.Object
   
   .. py:class:: selkie.newio.Dict
   
      An Object that behaves like a dict.
      For example, suppose ``foo.dat`` contains::
   
         foo bar
         baz
           a 1
   	b 2
   
      Then we have::
   
      #   >>> d = Dict('foo.dat')
      #   >>> d
      #   {'foo': 'bar', 'baz': {'a': '1', 'b': '2'}}
      #   >>> d['foo'] = 'hi'
      #   >>> d
      #   {'foo': 'hi', 'baz': {'a': '1', 'b': '2'}}
      #   >>> cat foo.dat
      #   foo hi
      #   baz
      #     a 1
      #     b 2
      

BaseFile
--------

Files of the usual sort are instances of RegularFile, and RegularFile is
an implementation of the generic class BaseFile. A BaseFile has just two
basic methods: ``__iter__()`` for reading, and ``store(contents)`` for writing.
The two are intended to be inverses: the iter method returns an
iteration containing lines, and what one stores is an iterable that
contains lines.

Unless one uses multiple threads, the iterable that one stores must
already exist in completeness. It is also possible to write elements
incrementally:

.. code-block:: console

    with bf.writer() as write:
        ...
        write(elt)
        ...

All elements are buffered in the writer, and ``bf``'s store method is called
when the with-clause exits.

There are currently five implementations of BaseFile. These are the
**primitive** BaseFiles:

 * ``RegularFile`` is a regular file on disk. It need not exist, and will
   automatically be created when stored. (If a RegularFile *f* does not exist,
   then ``list(f)`` returns the empty list; it does not signal an error.)
 * ``BinaryFile`` is like RegularFile, except that it contains bytes rather than
   strings.
 * ``StdStream`` reads stdin and writes to stdout.
 * ``FileFromString`` converts a string into a readable BaseFile. One may
   use store() to replace the initial string (which defaults to the empty string).
 * ``URLStream`` fetches a URL and iterates over the web page contents a line
   at a time. It is not writable.

Format and FormattedFile
------------------------

All of the primitive BaseFiles (with the exception of BinaryFile) contain lines.
When iterating over them, one iterates over strings representing file
lines. (A line includes the terminating newline.) What one stores to them are lists of
such lines. (Storing a line that contains an internal newline, or does
not contain a terminating newline, does not
raise an exception, but it does break round-tripping: the elements one
reads out differ from the elements one stored.)

However, the iter and store methods are agnostic about the kind of
elements in a file. It is possible to create **derived BaseFiles** whose elements
are (for example) **records** (lists of strings representing
tab-separated fields). The derived BaseFile is an iterable containing records, and
what one stores in it is an iterable containing records. To define a
derived BaseFile, one provides "read" and "render" functions. The read
function receives an iterable containing lines, and returns an
iterable containing elements of some sort. The render function takes
an iterable containing elements of that sort, and returns an iterable
containing lines. For example, ``lines_to_records()`` is a reader that
converts lines to records, and ``records_to_lines()`` is a renderer
that converts records back to lines. The general convention is to name
the read and render functions ``lines_to_X`` and ``X_to_lines``.

A **Format** is the pairing of a read and render function. It can be
called as a function in lieu of File(), taking the same arguments
that File takes. It uses its arguments to open a primitive
BaseFile, which becomes the **base** of the FormattedFile.
The FormattedFile's iter method calls the format's read function on
the base and returns the resulting iteration over formatted elements.
The FormattedFile's store method calls the format's render
function on the given contents, and stores the resulting lines in the
base.


One may create Files from other Files using a Format.  A
Format is associated with elements of a particular type *T*.
A Format has two members:

 * ``read`` — A function that is given an iteration over lines,
   and returns an iteration over elements of type *T*.

 * ``render`` — A function that is given an iteration over elements of
   type *T* and returns an iteration over lines.

Applying the format to a line-based File yields a File over elements
of type *T*.

..
   Commented Out

   For example, the Nested format looks at indentation,
   and returns a list of strings (and recursively nested lists) for each
   block at the same level of indentation::
   
   #   >>> f = Nested(File('/tmp/foo'))
   #   >>> list(f)
   #   ['foo\tbar', 'baz', ['a\t1', 'b\t2']]
   
   File formats implicitly call ``File()`` if given an argument that is
   not already a ``BaseFile``:
   
   #   >>> f = Nested('/tmp/foo')
   
   Single can be wrapped around a (formatted) file that contains a single
   object.  It has the methods ``load()`` and ``save()``::
     
   #   >>> foo3 = Single(NestedDicts('/tmp/foo3'))
   #   >>> foo3.save({'foo': 'hi', 'bar': 'bye'})
   #   >>> foo3.load
   #   {'foo': 'hi', 'bar': 'bye'}


Module Documentation
--------------------

.. function:: File(filename, ...)

   Returns an object that inherits from ``BaseFile``.
   Optional arguments are ``encoding``, ``binary``, ``format``, and ``contents``.
   *Binary* is boolean.  If *format* is provided, it is called on the
   file after opening it, and the result is returned.  The keyword
   *contents* is used to specify that the given string is to be
   interpreted as file contents rather than filename.  It is an error
   to provide both *filename* and *contents*.

   Note: the objects returned by File() can be iterated over even if
   the file does not exist.  (The iteration will be empty if the file
   does not exist.)

   This function is a convenience interface to the constructors of the
   various implementations of BaseFile. It uses the filename to
   distinguish the cases RegularFile, StdStream (filename is ``-``),
   and URLStream. The keyword arguments distinguish the final two cases:

    * ``binary`` — if True, create a BinaryFile.
    * ``contents`` — if provided, use it to create a FileFromString.
    * ``format`` — if provided, wrap it around the BaseFile that is created.

   For example:
    
   >>> from selkie.pyx.formats import File
   >>> f = File('/tmp/foo')
   >>> with f.writer() as write:
   ...     write('Test\n')
   ...     write('123\n')
   ... 
   >>> list(f)
   ['Test\n', '123\n']
   >>> str(f)
   'Test\n123\n'

   Here is an example in which one specifies contents:
    
   >>> f = File(contents='hi\nthere\n')
   >>> list(f)
   ['hi\n', 'there\n']

   One can print to a string this way:

   >>> f = File(contents='')
   >>> with f.writer() as out:
   ...     print('foo', file=out)
   ...     print('bar', file=out)
   ...
   >>> str(f)
   'foo\nbar\n'

.. py:class:: BaseFile

   .. py:method:: __iter__()

      Must be implemented by specializations.  Returns an iteration
      over the elements of the file.

   .. py:method:: store(contents)

      Must be implemented by specializations.  Replaces the contents
      of the file with *contents*, which must be an iteration over
      elements of the correct type.

   .. py:method:: __str__()

      The return value is the concatenation of the string representations
      of the File's elements.  A newline is inserted between elements
      if the preceding element's representation does not end with newline.

   .. py:method:: writer()

      Returns a function that can be used in a with-clause to write
      elements to the File one at a time.  The writer collects
      all elements into a list before storing them, so it should not
      be used for extremely large files.

.. autoclass:: Buffered

.. autoclass:: Format

   .. py:attribute:: read

      The value is a function that takes an iteration over lines and
      returns an iteration over the elements.  Note
      that this is a *member* whose value is a function; it is not a
      bound method.

   .. py:attribute:: render

      The value is a function that is the inverse of ``read()``.  It
      takes an iteration over elements and returns an
      iteration over lines.

   .. automethod:: __call__

.. autoclass:: FormattedFile

   .. automethod:: base
   .. automethod:: format

   .. py:method:: __call__(f)

      Apply to *f*, which is an instance of ``BaseFile``.  The return
      value is a ``FormattedFile``.

Catalog of formats
------------------

Lines
.....

.. py:data:: selkie.pyx.formats.Lines

   A file format whose elements are lines.  Its ``read`` and
   ``render`` functions are both identity functions.

Records
.......

.. autofunction:: lines_to_records
.. autofunction:: records_to_lines
.. py:data:: Records

   A file format whose elements are *records*.  A record is a list
   of strings corresponding to the tab-separated fields of a line.

.. py:data:: Tabular

   A synonym for ``Records``.

Simples
.......

.. py:function:: lines_to_simples(lines)

   Converts an iteration over lines to an iteration over simples.  A
   **simple** is a string, or a simple item (a pair whose first
   element is a string and whose second element is a simple), or a
   simple list (one whose elements are simples), or a simple dict (one
   whose keys are strings and whose values are simples).

.. py:function:: lines_to_simple(lines, terminator=None)

   Reads the first simple and returns it.
        
.. py:function:: simples_to_lines(objs)

   Converts an iteration over simples to an iteration over lines.

.. py:function:: simple_to_lines(obj)

   Converts a simple to an iteration over lines.

    * A string is rendered as vertical bar followed by the string.

    * A key-value pair is rendered by a line consisting of ``:`` plus
      the key, followed by the rendering of the value.

    * A list is rendered as a line ``[``, followed by the rendering of
      each member, terminated by a line ``]``.

    * A dict is rendered as a line ``{``, followed by renderings of
      the items, terminated by a line ``}``.

.. py:data:: Simples

   A *simple* is an object constructed entirely from strings, pairs,
   lists, and dicts.  A pair must have a string as its first element,
   and a dict must have strings as its keys.  Strings may not contain
   embedded newline.

   The disk format uses the first character of each line to represent
   the structure.  A line containing a single string begins with ``|``.
   A pair consists of a line beginning with ``:``, containing the key,
   followed by an arbitrary simple.  A list begins with ``[`` and ends
   with ``]``.  A dict begins with ``{`` and ends with ``}``, and the
   simples that it contains must all be pairs.

   Suppose foo.simples contains::

      :foo
      [
      |hi there
      |bye now
      ]
      :bar
      {
      :boo
      |blah blah
      :beer
      [
      |the beginning
      |the middle
      |the end
      ]
      }

   Then ``list(Simples('foo.simples'))`` yields::

      [('foo', ['hi there', 'bye now']),
       ('bar',
        {'boo': 'blah blah', 'beer': ['the beginning', 'the middle', 'the end']})]

   When loading, the original objects are not reconstructed.  The value consists                             
   of strings, pairs, lists and dicts.
   
   The format on disk is line-based:
   
    * A line starting with ``|`` constitutes a string, sans vertical bar
      and newline.
    * A line starting with ``:`` represents a key (sans colon and
      newline). The next simple that is read constitutes the value.
    * A line consisting of ``[`` starts a list. The elements are all
      simples read until a matching line consisting of ``]`` is found.
    * A line consisting of ``{`` starts a dict. The elements are all
      key-value pairs read until a matching line consisting of ``}`` is
      found. An error is encountered if a simple without a key is
      encountered.
   
   For example:
   
       >>> from selkie.pyx.formats import File, Simples
       >>> f = File(contents='')
       >>> with f.writer() as out:
       ...     print(':foo', file=out)
       ...     print('{', file=out)
       ...     print(':bar', file=out)
       ...     print('|baz', file=out)
       ...     print('}', file=out)
       ... 
       >>> list(Simples(f))
       [('foo', {'bar': 'baz'})]
   
   In that example, there is one top-level item, which is a key-value pair.


Blocks
......

.. py:function:: lines_to_blocks(lines)

   Convert an iteration over lines to an iteration over blocks.  A
   block is a list of records.

.. py:function:: blocks_to_lines(blocks)

   Converts an iteration over blocks to an iteration over lines.
   Blocks are separated by empty lines.

.. py:data:: Blocks

   A file format whose elements are *blocks*.  A block is a list of
   records, corresponding to groups of lines separated by empty
   lines.  Multiple empty lines represent a single separator.  That
   is, blocks cannot be empty.

   Suppose foo.blocks contains::

      foo     2
      bar     3

      baz     42

   Then ``list(Blocks('foo.blocks'))`` yields::

      [[['foo', '2'], ['bar', 3]],
       [['baz', '42']]]

Dicts
.....

    
.. py:function:: lines_to_dicts(lines)

   Converts an iteration over lines to an iteration over dicts.  Lines
   are split into key and value at the first whitespace character.
   (Values are not stripped.)  An empty line terminates the dict.

.. py:function:: dicts_to_lines(dicts)

   Converts an iteration over dicts to an iteration over lines.

.. py:data:: Dicts

   A file format whose elements are *dicts*.  The file contents are
   treated as blocks separated by empty lines, and it is expected that
   each line in a block contains a whitespace character.  The first
   whitespace character separates the line into key and value, and
   the block corresponds to a dict.  Duplicate keys cause an error.

   Continuing the previous example, ``list(Dicts('foo.blocks'))`` yields::

      [{'foo': '2', 'bar': '3'}, {'baz': '42'}]

ILines
......

.. py:function:: lines_to_ilines(lines)

   Converts an iteration over lines to an iteration over **ilines**,
   which are (indent, line) pairs.  *Indent* is an integer.

.. py:function:: ilines_to_lines(ilines)

   Converts an iteration over ilines to an iteration over lines.

.. py:data:: ILines

   A file format whose elements are *indented lines*.  An indented
   line is a pair (*indent*, *line*), in which *indent* is an int
   indicating the number of leading spaces, and *line* is the contents
   of the line without the leading spaces and without terminating
   return/newline.

   For example, suppose that ``foo.dat`` contains::

      foo bar
      baz
        a 1
	b 2

   Then ``list(ILines('foo.dat'))`` yields::

      [(0, 'foo bar'), (0, 'baz'), (2, 'a 1'), (2, 'b 2')]

NestedLists
...........

A NestedList is just what it sounds like: a list whose elements are
either strings or other nested lists. On disk, a level of embedding
corresponds to a level of indentation. Algorithmically, there is a
current level of indentation, which is initially -1.

 * A line whose indentation is greater than the current level
   contributes the first string in a new nested list. Its indentation
   becomes current.
 * A line whose indentation is less than the current level ends the
   current list, reverting to the list that came before. The line is
   then re-processed.
 * A line whose indentation equals the current level contributes a
   string that is appended to the current list.

The final output is the list at level -1. Since it is not possible to
have an actual line with indentation -1, this list contains at most
one element, which is a nested list.

.. py:function:: lines_to_nested_lists(lines)

   Converts an iteration over line to an iteration over nested lists.
   The elements of any list are at the same level of indentation.
        
.. py:function:: nested_lists_to_lines(lst)

   Converts an iteration over nested lists to an iteration over lines.

.. autodata:: NestedLists

Containers
..........

.. py:function:: lines_to_containers(lines)

   Converts an iteration over lines to an iteration over containers.

.. py:function:: containers_to_lines(conts)

   Converts an iteration over containers to an iteration over lines.

.. autodata:: Containers


..
    Commented Out

    .. py:data:: selkie.newio.NestedLists
    
       A file format whose elements are *nested lists*.  The lists contain
       lines at the same level of indentation, or embedded sublists at a
       deeper level of indentation.
       Leading spaces and terminating return/newline are removed.
    
       For example, ``list(NestedLists('foo.dat'))`` yields::
    
          [['foo bar', 'baz', ['a 1', 'b 2']]]
    
       N.b.: although NestedLists, in keeping with its name, returns an
       iteration, the iteration always contains exactly one element, the
       topmost list.
    
    .. py:data:: selkie.newio.NestedList
    
       NestedList is not actually a Format, but a function that takes a
       file or filename *f* and calls ``Single(NestedLists(f))``.
    
    .. py:data:: selkie.newio.NestedDicts
    
       A format for a file containing *nested dicts*.  The file is read as
       nested lists, and each list is converted to a dict by first
       converting it to a list of key-value pairs, as follows:
    
        * An embedded sublist must be preceded by a simple line (a
          string).  The preceding line is the key and the dict
          resulting from the embedded sublist is the value.
    
        * Otherwise, the line is split at the first whitespace character
          to produce key and value (both strings).  If there is no
          whitespace, the entire line is the key and the value is ``''``.
    
       For example, ``list(NestedDicts('foo.dat'))`` yields::
    
          [{'foo': 'bar', 'baz': {'a': '1', 'b': '2'}}]
    
       As with NestedLists, the iteration returned by NestedDicts always
       contains exactly one dict.
    
    .. py:data:: selkie.newio.NestedDict
    
       NestedDict is not actually a Format, but a function that takes a
       file or filename *f* and calls ``Single(NestedDicts(f))``.
