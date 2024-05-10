
Python Servers
**************

Introduction
------------

The CLD application framework builds on the Python HTTP server.
This is a summary of the standard library code, to make it easier for
developers to understand the CLD server code.

The Python TCP server
---------------------

The Python TCP server (SocketServer.TCPServer)
handles the lowlevel connection to the client
(that is, to the browser).

Sockets
.......

The TCP server creates a **socket**, which is an endpoint for
communication.  It binds the socket to a **port**, and associates it
with a hostname.  (The empty string can be used for localhost.)
This initial socket is known as the **listening socket**.

When a client sends a TCP request to the port, the listening socket
accepts the connection, and spawns a new socket, called the
**connection socket**, that represents the connection to this
particular client.  The listening socket then continues listening for
new connections, while the connected socket processes the request from
the client.

The port remains bound until the listening socket and any connected
sockets are closed.  An attempt to create a new socket bound to the
same port will fail with an error.

TCP server
..........

A TCPServer is created with an address and a handler class.  The
address is a pair (*host, port*).  One can use the empty string for
localhost.  This becomes the initial value for the attribute
server_address; the attribute is updated after the socket is
bound.  Here is an example::

  server = TCPServer(('', 8000), TCPTestHandler)
  server.serve_forever()

(Instead of calling serve_forever(), one could call
server.handle_request() to process a single request.)

When the server's listening socket receives a connection, spawning a
connected socket, the server
instantiates the handler class, and the handler instance is wrapped
around the connected socket.  The handler class should be a
specialization of StreamRequestHandler.
In the above example, the handler class is TCPTestHandler.

A StreamRequestHandler has the following attributes:

 * request is the connection socket.

 * client_address is a (*host, port*) pair.

 * server is the TCPServer instance.  The server, in
   turn, has the attribute server_address, which is a
   (*host, port*) pair.

 * connection is set equal to request by
   StreamRequestHandler.setup().

 * rfile and wfile get set by
   StreamRequestHandler.setup().  These are streams that read from and
   write to the connection socket.

 * handle() is a no-op method that is intended to be overridden.

TCP test handler
................

The class seal.server.TCPTestHandler provides an
implementation of handle()
that prints out information about the handler, and generates a simple
HTTP response.  Point a browser at::

   http://localhost:8000/

The server should generate output that looks something like this::

   Client address: ('127.0.0.1', 51958)
   Server address: ('0.0.0.0', 8000)
   BEGIN REQUEST
   GET / HTTP/1.1
   Host: localhost:8000
   User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:11.0) Gecko/20100101 Firefox/11.0
   Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
   Accept-Language: en-us,en;q=0.5
   Accept-Encoding: gzip, deflate
   Connection: keep-alive
       
   END REQUEST

The test handler also sends an HTTP response (using the
utility function write_test_response()).
In the browser, you should see a web page containing the text "Hello, World!"

Start and stop
..............

The server method serve_forever() processes TCP requests forever.
If one calls it in the main thread, one must
press control-C to break the loop.  The utility function start()
calls it in a new thread, so that it can be stopped again more gracefully::

   >>> server = TCPServer(('', 8000), TCPTestHandler)
   >>> start(server)

This is essentially the definition of the function tcp_test(),
which creates and starts a TCP server using the TCP test handler::

   >>> server = tcp_test()

One can do manually what start() does, as follows::

   >>> from thread import start_new_thread
   >>> start_new_thread(server.serve_forever, ())
   -1341648896

The first argument to start_new_thread() is a function, and the
second is an argument list for it, which in this case is empty.  The
return value is the thread ID.

Once the server is running, we can send it a request by using a
browser.  Alternatively, we can issue a TCP request programmatically::

   >>> s = GET('http://localhost:8000/')
   Client address: ('127.0.0.1', 51952)
   Server address: ('0.0.0.0', 8000)
   BEGIN REQUEST
   GET / HTTP/1.0
   Host: localhost:8000
   User-Agent: Python-urllib/1.17
   
   END REQUEST

