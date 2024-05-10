
Files and directories
*********************

The selkie.cld.db package provides a database implemented as a
directory hierarchy whose files and subdirectories represent database
objects.

Persistent Objects
------------------

The File class
..............

A File represents a persistent object, that is, one whose contents
live on disk.  Files support multiple users, including a permissions
system and file locking and backup.  The main
complexity lies in synchronizing changes between the object in memory and the disk
representation.

One does not directly instantiate File, rather, one
defines specializations of File.  When defining a specialization, the
most basic information that is required is how to **write** the
contents of the object to a stream, and how to **read** the
contents from a stream.  The methods __write__
and __read__ implement those operations, and must be provided
by the specialization.

One also does not directly instantiate
the specialization.
Rather, a File is obtained from a persistent Directory,
either by calling the Directory's **__getitem__** method to obtain an existing
object or by calling its **new_child** method to create a new
object.  (The root object is created by calling **open_database,**
discussed below.)
Each child has a **name** (a string) that uniquely
identifies it relative to the parent directory.

When instantiating a child, the Directory determines which
class to instantiate by determining the
child's **typename.**  The environment, which is accessible as the
File member **env,** provides a one-one mapping
between typenames (which are strings) and classes.  The child's typename is determined
as follows:

 * If the child already exists, it is stored with a record of its
   typename.

 * The Directory may have a **signature,** which is a
   table that maps child names to typenames.

 * If the child name is not listed in the signature, or there is no signature,
   the Directory may have a value
   for **childtype,** giving a default typename to use for
   children.

 * Otherwise, the user must specify the typename when
   calling **new_child.**

A File's representation on disk is created by the method **__create__.**
The new_child method immediately calls __create__.
The function **create_database** is used to create root File.  It
calls open_database to instantiate the root file, and then it calls
the file's **create** method (no underscores).  The *create*
method is only available for root Files.

When a File is instantiated, its contents are not
immediately loaded.  The reason is that one should be able to list the contents of a
directory without loading into memory the entire hierarchy, or even all the files
in the directory.  To break the recursion, Files are initially instantiated
as unloaded stubs.

The possible **states** that a File may be in are as
follows:

 * **instantiated** - the object has been instantiated, but
   its contents have not yet been loaded from disk.

 * **loaded** - the object has been loaded from disk; its content
   members have been set.

 * **writing** - we are currently within the scope of a writer.

 * **modified** - the contents have been modified and a save is
   required.  Saving will return the object to the loaded state.

 * **deleted** - the object has been deleted.  Any attempt to
   access the content members results in an error.

The following methods change the object's state:

 * **__create__** - This is a private method intended
   for the sole use of *new_child* and *create.*  It creates an empty
   content file.  If any of the ancestor directories are missing, it
   creates them, as well.
   Note that __create__ does *not* do permissions checks nor
   update the index.  Those are handled by *new_child,* and unnecessary in
   the case of the *create* method.

 * **require_load** - Assures that the contents have been loaded, and
   that they are only loaded once.  The
   first time require_load is called, it immediately calls __load__, and
   after that, it is a no-op.

 * **__load__** - Opens an input stream and
   calls __read__, which a specialization must
   implement.  This is a private method intended for the sole use of
   require_load.

 * **writer** - Any modification to the contents should be done
   within the scope of a writer, which means, in
   the body of a *with self.writer()* statement.  One need not actually modify
   the contents, but if one does modify them, one should also
   call *modified* to mark the File as being modified.
   When the body of *with self.writer()* is exited, if the File has
   been marked as modified, its __save__ method is called.

 * **__save__** - Opens an output stream
   and calls __write__, which a specialization must
   implement.  This is a private method intended for the sole use of
   the writer.

 * **reparent** - Changes the File's parent.  That is, the
   File is moved to a different directory.

 * **delete** - Deletes the File.  The disk representation is
   deleted and the File is removed from the parent's list of
   children.  The instance is flagged as deleted, so that any 
   subsequent attempt to access its content signals an error.

