
Dict file format — ``selkie.pyx.dct``
=====================================

.. py:module:: selkie.pyx.dct

File format
-----------

The DCT format is a lighter-weight alternative to JSON, for objects
that consist exclusively of strings and dicts. Let us call the
following "Example 1"::

   #!selkie file foo
   foo
     bar.1
       a 10
       b 20
     bar.2
       a 30
       b 40

This reads in as nested dicts::

   {'foo':
      {'bar.1':
         {'a': '10',
          'b': '20'},
       'bar.2':
         {'a': '30',
          'b': '40'}}}

The dicts are thought of as
objects consisting of attribute-value pairs. When the value is a
sub-object, the attribute doubles as the type of the sub-object. For
example, the 'bar.1' object has type 'bar', but it is also the value of
the 'bar.1' attribute of the 'foo' object. Note that discriminators
like ``.1`` are used to convert a list of objects of the same type
into a collection of distinct attributes.

Each type has a list of legal attributes, and the association of types
with attributes (called the **signature**) determines how the
file parses. In Example 1, the type ``bar`` has attributes ``a`` and ``b``,
and type ``foo`` has attribute ``bar``. That
prevents a tree structure in which an ``a``, for example, is attached
directly to the ``foo`` object, or in which one ``bar`` object is
attached to another.
In fact, the signature makes the indentation entirely
optional. It is added for readability only.

Data types
----------

A ``File`` represents a storage location. The basic File class is
defined by a Path (or string, which will be converted to a
Path). A File
has a ``read()`` method that returns the contents of the
location as a string, and a ``write()`` method that takes a string
and makes it be the contents of the location.
A non-existing location has the empty string as content-string.

A File is also associated with a ``Format``. A Format provides two
methods: ``decode()`` takes a content-string and converts it to an object
representing the contents, and ``encode()`` takes the contents object
and converts it to a string.

The contents of a File resides in the attribute ``contents``.
When the File is instantiated, it reads its location and decodes the
content-string to set ``contents``.
One may (destructively) modify the contents object,
and then save the changes by calling the ``save()`` method.
Alternatively, one may reset the ``contents`` to match what is in the
location by doing ``revert()``.

One may produce content-strings encoded for other formats by doing
``export(fmtname)``, for example, ``export('json')``. Note that this
uses the current ``contents`` object; it does not revert.

Example
-------

First, we define the format:

>>> from selkie.pyx.dct import DCTFormat
>>> fmt = DCTFormat('foo', {'foo'}, foo={'bar'}, bar={'a', 'b'})

The first argument, ``'foo'``, is the format name. The second
argument, ``{'foo'}``, is the set of root types. The keyword
arguments give the sets of attributes for each type.

Now we can create a formatted file:

>>> from selkie.pyx.dct import File
>>> fi = File('/tmp/foo.dct', format=fmt)

Since the file does not (yet) exist, the contents is empty:

>>> fi.contents
{}

We can create Example 1 from a dict as follows:

>>> bar1 = {'a': '10', 'b': '20'}
>>> bar2 = {'a': '30', 'b': '40'}
>>> foo = {'bar.1': bar1, 'bar.2': bar2}
>>> fi.contents = {'foo': foo}

To get the text of Example 1:

>>> print(fi)
#!selkie file foo
foo
  bar.1
    a 10
    b 20
  bar.2
    a 30
    b 40
<BLANKLINE>

To convert it to JSON:

>>> s = fi.export('json')
'{"foo": {"bar.1": {"a": "10", "b": "20"}'

To permit the format to be referred to by name, one may register it:

>>> File.__formats__['foo'] = fmt

Then one can do, for example, ``File(fn, fmt='foo')`` or ``fi.export('foo')``.
