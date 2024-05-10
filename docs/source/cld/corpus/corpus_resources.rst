
Global resources
****************

Users
-----

User object
...........

The main representation for a user is found in the users
directory within the Corpus instance.  The users directory
is an instance of UserList, and its members are instances of User.

The permissions system has its own user information, contained in the
GroupsFile object.  See <a href="toplevel.html#3">Permissions</a>.

The primary constraint that is placed on user names is that they be
suitable for use as a filename component.  They must not contain slash
or dot.  There is a general expectation that they contain only ASCII
letters, digits, or underscore.  Nevertheless,
when using a user name as part of a URL, it is safest to hex-encode it.

The Environment method **user** takes a username and returns
an instance of either User or UnknownUser.  Both
classes provide the following members and method:

 * props — A PropList.

 * media — A PropList mapping media suffix to relpath.

 * name() — A string, the user name.  (Inherited
   from File, in the case of User.)

One can use the new_child() method of UserList to add new
Users.

User editor
...........

Romanizations
-------------

Romanization
............

A Romanization is a mapping from 7-bit ASCII strings to Unicode
strings.

 * decode(b) —
   Returns the decoding of the byte-sequence *b*.

 * decoder() —
   Returns a decoder.  (The decode method creates a new one each time
   it is called.)

 * romanization() —
   Returns the romanization itself; the file contents.

 * __setitem__(k,v) —
   Modifies the mapping.

A ReadOnlyRomanization behaves the same, except that it signals an
error if one tries to set an entry.

Registry
--------

A Registry is a specialization of Directory that contains
Romanizations.  The following methods are useful:

 * new_child(name) —
   Create a new Romanization.

 * __getitem__(name) —
   Returns an existing Romanization.  Returns a Romanization file.
   If the directory contains a file with the given name, it is
   returned, and otherwise, if there is a "standard" romanization with
   the given name, it is returned, wrapped in the ReadOnlyRomanization class.

 * __contains__(name) —
   True if there is a file in the directory or a standard
   romanization with the given name.

 * __iter__() —
   Iterates only over the files that are actually in the directory.

Editor
------