Some of the actions signal an error unless the user has proper
permissions.  In particular:

 * **__create__** - The user must have write permission for the
   File and Directory.

 * **__load__** - The user must have read permission.

 * **__save__** - The user must have write permission.

 * **reparent** - The user must have write permission for
   the File and for both the source and target Directories.

 * **delete** - The user must have write permission for the
   File and Directory.

To change the permissions of a File or Directory, the user must have
admin permission.

Defining a specialization
.........................

When defining a specialization of File, it is the
specializer's responsibility to manage the contents.  To assure that
the object behaves as expected, one should adhere to the following discipline:

 * Contents reside in private members, and the only access to the
   contents or to any part of them is via the object's **access
   methods** (like __getitem__) and **update methods** (like
   __setitem__).

 * Contents and parts of contents are either immutable, or they are
   constructed from "virtual view" classes that dispatch to the access and
   update methods of the File.

 * Each access method definition begins with a call to require_load,
   assuring that the content members have been set.

 * Each update method definition is **protected** by being wrapped
   in *with self.writer().*  The writer immediately calls
   require_load, so one can count on the content members existing.
   An update method is not obliged to modify the contents, but if it does,
   it should call *modified*.

 * The __read__ method is given an input stream, and it should
   set the content members.  The first time it
   is called, the input stream will be empty; it should accommodate
   that case.  It should not count on the content members being
   undefined: it is also used to re-initialize the File after a failed
   save.

 * The __init_contents__ method is called by __create__.  The default
   implementation is a no-op, but specializations may override it to
   initialize the content members.  It is an *update*
   method, meaning that it should either be protected with a call
   to *with self.writer()* or it should only call protected
   update methods.  Since the writer calls
   require_load, the __read__ method actually gets
   called *before* __init_contents__ is called.

 * The __write__ method is given an output stream as argument.  It
   should write the contents in the form expected by __read__.

 * One may specify that this File **requires** one or more
   other Files.  Then any time a writer is created for this file, the
   required files are automatically added to it.  (See section XX
   below.)

Metadata
........

In addition to the usual contents, a File may contain **metadata.**
For example, any specialization that sets __has_permissions__ to True
will have a permissions metadata item.  Metadata
items are a special form of content, and are treated accordingly.
They reside in private members; accessors should call
require_load; and updaters should be protected by a writer.

A metadata item should be a specialization of Metadata, not of File.
Among other things, a metadata item is not independently loadable and
cannot be moved or deleted.  The File that the metadata item belongs
to is called the **host.**  There is an implementation issue that is
handled by the Metadata class: the *require_load*
and *writer* methods do not directly call __load__ and __save__
(which do not exist for Metadata), but rather
dispatch to the corresponding methods of the
host.

A specialization of Metdata should have __read__ and __write__
methods, like a File.
When the host's contents are read or written, calls are also placed to the __read__ or
__write__ method of all of its metadata items.

(There are two constraints, which are due to my laziness.  The
__write__ method must **not** write the line "##EOM", which is
used as a separator between metadata sections.  And the last line
that is written **must** end in a newline.)

To add metadata items,
a specialization should set the class member **__metadata__** to be a
tuple that extends the parent class's value.  Elements are pairs
(member, class).  For example::

   class MyObject (Directory):
       __metadata__ = Directory.__metadata__ + (('_foo', Foo),)

Summary of members and methods of File
......................................

The following provides a summary of the members and methods of File.
Some of the following have not yet been introduced, but will be
introduced in later sections.

Members:

 * __metadata__ —
   List of metadata member names.  (A class variable.)

 * __has_permissions__ —
   Set to True to add permissions to the metadata.

 * env —
   The environment.

 * indexed —
   The list of typenames that are to be indexed.  Discussed in
   section XX.

Instantiation:

 * create_root_env() —
   Create the environment for the root File.  Discussed in section XX.

 * create_env() —
   Create the environment for a non-root File that hosts an index.
   Discussed in section XX.

Creation:

 * __create__() —
   Creates the disk representation.

 * create() —
   Create the disk representation for a root File.  Signals an error
   if called for a File that is not root.

Reading:

 * require_load() —
   Calls __load__, and assures that it is called only once.

 * __load__() —
   Load the contents from disk.  Opens an input stream and calls __read__.

 * __read__(f) —
   Read the contents from an input stream.  To be provided by the specialization.

