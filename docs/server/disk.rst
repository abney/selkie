
.. py:module:: selkie.disk

``selkie.disk`` — Virtual disks, REST
=====================================

This module provides "virtual disks" that behave like dicts whose
keys are pathnames and whose values are the file contents.
The virtual disk's directory serves as root.
Getting a value reads the named file, and setting a
value writes the named file.  Deleting a key deletes the named file.
For consistency with typical webserver expectations, the methods
``GET()``, ``PUT()``, and ``DELETE()`` are provided as synonyms.

A virtual disk behaves just like a dict, except that it is backed by
files and thus persistent.  For example::

   >>> disk = VDisk('/tmp/foo')
   >>> disk['/bar/baz'] = ['hi there\n', 'just a test\n']

The assignment causes the directory ``/tmp/foo/bar`` to be created if it did
not previously exist, and it writes the file ``/tmp/foo/bar/baz``, containing
two lines of text.  One can subsequently fetch the contents::

   >>> for line in disk['/bar/baz']:
   ...     print(line)
   ...
   hi there
   just a test

The return value is a ``BaseFile`` instance (see selkie.newio), which
behaves like an iteration over lines (which include the terminating newline).

Opening a new VDisk with the same directory name reads the same
values::

   >>> disk2 = VDisk('foo')
   >>> list(disk2['/bar'])
   ['hi there', 'just a test']

Since the values are BaseFile instances, one can specify a format::

   >>> from selkie.newio import NestedDict
   >>> baz = NestedDict(disk['/bar/baz'])
   >>> baz.save({'foo':'bar', 'baz': {'a':'1', 'b':'2'}})
   >>> baz.load()
   {'foo': 'bar', 'baz': {'a': '1', 'b': '2'}}

As an iteration, a VDisk contains all valid pathnames.  It is not
hierarchically structured.

   >>> list(disk)
   ['/bar/baz']

One can, however, access an (existing) directory to obtain a
``Directory`` object (rather than a BaseFile).  Iterating over the
directory object yields only the names within that directory::

   >>> bar = disk['/bar']
   >>> list(bar)
   ['baz']

One may use one of the names (note the lack of leading slashes) to
access the actual files from the Directory object::

   >>> baz = NestedDict(bar['baz'])
   >>> baz.load()
   {'foo': 'bar', 'baz': {'a': '1', 'b': '2'}}

Thus one may alternatively use a sequence of directory accesses::

   >>> disk['/']['bar']['baz']
   <selkie.newio.RegularFile at 0x7f833f3c5d60>

.. py:class:: VDisk(root)

   The argument *root* is a directory name.  If it does not exist, it is
   created the first time a value is stored.

   .. py:attribute:: root

      The value passed to the constructor.

   .. py:attribute:: ignore

      A function that takes a filename and returns True if the
      filename should be ignored.  A default is provided that ignores
      filenames that end in ``~`` or contain a component beginning
      with ``tmp`` or ending with ``.safe``.

   .. py:method:: physical_pathname(fn)

      Returns the physical pathname corresponding to the given
      VDisk-internal filename.  VDisk-internal filenames always have
      the root of the VDisk as root, and use ``/`` as separator.
      The physical pathname has the root of the filesystem as root,
      and uses the separator that is appropriate for the filesystem.

   .. py:method:: iterdirectory(fn)

      The physical pathname corresponding to *fn* must be an existing
      directory.  The iteration contains all names in the directory
      except ``.`` and ``..``.

   .. py:method:: __getitem__(fn)

      The return value is the contents of the named file.  The *fn* is
      converted to a physical pathname.  A ``BaseFile`` instance is
      returned.  A NameError is signalled if the file does not exist.

   .. py:method:: __setitem__(fn, value)

      The ``BaseFile`` is fetched, and the *value* is passed to its
      ``save()`` method.

   .. py:method:: __contains__ (fn)

      The *fn* is converted to a physical pathname, and the return
      value is a boolean indicating whether the file exists or not.

   .. py:method:: __delitem__ (fn)

      The *fn* is converted to a physical pathname, and the file is
      deleted.  A NameError is signalled if the file does not exist.

   .. py:method:: GET(fn)

      Synonym for ``__getitem__(fn)``.

   .. py:method:: PUT(fn, value)

      Synonym for ``__setitem__(fn, value)``.

   .. py:method:: DELETE(fn)

      Synonym for ``__delitem__(fn)``.

   .. py:method:: HEAD(fn)

      Synonym for ``__contains__(fn)``.

   .. py:method:: __iter__()

      Returns an iteration over the valid filenames.  These are
      VDisk-internal filenames of regular files (not subdirectories).

   .. py:method:: __len__()

      Returns the number of filenames in the iteration `__iter__()`.

   .. py:method:: keys()

      A synonym for `__iter__()`.

   .. py:method:: items()

      Returns an iteration over (key, value) pairs.

   .. py:method:: values()

      Returns an iteration over the values (regular files).