Note that the printing comes from the TCP test handler, not from
GET.  The string *s* contains the response from the test
handler::

    >>> print s,
    <html><head><title>Hello</title></head>
    <body>Hello, World!</body>
    </html>

The function GET() is merely a convenience.  One can do the
same thing manually like this::

   >>> from urllib import urlopen
   >>> s = urlopen('http://localhost:8000/').read()

To stop the server gracefully, and free the port, Seal provides the
utility function stop()::

   >>> stop(server)

It calls the method shutdown() to stop the server, and it calls
the method server_close() to cause the port to be released.
It may take a few seconds for the port to be freed.  After that, one
can create a new server.

Hypertext Transfer Protocol
---------------------------

Format of HTTP requests
.......................

In the above examples of the TCP test handler print-out, the "REQUEST"
portions represent HTTP requests.  For example::

   GET / HTTP/1.0
   Host: localhost:8000
   User-Agent: Python-urllib/1.17

An HTTP request consists of three parts:

 * The **request**, which is GET or POST followed by
   a pathname followed by an HTTP version.  In our example:
   "GET / HTTP/1.0."

 * The **mime headers** with various additional information.  They
   are terminated by an empty line.  In our example, there are two mime
   headers ("Host" and "User-Agent").

 * The **data**, which begins after the empty line.  The data
   section is empty for a GET request, but contains form
   information for a POST request.  In our example, the data
   section is empty.

GET requests
............

As we have just seen, one can issue a GET request by visiting::

   http://localhost:8000/

The URL may contain an arbitrary pathname - the request handler may
interpret it however it likes.
The HTTP request contains only mime headers, no data.

POST requests
.............

To see an example of an HTTP POST request, use tcp_test()
to start up the TCP server, and visit the URL::

   file:///cl/examples/form.html

The form on that page looks like this::

   <form method="POST" action="http://localhost:8000/foo/bar">
   User: <input type="text" name="user" size="20" value="James & Nancy Kirk"></input><br/>
   User2: <input type="text" name="user2" size="20"></input><br/>
   Vote: <input type="radio" checked name="vote" value="Y">Yes</input>
         <input type="radio" name="vote" value="N">No</input><br/>
   Pets: <input type="checkbox" checked name="pets" value="dog">Dog</input>
         <input type="checkbox" checked name="pets" value="cat">Cat</input>
         <input type="checkbox" name="pets" value="iguana">Iguana</input><br/>
   Comments: <textarea name="comments"></textarea><br/>
   <input type="submit" value="OK">
   </form>

If you simply click "OK," the print-out from the test handler will
include a request section that looks something like this::

   BEGIN REQUEST
   POST /foo/bar?hi=john%20doe HTTP/1.1
   Host: localhost:8000
   User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:11.0) Gecko/20100101 Firefox/11.0
   Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
   Accept-Language: en-us,en;q=0.5
   Accept-Encoding: gzip, deflate
   Connection: keep-alive
   Content-Type: application/x-www-form-urlencoded
   Content-Length: 67
   
   user=James+%26+Nancy+Kirk&user2=&vote=Y&pets=dog&pets=cat&comments=
   END REQUEST

The entire form is sent as a single line of text.
The format of the POST data is called **urlencoded**;
it is the same as the format of the query string following the
"?" in the URL of a GET request.
Note that spaces in the text value for user get replaced
with + characters, and %26 is the code for
ampersand.

Upload requests
...............

A special case of a POST request is a file upload.  To generate an upload
request, visit::

   file:///cl/examples/upload.html

The form on this webpage is as follows::

   <form method="POST" enctype="multipart/form-data"
         action="http://localhost:8000/foo/bar">
   File: <input type="file" name="myfile"></input><br/>
   <input type="submit" value="OK"></input>
   </form>

Click on "browse" to specify the file.  A convenient choice is::

   /cl/examples/text1