Writing:

 * writer() —
   Returns a Writer.  Should be called in a with-statement.  The File
   will be saved when the body of the 'with' exits, provided that it is modified.

 * modified() —
   Marks the File as modified.

 * __save__() —
   Save the contents to disk.  Opens an output stream and calls __write__.

 * __write__(f) —
   Write the contents to an output stream.  To be provided by the specialization.

Hierarchy modification:

 * reparent(par,i) —
   Par is the new parent.  The argument *i* is optional; it
   indicates the position among the new parent's children where this
   File is to be inserted.

 * delete() —
   Delete the File.

The Directory class
...................

A Directory behaves like a dict that maps names to child
Files.  I have already mentioned that the method __getitem__ accesses
an existing child, and new_child adds a new child to the Directory.

Directory is a specialization of File, so one Directory may be
a sub-Directory of another.  The absolute location of a File can be
given as a **path,** which is a sequence of names.  The
method **follow** takes a path as argument.  If the path contains
only one name, it simply calls __getitem__ with that name.  Otherwise,
it calls __getitem__ with the first name to get a subdirectory, and
passes the remaining names to the subdirectory's follow method.

We have already encountered the methods that modify the directory hierarchy:

 * The parent directory's **new_child** method is used to create a file.

 * The file's own **reparent** method is used to move a file to a
   different location.

 * The file's **delete** method is used to delete the file and all
   its descendants.

The set of children represents the Directory's primary contents.  The
children are read by the __read__ method and written by the __write__
method, and they are stored
in the private member **_children.**  Hence, specializations
do not need to define __read__ and __write__.

Summary of members and methods of Directory:

 * signature —
   A table that maps child names to typenames.

 * childtype —
   The default typename for children.

 * __getitem__(name) —
   Get the child with the given name.

 * new_child(name,suffix,cls,i) —
   Create a new child.  All parameters are optional keyword arguments.

 * follow(path) —
   Find a particular descendant given a sequence of names.

Database and Environment
........................

The module selkie.cld.db.core contains two functions for opening a database.
An existing database is opened by calling **open_database**, and a
new database is created by calling **create_database.**  A database
is really just a root File, that is, a File whose parent
is None.  The main thing that sets a database apart from any other
File is that it creates an Environment for itself and its
descendants.  A root File also automatically includes a GroupsFile
metadata item for use of the permissions system.

The Environment is a dict-like object containing global information.
It contains a pointer to the database, under the key 'root',
and it contains the tables that map
between typenames and classes.
If there is an index, it also contains a pointer to the index.
(Environments are discussed in more detail later.)

Files other than the root are allowed to create an index, by having a
list of typenames in the class variable __indexed__.  A File with an index creates a
fresh copy of its parent's environment, and
sets 'index_root' to itself.

If a File is neither a root nor indexed, it simply uses its
parent's environment unmodified.

The motivation for having indices is as follows.
Organizing Files into a hierarchy, rather than using the
usual relational representation, has the advantage that
entire subhierarchies can be moved or deleted as a unit.  It has the
disadvantage that one requires a path, and not just a name, to
find an object.  Indices make it possible to access Files
by **identifier** instead of path, where an identifier is a pair
(typename, name).

A simple identifier suffices for Files that are indexed in the root
directory.  When there are multiple indices, we must also include
the index name in identifiers.  A
**global identifier** is a triple (indexname, typename, name).

When writing specializations of Directory, one may also write
specializations of Environment.  To link the two,
define the File method **create_env**.
The default implementation instantiates and returns Environment,
provided that the File is either the root or indexed.  Otherwise, it
returns None, which indicates that the parent environment should be
used.

To delete a database that one has opened, call its *delete* method.
A function **delete_database** is also available that takes just a filename.

Implementation issues
---------------------

Filename
........

A Directory is implemented as a disk directory containing a
distinguished file called *_children,* which contains the actual
contents.  The distinction between the disk directory and the
file *_children* is hidden in the implementation.

