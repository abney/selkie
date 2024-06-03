
Formatted Files — ``selkie.pyx.formats``
****************************************

.. automodule:: selkie.pyx.formats

Files
-----

Selkie provides an abstract class called BaseFile that represents the
contents of a read/writeable location (such as an actual file).
The function ``File()`` creates one::

   >>> from selkie.pyx.formats import File
   >>> foo = File('/tmp/foo')

The return value is an instance of BaseFile, which is, conceptually,
a named location that contains a sequence of
**elements**. When one passes a pathname to File, as in the previous
example, the return value is an instance of RegularFile, whose elements are
newline-terminated lines. Other specializations of BaseFile may have
different element types.

BaseFile has two basic methods: ``__iter__()`` returns an iteration over
the elements of the file, and ``store()`` takes an iterable containing
elements and replaces the existing contents with them::

   >>> foo.store(['foo bar\n', 'baz\n'])
   >>> list(foo)
   ['foo bar\n', 'baz\n']

The ``__iter__()`` and ``store()`` methods are intended to be
inverses: ``foo.store(list(foo))`` should not change the contents of
the file. However, since different objects may produce the same
iteration over lines, writing and then reading an object may fail to produce one that is
equal to the original object. The two objects should be equivalent,
though, in the sense of yielding the same iteration over lines.

One can also write elements one at a time as follows::

   >>> with foo.writer() as write:
   ...     write('foo')
   ...     write(' ')
   ...     write('bar\n')
   ...

All elements are buffered in the writer, and the file's store method is called
when the with-clause exits.

One can view the contents of the File by printing it::

   >>> print(foo, end='')
   foo bar

There is no method for deleting a file; use 'unlink'::

   >>> from os import unlink
   >>> unlink('/tmp/foo')
   >>> list(foo)
   []


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
      

There are currently five implementations of BaseFile. These are the
**primitive** BaseFiles:

 * ``RegularFile`` is a regular file on disk. It need not exist, and will
   automatically be created when stored. (If a RegularFile *f* does not exist,
   then ``list(f)`` returns the empty list; it does not signal an error.)

 * ``BinaryFile`` is like RegularFile, except that it contains bytes rather than
   strings.

 * ``StdStream`` reads stdin and writes to stdout.

 * ``StringFile`` converts a string into a readable BaseFile. One may
   use store() to replace the initial string (which defaults to the empty string).

 * ``URLStream`` fetches a URL and iterates over the web page contents a line
   at a time. It is not writable.

String files can be useful for testing::

   >>> from selkie.pyx.formats import StringFile
   >>> s = StringFile()
   >>> s.store(['hi there\n', 'bye\n'])
   >>> list(s)
   ['hi there\n', 'bye\n']

Format
------

All of the primitive BaseFiles (with the exception of BinaryFile) contain lines.
When iterating over them, one iterates over strings representing file
lines. (A line includes the terminating newline.) What one stores to them are lists of
such lines. (Storing a line that contains an internal newline, or does
not contain a terminating newline, does not
raise an exception, but it does break round-tripping: the elements one
reads out differ from the elements one stored.)

It is convenient to have BaseFiles that contain other kinds of
elements. Indeed, the iter and store methods are agnostic about the kind of
elements in a file. It is possible to create **derived BaseFiles** whose elements
are something other than lines.

To do so, one specializes the class Format (which is itself a
specialization of BaseFile). Format has two required class methods:
``from_lines()`` converts lines to the elements of the format, and
``to_lines()`` converts elements of the format to lines. One
instantiates Format with the same arguments one passes to File. A
number of specializations of Format are provided.

For example, the format Records represents the contents of a tabular
file with tab-separated fields. The elements in a Records file are
lists of strings::

   >>> from selkie.pyx.formats import Records
   >>> recs = Records(s)
   >>> recs.store([['This', 'is'], ['a', 'test']])
   >>> list(recs)
   [['This', 'is'], ['a', 'test']]

To view the contents of the file, we can look at the underlying StringFile::

   >>> list(s)
   ['This\tis\n', 'a\ttest\n']

