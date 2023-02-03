
.. :py:module:: selkie.manifest

``selkie.manifest`` — Manifest of sizes, hashes
===============================================

Executable
----------

Usage::

   $ manifest foo         # writes foo.sizes
   $ manifest -s foo      # writes foo.chksum
   $ manifest -h foo      # writes foo.hashes
   $ manifest -H foo      # writes foo.md5
   $ manifest -c foo  | diff - foo.sizes
   $ manifest -cs foo | diff - foo.chksum
   $ manifest -ch foo | diff - foo.hashes
   $ manifest -z foo -o foo.sizes
   $ manifest -s foo -o foo.chksum
   $ manifest -h foo -o foo.hashes
   $ manifest -Z foo.hashes | diff - foo.sizes
   $ manifest -l foo > foo.dirs
   $ manifest foo.dirs
   $ manifest -d foo old.sizes  # writes to stdout
   $ manifest -d foo old.sizes -o foo.diffs
   $ manifest -e delta.tgz -d foo old.sizes
   $ manifest -e delta.tgz foo.diffs
   $ manifest -i delta.tgz


Create foo.sizes
^^^^^^^^^^^^^^^^


The script ``manifest`` creates a listing of the files in a directory
hierarchy, recording their sizes, or their sizes and MD5 hash values.
The basic usage is::

   $ manifest foo


This expects ``foo`` to exist and to be a directory.  It writes a
file called ``foo.sizes``, in which it records the pathnames and
sizes of all files in the directory hierarchy under ``foo``.
One can then use ``diff`` to compare that listing to the listing
created for another copy of ``foo``.  For example::

   $ diff foo.sizes /Backups/foo.sizes


Create and check foo.md5
^^^^^^^^^^^^^^^^^^^^^^^^

To compute an MD5 hash for each file::

   $ manifest -H foo

Computing the hash values is *much* slower than just getting the
sizes.  For that reason, ``-H``
checkpoints foo.md5 every 2 seconds.  It writes first to a temp
file, and replaces foo.md5 only if the temp file is successfully
written.

It prints out "Compute hash ..." for each file when it computes the
MD5 value, and it prints out "Writing ..." each time it checkpoints
the .md5 file.

After computing hashes, one should save foo.md5 to a safe place.
Subsequently, one can recompute foo.md5 and do a diff to the saved
copy to determine whether any files have become corrupted.

Create foo.hashes
^^^^^^^^^^^^^^^^^

(Deprecated.)  This is an old version of ``-H``, which does not do
checkpointing::

   $ manifest -h foo

The listing is written to ``foo.hashes``.

Creating foo.chksum
^^^^^^^^^^^^^^^^^^^

The ``-s`` flag causes checksums to be produced.  This is still
much slower than just a size listing, but it is about four times
faster than hashes.  It is not crytographically secure, but is just as
good at detecting changes that were not specifically intended to
deceive.

Writing to stdout
^^^^^^^^^^^^^^^^^

One may use the ``-c`` flag to cause the sizes to be
written to standard output instead of a file::

   $ manifest -c foo | diff - foo.sizes

The ``-c`` flag may be combined with ``-h`` or ``-s``.  When hashes are
written to a file, progress messages are printed to standard error,
but the progress messages are suppressed when ``-c`` is provided::

   $ manifest -ch foo | diff - foo.hashes


Extracting sizes from foo.hashes or foo.chksum
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

One may use the ``-Z`` flag to extract a size listing from a
hashes or checksum.  For example::

   $ manifest -Z foo.hashes | diff - ~/Backups/foo.sizes
   $ manifest -Z foo.chksum | diff - ~/Backups/foo.sizes


Selecting directories
^^^^^^^^^^^^^^^^^^^^^

Finally, one may limit the listing to a subset of the directories.  To
get a raw listing of the directories::

   $ manifest -l foo > foo.dirs

Then edit ``foo.dirs`` by hand to leave only the directories that
should be included, and do::

   $ manifest foo.dirs

As a safety precaution, the filename must end in ``.dirs``,
otherwise an error is signalled.  The output is written to
``foo.dirs.sizes``, so that it can be readily distinguished from
``foo.sizes``, which includes all subdirectories.

Synchronizing directories
^^^^^^^^^^^^^^^^^^^^^^^^^

Suppose ``foo`` is a working version of a shared project.
Before making any edits, create a manifest ``old.sizes``.
After making changes to ``foo``, the following creates a list of
all files that have been changed (added, modified, deleted)::

   $ manifest -d foo old.sizes