The distinction resides primarily in associating two different disk
filenames with a Directory object.  The
method **_filename** returns the absolute pathname of the
disk representation for the sake of relocating or deleting the File.
In the case of a Directory, it returns the filename of the disk
directory.  The method **_contents_filename** returns the
absolute pathname of the disk representation for the sake of loading
and saving the File.  In the case of a Directory, it returns the
pathname of the *_children* file.  In the case of a File that is
not a Directory, _filename and _contents_filename are the same.

**Relocatability of Files.**
Because a File may be moved, we would like to minimize the number of
things that need to be updated if a File's location in the hierarchy
changes.  There are three aspects to the issue: a File should be
self-contained, a File should not cache context-dependent information,
and external information that needs updating when the File moves or is
deleted should be minimized.

**Self-containedness.**
All pieces of the File should be containined within the physical file
that represents it.  To give an example: we wish to be able to
identify a file's type by inspection, and one way of doing that would
be to place type information in the parent's list of children.
However, doing so would reduce self-containedness: the type
information would reside outside the child file and would need to be
updated if the child moved.  Instead, in the current implementation,
the filename on disk combines the File's name and typename.

This consideration also motivates the current implementation of
metadata (including permissions), in which metadata is represented on
disk as a section of the same file that contains the File contents.
A less acceptable approach would be to store permission information in
a sibling file.

**No context-dependent cached information.**
To give an example, it would be natural to cache a File's physical
disk location, but that information would need to be
updated if the File is moved.  In the current implementation, the
pathname is always computed rather than cached.

One unavoidable form of context caching is the env member,
which contains global information.  The current approach is to insist
that env be essentially immutable, and hence to restrict a
File from being attached to a new parent whose value from env
differs from the File's.

**Minimizing location-dependent external records.**
If the File has an indexed type, then
information about the location of a file is stored in an index.
That is hardly avoidable, and must be updated if the File is
relocated.  In the current implementation, that is the main case of
external information that must updated, apart from the obvious modifications to
the new and old parents.

There are a couple of additional dependencies that arise in CLD.

 * The *user*.media PropDict maps suffixed names to
   text IDs.  If the text is deleted, the PropDict needs to be updated.

 * A Lexicon contains lists of **references** to locations where tokens of a
   given lemma occur.  If a TokenFile is deleted, references to it need
   to be deleted as well.

To manage updates to external records, there are three
methods of File that can be used to notify resources of relevant events:

 * **Created.**
   A file is created by the Directory's **new_child** method or by
   its own **create** method (in the case of a root File).
   A newly created file
   receives a *created* call,
   which creates an entry in the
   index, if appropriate, and may be wrapped by specializations.

 * **Moved.**  A file is relocated by its own **reparent** method.  The
   file and all its descendants receive a *moved* call, which
   updates the index entries and may be wrapped by specializations.

 * **Deleted.**  A file is deleted by its own **delete** method.  The file
   and all its descendants receive a *deleted* call,
   which deletes the index entries and may be wrapped by specializations.

When an entire directory is moved or deleted, the *reparent*
or *delete* method walks the
subhierarchy and notifies each descendant of the change.

**File format.**
In the current implementation, metadata is stored in the same disk
file as the File contents.  For this reason, all Files are opened as
text files using UTF-8 character encoding.  Binary files such as audio
and video are stored separately; they cannot directly provide the
contents of a File.

The input stream passed to __read__ is not a genuine stream, but
rather a "pseudo-stream" (of type MetadataInputStream) that is merely
an iterator over lines of
text.  One MetadataInputStream is created for each section of the file
metadata header.

**Initialization.**
When a File is initialized, the Environment and Metadata items are
instantiated.  To keep things from becoming an unmanageable snarl, the
sequence is strictly as follows:

 * File.__init__ is called first.  It is always responsible for
   instantiating Environment and Metadata.  One should never create the
   Environment first.

 * Metadata.__init__ stores the host's *env* in its
   own *env* member.  For that reason, the Environment must be
   instantiated before instantiating the Metadata items.

 * However, Metadata.__init__ should not assume that all environment
   variables have been set.  Some depend on other metadata items.

