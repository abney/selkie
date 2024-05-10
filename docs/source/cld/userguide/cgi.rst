
Running CLD as a web service
****************************

.. warning::

   CLD has not been vetted by a security expert. It is not safe to run
   it on a public server.

There are a couple of differences between the desktop application and the
web application.  When running on the desktop, one automatically
has full permissions; the internal password authentication system is
not used.  One also has access to the corpus manager, which allows one
to switch between corpora and create new corpora.  The web
version only accesses a single fixed corpus.

That being said, the differences have to do with configuration rather
than code.  The desktop application actually just runs the web
application within a Python web server that it runs internally,
effectively using a browser as its user interface.

Local testing
-------------

It is recommended to create a directory just for the CLD corpus and
supporting materials, outside of the Apache document
directory::

   $ mkdir cld
   $ cd cld

Create an empty corpus::

   $ cld corpus.cld create

One can do local testing first, before deploying.  Run in webserver
mode rather than desktop mode::

   $ cld corpus.cld -w

This will start an internal Python webserver and open a browser window
pointing at localhost:8000.  You should get a Login page.

One cannot log in without defining users.  For the sake of
illustration, let us create a user named leo.
Stop CLD (use ctrl-C), and do::

   $ cld corpus.cld auth set leo

This creates an account for leo and prompts you for a password.
Notice that the password and sessions file reside in a directory
called 'auth' that is a sibling to the corpus directory.  That
location is a configuration setting, which you may change if you
desire.  To see the current configuration settings::

   $ cld corpus.cld config

Now that we have created a user, let us restart the web server (cld corpus.cld -w)
and log in using user name 'leo' and the password you chose.

When you do so, you get a new page, and it should indicate, in the upper right
corner, that 'leo' is logged in.  But it says the corpus is not
readable.  When a corpus is created, no permissions are automatically
granted.

Stop the web server again, and make leo be an owner of the corpus::

   $ cld corpus.cld perm / add leo owners

The slash indicates the root directory; leo is being added to the list
of owners.  Permissions are inherited, so leo will be owner of any
additional subdirectories that we create, unless we explicitly remove
leo from the owners list of some subdirectory.

Now restart the web server.  Unless you clear your browser history, or wait long enough
for the session to time out, leo will still be logged in, and you 
will now get a list of corpus contents.

Creating a CGI script
---------------------

One can create a CGI test script that just displays environment
variables.  The contents of the script::

   #!/Users/abney/anaconda3/bin/python
   
   import site
   site.addsitedir('/Users/abney/git/seal/python')
   
   from seal.app.toplevel import test_app, Manager
   Manager(app=test_app).cgi()

To run CLD, the CGI script should look something like the following.
(The pathnames may need to be different in your environment)::

   #!/usr/local/bin/python
   
   import site
   site.addsitedir('/usr/local/seal/python')
   
   from seal.cld.toplevel import CLDManager
   mgr = CLDManager('/usr/local/cld/corpus.cld',
                    auth_dir='/usr/local/cld/auth',
                    log_file='/usr/local/cld/log',
                    logging='all')
   mgr.cgi()

For debugging, examine the log file.  Its pathname is given in the CGI
script.

Configuration
-------------

Configuration file
..................

The configuration file may be stored in a file, or it may be provided
on the command line, or as created as a dict in Python.  It is passed
to the App constructor.

A complete list of configuration variables is provided in the
section Configuration keys.
One may also wish to refer to the list
of Logging conditions.

Password and session files
..........................

To enable password protection, one requires a password file and
sessions file.  These are plain-text files named 'users.txt'
and 'sessions.txt' in the server_dir.  They should be readable
by httpd, but not world-readable.  **They should absolutely not be
under htdocs.**

The password file contains one line for each user.  The fields are the
user name, the salt, and the password hash value.  The sessions file
also contains one line for each user; its fields are user name, token,
expiration, and client address.

The 'auth' script can be used to manage them.  Here are
examples of the commands::

   $ auth ls
   $ auth set <i>user</i>
   $ auth check <i>user</i>
   $ auth delete <i>user</i>

All of the commands print out the locations of the
password file and the sessions file.

 * The 'ls' command simply lists the user names

 * The 'set' command prompts for a (new) password, and sets
   the password for the user.  It also deletes any active session that
   the user may have.

 * The 'check' command prompts for a password and indicates
   whether or not it is correct.

 * The 'delete' command deletes a user from both the password
   and sessions files.

