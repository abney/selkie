
The Selkie web server
=====================

The Selkie web server is essentially a very stripped-down version of Jupyter
notebooks.  It uses the Tornado web server as back end and React as
front end.  The front end communicates with the web server via
Websockets.  The entirety consists of a remarkably small amount of
code: the selkie.webserver module and js/client.

To implement a new application, one creates two pieces: the back end
and the front end.

The back end is a specialization of selkie.webserver.Backend.  It
behaves like a dictionary in which values are JSON objects, except
that the values are dynamically generated.  (A JSON object is
any object formed entirely of dicts, lists, strings, numbers,
booleans, and None).

The front end is a React application that uses Corpus as interface to
the back end.

Front end
---------

How to create a React app.

App, Corpus, Menu.