The exact sequence is as follows:

 * Initialize members.
    
     * The arguments to File.__init__ are the parent directory, the name,
       and typename.  If the File is the root file, all three must be None.

     * The members _parent, _name_, and _suffix are set from the arguments.  The
       members _perm and _writer are set to None.  The members _loaded and
       _modified are set to False.  The member _metaitems is set to an
       empty list and _npermitems is set to 0.

 * Create the _metaitems list.
    
     * If __has_permissions__ is non-null or the File is the root, a
       Permissions item is put first on the list and _npermitems is advanced.

     * If the File is the root, a GroupsFile is added to the list and
       _npermitems is advanced.

     * If *indexed* is non-null, an Index is added to the list.

     * Any items on __metadata__ are added to the list.

 * Set up env.
    
     * The method create_env is called and the value is stored in *env.*
       If the value is None, parent.env is used.

     * If the File is a the root, the env
       keys 'root', 'log', and 'disk' are set; 'username' is set to
       '_root_' unless it already has a value.

     * If *indexed* is non-null, 'index_root' is made to point back
       to the File.
    
 * If there is no Permissions object on the _metaitems list, then
   _perm is set to an InheritedPermissions instance.

 * Each of the _metaitems is instantiated.

One uses **open_database** to instantiate the root File.
It takes the class of the root File and a filename as arguments.
It sets the *env* variable 'filename' to the filename and updates
*env* with any additional keyword arguments.
If the disk representation does not already exist, one should
use **create_database** instead of open_database.

A specialization of Environment is instantiated within create_env, and
keys are subsequently added to it.  The __init__ method should not
expect all keys to be present.  The File initializer adds some
keys, and open_database adds some more.

When Environment is instantiated, the File already exists; it is
called the *host.*  Environment.__init__ accesses the
host's *types* variable and *default_types* variable to set
up type tables.

An import paradox arises in setting
the default_types in selkie.cld.db.env.  The *env* module is imported by *file,*
which is imported by *dir.*  But the classes needed to set
default_types reside in *file* and *dir.*  The solution is
to set selkie.cld.db.env.default_types in the __init__.py file.

Checking permissions
....................

Read checks are performed when one does require_load() - specifically,
in File.__load__, just before calling the
__read__ methods of the metadata items and the File itself.  Write
checks are performed when one does "with self.writer()" -
specifically, in the Writer.lock_all method, which is called when the
writer is entered, or when a File is added to an active Writer.  The
write check is done just before locking the file, which is the first
step in writing it.

Permissions are stored in the File member **_perm.**
A File may have independent Permissions, or it may have
InheritedPermissions that always just defer to the parent.  The class
variable __has_permissions__ determines whether it has independent
permissions or not.  If it does have independent permissions, '_perm'
is added at the beginning of the __metadata__ list (in __init__).

**Permission-system items** are metadata items of class Permissions
or GroupsFile.  They require special treatment.

(1) Permission-system items require admin checks for writing.
Those checks are placed in the *writer* method of PermItem (of
which both Permissions and GroupsFile are specializations);
the *writer* method is called by all methods that modify
contents.

One might expect the check to be placed in the *__write__*
method, but that would be incorrect.  The Permissions metadata item
gets written any time one writes its host, and to do that, one only needs
write permission, not admin permission.

(2) Anyone should be allowed to examine permissions, even if they
do not have read access to the Files that host the permission-system
items.  It is not enough to postpone the read check till after reading
the permission-system items: one should not signal an error at all for
reading permission-system items, only for attempting to read the File
contents or other metadata files.

To deal with that issue, permission-system items have a require_load
method that does not simply dispatch to their host.

Details
-------

New child
.........

The new_child method is the standard way to create a new file.  There
is also a method called **need_child** that returns an existing
child, if available, and otherwise dispatches to new_child.  (The
child name is obligatory for need_child, but not for new_child.)

The new_child method is called with some subset of the keyword
arguments name, suffix, and
cls.  Its behavior is influenced by two class
variables: **signature** and **childtype**.  The signature
maps child names to classes, and childtype provides a default class.
Both are optional.