Then click "OK."
The resulting request looks like this::

   BEGIN REQUEST
   POST /foo/bar HTTP/1.1
   Host: localhost:8000
   User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:11.0) Gecko/20100101 Firefox/11.0
   Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
   Accept-Language: en-us,en;q=0.5
   Accept-Encoding: gzip, deflate
   Connection: keep-alive
   Content-Type: multipart/form-data; boundary=---------------------------9849436581144108930470211272
   Content-Length: 264
   
   -----------------------------9849436581144108930470211272
   Content-Disposition: form-data; name="myfile"; filename="text1"
   Content-Type: application/octet-stream
   
   This is a test.
   It is only a test.
   
   -----------------------------9849436581144108930470211272--
   
   END REQUEST

HTTP Server
-----------

HTTPServer class
................

The Python HTTPServer (module BaseHTTPServer)
is almost identical to TCPServer.
The only difference is that it looks up the server host name, and sets
the attributes server_name and server_port.

The main difference is not in the server but in the request handler.
The appropriate class is
BaseHTTPRequestHandler (module BaseHTTPServer),
which builds on
StreamRequestHandler (module SocketServer).  It reads the mime headers
from rfile and parses them.  (It knows it has reached the end
when it reads an empty line.)

The parsed headers are of class mimetools.Message.  For basic
purposes, they can be treated simply as a dict.  For example::

   for key in headers:
       print key, headers[key]

The values are strings.

The function http_test() is defined as follows::

   def http_test ():
       server = HTTPServer(('', 8000), HTTPTestHandler)
       start(server)
       return server

If one visits http://localhost:8000/, the output
from the HTTP test handler looks like this::

   Client address: ('127.0.0.1', 51072)
   Server address: ('0.0.0.0', 8000)
   Server name: skye.local
   Mime:
       requestline: GET / HTTP/1.1
       command: GET
       path: /
       request_version: HTTP/1.1
       Headers:
           accept-language: 'en-us,en;q=0.5'
           accept-encoding: 'gzip, deflate'
           host: 'localhost:8000'
           accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
           user-agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:11.0) Gecko/20100101 Firefox/11.0'
           connection: 'keep-alive'

The handler reads and digests the mime-headers portion of the request.
Note, however, that in the case of a POST request, the data
section of the request is left unread in rfile.

Processing the data section
...........................

Python provides the class cgi.FieldStorage to process the data
section of POST requests.  It also handles the query string portion of
a GET request, to provide a uniform interface to key-value information
regardless of the request method.  The class CGITestHandler
in seal.server gives examples of using FieldStorage
to process GET and POST requests::

   class CGITestHandler (BaseHTTPServer.BaseHTTPRequestHandler):
   
       def do_GET (self):
           (path, qs) = parse_path(self.path)
           self.form = cgi.FieldStorage(fp=None,
                                        headers=None,
                                        keep_blank_values=True,
                                        environ={'REQUEST_METHOD':'GET',
                                                 'QUERY_STRING':qs})
           print_request_info(self, 'GET')
   
       def do_POST (self):
           ctype = self.headers['Content-Type']
           self.form = cgi.FieldStorage(fp=self.rfile,
                                        headers=self.headers,
                                        keep_blank_values=True,
                                        environ={'REQUEST_METHOD':'POST',
                                                 'CONTENT_TYPE':ctype})
           print_request_info(self, 'POST')

The information contained in the resulting FieldStorage object
can be accessed as follows::

   for key in form:
       print key, repr(form.getlist(key))

The method getlist() returns a list of strings.  There is also a
method getfirst() which returns a single string.

Query string example
....................

The function cgi_test() is identical to http_test(), except
that it uses CGITestHandler as its request handler.
Start cgi_test() and visit::

   http://localhost:8000/foo?x=42&y=10

The handler prints out::

   Client address: ('127.0.0.1', 51086)
   Server address: ('0.0.0.0', 8000)
   Server name: skye.local
   Mime:
       requestline: GET /foo?x=42&y=10 HTTP/1.1
       command: GET
       path: /foo?x=42&y=10
       request_version: HTTP/1.1
       Headers:
           accept-language: 'en-us,en;q=0.5'
           accept-encoding: 'gzip, deflate'
           host: 'localhost:8000'
           accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
           user-agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:11.0) Gecko/20100101 Firefox/11.0'
           connection: 'keep-alive'
       Form:
           y ['10']
           x ['42']

