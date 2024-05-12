
.. automodule:: selkie.cld.app.toplevel

Server top level — ``selkie.cld.app.toplevel``
==============================================

This chapter describes the module ``selkie.cld.app.toplevel``.  The
major classes are Manager and RuntimeContext.  The Manager provides a
command-line interface and may be specialized for particular
applications.  In particular, CLD provides a specialization,
CLDManager, which is discussed in the CLD section of the documentation.

Manager
-------

Introduction
............

The Manager provides a command-line executable for a given
application.
It can be used to run the application in a variety of configurations, or to
manage the application file, configuration files, and so on.

The class Manager can be used to invoke an application by providing
the application function as the keyword argument ``app``.  For
example, encyd is invoked as::

   mgr = Manager(app=EncyApp, log_file=log_file, server_port=port)
   mgr.run()

Alternatively, Manager may be specialized, adding ``app`` to its
__defaults__ table.  For example, the beginning of the class
definition for CLDManager is::

   class CLDManager (Manager):
       __defaults__ = dict(Manager.__defaults__, 
                           app = CLD,
                           media_dir = None)

Command-line processing is provided by class methods.  For example,
CLD is run simply by calling the class method __main__ of CLDManager.
That is, the selkie.script.cld executable module consists essentially of just the
following::

   CLDManager.__main__(sys.argv)

The class members of Manager are:

 * ``__defaults__`` —
   A dict containing configuration defaults.  The
   value of 'app' (if present) is the application function.

 * ``__usage__`` —
   A command-line usage string.

 * ``__commands__`` —
   A table mapping command names to triples
   (*commandcls, method, syntax*).

 * ``__flags__`` —
   A dict mapping flags (strings, including the hyphens)
   to tuples containing keyword arguments or key-value pairs.

The class methods of Manager are:

 * __parse__(argv)
   Takes a command line and parses it into a
   triple (command, args, kwargs), where *command* is a
   Command instance.

 * __main__(argv)
   It calls __parse__(argv) to get (command, args, kwargs),
   and then it calls command(\*args, \*\*kwargs).

The __parse__ method instantiates Manager (or whichever subclass of
Manager is used to invoke it).  The Manager instance contains
a **subject** and a **config dict**.  The Manager instance is
then packaged into a Command instance, along with the method name to
be invoked.  When the Command instance is called, it dispatches to the
specified method.

The next sections describe command-line parsing (and what is meant by
a "subject"), Manager instances, and Command instances.

Command-line processing
.......................

The __main__ method simply passes its argument to the __parse__ method,
which takes a single argument: a command line.  The command line
should be in the format of sys.argv, namely,
a list of words, the first of which is the name of
the executable.

The Manager distinguishes three syntactic types of words:

 * A word that begins with '-' and contains at least one
   more character is defined to be a **flag**.

 * Otherwise, a word that contains an '=' is defined to be
   a **key-value pair**.

 * Otherwise, the word is a **regular word**.

Key-value pairs are converted to pairs of strings (key and value).
Flags are also converted to key-value pairs, by looking up the flag in
the __flags__ table.  The value is a list of key-value pairs, which
replaces the flag.  The last element in the list may be just a key
rather than a pair, in which case the next word in the command line
provides the value, regardless of its syntactic type.

A command line has the following pattern::

   *executable* [*subject*] *kvpair*\* [*command*] [*arg*|*kvpair*]\*

The first word is always the executable.
If the next word is a regular word and it contains a period, it is
taken to be a file name, which is called the *subject* of the
command.  When there is a subject, the command is conceptually like a
method of the subject.

After the subject, any
key-value pairs are recognized syntactically and preprocessed into
Python pairs.  These are then converted to a dict representing
**config settings**.

If a regular word remains, it is taken to be the command name;
otherwise the default command 'run' is supplied.  All
following words become arguments to the command, and they are
processed according to the command's **syntax string**, as
follows.

