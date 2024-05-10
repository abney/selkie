
Configuration and Logging
*************************

This chapter documents the module selkie.cld.app.config.

Environment
-----------

Create config
.............

The environment dict contains configuration settings that can be used
to adapt the various components of the application framework.  An
application may define its own configuration keywords as well.

The function **create_config()** creates an environment dict.
It takes the following arguments:

 * app - the application function.

 * filename - the filename of a configuration file to load.

 * items - command-line settings to add to the
   environment.  They override settings in the configuration file (if provided).

 * defaults - additional (key, value) pairs that are added
   only if they are not set from the configuration file or command line.

Some of the keywords have special handling.

 * The value of 'config_file' is set from
   the filename argument passed to create_config.  This
   overrides any setting in the config file itself or the command line.

 * If 'log' is provided, the value should be a Logger.  If it is not
   provided, a Logger will be created and stored under 'log'.

 * The key 'server' is initialized to None.
   The server is generally created later and stored under 'server'.

 * The value of any key ending in '_file' or '_dir'
   is turned into an absolute path.

 * The value of 'port' or
   of any key ending in '_port' or '_num' is turned
   into an int.

 * The value of any key ending in '_on' is turned into a boolean.

An example (OUT OF DATE)::

   >>> from selkie.cld.app.config import create_config
   >>> from selkie.cld.app.server2 import EchoApp
   >>> cfg = create_config(app=EchoApp)

.. _configuration_keys:

Configuration keys
..................

The following keys are set or used by the components of the
application framework.
The code following the key indicates which component uses the key.  The values
are: A = the application, assuming it specializes SealApp,
C = finding the config file,
L = Logger,
S = Server,
M = the manager,
U = Authenticator, only in webserver mode,
W = constructing an environ for the WsgiApp; only used by com_wsgi.

 * application_file (A) — The pathname
   of the database.  Default: None.

 * auth_dir (U) — Where authentication
   files reside.  Default: 'auth'.

 * cert_file (S) — The filename of the SSL
   certificate file.

 * cgi_file (T) — Default value for the
   CGI script filename

 * client_type (T) — 'external', 'internal', or None

 * config_file (C) — The pathname of the
   config file.  Cannot be set within the configuration file, only on
   the command line.  Defaults to /_config under
   application_file, if defined, otherwise None.

 * debug_on (A) — Whether the /.debug path is enabled.
   Default: False.

 * desktop_user (A) — The Authenticator
   uses this as the user name when running in desktop mode.

 * execmode (T) — Either 'desktop'
   or 'webserver'.

 * log_file (L) — Filename.  In desktop
   mode it defaults to '-' (stdout), and in webserver mode it
   defaults to '/dev/null'.

 * logging (L) — Comma-separated list of
   logging conditions.  Default: 'all'.

 * loopback_testing_on (A) — If true and the client address is indeed 127.0.0.1, then the
   Authenticator will not insist on HTTPS.  Default: False.

 * media_dir (A) — Pathname of media directory.  Default: 'media'.

 * rootprefix (W) — Used only when the toplevel call is the testing function com_wsgi.
   In all other cases, the root prefix is provided in the
   environment set up by the server or CGI handler.

 * server_authentication_on (U) —
   Whether the server handles authentication.  If True, we will
   trust the username obtained from the CGI environment.

 * server_host (S) — The hostname that the
   server should use.

 * server_port (S) — Default 8000.
   This specifies which port the internal Server should use;
   the application is accessible at http://localhost:*server_port*/.
   Has no effect if running under an external server such as Apache.

 * server_type (T) — 'external', 'internal', or None

Logging
-------

Logger
......

A Logger provides logging services.
Its __init__ method takes a log file name and a list
of **conditions,** either in the form of a list or tuple of
strings, or a single string containing comma-separated words.
The function create_config() takes the log file name and log
conditions from the settings for
'log_file' and 'logging'.

The Logger is callable, which makes it appear to be a method of
any object that has a Logger as the value of member log.

The Logger manages a log file, which may
either be a file on disk or stdout.  Calling the Logger as a function
prints a message to the log file.

Log messages are printed conditionally.  In the above
example, 'path' is the logging condition: the message
is only printed if the logging condition 'path' is enabled.
The configuration setting logging allows one to specify which
logging conditions are enabled.  By default, all logging conditions are enabled.

Logging conditions
..................

The logging conditions that can be used in the value of logging
are as follows:

 * auth — Authentication messages
 * server — Server messages
 * error — Error information
 * traceback — Include traceback, implies error
 * req — Print out requests
 * path — Add pathname info, implies req
 * trace — Add trace detail, implies path
 * disk — Information about changes on disk
 * all — Everything is printed.

Logging conditions are organized hierarchically, such that enabling a
condition automatically enables all of its descendants.  The hierarchy
is as follows:

 * all

     * auth

     * disk

     * server

     * trace

         * path

             * req

     * traceback

         * error

