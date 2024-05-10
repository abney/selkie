
Implementation as WSGI app
**************************

The WSGI specification
----------------------

Overview
........

WSGI stands for Web Server Gateway Interface.  It is a Python
standard, but it is implemented by Apache and other web servers.
A WSGI script is much like a CGI script, except that it is executed by
Python rather than by the shell.  A WSGI script usually has file
suffix .wsgi and resides in the web server's cgi-bin directory.
The script must set the variable application to an application that
conforms to WSGI expectations.

A WSGI application may also be called from a CGI script using
the CGIHandler class from wsgiref.handlers.

Definition
..........

The WSGI standard defines a **WSGI application** to be a callable
that behaves as follows: it takes two arguments, *environ*
and *callback*, and it responds by
passing status and header information to *callback*,
and by returning the page contents as
a list of byte-strings.  The following provides a
bare-bones example::

   def app (environ, callback):
       value = [b'This is a test.\r\n'
                b'It is only a test.\r\n']
       nbytes = sum(len(s) for s in value)
       callback('200 OK', 
                [('Content-Type', 'text/plain'),
                 ('Content-Length', str(nbytes))])
       return value

This little example ignores *environ.*
The value for *callback* is a function that accepts two
arguments, *status_line* and *headers.*
The *status_line* is a string that conforms to the HTTP standard;
here it is '200 OK'.  The value for *headers* is a list
of pairs of form (*key,* *value*).  Keys and values are all
strings.  The keys must be valid HTTP header keys.

The server further expects the app's return value to be a list of byte-strings
representing the contents of the HTTP response.
'Content-Length' must be included in the headers passed to *callback,*
and its value must match the total number of bytes in the return value.
Note that
the arguments to *callback* consist of strings, whereas 
the return value consists of byte-strings.

Running a WSGI application
..........................

Python also provides an implementation of a WSGI server, which can be
run as in the following example::

   >>> from wsgiref.simple_server import make_server
   >>> server = make_server('localhost', 8000, app)
   >>> server.serve_forever()

Then visit the URL http://localhost:8000/.
Alternatively, do the following in a separate terminal window::

   $ curl http://localhost:8000/

One can alternatively run a WSGI application inside
a CGI script.  Here is a hypothetical example::

   #!/home/clling/bin/python
   import site
   site.addsitedir('/home/my/python')
   from mystuff import app
   from wsgiref.handlers import CGIHandler
   CGIHandler().run(app)

WsgiApp
-------

The WsgiApp __call__ method
...........................

The class WsgiApp wraps a
Seal application function and makes it behave like a WSGI app.  To be precise,
the WsgiApp constructor is called on a Resources instance, which
contains a pointer to a Seal application in the member app.
The WsgiApp accepts *environ* and *callback* arguments
in accordance with the WSGI specification, and it instantiates Request
from the environ and resources.  It passes the request to the
Seal application to obtain a
Response, and it calls the
Response methods http_status(), http_headers(),
and body() to get the pieces of the WSGI output.
In accordance with the WSGI specification,
the status headers are passed to *callback,* and the body is returned.

If an error occurs in the call to the Seal application, the
WsgiApp constructs the status, headers, and body
from the error.

Response methods
................

The Response provides the following three methods for the use of
WsgiApp:

 * http_status() — Returns a string consisting of the page's
   response_code and the corresponding message.

 * http_headers() — With the exception of redirects
   (status 303), there are two headers: Content-Type and Content-Length.
   The value of the Content-Type header is constructed from the mime type and
   character encoding, and the value of the Content-Length
   header comes from nbytes.
   A redirect substitutes Location for Content-Type; the
   value for Location comes from
   the page's uri member.

 * body() —
   Simply returns the contents.

The WsgiApp calls these three methods and returns the results
to its caller in accordance with the WSGI specification.