It prints out a list of actions that would need to be applied to the
*old* version of ``foo`` to bring it in sync with its
current state.  That is, it is a summary of the editing actions that
have been taken since the manifest ``old.sizes`` was created.

One can capture just the edits and apply them to other copies of ``foo``.
To create a tarfile containing the edits::

   $ manifest -e delta.tgz -d foo old.sizes

To update an old version of ``foo``, e.g., on another machine,
copy ``delta.tgz`` to the other machine and do::

   $ manifest -i delta.tgz

The tarfile ``delta.tgz`` includes a listing of the diffs,
containing relative pathnames; that is why one does not
specify ``foo`` on the command line.

Module
------

Toplevel functions
^^^^^^^^^^^^^^^^^^

The command line versions translate to function calls as follows.
First, flags translate into keyword-value settings.  Some flags take one or two
arguments; their arguments are taken as the flags are encountered.  In
the end, if any arguments remain, the null flag is imputed.

.. list-table::

   * - z
     - fnc=create, ifile=*arg*, otype='z'
   * - s
     - fnc=create, ifile=*arg*, otype='s'
   * - h
     - fnc=create, ifile=*arg*, otype='h'
   * - c
     - ofile='-'
   * - o
     - ofile=*arg*
   * - Z
     - fnc=extract_sizes, ifile=*arg*
   * - l
     - fnc=list_directories, ifile=*arg*
   * - d
     - diff=(*arg1*, *arg2*)
   * - e
     - fnc=export, ofile=*arg*
   * - i
     - fnc=import_into, ifile=*arg*
   * - *null*
     - arg=*arg*


The following information is then supplied:

If keyword 'diff' is provided, then *fnc* defaults to
'diff'.  Otherwise, *fnc* defaults to 'create'.
The keyword 'arg' gets replaced by:
    
    'ifile' if the fnc is 'create'
    'diff' if the fnc is 'export'
    'dest' if the fnc is 'import'
    



The calls at
the top of the page translate as follows.  The supplied information is
marked with brackets:

manifest([fnc='create',] arg[ifile]='foo')
manifest(fnc='create', ifile='foo', otype='s')
manifest(fnc='create', ifile='foo', otype='h')
manifest([fnc='create',] arg[ifile]='foo', ofile='-')
manifest(fnc='create', ifile='foo', otype='s', ofile='-')
manifest(fnc='create', ifile='foo', otype='h', ofile='-')
manifest(fnc='create', ifile='foo', otype='z', ofile='foo.sizes')
manifest(fnc='create', ifile='foo', otype='s', ofile='foo.chksum')
manifest(fnc='create', ifile='foo', otype='h', ofile='foo.hashes')
manifest(fnc='extract_sizes', ifile='foo.hashes')
manifest(fnc='list_directories', ifile='foo')
manifest([fnc='create',] arg[ifile]='foo.dirs')
manifest([fnc='diff',] diff=('foo', 'remote.sizes'))
manifest([fnc='diff',] diff=('foo', 'remote.sizes'), ofile='foo.diffs')
manifest(fnc='export', diff=('foo', 'remote.sizes'), ofile='delta.tgz')
manifest(fnc='export', arg[diff]='foo.diffs', ofile='delta.tgz')
manifest(fnc='import_into', ifile='delta.tgz', arg[dest]='foo')


The functions that are dispatched to are as follows:


``create(ifile, otype, ofile, update, trace, force)``

    
    *ifile* may end with '.dirs', or it may name a directory.
    *otype* is one of 'z', 's', or 'h'.
    *ofile*, if provided, may be a filename, '-', a list, a dict, or a file.
    It defaults to dir + a suffix depending on *otype*.
    If *update* is True, then otype, ofile, and force must be None.
    Otype is determined from the ifile suffix, ofile is set to
    ifile, and force is set to True.
    *trace* defaults to False for type 'z' and True for types 's'
    and 'h'.
    *force* defaults to False.  If False, create will refuse to
    overwrite an existing ofile.
    


``extract_sizes(ifile)``

Ofile defaults to stdout


``list_directories(ifile)``

Ofile defaults to stdout


``difference(diff, ofile)``
*ofile* defaults to stdout

``export_delta(diff, ofile)``
*diff* may either be a filename containing diffs, or a pair
consisting of directory and remote sizes listing.  The diffs specify
what must be done (additions, replacements, deletions)
to make the **remote directory** match the
given directory.


``import_delta(dest, ifile)``
*Dest* must be a directory and *ifile* must be a tarfile
produced by export().