The command is looked up in __commands__ to obtain a
triple (*command_class, method, syntax*).
The syntax string controls the processing of the remaining words on
the command line, and it helps determine which are positional arguments and which are
keyword arguments.  It uses the following symbols:

 * ``!`` — An obligatory argument.  If there are no remaining words,
    or if the next word is not a regular 
    word, an error is signalled.

 * ``?`` — An optional argument.  If the next
    word is a regular word, it is used, otherwise the value is
    None.

 * ``=`` — A list of key-value pairs.  As long as the
    next argument is either a flag or key-value pair, it is
    preprocessed and added to
    the list.  (Unlike a dict, a list preserves the original order,
    and it may contain multiple pairs with the same key.)

 * ``@`` A dict of keyword arguments.
    A list of key-value pairs is collected as for '=', but
    instead of being added to the list of positional arguments, they
    are converted to a dict to be used as
    keyword arguments.

 * ``*`` A list of arguments.  All remaining
    words, regardless of
    type, are added to the list of positional arguments.

For example, let us suppose that the command 'foo' has the
following entry in the __commands__ table::

   (FooCommand, 'show', '!=?@')

and consider the following hypothetical command line::

   cld corpus.cld logging=all foo / x=10 y=20 leo bar=yes

This is parsed into:

 * Executable: 'cld'
 * Subject: 'corpus.cld'
 * Config settings: {'logging': 'all'}
 * Command name: 'foo'
 * Command class: FooCommand (from the __commands__ entry)
 * Method name: 'show' (from the __commands__ entry)
 * Args: ['/', [('x', '10'), ('y', '20')], 'leo']
 * KWArgs: {'bar': 'yes'}

Note that the kvpairs ``x=10 y=20`` are processed into a list
that is included among the positional arguments, whereas the
kvpair ``bar=yes`` becomes an entry in the keyword-argument
dict.

After the command line has been thus parsed, the information is
packaged up.  A Manager instance is created from
the subject and config settings, and it is then
combined with the method name to construct an instance of the
command class.  The return value from
__parse__ is a triple consisting of command instance, args, and
kwargs.  (The executable and command name serve no further purpose and
are discarded.)

Schematically::

   mgr = manager_class(subject, **settings)
   cmd = command_class(mgr, method_name)
   return (cmd, args, kwargs)

The config dict
...............

There are several sources of configuration settings.

   * **Manager class defaults.**
     The class member 'Manager.__defaults__' contains default
     settings.

   * **Subclass defaults.**
     Subclasses of Manager (e.g., CLDManager) may override the value
     of 'Manager.__defaults__.'

   * **Manager instance from command line.**
     A Manager instance may be created from a command line, as
     described in the previous section.  A fresh configuration
     dict is created, initially as a copy of the subclass defaults.
     Then:

       * **Config file.**
         If there is a subject, its config file is determined
         using the manager's __configfile__ method.  
         The implementation provided by
         Manager returns the subject itself, if it ends with '.cfg','
         and otherwise the subject joined with '_config'.'  Subclasses
         of Manager may override __configfile__ with an application-specific
         procedure.
         If the config file
         exists, its contents are added to the manager's configuration dict.

       * **Command-line settings.**
         The keyword arguments passed to Manager.__init__ are added after the
         contents of the config file.

       * **Postprocessing.**
         After config file and command-line settings have been
         processed, the keys
         'config_file' and 'application_file' are set.  (An error is
         signalled if they are set in the defaults, the config file, or
         on the command line.)  Then values are standardized.
         If a key
         ends in '_file' or '_dir', the value is converted to an
         absolute pathname.  If a key is 'port' or ends
         in '_port' or '_num', the value is converted to an int.  If a
         key ends in '_on', the value is converted to a boolean.

   * **Cloned manager instance.**
     A Manager instance may be cloned by calling it.  A fresh copy of
     __config__ is created, and updated with any settings passed to
     the call.  Values are standardized.

   * **Command instance.**
     When a Command instance is created, a fresh copy of the
     manager's __config__ dict is created.  This prevents any
     cross-talk between command instances.

   * **RuntimeContext settings.**
     As discussed below, if the Command is a RuntimeCommand, the command constructor
     (destructively) sets the values of the keys 'execmode',
     'server_type', 'client_type', and possibly
     'log' and 'server'.  This modification is
     destructive on the assumption that Command instances are
     never re-used.

   * **Request instance.**



