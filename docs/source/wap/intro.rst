
Introduction
============

A Selkie web application (WAP) uses a web browser as interface. User
interface code is written in python and runs in the browser itself,
under Pyodide. The application can be launched from the command line,
in which case it runs the tornado web server and opens a browser
window to localhost, or it can run under a third-party web
server. The server provides access to local files; files may also be
uploaded to the browser. When running under a third-party web server,
a CGI script may optionally be installed to provide access to local 
files on the server.

Hello, world (command line)
---------------------------

Create a directory called `hello` containing the following two files.
In `hello.py`::

    from selkie.wap import Element

    class Hello (Element):
        def __init__ (self):
            Element.__init__(self)
            self.write('Hello, world')

In `__main__.py`::

    from selkie.wap import exec_app
    from .hello import Hello
    exec_app(Hello)

On the command line::

    $ python -m hello start

Running this creates the directory ``~/.cache/wap`` and uses it as a
workspace.

The server runs in the terminal window until one stops it using
ctrl-C.

Browser-only
------------

One may also run the application under a third-party web server. In
the server's document directory, do::

   $ python -m hello build

This creates two files, ``index.html`` and ``stylesheet.css``, and a
subdirectory ``dist`` in which it installs a copy of the application code.

Note: it is **not** possible to use a "file:" URL in lieu of a web
server. When the application in the browser attempts to load the code
from 'dist', the browser will signal a security error. There is,
however, an easy solution; run the python development web server as follows::

   $ python -m http.server

Options
-------

One can change the name used for the start page to something other
than 'index.html'::

   $ python -m hello build start_page=foo.html

If the application is available on pypi, one can use pypi instead of
creating 'dist'::

   $ python -m hello build use_pypi=True

When running under a third-party server, one can provide access to
local files on the server by installing a CGI script::

   $ python -m hello build cgi=foo.cgi

This is shorthand for::

   $ python -m hello build servlet=cgi servlet_name=foo.cgi

It creates an additional file, ``foo.cgi``.

If one needs to specify multiple keyword arguments, one may
alternatively place them in a file called ``wap.config``, one per
line, using space instead of '=' between keyword and argument.
