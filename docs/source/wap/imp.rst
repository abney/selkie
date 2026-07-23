
Implementation overview
=======================

Launch
------

There are five distinct tasks involved in launching and running the
application:

 1. Setting up the document directory.
 2. Starting a specialized web server (if servlet is 'tornado').
 3. Asking the browser to open the start page (if command is 'start' or 'open').
 4. Starting the application in the browser.
 5. Serving application requests for local files (if a servlet exists).

Which of these are actually carried out depends on how the application
is invoked, and which configuration parameters are set.
As we saw in the introduction, there are two basic commands::

   $ python -m myapp build
   $ python -m myapp start

(Omitting the command defaults to 'start'.)
The 'build' command does only the first task, setting up the document directory.
The 'start' command does the first three tasks: setting up the document directory,
starting the tornado web server, and opening the start page. As for
the remaining two tasks:

 * The application is started in the browser when the start page is
   visited. If one does not use 'start', one may run a
   third-party web server, or one may even visit the start page using a "file:" URL,
   without running any web server at all.

 * If a **servlet** is available, the application will generate server
   requests as it is running, to get access to local files. 
   There are two servlet implementations: the tornado web server contains one,
   or else one may be created as a CGI script. If no web server is
   running, no servlet is available, and the application will have no
   local-file access apart from upload and download.

Command lines are executed by doing ``exec_app(START_FUN)``. (Recall
the *__main__.py* code given in the 'Introduction' section.)
Although the start function is passed to exec_app(), it is not run
by it; it is run later, when the browser opens the start
page. The reason for providing it to exec_app() is to determine its module and name,
which are recorded in the start page, enabling it to be invoked when
the start page is visited. Note that the start page is written by
either command, 'build' or 'start', as part of document-directory set-up.

Configuration
-------------

The configuration is created by exec_app(). Initial settings are taken from
'wap.config' in the local directory, if it exists, or otherwise
'~/.wap', if it exists. Settings on the command line are added
(overriding settings from the config file, in cases of conflict).
Two settings are imputed if not explicitly provided:

 * If the command is 'start', ``document_directory`` is set to
   '~/.cache/wap' and ``servlet`` is set to 'tornado'.
 * If the command is 'build', ``document_directory`` is set to '.'.

After combining the command-line settings with config-file settings,
two abbreviations are expanded out:

 * ``cgi=NAME`` becomes ``servlet=cgi, servlet_name=NAME``.
 * ``use_pypi=VALUE`` becomes ``app_use_pypi=VALUE``.

Finally, missing settings are computed:
   
 * ``pkg_filename``, ``start_fnc_package``, ``start_fnc_module``, and ``start_fnc_name``
   are computed from the start function.
 * ``port`` defaults to 8000.
 * ``start_page`` defaults to 'index.html'.
 * ``servlet_name`` defaults to 'call.cgi' if servlet is 'cgi', and 'call' if servlet is 'tornado'.
 * ``app_use_pypi`` defaults to False.
 * ``selkie_use_pypi`` and ``document_source_directory`` are determined automatically.
 * ``archiver`` defaults to 'zip'.
 * ``archiver_suffix`` defaults to '.zip' if archiver is 'zip', and
   '.tar.gz' if archiver is 'tar'.


1. Setting up the document directory
------------------------------------

The document directory is the directory from which the web server
serves documents. The items that may be created, depending on
configuration, are:

 * ``index.html`` — the start page.
 * ``stylesheet.css``
 * ``call.cgi`` — created if servlet is 'cgi'.
 * ``dist`` — created unless pypi is used for both selkie and the application.

Note that servlet defaults to 'tornado' if one uses 'start', and
defaults to None otherwise. If one wishes to use
a CGI servlet with a third-party web server, use 'build' with 'servlet=cgi'.

Pypi is not used unless one specifies 'use_pypi=True'. (One may do so
either with 'start' or 'build'.)

The contents of 'index.html' vary depending on the configuration. It
is sensitive to a number of configuration parameters. To install 

 * ``start_fnc_package``
 * ``start_fnc_module``
 * ``start_fnc_name``
 * ``servlet``
 * ``servlet_name``
 * ``selkie_use_pypi``
 * ``app_use_pypi``
 * ``archiver_suffix``
 * ``document_source_directory``

2. Specialized web server
-------------------------

The 'start' command runs a web server that is a specialization of
Tornado. It serves the start page from the document
directory. Requests for files in the 'call' pseudo-directory are
dispatched to a Servlet.

3. Visit start page
-------------------

Directing the browser to open the start page is done using the
standard module 'webbrowser'.

4. Starting the application
---------------------------

The start page is written when the document directory is set
up. Although the exact code differs depending on configuration, the
overall structure remains constant.

 * Pyodide is installed from a public repository. This is done in a
   script that is linked in the 'head' element.
 * The stylesheet is also linked in the head.
 * The body has an 'onload' action that runs a Javscript function
   called 'main', defined in the body.
 * The body consists exclusively of a 'script' element containing a
   definition of 'main'.

The main function does the following:

 * Pyodide is loaded.
 * Micropip is loaded, if needed, and it is used to install selkie
   and/or the application, if they use pypi.
 * Pyodide then runs a block of python code, asynchronously.

The python code does the following:

 * Pyfetch is imported, if needed, and it is used to install selkie
   and/or the application, if they do not use pypi.
 * The start function is imported. If a servlet is available, the
   class ServerConnection is also imported.
 * The start function is called with a ServerConnection as
   argument. (If there is no servlet, the argument is None.)

5. Serving application requests
-------------------------------

Serving application requests is done by the class Servlet. The servlet
may either be used inside a tornado call handler, or in a cgi script
(wrapped in CGIHandler).

The Servlet accepts two commands:

 * 'listdir' — lists the directory from which the
   user ran the 'start' command.
 * 'text' — accepts a 'fn' argument, e.g. ``/call/text?fn=foo.txt``,
   and returns the contents of the named file.

