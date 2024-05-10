
Database toplevel
*****************

Environment
-----------

There is an Environment object that contains global (or
at least contextual) information.  It was introduced previously.
The environment is created when the
root File is instantiated.  It is stored in the
file's env member and passed down from parent to child.

Some of the environmental information is associated with keys, as in a
dict, and other information is accessed by special-purpose methods.
Basically, information that is essentially configurational, and
available without access to the Database file, is stored in the dict,
and information that must access files inside the Database is
implemented as a method.

Files other than the root are permitted to have their own environment.  For
example, a multilingual corpus may contain monolingual subcorpora with
language-global (but not corpus-global) information in their
environments.

To write a specialization that has its own environment, one simply
defines the method *create_env* to return the new environment.
The choice can also be conditional - if *create_env* returns
None, the parent environment will be used.  The default implementation
of *create_env* returns a new environment if the file is root or
if it has a value for *indexed.*

The Environment initializer takes the host file as sole argument.  If
the host file has a parent, the Environment will copy the parent's env
by passing it to its own *update* method.
Subsequent changes to the parent environment do not affect the child
environment; nor do changes to the child environment affect the parent.

The basic file classes rely on the following environmental dict
entries and methods:

 * env['root'] - the root directory.

 * env['index_root'] - the directory that contains the
   Index.  Only files within this directory can be indexed.

 * env['filename'] - the pathname of the database as a whole.  It
   forms a prefix for the absolute pathnames of all objects in the
   database.  The Environment initializer makes sure that it is an
   absolute pathname.

 * env['username'] - a string.

 * env['disk'] - a Disk object that manages low-level
   interactions with the disk.  The Environment initializer keyword
   argument 'log' is passed to Disk when instantiating the disk.

 * env['types'] - a dict, maps suffixes to classes.

 * env['suffixes'] - a dict, maps classes to suffixes.

 * env.groups() - a GroupsFile, used by Permissions.

 * env.index() - an Index that tracks the locations of indexable
   objects.

The **scope** of an environment *e* is the set of files whose env
equals *e*.  With the exception of 'index', none of the
keys listed above should be overridden; they should all be genuinely
global.  New keys may be added, however, without restriction.

**Implementation Issue.**
The classes that make up the default-types table are not available
when the selkie.cld.db.env module is loaded.  They are actually set in
selkie.cld.db.__init__.

Indexation
----------

The environment contains an **index** (of class Index) that tracks the
location of files of certain types.  Directories within the hierarchy
are allowed to copy the environment and provide a new index,
so there may be different
indices for different portions of the hierarchy.  For example, a
corpus may consist of subcorpora, and each subcorpus may have its own
index.  For simplicity, however, there is only one index at any
given location in the hierarchy.

A directory that provides an index is known as an **index root.**
An index root is an instance of EnvRoot with a non-empty value for indexed.
A directory *d* that is an index root has the following properties.

 * By virtue of instantiating EnvRoot, *d* has its own Environment
   instance.  If *d* is the root of the database, the Environment is
   created fresh, and if *d* has a parent, the Environment is initially
   a copy of the parent environment.

 * In either case, *d*.env['envroot'] equals *d*.

 * Since *d*.indexed is non-empty,
   EnvRoot.__init__ method creates a metadata
   file _index of type Index.

 * The Environment.__init__ method sets *d*.env['index_root']
   equal to *d*.

An indexed file calls env.index() to get the index.
The Environment method index returns the _index
metadata file of the index root.  There is also an Environment method
indexed_types that returns
the indexed member of the index root.

An Index maps file suffixes to **tables** that keep track of
all files that have the given suffix.  The name of an indexed object must be
unique within its table, but names are not necessarily unique across
tables.

Because tables are named by suffixes, it is possible to
index an object, or to check that it is already properly indexed, knowing
only its typed name, without loading its contents.

To index an object, one requires the relpath, which includes the
object's name and suffix.  The suffix is used to select
a table from the index, then an entry
is created in the table, mapping the name to the relpath.
(If an entry for the name already exists in the table, an
error is signalled.)
Subsequently, one can directly access the object by typed name,
to determine the pathname.

It is 
permissible for an object to lack a name at the time of
indexing, provided that it does have a suffix.  In that case, a name is
obtained by calling the table's allocate_name method.
The table keeps track of the largest numeric name in the table, and
returns the next higher number as name.

If the object is moved (see <a href="#reparenting">Reparenting</a>) or
deleted, the table is notified.  Instead of walking the tree rooted at
the affected object, a pass is made through the index.  Any entry whose
path begins with the path of the affected object corresponds to one of
its descendants, and is modified or deleted, as appropriate.