There are four cases:

 * Neither class nor suffix are provided.  If name is provided and
   has an entry in signature, the corresponding class is used.
   Otherwise, the childtype is used if available.  Otherwise, an error
   is signalled.  The suffix is determined from the class
   using env['suffixes'].  If not found, an error is
   signalled.

 * Suffix is provided but not class.  The
   table env['types'] is used to get the class.  If there
   is no entry, an error is signalled.

 * Class is provided but not suffix.  The table <code>env['suffixes']</code>
   is used to get the suffix.  If there is no entry, an error is
   signalled.

 * Both class and suffix are provided.  A check is done to confirm
   that <code>env['types']</code> maps the suffix to the given class,
   otherwise an error is signalled.

If the name is not provided, a call is placed to the allocate_name
method of the index table.  If there is no index table, an error is
signalled.

New_child then does the following:

 * A permissions check is done; the user must have write permission
   for the directory.

 * The class is instantiated to obtain the child.

 * The parent's attach_child method is called.  New_child accepts
   keyword argument i, which is passed on to attach_child.

 * The child's created method is called.
   If there is an index table, an entry is created for the child.
   The child has no children at this point, so recursion is not an issue.

 * The child's __create__ method is called, creating the disk-file.
   If the child is a regular file, an empty disk-file is created.  If
   the child is a directory, an empty directory is created, then the
   metadata files are created.  Specializations may wrap __create__ to
   create obligatory children by recursive calls to new_child.

Writer
......

The File method *writer* dispatches to the function *writer*
of selkie.cld.db.disk.  The function accepts any number of Files as
arguments.  It tosses out any that are already protected, a File being
protected if it has a value for *_writer.*  If any
unprotected Files remain, a Writer instance is created and each
unprotected File is added to it.  The Writer instance is returned, or
a dummy writer, if there are no unprotected Files on the list.

A Writer instance maintains a list of *files.*  Adding a file
consists of the following steps.  It is possible to
add additional Files to an existing Writer, so a check is first done
to see if the File is protected; if so, no further action is taken.
Otherwise, the File
is appended to *files,* its *_writer* member is
set to the Writer, and each of the Files that it requires is added to
the Writer.  Finally, if the Writer is already active, any new
unlocked Files are locked.

A Writer should be created in the context of a *with*-statement.
Accordingly, it expects a call to __enter__, and later a call to
__exit__.  The file becomes **active** when __enter__ is called,
and becomes inactive again when __exit__ is called.  When a Writer
becomes active, all Files on the *files* list are locked.  (Any
Files added while the Writer is active are locked when they are added.)

Locking a File consists of the following steps.
The Writer has a *locks* member that is None when the Writer is
inactive, and a list when the Writer is active.  To lock a File, a
check is first done that it is writable, then its require_load method
is called, and finally a Lock object is created for it and placed on
the *locks* list.  The Lock object locks the file on disk.
While the Writer is active, each of the the locked
files is said to be **under the control of the writer.**

On __exit__, each of the files is saved.  (Unless an error has
occurred, in which case each of the files is reloaded.)
The method __save__ opens a temporary file for writing,
and passes the resulting output stream to __write__.  If writing
completes without error, the current version of the file becomes a
backup and the temporary file is moved into its place.
After saving, each of the locks is released.

If an error occurs at any point - whether the error arises in the
write-permission check, or in the body of the *with* statement,
or during __write__ - then all of the files are restored to their
saved state by calling *_reload,* which calls the __read__ method
to restore the content members.

For some file classes, every time a file of the class is placed under
the control of a writer, there is a related file that should be put
under the control of the same writer.  For example, when editing a
TokenFile, one also needs the associated Lexicon to be editable, so
that one can intern new word forms.
There is a File method **requires** that can be overridden to provide an
iteration over the required files.  (The default implementation
returns the empty list.)  When the File is added to the Writer,
its *requires* method is called, and each File that is returned
is also added to the Writer.

Reparenting
...........

Reparenting consists of the following steps:

 * Check that the user has write permission for both the old parent
   and the new parent.

 * Call the old parent's detach_child method to remove it
   from the list of children.

 * Move the child's file or directory on disk.

 * Change the child's internal _parent member.

 * Call the new parent's attach_child method to add it to
   the list of children.  One may optionally specify the position with
   keyword argument i.

 * Call the child's moved method with old and new relpaths.
   That updates the cached relpath and,
   if the child is indexed, notifies the index of the old and new
   relpaths.  It recurses to the child's descendants.

