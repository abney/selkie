
.. automodule:: selkie.cld.__main__

Running CLD
***********

To run the corpus editor::

   $ python -m selkie.cld

In its current instantiation, the corpus editor uses the default web
browser as its window system. The original motivation for designing it
that way was to have a single code base that runs either as a local
application or as a web service, and to make the editor independent of
any one platform.

Creating a corpus
-----------------

One can create a new corpus by typing in a filename under 'New File'
and clicking 'Create' (or hitting Return).

One can create a test corpus to play with as follows::

   $ python -m selkie.cld /tmp/foo.cld create_test

That creates the directory foo.cld.
One can then examine or edit it by doing::

   $ python -m selkie.cld /tmp/foo.cld

This runs a web server and opens the user's default web browser. As
one interacts with the browser window, log information is printed in
the original terminal window. To stop CLD, type ctrl-C in the original
terminal window.


Corpus contents
---------------

At the highest level, a corpus consists of a list of **languages**
(along with some global resources such as *romanizations*).
A language, in turn, consists of a **lexicon** and a list of **texts.**
A text may be a **complex text**, which is essentially a listing of
smaller texts, or a **simple text**.
If we view the document structure as a tree, the
nonterminal nodes are complex texts, and terminal nodes are simple
texts. A simple text is a list of sentences (loosely
understood). It may also include a translation. A text may also be
associated with an audio file, in which case the text is a
transcript. We may think of a transcribed recording interchangeably as an audio
file with annotations, or a text backed by audio.

Despite the hierarchical structure, a corpus may also be viewed as a
flat list of **items.**  Each language, romanization, lexicon, and
text constitutes a separate item.

The item for a language contains only the information that is not
part of a smaller item that it contains. To be precise, a language item
contains only summary information about the language.
To get the list of items in the corpus, do::

   $ cld /tmp/foo.cld items

Usage
-----

For the sake of reference, I give a
full command listing here::

   $ cld SPEC
   $ cld SPEC auth ls|set|check|delete [USER]
   $ cld SPEC call PATH [CKW*]
   $ cld SPEC config
   $ cld SPEC create|-c
   $ cld SPEC create_cgi CGIFN [CKW*]
   $ cld SPEC create_test
   $ cld SPEC delete|del|-d [LANG] [ITEM*]
   $ cld SPEC export|-e EFN [LANG] [ITEM*]
   $ cld SPEC extract [DIR] [CKW*]
   $ cld SPEC get ITEM [CKW*]
   $ cld SPEC glab COM [USER*] [CKW*]
   $ cld SPEC group [GRP] [COM] [USER*] [CKW*]
   $ cld SPEC import|-i EFN
   $ cld SPEC info [PATH]
   $ cld SPEC list|-l [ITEM*]
   $ cld SPEC ls [PATH]
   $ cld SPEC perm [PATH] [add|remove USER ROLE]
   $ cld SPEC rm [ITEM] [CKW*]
   $ cld SPEC run [CKW*]
   $ cld SPEC set [KV*]
   $ cld SPEC tree [KW*]
   $ cld SPEC unset [KEY*]
   $ cld SPEC user [USER [add|remove GRP]] [CKW*]

Parameters
..........

The usage is "object-oriented" in the sense that the parameter SPEC is a
specification for an application file, configuration, or export file,
and the command is treated conceptually as a method of that file.
The SPEC may be a single filename, or a list of
**configuration keyword-value pairs** (CKW).  With some commands, additional keyword-value pairs may
be added at the end of the command line, as indicated by "[CKW*]".

A keyword-value pair is a single word of form KEY=VALUE, containing a
literal '=' character.
The list of configuration keywords is given in the section :ref:`configuration_keys`.
In addition, some shorthands are permitted for convenience.

 * If the first word in SPEC does not contain an '=', the keyword
   'application_file' is supplied.  In other words, one may simply give
   the filename of the CLD corpus, configuration file, or export file
   as SPEC.

 * '-u' is a shorthand for 'desktop_user=X', where the next word in
   line is used to supply the value of *X*.

 * '-p' is a shorthand for 'server_port=X'.

 * '-M' is a shorthand for 'media_dir=X'.

 * '-A' is a shorthand for 'auth_dir=X'.

 * '-w' is a shorthand for 'execmode=webserver log_file=- logging=all loopback_testing_on=True'.

Commands
........

