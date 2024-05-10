
Framework Overview
******************

Writing a Seal application
--------------------------

App and request handler
.......................

In order to inherit a variety of functionality, it is useful to define
an application function as a class that is instantiated.  One may
then customize it by overriding methods.  This approach is most useful
if we may also store information inside the application instance while
processing a request.

However, we must take care in a multi-threaded environment.  In
particular, the Python web server may handle multiple simultaneous
requests, and each of those requests is handled in a separate thread.
If a Seal application function stores any internal state,
**there must be one application instance per request.**

This creates a quandary: we pass a single Seal application function to
the server, but we need separate instances for each request.
Our solution is to distinguish between a SealApp and a
SealRequestHandler.  There is a single instance of SealApp, held by
the web server (wrapped in a WsgiApp).  When the SealApp is called on
a request, it immediately creates a SealRequestHandler that is
dedicated to that single request, and it calls the request handler.  In
short, SealApp is a very simple shell; all the real work is done by
the request handler.  The request handler receives the request
as an argument of __init__, and its __call__ method takes no
arguments.  It will not be called multiple times; it is discarded
after one call.

One defines a new application by specializing SealRequestHandler.
The application function is then created by doing::

   my_app_function = SealApp(MyRequestHandler)

The resulting function *my_app_function* is thread-safe.  Each time it is called on a
request, it calls MyRequestHandler(request)() and returns
the result.

Specialization
..............

Each time a Seal request handler is instantiated, it calls three methods:

 * **make_root:** returns the root web directory.

 * **open_file:** instantiates the application file, represented in memory by a Database object.

 * **make_context:** instantiates a Context object that is wrapped around each
   request and provides global resources as one descends through the web
   hierarchy.

Specializations of SealRequestHandler may override the first two methods to provide
the UI and disk portions, respectively, of the application content.

To define a new application, one minimally needs to define a root
web directory.  To assist in doing so,
the classes HtmlDirectory and Page are provided, along with a number
of specializations.  The Seal request handler does not specifically require that
one use them, but they do assure that the request handler's expectations are met,
namely:

 * A **web directory** must have a __getitem__() method that
   takes a string and returns either another web directory or a web page.

 * A **web page** must have:
    
     * A member response_code whose value is an int representing
       an HTTP response code: 200 for a regular page, 303 for a
       redirection, etc.

     * A member content_type whose value is either a pair of strings
       (mime-type, encoding) or a common filename suffix, such
       as 'html', 'txt', 'css', 'js', 'mp3',
       etc.  (Exception: content_type is not required
       if response_code is 303.)

     * A member uri, if response_code is 303.

     * A method __iter__() that returns an iteration over
       a mixture of strings and byte-like objects.  (Strings are not allowed
       if encoding is None.)

One may write an application by specializing SealRequestHandler and overriding (some
of) the methods that are called during set-up, namely:

 * make_context(*request*):
   the return value must be a specialization of Context.

 * open_file(*filename, context*):
   opens the application file.  No constraints are placed on the application file.

 * make_root(*rootpfx, file, context*):
   to instantiate the root web directory.
   The member *context*.root is set to the return value.

Alternatively, one may provide classes for the root web directory,
application file, and context, by setting the following keys in the
config file, or by providing them as keywords to the App constructor:

 * 'rootclass': the class for the web root directory

 * 'fileclass': the class for the application file, or:

 * 'file': the pre-instantiated application file

No facility is provided for specializing Context, apart from
overriding the make_context method.

Initialization
--------------

**OUT OF DATE FROM THIS POINT ON**

The App's __init__ method takes
arguments *mode* and *settings,* and any number of keyword
arguments.  The members of App are set as follows:

 * execmode is set to *mode.*

 * config is set to a new Config instance.
   The *settings* and keyword arguments are passed to
   the Config constructor.
   (See the section on Config
   below.)
   Then config['app'] is set to the
   App itself.

 * filename is set to the absolute pathname of config['application_filename'].

 * server_dir is set to the absolute pathname of config['server_dir'].

 * server_type is set to config['server_type'].

 * server_port is set to config['server_port'],
   converted to an int.

 * log is set to a newly created Logger.  If
   the execmode is a desktop mode, the log file is stdout.
   Otherwise, the log file is the absolute pathname
   of config['logfile'], interpreted relative to the server_dir.
   The logging conditions are taken
   from config['logging'], split at whitespace.

 * wsgi is set to a newly created WsgiApp.

 * auth_dir is set to the absolute pathname
   of config['auth_dir'], if specified, and otherwise it
   is set equal to server_dir.

 * authenticator is set to a newly created Authenticator,
   unless auth_dir is None, in which
   case authenticator is also None.

 * server is set to None.  It will be set by
   the run method if the App is run
   as a desktop application.