To be precise, the following methods update the relevant table:

 * **new_child** of Directory creates a new entry.

 * **reparent** of File changes all relpaths that are
   extensions of the affected file's relpath.

 * **delete** of File deletes all entries where the relpath
   extends the deleted file's relpath.

Permissions
-----------

Overview
........

Permissions are granted to users to perform actions.
There is no fundamental distinction between users and groups: a group
is simply a user that has members.  Granting permission to a group
grants permissions to all members of the group.  The actions
are **'read'**, **'write',** and **'admin'.**  (Changing
permissions is currently the only thing that falls under admin.)

When changing permissions, one does not specify the action directly.
Rather one assigns users to **roles.**  The roles
are **'owners'**, **'editors',** and **'shared'.**  An owner
has read, write, and admin permission; an editor has read and write
permission; and a user on the shared list has read permission.

Finally, an item may inherit permissions from its parent.  If the
file's value for *__has_permissions__* is False, then the file
only has the permissions that it inherits from its parent, but if *__has_permissions__* is True, then
one may independently
specify whether ownership, editorship, and sharing are inherited or
not.  By default, *__has_permissions_* is True for Directories and
False for non-Directory files.

The method authorized_users() integrates both local and
inherited permissions.  The return value consists of three sets:
owners, editors, and shared::

   >>> perms.authorized_users()
   authusers= [{'abney'}, set(), set()]

The methods add() and remove() are used to change
permissions.  When applied to a File that lacks its own permissions,
they actually change the parent's permissions::

   >>> perms.add('foo', 'editors')
   >>> perms.authorized_users()
   [{'abney'}, {'foo'}, set()]
   >>> trans.permissions().authorized_users()
   [{'abney'}, {'foo'}, set()]
   >>> perms.remove('foo', 'editors')
   >>> perms.authorized_users()
   [{'abney'}, set(), set()]
   >>> trans.permissions().authorized_users()
   [{'abney'}, set(), set()]

There are two special users.  The user '_root_' has
permission to do anything; one cannot deny permissions
to _root_.  The user 'everyone' is a group that
everyone belongs to.  Permissions granted to 'everyone' do in
fact apply to everyone.

Protected files
...............

A **permissions file** regulates access to a **protected file**.
The permissions file is an instance of class Permissions.  The
permissions file is actually technically not a file but rather a
metadata item, and the protected file is its host.  The Permissions
object is stored in the member *_perm* of the host file.
The permission file protects its host file, and
all descendants of the host file that do not have their own permissions.

The method *check_permission* conducts a permissions check.
It is called by the *require_load* method
and the *writer* function.

The File method *permissions* returns the Permissions object.
If *__has_permissions__* is false, it returns an InheritedPermissions
object, which passes all requests to the parent's Permissions object.

**Implementation issue.**
There is a bootstrapping issue in loading the Permissions metadata
item.
To know whether we may load the host file, we first need to check the
Permissions object, but we cannot do that until we have loaded the
host file!  The solution was <a href="database.html#2.5">discussed previously</a>.

Controlling access
..................

There are two aspects to controlling access: what actions the corpus
permits without signalling an error,
and what actions the user interface makes available.  Violations of
corpus-level permissions result in a rather ugly and uninformative
"Permission denied'" page.  It is better for the user interface to
test permissions and avoid providing links to unauthorized
resources.

To check permissions, one needs a user name.  It is obtained from
env['username'].

The Permissions object provides two basic methods:

 * permitted(*a,u*) — Returns a
   boolean value indicating whether the user *u* is allowed to perform the
   action *a*.  The user is optional; if
   omitted, env['username'] is assumed.

 * check(*a,u*) — Calls permitted() to determine whether the
   action is allowed, and if not, raises a PermissionDenied
   exception.  Within the user interface, this causes a permission-denied
   page to be displayed.

The possible actions are: 'read', 'write', 'admin'.  The
following file methods check permissions:

 * require_load() — Calls check_permission('read'),
   which (for a File or Directory) signals an error if the user does not
   have **read** permission.

 * require_writer() — Calls check_permission('write'),
   which (for a File or Directory) signals an error if the
   user does not have **write**
   permission.

A call check_permission('write') executed on a Permissions
file or on a GroupFile gets translated into a check
for 'admin' permission.  Specifically, a Permissions object
does a write check by checking the 'admin' permissions listed
within itself, and a GroupFile handles a write check by
checking 'admin' permissions in the database root.

Determining permission
......................

The user '_root_' automatically has permission to do anything.
For any other user, permission is determined as follows.

There are three **roles:** owners, editors, and shared.
Which roles are relevant, or **enabled**, is determined by the action.
Specifically, only owners are enabled to perform an 'admin' action,
owners and editors are enabled to 'write', and
all three roles are enabled to 'read'.