Calling commands within Python
..............................

Recall that the pieces of information that are extracted from the
command line and packaged in a Command are: 'settings,'
'subject,' 'command_class,' and 'method_name.'
The subject and settings are first combined to create a Manager, and then the
manager is combined with the method name when instantiating the command
class.

Accordingly, one may do the following directly::

   mgr = manager_class(subject, **settings)
   cmd = command_class(mgr, method_name)

For further convenience, the Manager __getattr__ method recognizes any
command name as a member whose value is obtained
as <code>command_class(self, method_name)</code>, the command class
and method name being obtained from the __commands__ table.

Thus, for example, one may do the following::

   >>> from selkie.cld.toplevel import CLDManager
   >>> mgr = CLDManager('foo.cld', logging=False)
   >>> mgr.create_test()

As one can confirm, the value of 'mgr.create_test' is a
Command::

   >>> mgr.create_test
   <CorpusCommand create_test>


Commands
........

As we have seen, Command instances are created either by calling
the class method __parse__ or by accessing an instance member whose
name is a command name.  A Manager instance and method name are passed
to the constructor.  In that way, the command instance can be subsequently
executed simply by calling it as a function.

Command classes are specializations of 'Command.'
The __init__ method takes a manager and method name.  The instance has
the following members::

 * 'manager' — A backpointer to the Manager.

 * 'method_name' — The method name (a string).

 * 'function' — The bound method itself.  Hence the method
   name is actually only used for display.

 * 'subject' — Identical to manager.__subject__.

 * 'config' — A copy of manager.__config__.  A copy is made
   because the config dict might be modified when the command runs.  It
   is possible for multiple commands to be created from the same
   manager instance, so each requires its own copy of the config dict.

Specializations of Manager may extend the command table to introduce
new command classes.
The generic Manager __commands__ table provides the following commands.

 * 'RuntimeCommand': run, serve, cgi, call, direct, open

 * 'UsageCommand': print_usage

 * 'AuthenticationCommand': get_auth, ls, set, check, delete

 * 'CGICommand': create

 * 'ConfigCommand': print_config, set, unset


Runtime Commands
----------------

The RuntimeCommand class implements the commands
*run*, *serve*, *cgi*, *call*, *direct*, and *open*.
It passes off all the actual work to RuntimeContext.

Invoking the application
........................

As previously discussed, from the perspective of the Server Framework,
an application is simply a function that takes a Request and returns a
Response.  There are, however, multiple ways in which an application
may be invoked.  Briefly:

 * **run** - As a desktop application run from the command line, using the
   internal web server of selkie.cld.app.server and using an external web
   browser as UI.

 * **serve** - As a web service, using the internal web server and accessed from
   an external web browser.  The differences between invocation as a
   web service and as a desktop application are discussed in the next section.

 * **call** - Running the application using the internal web server, but
   calling it from software using the internal web
   client of selkie.cld.app.client.  This permits
   automated regression testing.  The application may run either in
   web-service mode or desktop mode.

 * **cgi** - Running the web service as a WSGI or CGI script under a
   third-party web server such as Apache.

 * **direct** - Calling the application directly, without the intermediation of
   server and client.  This may be useful in debugging issues in the
   server framework itself.

The class RuntimeContext represents a configurable
invocation pipeline that covers all of these cases.

In the cases where there is no external web browser,
the class RTFunction can be used to convert a
RuntimeContext to a simple function that takes **request strings** 
as input and prints out the response.  A request string consists
essentially of the pathname and query portions of a URL.

Execmode
........