The "form" portion comes from the query string in the URL path.

Form example
............

Visit file:///cl/examples/form.html and click "OK."
The handler prints out::

   Client address: ('127.0.0.1', 51090)
   Server address: ('0.0.0.0', 8000)
   Server name: skye.local
   Mime:
       requestline: POST /foo/bar?hi=john%20doe HTTP/1.1
       command: POST
       path: /foo/bar?hi=john%20doe
       request_version: HTTP/1.1
       Headers:
           content-length: '67'
           accept-language: 'en-us,en;q=0.5'
           accept-encoding: 'gzip, deflate'
           host: 'localhost:8000'
           accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
           user-agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:11.0) Gecko/20100101 Firefox/11.0'
           connection: 'keep-alive'
           content-type: 'application/x-www-form-urlencoded'
       Form:
           vote ['Y']
           user2 ['']
           user ['James & Nancy Kirk']
           pets ['dog', 'cat']
           comments ['']

Note that the FieldStorage object hides the fact that the
information is coming from the form on the web page instead of from
the query string at the end of the URL path.  Observe also that
there are multiple values for pets.
The value for user2 is the empty string because we specified
keep_blank_values=True.  If we had not specified keeping blank
values, the key user2 would have been entirely absent.

Upload example
..............

Finally, visit file:///cl/examples/form.html
and browse to /cl/examples/text1.  Click "OK."  The handler
prints out::

   Client address: ('127.0.0.1', 51091)
   Server address: ('0.0.0.0', 8000)
   Server name: skye.local
   Mime:
       requestline: POST /foo/bar HTTP/1.1
       command: POST
       path: /foo/bar
       request_version: HTTP/1.1
       Headers:
           content-length: '256'
           accept-language: 'en-us,en;q=0.5'
           accept-encoding: 'gzip, deflate'
           host: 'localhost:8000'
           accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
           user-agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:11.0) Gecko/20100101 Firefox/11.0'
           connection: 'keep-alive'
           content-type: 'multipart/form-data; boundary=---------------------------168072824752491622650073'
       Form:
           myfile ['This is a test.\nIt is only a test.\n']

Observe that the contents of the uploaded file is returned as a single
string.

Secure HTTP
-----------

The Secure Socket Layer (SSL) protocol runs on top of TCP.
HTTP requests and responses are sent via TCP, whereas
HTTPS consists simply of HTTP requests and responses sent via SSL.

SSL server
..........

The function ssl.wrap_socket() wraps a TCP socket, returning an
SSL socket.  All writes on the SSL socket are encrypted and written as
ciphertext to the TCP socket, and all reads from the SSL socket read
ciphertext from the TCP socket, decrypt it, and return the plaintext.

If one wraps a listening socket, rather than a connection socket, then
the result is a SSL listening socket.  When a connection is accepted,
it creates a TCP connection socket and automatically wraps it in an
SSL connection socket.

The class SSLServer is a specialization of TCPServer that
contains an SSL socket.  All communication with clients is encrypted.
Here is an example of creating an SSLServer::

   def ssl_test ():
       server = SSLServer(('', 8003), TCPTestHandler)
       start(server)
       return server

Note that ssl_test() and tcp_test() are identical except for
the server class.  In particular, they both use the same TCP test
handler.  After starting ssl_test(), visit the url::

   https://localhost:8003/

The results are also the same as for tcp_test(), except that
among the other information printed out, one will see::

   Cipher: ('AES256-SHA', 'TLSv1/SSLv3', 256)

Secure HTTP Server
..................

The class SecureHTTPServer is a specialization of
HTTPServer.  The only modification is in the init method:
the secure server wraps the socket and sets self.socket to the
resulting SSL socket.

There is, again, a test function::

   def https_test ():
       server = SecureHTTPServer(('', 8003), HTTPTestHandler)
       start(server)
       return server

Note that there is again no special handler: one uses the same HTTP
test handler as in http_test().  After starting https_test(),
visit the url::

   https://localhost:8003/

The result is the same as for http_test(), except that
"Cipher" is now present.