Deletion
........

The delete method does the following:

 * Check that the user has write permission for the directory.

 * Call the parent's detach_child method to remove the
   child from its list of children.

 * Call the child's deleted method.
   If the object is indexed, this deletes it from the index.  It also
   recurses to the child's descendants.

 * Finally, delete the disk-file or -directory.  If it is a directory,
   the deletion is recursive.  If it is a regular file, any file with
   the same suffixed name plus an added suffix (such as a backup) is also deleted.

Reorder children
................

The Directory method reorder_children takes a list of child indices,
and a target index.  The *target child* is the child at the
target index, or end-of-list.  The children indicated by the indices are removed
from the child list, then reinserted as a group, in the order given,
just before the target child.

This only involves the _children list; it does not call reparent.

Reparent children
.................

The Directory method reparent_children takes the same arguments: a
list of child indices and a target index.  The target index identifies
the target child, which must be a real child and not end-of-list.

The target child's **attachment_target** method is called to determine
the new parent.  The default implementation of attachment_target
returns the child itself, but classes may override it.  (The method
need_child is useful here.)  The new
parent's attachment_target method must return the new parent itself;
otherwise an error is signalled.

To give a concrete example from CLD, a Text is initially created as a
stub.  Conceptually, one text attaches to another, but to be precise,
a complex Text contains a Toc, and the child Text attaches to the
Toc.  Nonetheless, we may provide a Text as the target of reparent.
The target Text's attachment_target method returns the Toc, creating
it if necessary.

The children indicated by the indices are processed in the order given.
For each, child.reparent(newparent) is called.  If the
child originally preceded the new parent, it is attached at the
beginning of the new parent's children, and if it followed the new
parent, it is attached at the end.  If multiple children are attached
at beginning or end, they occur in the order their indices are
listed.

Delete children
...............

The Directory method delete_children is called with a list of
indices.  The children at those indices are deleted by calling
their delete method.

A method **delete_child** is also provided as a convenience.  It
takes a single index.

Example
-------

A CLD corpus provides an example of a Database.  First, let us create
a CLDManager:

>>> from selkie.cld.toplevel import CLDManager
>>> mgr = CLDManager('/tmp/foo.cld')

A string argument is interpreted as the application filename, which
for CLD is the corpus.  The corpus does not yet exist; we can create a
corpus for testing using the 'create_test' command:

>>> mgr('create_test')
Create corpus '/tmp/foo.cld'
...

A lot of output is generated as each file is created.
Incidentally, *create_test* also creates a
file called *media* in the same directory as the corpus (namely, /tmp).

Now we can load the corpus:

>>> corpus = mgr.corpus()
>>> corpus
<Corpus /tmp/foo.cld>

A Corpus object is a specialization of Database, which is a
specialization of Directory.  It behaves like a dict in which the keys
are names of children:

>>> corpus['langs']
<LanguageList langs>

Like a dict, its length is the number of keys, and converting it to a
list returns a list of keys:

>>> len(corpus)
4
>>> list(corpus)
['langs', 'users', 'roms', 'glab']

In this particular case, all four children are subdirectories.  
If one recurses far enough, one reaches a file:

>>> orig = corpus['langs']['deu']['texts']['1']['toc']['2']['orig']
>>> orig
<TokenFile orig>

One can distinguish a file from a directory using the
method is_directory():

>>> corpus.is_directory()
True
>>> orig.is_directory()
False

Instead of repeatedly accessing members, one may use
the follow() method, which takes a pathname:

>>> corpus.follow('/langs/deu/texts/1/toc/2/orig')
<TokenFile orig>

Files may also behave like dicts or lists, depending on their
contents.  In this particular case, a TokenFile behaves like a list of
TokenBlocks (essentially, tokenized sentences):

>>> list(orig)
[<TokenBlock ('2', 0)>, <TokenBlock ('2', 1)>]

One may also go up the hierarchy using the
method parent():

>>> orig.parent()
<Text 2>

