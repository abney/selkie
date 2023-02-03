
``selkie.store`` — Object store
===============================

JSONDisk - unit is the file.  Directories are created incidentally.

An Object is either a Dict or a List.  It represents the contents of a
JSONDisk at a finer grain.  An Object may be attached to a file, or an
element inside of a file, or a directory.  It may also be unattached.

An Object has a ``_contents`` member that contains the current
contents of what is on disk.  If ``_contents`` is None, the Object is
unattached.

which 


An ``Object`` is a dict-like JSON object that is backed
by a JSONDisk, and a ``Store`` maps pathnames to Objects.
To clarify, let us define some terms:

**Dict-like object**
   An object that has an ``items()`` method.

**List-like object**
   An object that has an ``__iter__()`` method, but is not dict-like.

**JSON object**
   None, a boolean, int, float, or string, or a dict-like or list-like
   object consisting of JSON objects.  

**Backing**
   A directory, file, or part of a file that provides the persistent
   content of an Object.

**Key**
   A member of an Object that contributes an item to ``items()``.

**Basic key**
   A key that has a direct backing.  The value of the key
   is set when the Object is instantiated, and setting the
   value causes the backing to be rewritten.

**Defined key**
   A key that is not basic.  Its value is computed from the values of
   basic keys, and setting its value sets the values of basic keys.



An Object is instantiated from a directory, file, or part of a file,
known as its **backing**.  Object classes are never instantiated by
the user, but are always obtained by reading from a store.

Instantiating the object from its backing sets certain keys, which are distinguished as
**basic keys**.  Setting the value of a basic key causes 



**Defined keys** are also permitted.  Their values
are determined by the values of basic keys, and setting them


provides construction from JSON and rendering to
JSON.  It is intended for use with a ``Store``, which is a
specialization of JSONDisk (see :py:mod:`selkie.disk`) that provides a
store of persistent objects.


Distinguish directory objects or file objects from meta-objects.
The backing of a meta-object is just a part of a file; typically a
listing.  A file object is immediately loaded in entirety, but
the members of a directory object are only loaded on demand.  The
members of a directory object are files or subdirectories.

We distinguish between *instantiation* and *loading*.  Loading
involves reading something from disk.  We rely on schemas to know what
the contents of a directory are (or rather, should be).  Directory
listings are never taken.  Loading consists exclusively of the loading
of individual files.

A **directory object** is backed by a directory.
Directories are never loaded.  The first time a key is accessed, the
value of that key (and only that key) is instantiated.  The key's
value (which must be a directory object or file object) is only
instantiated, not loaded.

A **file object** is backed by a file.  Nothing is loaded when the
file object is instantiated.  The file is loaded the first
time any key is accessed.

A **partial-file object** is an object that cannot be independently
read or written.  Its contents exist in entirety when it is instantiated.
It has a pointer to the file object that contains it.  If the
partial-file object is modified, it instructs
the containing file to save itself.

Objects wrap plain lists and dicts produced by ``read_kvi()``.
A subclass defines ``__schema__``, which determines the basic keys.
A defined key is added for each method whose name begins ``get_``.

Object provides ``__getattr__()``, etc., ``__getitem__()`` etc., and ``GET()`` etc.

As a JSON object, an Object is equal to its contents (which is what
the JSONDisk reads in).