The choice of web service versus desktop application is called
the **execmode.**  The strings 'desktop' and 'webservice'
represent the two legal values for execmode.  The differences between the
modes are as follows:

 * Desktop mode is a single-user mode.  Authentication is disabled,
   and the invoking user has unlimited permissions.
   By contrast, webservice mode is multi-user, and all requests must
   be authenticated.

 * In desktop mode, the server and browser must run on the same
   machine.  Webservice mode permits remote clients.

 * Only webservice mode is possible when using a third-party
   server.

 * The default log file is '-' (stdout) in desktop mode,
   but '/dev/null' in webservice mode.

 * Changing to a different application file is allowed only in desktop
   mode.


Runtime commands
................

Several different ways of invoking the application were introduced in the
section 'Invoking the application.'  The differences can be boiled down to three
choices:

 * The execmode.

 * Whether one uses the internal server of selkie.cld.app.server; an
   external, third-party web server; or no server at all.

 * Whether one uses the internal client of selkie.cld.app.client; an
   external web browser; or no client at all.

In principle, then, there are 2 x 3 x 3 = 18 different combinations.
However, there are constraints that rule out many of them:

 * If the server is external, the client must be external as well.

 * If the server is internal, the client may be external or internal,
   but we do require there to be a client.

 * If there is no server, there is no need for a client.

 * Desktop mode is not available if there is an external server.

Let us write 'X', 'I', or 'N' for external, internal, or neither, and
let us write first the choice for server and then the choice for
client.  The first three constraints can be restated as permitting
only four combinations: XX, IX, II, NN.

Let us prefix 'D' for desktop mode, 'W' for webservice mode, and '\*'
for either.  Then the four combinations become 'WXX', '\*IX', '\*II',
and '\*NN'.