The individual commands are as follows.

 * **(no command)** — Same as ``run``

 * **auth ls|set|check|delete** [*USER*] —
   USER is optional for ls, though it is obligatory for all other subcommands.

    * ls — list the users, or confirm that the given USER is present

    * set — set the password for USER

    * check — check the password for USER

    * delete — delete the entry for USER

 * **call** *PATH* [*KV*] — Instantiate the app and run it.  First, it launches
   an internal Python web server that calls back to the app to
   handle requests.  Then it packages *PATH* [*KV*\*] as an HTTP
   request and sends it to the server.  Note that, in this case only,
   a given key may appear multiple times, provided that the key
   begins with \*.

 * **config**
   — Print out the corpus configuration file.

 * **create**
   — Create the named corpus directory as an empty corpus.

 * **create_cgi** *CGIFN* [*KW*]
   — Create a CGI file that uses the named corpus.  CGIFN is the
   filename to create.

 * **create_test**
   — Creates a test corpus.  Prepopulates it from seal/examples/corp1.ef.
   Also creates a media directory.  If not otherwise specified, the
   media directory will be called 'media' in the current directory.

 * **delete** [*LANG*] [*ITEM*\*]
   — Delete the indicated items.  See Chap 18, Export files.

 * **export** *EFN* [*LANG*] [*ITEM*\*]
   — Export the indicated items to the file EFN.  The value
   '-' may be used for stdout.  
   LANG is a subcorpus identifier, which may be a language code,
   'roms', or 'glab'.
   ITEM is a designator for a specific item in the corpus,
   such as 'oji/1'.  If LANG is provided, 'oji' may be omitted.
   If no items are named, the entire corpus is exported.
   See Chap 18, Export files.

 * **glab** ls [*USER*\*]
   — List the notebooks belonging to each of the named USERs.  If no
   USER is provided, list the users.  Equivalent to 'cld CFN ls glab'
   or 'cld CFN ls glab/USER'.

 * **glab** add *USER*\*
   — Add libraries for each of the given USERs.

 * **glab** rm *USER*\*
   — Delete the libraries of each of the given USERs.  Use with
   caution!  Cannot be undone.

 * **import** *EFN*
   — Import from EFN.
   See Chap 18, Export files.

 * **info** [*PATH*]
   — Print out name, file type, and permissions for the given PATH.
   The PATH omits filename suffixes; e.g. 'langs/oji/texts'.
   Any leading slash is ignored.  If PATH is omitted, use the root.

 * **list** [*ITEM*]
   — List the named items.  If none are specified, list the entire corpus.

 * **ls** [*PATH*]
   — List the children of a given directory.  PATH is interpreted as
   for 'info'.

 * **perm** [*PATH*] [add|remove *USER* *ROLE*]
   — Show or modify permissions.  PATH is interpreted as for 'info'.
   'add' causes the USER to be added to the ROLE for this
   file, and 'remove' causes the USER to be removed from the
   ROLE.  If neither 'add' nor 'remove' are
   specified, the permissions are displayed.
   The legal values for ROLE are 'owners', 'editors', or 'shared'.

 * **run** [*KW*\*]
   — Run the CLD application.  This is the default, if no command is
   provided.  See: Running CLD as
   an application and Running as a web service.

 * **set** [*KV*\*]
   — Set values of configuration keys.
   KV represents a keyword-value pair of
   form *key=value*.  A given key
   is permitted to appear multiple times, provided that it starts with '*'.

 * **tree** [*KW*\*]
   — Print out the contents of the corpus in tree format.
   KW is a keyword argument of form *key=value*
   that controls printing.

 * **unset** [*KEY*\*]
   — Unset values of configuration keys.
   KEY is just a keyword, without an indication of a value.

 * **user** [*USER* [add|remove *GRP*]] [*CKW*\*]
   — USER and GRP are both user names, but GRP is treated as a group
   (a user with members).

Programmatic interface
----------------------

Executing selkie.cld from the command line does::

   $ from selkie.cld.toplevel import CLDManager
   $ mgr = CLDManager()
   $ mgr.main(sys.argv)

One can execute commands directly from Python by instantiating the
CLDManager, passing it the corpus filename, and calling it as a
function instead of using *main*.  For example::

   $ mgr = CLDManager('/tmp/foo.cld')
   $ mgr('create_test')

See the documentation of CLDManager for more
information.