One may create new formats by specializing Format and defining two
class methods: from_lines() and to_lines(). The former takes an
iteration over lines and should produce an iteration over format
elements, and the latter takes an iteration over elements and should
produce an iteration over lines. An instance of the format contains a
primitive file internally, and uses the from_lines() and to_lines()
methods to translate lines to elements and back again.

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
 
.. py:class:: BaseFile

   .. py:method:: __iter__()

      Must be implemented by specializations.  Returns an iteration
      over the elements of the file.
   
      Note: an instance of BaseFile can be iterated over even if
      the underlying file does not exist. (The iteration will be empty if the file
      does not exist.)

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

.. py:class:: RegularFile(fn, encoding)

   A primitive BaseFile that is backed by a file on disk.

.. py:class:: StdStream

   A primitive BaseFile whose iterator reads from sys.stdin and whose
   'store' method writes to sys.stdout.

.. py:class:: URLStream

   A primitive BaseFile that fetches its contents from a URL. The
   'store' method raises an exception.

.. py:class:: StringFile(contents='')

   A primitive BaseFile that contains a string representing its contents.
   Iterating over it breaks the string at newlines.

.. py:class:: BinaryFile(fn)

   A primitive BaseFile that is backed by a binary file on disk.

.. py:function:: File()

   Takes keyword arguments *filename*, *binary*, and *contents*.
   *filename* is a pathname, a URL, or "-".
   *Binary* is boolean. The keyword
   *contents* is used to specify that the given string is to be
   interpreted as file contents rather than filename.  It is an error
   to provide both *filename* and *contents*.

   Returns one of the primitive BaseFiles, chosen as follows:

    * If *contents* is provided, the value is a StringFile.

    * Else if *filename* is "-", the value is StdStream.

    * Else if *filename* begins with a protocol (that is, letters followed
      by a colon), the value is a URLStream.

    * Else if *binary* is True, the value is a BinaryFile.

    * Otherwise, the value is a RegularFile.

   For example:
    
   >>> f = File(contents='hi\nthere\n')
   >>> list(f)
   ['hi\n', 'there\n']
   >>> type(f)
   <class 'selkie.pyx.formats.StringFile'>
    
.. py:class:: Format(base)

   This is a specialization of BaseFile. It is an abstract base class
   for derived files.

   The constructor takes a primitive BaseFile and returns a derived BaseFile.

   .. py:method:: base()

      Returns the underlying primitive BaseFile.

   .. py:method:: from_lines(lines)

      This is a class method that must be implemented by specializations.
      The argument *lines* is an iterable
      containing lines, and the method produces an iteration over
      derived elements.

      Since this is a class method, it can be called without
      instantiating the class first. For example::

         >>> list(Records.from_lines(['a\t1\n', 'b\t2\n']))
         [['a', '1'], ['b', '2']]

   .. py:method:: to_lines(elts)

      A class method that specializations must implement.
      *Elts* is an iterable containing derived elements, and the
      method must produce an iteration over lines. This can also be
      called without instantiating the class:

         >>> list(Records.to_lines([['a', '1'], ['b', '2']]))
	 ['a\t1\n', 'b\t2\n']

Catalog of formats
------------------

.. py:class:: Records

   A Format whose elements are lists of strings. Each element
   corresponds to one line in the base file, with fields separated by
   tabs.

.. py:data:: Tabular

   A synonym for ``Records``.

.. py:class:: Blocks

   A Format whose elements are blocks, separated on disk by empty lines.
   Multiple empty lines represent a single separator.  That
   is, blocks cannot be empty. The lines within a block are
   interpreted as records with tab-separated fields.
   For example::

      >>> from selkie.pyx.formats import Blocks
      >>> f = Blocks(s)
      >>> f.store([[['a', '1'], ['b', '2']], [['c', '3']]])
      >>> list(s)
      ['a\t1\n', 'b\t2\n', '\n', 'c\t3\n']

.. py:class:: PLists

   A Format whose elements are property lists. A property list is a
   list of (*key*, *value*) pairs. The disk format is the same as for
   Dicts, except that the ordering of pairs matters and duplicates are
   allowed.