Then run is called.  If execmode is 'cgi',
a CGIHandler is created and run, directing callbacks to wsgi.
If execmode is 'run' or 'call', a Server is
created and stored as server, with callbacks directed to the
App.  The server's run
or call method, respectively, is then invoked.

Running
-------

Exactly what "running"
means depends on the **execution mode,** as discussed in the
following sections.

Internal and external servers
.............................

The App is designed to run in the context of two different kinds of
server.  An **internal server** is a python web server that is
launched by the App and run in a separate thread.  When using the App
as a stand-alone application, it is natural to use an internal server.
An **external server** is a standard web server, such as Apache.
When using an external server, the App runs in a CGI or WSGI script.

When run with an external server, a fresh instance of App is created
for every request.  When run with an internal server, a single App
instance handles all requests.  However, as already mentioned, an App
instance behaves as a stateless function; this guarantees that the
behavior is identical whether a single App instance is re-used or a
new one is created for each request.

There is one caveat.  The App class does have certain configuration
parameters.  Multiple instances of App behave identically *if they
are configured in the same way*.  With an external server, the
configuration parameters are usually read from a static file, assuring
that all instances of the App are configured identically.

Running as application
......................

The only required argument for the App constructor is *mode*.
It determines the manner in which the application executes.  There
are two modes for running as a desktop application ('run'
and 'call') and two for running as a web service ('cgi'
and 'wsgi').

When running as an application, the App's __init__ method
ends by launching an
internal web server that calls back to the App to handle requests.  For example,
the module seal.script.encyd ends with::

   EncyApp('run', sys.argv[1:], server_port='8004')

The server runs in a subordinate thread.  To stop it, one may call the
Server's quit method, or one may use control-C at the terminal.

The internal web server is an instance of class Server.
The mode determines which method of the server is
invoked: run or call.
The only difference between them is that
run calls sys.exit when it completes,
but call does not.

When running as an application, logging by default goes to stdout,
whereas when running as a web service, logging by default goes to
a log file.

Running as a CGI script
.......................

There are two modes for running as a web service, 'cgi'
and 'wsgi'.  The choice depends on
whether the service is invoked in a CGI script or in a WSGI script.

In 'cgi' mode,
the App's __init__ method ends by launching a generic CGI script
engine (CGIHandler from wsgiref.handlers) that reads the request from
the execution environment, calls back to the App instance to
process the request, and prints the response in the form that a CGI
script expects.

For example, the following is a possible CGI script for CLD::

   #!/Users/abney/anaconda/bin/python
   
   import site
   site.addsitedir('/Users/abney/git/seal/python')
   
   from seal.cld.app import CLDApp
   CLDApp('run', '/Users/abney/git/cld/corpus.cld')

To test how the application behaves in a CGI context
without actually placing it in the
cgi-bin directory of a running web server, one can use the function cgi_call
to emulate a web server.  It sets up os.environ to reflect the
environment in which a CGI script runs, uses cgi_run
to run the application, captures the output and returns it as a byte
sequence.  For example::

   >>> from seal.app import cgi_call
   >>> url = 'http://localhost:8000/bar/foo.10'
   >>> bs = cgi_call(TestDirectory(), url)
   >>> print(bs.decode('ascii'))
   Status: 200 OK
   ...

Running as a WSGI script
........................

The 'wsgi' mode is the only one that simply initializes the
App without launching an engine that calls back to it.
In this
case, the App creates a WsgiApp in its wsgi member.  The
WsgiApp is not executed, but it will eventually be executed by the web
server.  The WsgiApp will accept a call from the web server in the
form specified by the WSGI protocol,
convert it to a request, pass it to the App, receive
a Page from the App, and convert it to a WSGI-compliant response.

For example, the following is a possible WSGI script for CLD::

   #!/Users/abney/anaconda/bin/python
   
   import site
   site.addsitedir('/Users/abney/git/seal/python')
   
   from seal.cld.app import CLDApp
   application = CLDApp('wsgi', '/Users/abney/git/cld/corpus.cld').wsgi