Incidentally, SecureHTTPServer also emulates HTTPServer.
If it is created with the keyword argument use_ssl=False, it
uses TCP without SSL, and listens (by default) to port 8000 instead of
8003.

WSGI Server
-----------

A WSGI server is simply a web server that uses the Web Services
Gateway Interface (WSGI) to interact with a handler representing an
application (service).

A WSGI **handler** is a function that takes two
arguments, *environ* and *send function*, and returns a *response*.
Let us consider environ, send function, and response in turn.

Environ
.......

The environ is a dict
containing calling information that corresponds to the environment
variables that a web server passes to a CGI script via
environment variables.  The variables of particular interest are as
follows.

 * PATH_INFO contains the pathname component of the request.

 * REQUEST_METHOD has an HTTP request method as value.  By
   far the commonest values are 'GET' and 'POST'.

 * QUERY_STRING is provided for GET requests.

 * CONTENT_TYPE is provided for POST requests.  It

 * wsgi.input is an open file containing the body of a POST request.
   This is the only key whose value is not a string.

 * REDIRECT_REMOTE_USER, REMOTE_USER, USER
   are all possibilities for where the user name is stored.  Try them in
   that order.

 * SCRIPT_NAME, if present, should be prepended to the
   pathname to get the pathname that the browser actually requested.

 * HTTP_COOKIE has a value of form "key=value; key=value; ..."

To get the keys and values of a GET request::

   cgi.parse_qs(environ['QUERY_STRING'])

To get the keys and values of a multipart/form-data POST request::

   header = environ['CONTENT_TYPE']
   (ctype, pdict) = cgi.parse_header(header)
   if ctype != 'multipart/form-data':
       raise Exception('Expecting multipart/form-data')
   # bug fix
   pdict['boundary'] = bytes(pdict['boundary'], 'ascii')
   form = cgi.parse_multipart(env['wsgi.input'], pdict)
   for k in form:
       form[k] = [v.decode('utf8') for v in form[k]]

The response
............

The handler passes back several pieces of information to the server.
For concreteness, let us assume that the information is placed in
variables, as follows.

 * status.  This is a string indicating the kind
   of response.  The most commonly used possibilities
   are listed here:

     * '200 OK'

     * '303 See Other'

     * '400 Bad Request'

     * '401 Permission Denied'

     * '404 Not Found'

     * '500 Internal Server Error'

 * location.  In the special case of a redirect (status
   303), the location is a string representing the URL that the browser
   should redirect to.

 * mimetype.  Here are some common examples:

     * 'text/css;charset=us-ascii'

     * 'text/html;charset=utf-8'

     * 'application/javascript;charset=us-ascii'

     * 'video/mp4'

     * 'text/pdf'

     * 'text/plain;charset=utf-8'

     * 'audio/wave'

 * contents.  A list of bytelike objects (not strings).

A set of HTTP response headers is then constructed.
If the status is '303 See Other', the headers should be::

   [('Location', location), ('Content-Length', '0')]

Otherwise, the headers should be::

   [('Content-Type', mimetype), ('Content-Length', sum(len(bs) for bs in contents))]

Finally, the response is returned in two separate pieces:

 * The send function is called with arguments status and headers.

 * The contents are returned.

Running the server
..................

A web server that implements the WSGI is provided.  Assume that handler
is a variable containing our WSGI handler.  The server can be run as follows::

   from wsgiref.simple_server import make_server
   server = make_server('localhost', 8000, handler)
   server.serve_forever()

Point a browser as http://localhost:8000/.

A simple example
................

.. code-block:: console

   import cgi
   from wsgiref.simple_server import make_server
   
   def handler (environ, send):
       contents = [b'Hello, world!\n',
                   b'Path: ',
                   environ['PATH_INFO'].encode('ascii')]
       nb = sum(len(s) for s in contents)
       send('200 OK', [('Content-Type', 'text/plain;charset=utf-8'),
                       ('Content-Length', str(nb))])
       return contents
   
   server = make_server('localhost', 8000, handler)
   server.serve_forever()

