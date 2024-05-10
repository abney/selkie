
Server and Client
*****************

Overview
--------

The Seal web server is essentially a controller for a ServerDaemon
instance, which is a specialization of the standard
ThreadingHTTPServer (from the standard server module).  The
server daemon runs in a separate thread, so that it does not
monopolize the main thread.

When the server daemon receives an HTTP request, it starts a
thread for that request and instantiates an HTTPRequestHandler in the
new thread.  It is possible for the daemon to receive multiple
requests in rapid sequence, thus that multiple request-handler threads
run simultaneously.

The HTTP request handler is a specialization of the standard class
BaseHTTPRequestHandler (from the standard server module).
BaseHTTPRequestHandler has a large number of members and methods, so
to avoid any risk of adverse interactions, our specialization hands
off all the actual work to a separate class called ApplicationCaller.
The ApplicationCaller is instantiated with a back pointer to the HTTP
request handler, then its run() method is called.

User control of the server and application caller is via a
configuration dict, which is passed first to the Server, and thence to
the ServerDaemon.  The request handler is created within standard
library code, but the standard code provides it with a backlink to the
server daemon.  Hence the application caller's backlink to the handler
gives it indirect access to the server daemon, and thence to the
configuration dict.

The application caller creates a Request, fetches the application
function from the configuration dict, passes the request to the
application function and
receives a Response in return.  Then it renders the response in HTTP
format on the handler's output stream, which is connected to the
client.


Old Server
----------

The Server class is a wrapper for the "real" server, which is a
Python web server.  The web
server that is used combines WSGIServer (from module wsgiref.simple_server) with
ThreadingMixIn (from module socketserver).

The Server constructor takes a single argument, a WsgiApp.
It should be used in a with-statement.  The __enter__() method
calls start(), which runs _start_server()
in a separate thread.  The start() function waits, and does not return,
until the started flag has been set.

The _start_server() method instantiates the real server, sets
the started flag, and immediately calls the web
server's serve_forever() method.  In other words,
the start() method returns once the real-server thread has
started up and the real server has been created.

The Server's __exit__() method dispatches to stop(),
which calls the real server's shutdown() method to request
shutdown.  Then it waits for the stopped flag to be set
before returning.

When the real server shuts down, the subordinate thread
function _start_server() receives control again, and it sets
the stopped flag.  Then it returns, terminating the
subordinate thread.

Client
------

The Client class
................

The Client constructor takes a single argument, the server address,
which takes the form of a pair (host, port).  The instantiated client
behaves like a function.  Its __call__() method takes a
request and an optional follow_redirects
argument, which defaults to True.  The request is first normalized
using the function parse_request(),
then the method send_and_receive() is called to process the request.
If follow_redirects is True, then as long as the return value
from send_and_receive() is a redirect, it is used to issue a
new request to the server, until a non-redirect response is eventually
obtained.

A parsed request may be just a pathname, in which case an HTTP GET is
constructed and sent to the server, or it may be a 3-tuple of
pathname, form information, and cookie information, in which case an
HTTP POST is constructed and sent to the server.

String format for requests
..........................

There is a uniform string format for requests,
which parse_request() takes as input.
In the string format, a string containing no colons is a pathname, but
a string containing colons represents a complex request.
A complex request
contains either two or three fields separated by colons.  The first
field is the pathname, which obviously may not contain any colons.
The second field
is form information, and the third field (if present) contains cookie
information.

Form information and cookie information consist of
settings of the form "key=value" or just "key."  In the latter form,
where there is no equals sign, the empty string is supplied as value.  Multiple
settings are separated by commas.

A dict is constructed from the cookie settings.  A "multidict" is
constructed from the form information, meaning a dict in which each
key is associated with a *list* of values.  That is, a given key
may be repeated in the form settings, but keys cannot be repeated
among the cookie settings.  The values in a form dict are lists of
strings, and the values in a cookie dict are single strings.

To give the user additional flexibility, as an alternative to the
string format, a request may take the
form of a tuple containing two or three elements.  The first element
must be a string (the pathname).  The second and third elements should
be sequences of (key, value) pairs.

Here is an example of the behavior of parse_request()::

   >>> from seal.app.parse import parse_request
   >>> parse_request('/foo/bar')
   '/foo/bar'
   >>> parse_request('/foo/bar:x=10,y=20')
   ('/foo/bar', {'x': ['10'], 'y': ['20']}, {})
   >>> rs = '/foo.1/bar.2.4:x=10,*ss=hi,y=2,*ss=bye:user=abney,token=foo'
   >>> (pathname, form, cookie) = parse_request(rs)
   >>> pathname
   '/foo.1/bar.2.4'
   >>> form
   {'x': ['10'], '*ss': ['hi', 'bye'], 'y': ['2']}
   >>> cookie
   {'user': 'abney', 'token': 'foo'}