In these terms, the five configurations listed in the section
'Invoking the application' correspond
to the **runtime commands,** which are methods of the class
RuntimeCommand.  They are:

 * run (DIX) — Desktop application run from the command line

 * serve (WIX) — Web service provided using the internal server

 * call (\*II) — Calling the application from software, e.g. for regression testing

 * cgi (WXX') — Running the application as a WSGI or CGI script

 * direct (\*NN) — Calling the application directly, without using server or
   client.

For testing from software, one has two options: a *direct* call
that passes the request string directly to the application function,
and an (indirect) *call* in which the request string is passed to
the Client, which generates an HTTP request, which is digested by the
Server into the form of a CGI environment dict, which is passed to the
application function.

In both cases, the Request constructor calls the
function *digest_environ* (selkie.cld.app.env) to create its internal
representation of the request, but the way that *digest_environ*
digests a string is not identical to the processing that the original
string goes through in the path from client to server to CGI
environment dict.

RuntimeContext
..............

The methods that implement the runtime commands each instantiate a
RuntimeContext, passing in the config dict.
The RuntimeContext constructor determines the execmode, server type, and
client type, and uses that information to decide which of the
following components to create.  These are members of the
RuntimeContext instance.

 * 'log' - created as 'logger_from_config(config)' (selkie.cld.app.log)

 * 'server' - created as 'Server(config)' (selkie.cld.app.server2)

 * 'client' - created as 'Client(addr)' (selkie.cld.app.client)

 * 'wsgi' - created as 'WsgiApp(config)' (selkie.cld.app.wsgi)

Examples
........

[*Note: the code examples no longer work; the interfaces have changed.*]

First, one creates a Manager, passing the app (that is, the
application function) to it.  Here is a trivial "hello world" app::

   >>> from selkie.cld.app.response import Response
   >>> def hello (req):
   ...     return Response('Hello, world!\n', code=200, content_type='txt')
   ...

One may create a Manager by doing::

   >>> from selkie.cld.app.toplevel import Manager
   >>> mgr = Manager(hello)

For CLD, there is a specialization CLDManager that automatically sets
the app to be cld_app.

The primary purpose of the Manager is to provide implementation for
the CLD command line.  It parses a CLD command line into a Command
object.  It determines which specialization of Command to use, and
instantiates it with a configuration spec, the name of the method that
implements the command, and args and keyword args for the method.  For example::

   >>> com = mgr.parse_argv('hello call /foo/bar'.split())
   >>> com
   <RuntimeCommand call call ['/foo/bar'] {}>

Here the specialization is RuntimeCommand, the command name and method
name are both 'call', the args are ['/foo/bar'], and the kwargs are
the empty dict.
The configuration spec is not shown in the string representation, but
in this case it is the empty list.  The spec is converted to a Config
object by calling the Manager's *parse_config* method.  That
occurs when the Command is instantiated::

   >>> config = mgr.parse_config([])

The command can then be executed by calling the Command instance as a function.
The __call__ method finds the named method (in our example, 'call') and applies it to
the given args and kwargs.

The RuntimeCommand method 'call' takes one or more request specifications.  In our case,
'/foo/bar' is the only request specification::

   >>> com.call('/foo/bar')
   Hello, world!

The 'call()' method does not actually return a value; rather it
sends the request to an internal web server and prints out the
response.  (If there are multiple requests, it sends each in turn.)

Let us walk through the individual steps that the 'call()'
method goes through.  To be precise, the steps we will go through are
done partially by *call*, partially by a RuntimeContext
that *call* creates, and partially by an RTFunction that
*call* creates.

First, we need to add some settings to the Config.  (For this reason,
it is essential that the Config be created solely for this call.  That
is necessary not only to avoid contamination across calls, but also to
make calls be thread-safe.)
The value for 'execmode' needs to be set (assuming it was not already
specified by the user), and the values for
'server_type' and 'client_type' are set to 'internal'::

   >>> config.set('execmode', 'webservice', 'manual')
   >>> config.set('server_type', 'internal', 'manual')
   >>> config.set('client_type', 'internal', 'manual')

The third argument is the provenance; this makes it easier to debug
configuration issues.  The server type and client type are mostly
informational, but we have included them for completeness::

   >>> print(config)
   Config:
       app: <function hello at 0x...> [default]
       application_file: None [default]
       auth_dir: None [default]
       cgi_file: None [default]
       client_type: 'internal' [manual]
       config_file: None [default]
       debug_on: False [default]
       desktop_log_file: '-' [default]
       desktop_logging: 'all' [default]
       desktop_user: '_root_' [default]
       execmode: 'webservice' [manual]
       log_file: None [default]
       logging: None [default]
       loopback_testing_on: False [default]
       rootprefix: ' [default]
       server_authentication_on: False [default]
       server_port: 8000 [default]
       server_type: 'internal' [manual]
       webservice_log_file: 'log' [default]
       webservice_logging: 'req,auth,traceback' [default]

The next step is to create a Logger, using the function 'logger_from_config().'
If 'log_file' does not already have a value in Config, it is
set to '/dev/null' for a web service, and '-' for
desktop mode::

   >>> config.set('log_file', '/dev/null', 'manual')
   >>> log = config.make_logger()

The pieces that we have created so far are packaged into a Resources
object::

   >>> from selkie.cld.app.resources import Resources
   >>> resources = Resources(hello, config, log)

Next we create the Server.  It uses the WSGI protocol to interact with
the app, so we also need to wrap our app in a WsgiApp instance.  More
precisely, we pass the entire set of resources to the WsgiApp constructor::

   >>> from selkie.cld.app.wsgi import WsgiApp
   >>> wsgi = WsgiApp(resources)
   >>> from selkie.cld.app.server import Server
   >>> server = Server(wsgi)

Finally, we create the Client.  This permits us to issues HTTP
requests from Python, rather than going to a web browser::

   >>> from selkie.cld.app.client import Client
   >>> addr = ('localhost', config['server_port'])
   >>> client = Client(addr)

Note that the server address is provided to the Client in the form
(*host*, *port*).

Using the pipeline
..................

At this point we have created the complete pipeline, just as
the 'call()' method would do it.  We are now ready to pass a
request through the pipeline.

The client accepts two kinds of request.  A **simple request** is just a
pathname, represented as a string.  The client constructs a GET
request from it.  A **complex request** is distinguished by
containing colons, separating the string into a pathname, form
information, and cookie information.  The client sends a complex
request as an HTTP POST request.  See <a href="app_toplevel.html">Ch 8</a>
for more details.

One can call the client simply as a function.  However, the server
needs to be running at the time.  The easiest way to accomplish that
is to put the server in a "with" statement::

   >>> with server:
   ...     resp = client('/foo/bar')
   ...
   >>> resp
   <HTTPResponse 200 text/plain>
   >>> resp.string()
   'Hello, world!\n'

There are several further steps hidden in the call to the client.
First, the client constructs an HTTP request (either a GET or a POST,
depending on its input) and sends it to the server.  The server
receives it, digests it into WSGI format, and passes it as input to
the WsgiApp.  In accordance with the WSGI protocol, the WsgiApp
receives two arguments: the **CGI environment** and a
**send function** that is used by the WsgiApp to send HTTP response
headers.

We may create a CGI environment for testing purposes by calling the
function 'make_environ()'::

   >>> from selkie.cld.app.env import make_environ
   >>> env = make_environ(path='/foo/bar')
   >>> type(env)
   <class 'dict'>
   >>> sorted(env.keys())
   ['HTTPS', 'PATH_INFO', 'QUERY_STRING', 'REQUEST_METHOD', 'SCRIPT_NAME', 'USER']
   >>> env['PATH_INFO']
   '/foo/bar'

The WsgiApp creates a Request instance from the environ::

   >>> from selkie.cld.app.request import Request
   >>> req = Request(env, resources)
   >>> req
   <Request 'foo' 'bar'>

The Request is then passed to the Seal application function::

   >>> resp = hello(req)
   >>> resp
   <Response 200 text/plain;utf-8 14 bytes>

The Request instance is not automatically authenticated.  Calling
its *authenticate* method creates an Authenticator and stores it
in the request's *authenticator* member.  Our example application
function does not do authentication.

The application function returns a Response, which
the WsgiApp returns to the server in accordance with the WSGI
protocol.  Namely, it passes the status and headers to the send
function, and it returns the body as a bytes object::

   >>> resp.http_status()
   '200 OK'
   >>> resp.http_headers()
   [('Content-Type', 'text/plain;charset=utf-8'), ('Content-Length', '14')]
   >>> resp.body()
   [b'Hello, world!\n']

The server constructs an HTTP response from those pieces and sends it
to the client.  The client reads the HTTP response and packages it up
as an HttpResponse object.

Other Command classes
---------------------

Configuration-file management
.............................

Manager provides three additional commands.
The *print_config* method (command 'config') prints
out a configuration file.  If the first argument ends
with '.cfg', it is taken to be a configuration file and its
contents are printed out.  Otherwise, the first argument, *fn,* is assumed to
name an application file, and the config file is taken to be *fn*/_config.

The 'set()' method takes key-value pairs and sets values for keys in the
configuration file accordingly.

The 'unset()' method takes keys and unsets them in the
configuration file.

CGI scripts
...........

When using an external server, there is one additional piece, namely,
the CGI script that mediates between the server and WsgiApp.
It is created by a CGIManager, which can be obtained using the Manager
method get_cgi.  I use CLDManager for illustration, since
it has a built-in application function::

   >>> from selkie.cld.toplevel import CLDManager
   >>> mgr = CLDManager('/my/corpus.cld')

The 'create_cgi' command can be used to create the CGI
script.  As arguments, it takes a
filename for the CGI script, and optionally takes keyword arguments
that are included in the cgi call inside the script::

   >>> mgr('create_cgi', '/tmp/cgi', logging='all')

Writing /tmp/cgi::

   >>> from selkie.cld.seal.sh import cat, chmod, rm
   >>> cat('/tmp/cgi')
   #!/Users/abney/anaconda3/bin/python
   
   import site
   site.addsitedir('/Users/abney/git/hub/selkie/src')
   
   from selkie.cld.toplevel import CLDManager
   mgr = CLDManager('/my/corpus.cld',
           debug_on=False,
           log_file='.../log',
           logging='all',
           loopback_testing_on=False,
           server_authentication_on=False)
   mgr.cgi()
   >>> chmod('/tmp/cgi', '+w')
   >>> rm('/tmp/cgi')