When defining the permissions for a file or directory, one defines a
list of users or groups for each role, thereby granting those users
and groups permission to perform
the actions for which the role is enabled.  In addition, one chooses
whether additional role members should be inherited from the parent or
not.

Procedurally, the permissibility of user *u* taking action *a* is controlled by
two internal data structures within the Permissions instance:
the **local permissions list** and the **inheritance mask**.
Both are indexed by role.

The local permissions list consists of three sets of users, *S<sub>0</sub>, S<sub>1</sub>, S<sub>2</sub>*,
one for each role.  Let *U* be the set of ancestors of the user, including the
user him/herself.  If *U* &#8745; *S<sub>r</sub>* is nonempty for an enabled role *r*,
permission is immediately granted.

Otherwise, the inheritance mask is consulted.  The mask contains a
boolean value *b<sub>r</sub>* for each role *r*.  If *b<sub>r</sub>* is False then
role *r* is disabled; otherwise its status remains
unchanged.  In other words, the number of enabled roles can never
increase as one goes up the hierarchy.  After using the current mask
to update enablement status, one replaces the permissions with the
parent's permissions, and the process repeats.  Whenever there is no parent,
or no enabled roles remaining, permission is denied.

The method authorized_users returns a list of three sets: all
authorized owners, editors, and shared.

Setting permissions
...................

There are four methods that change the contents of Permissions:

 * set(o,e,s,i) —
   This entirely replaces any previous contents.  The first three
   arguments should be iterables over names; they will be converted to
   sets and stored in the local permissions for owners, editors, and
   shared, respectively.  The argument *i* should be a list of
   roles, drawn
   from 'owners', 'editors', 'shared'.  The
   new inheritance mask will have True for each in the list and False
   for any that are omitted.

 * add(name,r) —
   Adds *name* to the role *r* in the local
   permissions.

 * remove(name,r) —
   Removes *name* from the role *r* in the local
   permissions.

 * set_inheritable(r,v) —
   Sets the inheritability of role *r* to value *v*.  The
   value is optional; it defaults to True.

Users and groups
................

No essential distinction is made between users and groups: groups are
just users that are ancestors of other users.

The groups file is accessible as env['groups'].  The
key methods for reading it are:

 * users() —
   Iterates over all user names, including those that have no
   parents.  Does not include Everyone.

 * parents(u) —
   Returns a list.  Returns the empty list for any username that has
   not been previously encountered.

 * all_groups(u) —
   Returns a set.  The set always contains *u* itself and
   Everyone.  If *u* has not been previously encountered, the set
   contains nothing else.

The methods for modifying the file are:

 * set_parents(u,ps) —
   Stores *ps* as the parents of user *u*.

 * delete_user(u) —
   Deletes the parent list for *u*.  It does not scan through
   looking for users that have *u* as parent, so references
   to *u* as parent may survive.

Database
--------

Description
...........

A database is represented simply by a root directory.
It is created using a Manager, as discussed previously.

There is a **types table** that maps typenames to classes.  It is
actually defined in the Environment.  But to avoid the necessity of
defining a new specialization of Environment to supplement the types,
the Environment also incorporates any entries in the host directory's
variable types.

The reverse mapping, from class to typename, is constructed by the
Environment initializer.

The default types, with their typenames, are: Integer (int), String
(str), Strings (strs), Table (tab), PropDict (pd), and Directory
(dir).

An example
..........

Here is an example of defining a database.

>>> from selkie.cld.db.core import open_database, create_database, delete_database
>>> from selkie.cld.db.file import Integer, Strings, Table
>>> from selkie.cld.db.dir import Structure
>>> class Things (Structure):
...     signature = {'foo': Integer,
...                  'bar': Strings,
...                  'table': Table}
...
>>> class MyDatabase (Structure):
...     signature = {'strings': Strings,
...                  'things': Things}
...     types = {'thg': Things}
...

The *types* declaration is necessary to permit us to use Things
in the database.  Each specialization of File that is used must be
associated with a unique typename.  "Used" means used internally - the
root directory is excepted.

To create the disk representation:

>>> db = create_database(MyDatabase, '/tmp/my.db')
disk MakeDirs /tmp/my.db
...

We may set and access a value:

>>> db.things.foo.set(42)
locks Lock /tmp/my.db/things.thg/foo.int
disk Modify /tmp/my.db/things.thg/foo.int
locks Release /tmp/my.db/things.thg/foo.int
>>> db.things.foo.value()
42

We may confirm that it is persistent by re-opening the database:

>>> db = open_database(MyDatabase, '/tmp/my.db')
>>> db.things.foo.value()
42

Clean up:

>>> delete_database('/tmp/my.db')
disk RecursiveDelete /tmp/my.db