.. py:class:: Dicts

   A Format whose elements are dicts. The file contents are
   treated as blocks separated by empty lines, and it is expected that
   each line in a block contains a whitespace character.  The first
   whitespace character separates the line into key and value, and
   the block corresponds to a dict. Duplicate keys cause an error.

   Continuing the previous example::

      >>> from selkie.pyx.formats import Dicts
      >>> list(Dicts(s))
      [{'a': '1', 'b': '2'}, {'c': '3'}]

.. py:class:: OrderedDicts

   A Format whose elements are OrderedDicts. Identical to Dicts except
   for the class used for the dicts.

.. py:class:: ObjectTables

   An "object" is an OrderedDict, considered as an object with
   attributes and values. The first attribute (hence the need for an
   OrderedDict) is considered to be the attribute that represents the
   object identifier. All objects must have the same attribute as the
   first attribute, and objects must be uniquely identified by their
   value for that attribute. An object table is a map from the
   identifiers to the objects.

   An ObjectTables file builds an an OrderedDicts file, and constructs
   a table from all the OrderedDicts in the file. For the sake of
   consistency with the other formats, one iterates over object
   tables, but in fact, there is never more than one table.

   For example::

      >>> from collections import OrderedDict as Obj
      >>> table = {}
      >>> table['1'] = Obj([('id', '1'), ('b', 'hi')])
      >>> table['2'] = Obj([('id', '2'), ('b', 'lo')])
      >>> from selkie.pyx.formats import ObjectTables
      >>> f = ObjectTables(s)
      >>> f.store([table])
      >>> tables = list(f)
      >>> tables[0]['1']
      OrderedDict([('id', '1'), ('b', 'hi')])
      >>> tables[0]['2']
      OrderedDict([('id', '2'), ('b', 'lo')])

.. py:class:: ILines

   A Format whose elements are pairs (*ind*, *line*) where *ind* is
   the number of space characters at the beginning of the original
   line, and *line* is the original line without the leading spaces::

      >>> from selkie.pyx.formats import ILines
      >>> s.store(['a\n', '  b\n', '  c\n'])
      >>> list(ILines(s))
      [(0, 'a'), (2, 'b'), (2, 'c')]

.. py:class:: NestedLists

   A Format whose elements are nested lists. Nesting is represented by
   indentation. Continuing the previous example::

      >>> from selkie.pyx.formats import NestedLists
      >>> list(NestedLists(s))
      [['a', ['b', 'c']]]

.. py:class:: NestedDicts

   A Format whose elements are nested dicts. Nesting is represented by
   indentation. For example::

      >>> from selkie.pyx.formats import NestedDicts
      >>> f = NestedDicts(s)
      >>> f.store([{'a': '1', 'b': {'c': '2', 'd': '3'}}])
      >>> list(s)
      ['a 1\n', 'b\n', '    c 2\n', '    d 3\n']

.. py:class:: Simples

   A Format whose elements are "simples", which are somewhat like JSON
   values. A simple is recursively defined as a string, a list
   whose elements are simples, a dict whose keys are strings and whose
   values are simples, or key-value pairs consisting of a string and a simple.

   On disk:

    * A string is rendered as vertical bar followed by the string.

    * A key-value pair is rendered by a line consisting of ``:`` plus
      the key, followed by the rendering of the value.

    * A list is rendered as a line ``[``, followed by the rendering of
      each member, terminated by a line ``]``.

    * A dict is rendered as a line ``{``, followed by renderings of
      the items, terminated by a line ``}``.
   
   For example::
   
      >>> from selkie.pyx.formats import Simples
      >>> f = Simples(s)
      >>> f.store([('foo', {'bar': 'baz'})])
      >>> list(f)
      [('foo', {'bar': 'baz'})]
      >>> print(s, end='')
      :foo
      {
      :bar
      |baz
      }
   
   In that example, there is one top-level item, which is a key-value pair.

.. py:class:: Json

   A Format whose elements are JSON values, represented on disk in
   JSON format. A well-formed JSON file only contains one value; a
   Json formatted-file similarly may only contain a single object.

      >>> from selkie.pyx.formats import Json
      >>> f = Json(s)
      >>> f.store([{'a': 1, 'b': {'c': 2}}])
      >>> print(s, end='')
      {"a": 1, "b": {"c": 2}}
      >>> list(f)
      [{'a': 1, 'b': {'c': 2}}]

