
Introduction — ``selkie.wap``
=============================

A Selkie web application (WAP) uses a web browser as interface. User
interface code is written in python and runs in the browser itself,
under Pyodide. The application can be launched from the command line,
in which case it runs the tornado web server and opens a browser
window to localhost, or it can run in a CGI script under a
previously-installed web server.

Hello, world
------------

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

Running under an existing web server
------------------------------------

Alternatively, one can install the application as a web page and CGI
script::

    $ cd ~/public_html
    $ python -m hello install_cgi

One should run install_cgi in the server's document directory.
Three files are created: ``index.html``, ``stylesheet.css``, and ``call.cgi``.
One can change the names that are used for the webpage and CGI script::

    $ python -m hello install_cgi start_page=foo.html script_name=bar.cgi

