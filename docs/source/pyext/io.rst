
``selkie.io`` — Input/output functionality
==========================================

.. automodule:: selkie.io

Filename suffixes
-----------------

.. autofunction:: ispathlike
.. autofunction:: strip_suffix
.. autofunction:: split_suffix
.. autofunction:: get_suffix

Syntax
------

.. autoclass:: Token
.. autoclass:: Syntax

Special streams
---------------

.. function:: pprint(*strs)
.. autofunction:: tabular
.. autofunction:: redirect
.. autoclass:: BackingSave

Formatted Files
---------------

BaseFile
........

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

.. function:: File(filename, ...)

   This function is a convenience interface to the constructors of the
   various implementations of BaseFile. It uses the filename to
   distinguish the cases RegularFile, StdStream (filename is ``-``),
   and URLStream. The keyword arguments distinguish the final two cases:

    * ``binary`` — if True, create a BinaryFile.
    * ``contents`` — if provided, use it to create a FileFromString.
    * ``format`` — if provided, wrap it around the BaseFile that is created.

   For example:
    
   >>> from selkie.io import File
   >>> f = File('/tmp/foo')
   >>> with f.writer() as write:
   ...     write('Test\n')
   ...     write('123\n')
   ... 
   >>> list(f)
   ['Test\n', '123\n']

   Here is an example in which one specifies contents:
    
   >>> f = File(contents='hi\nthere\n')
   >>> list(f)
   ['hi\n', 'there\n']

.. autoclass:: Buffered

Format and FormattedFile
........................

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

.. autoclass:: Format
.. autoclass:: FormattedFile

Lines
.....

.. autodata:: Lines

Records
.......

.. autofunction:: lines_to_records
.. autofunction:: records_to_lines
.. autodata:: Records

Simples
.......

.. autofunction:: lines_to_simples
.. autofunction:: simples_to_lines
.. autodata:: Simples

Blocks
......

.. autofunction:: lines_to_blocks
.. autofunction:: blocks_to_lines
.. autodata:: Blocks

Dicts
.....

.. autofunction:: lines_to_dicts
.. autofunction:: dicts_to_lines
.. autodata:: Dicts

ILines
......

.. autofunction:: lines_to_ilines
.. autofunction:: ilines_to_lines
.. autodata:: ILines

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

.. autofunction:: lines_to_nested_lists
.. autofunction:: nested_lists_to_lines
.. autodata:: NestedLists

Containers
..........

.. autofunction:: lines_to_containers
.. autofunction:: containers_to_lines
.. autodata:: Containers
