
The WAP API — ``selkie.wap``
============================

.. py:module:: selkie.wap

Browser-side invocation
-----------------------

In the browser, the entry point to the application is its start
function *f*, which is invoked as ``f(ServerConnection(servlet_name))`` or
``f(None)``, depending on whether a server is available.
The start function for the editor is selkie.editor.Editor.

.. py:class:: ServerConnection

   .. py:attribute:: servlet_name

      The name of the servlet. Used to construct the URL for pyfetch
      calls.

   .. py:method:: __init__(servlet_name)

      Sets servlet_name.

   .. py:method:: call(msg)

      Sends a request to the server. Keyword argument ``binary`` can
      be used to specify that the response is bytes rather than a
      string. Any other keyword arguments are passed as part of the
      call.

   .. py:method:: close()

      Send a 'close' call. Shuts the server down.

   .. py:method:: list_dir()

      Get a directory listing of the current local directory (the
      directory in which the server was invoked).

   .. py:method:: load(fn)

      Loads a text file. The *fn* is relative to the server's current
      local directory. Returns a string representing the file contents.

   .. py:method:: save(fn, contents)

      Writes the given *contents* to the named file. *Fn* is relative
      to the server's current local directory.

.. py:class:: Servlet

   This is the servlet for the Tornado web server. It runs inside the
   server and handles the messages sent from the ServerConnection.

Command-line invocation
-----------------------

The classes described in this section are used only from the command line.

.. py:function:: exec_app(f)

   Creates a Context from the start function *f*. (One may
   alternatively pass in a Context in lieu of a start function, in
   which case it is used as is.) Creates an Application from the
   context, and calls its ``execute()`` method.

.. py:class:: Context

   .. py:attribute:: start_fnc

      The start function.

   .. py:attribute:: com

      The command (a string).

   .. py:attribute:: args

      The command arguments (a list of strings).

   .. py:attribute:: config

      The config dict.

   .. py:method:: __init__(fnc)

      The start function is *fnc*. Read the config file, then parse
      the command line. Sys.argv is used by default, but one may
      override it using the keyword argument ``argv``. Once all
      settings have been collected, they are digested.

   .. py:method:: read_config_file()

      If ``./wap.config`` exists, it is the config file. Otherwise, if
      ``~/.wap`` exists, it is the config file. Otherwise, the initial
      config dict is empty. Once the config file is identified, it is
      read line by line. Empty lines and lines beginning with hash are
      skipped. Other lines are split into key and value at the first
      space character. (A warning is printed and the line is skipped
      if it contains no space.) Leading and trailing whitespace is
      stripped from the value. The key-value pair is added to the
      config dict. Sets the value of ``config``.

   .. py:method:: parse_command_line(argv)

      Ignores the first element in argv. If the next element contains
      no ``=``, it is the command; otherwise, the command is
      'start'. Additional elements that contain no ``=`` are collected
      as arguments, until an element is found that contains
      ``=``. From that point, elements are split at the (first) ``=``
      into key and value, and added to the config dict in
      ``config``. (An element that contains no ``=`` is silently ignored.)
      Sets the values of ``com`` and ``args``.

   .. py:method:: digest_config()

      A new config dict is created, as follows.

       * ``start_fnc_module``, ``start_fnc_name`` —
         If the start function is a string, it is split at the last
         period into the start function module and
         start function name. Otherwise, the start function must be a
         function (or class); its module is
         the start function module, and its name is the start function
         name.

       * ``start_fnc_package`` — the first component of the start function
         module.

       * ``pkg_filename`` — Determined by importing the start function
	 package and getting its filename. (If the package filename is
         '__init__.py', the parent directory is used instead.)

       * ``document_directory`` — The old value is normalized. '~' is
	 expanded out and the filename is converted to an absolute pathname.

       * ``port`` — The old value, if any, or defaults to 8000.

       * ``start_page`` — The old value, if any, or
	 defaults to 'index.html'.

       * ``servlet``, ``servlet_name`` — If 'cgi' has an old value,
	 servlet is set to 'cgi' and servlet_name is set to the old
	 value of 'cgi'. Otherwise, both are set to their old
	 values. If servlet has an old value, but servlet_name does
	 not, servlet_name defaults to 'call.cgi' if servlet is 'cgi',
	 and it defaults to 'call' if servlet is 'tornado'.

       * ``selkie_use_pypi`` — Set to True if the version on pypi is
	 the current version, and False otherwise.

       * ``app_use_pypi`` — The old value of 'use_pypi', if
	 any, or defaults to False.

       * ``archiver`` — The old value, if any, or defaults to 'zip'.

       * ``archiver_suffix`` — '.zip' if archiver is 'zip',
	 '.tar.gz' if archiver is 'tar', and None otherwise.

.. py:class:: Application

   .. py:attribute:: context

      The context.

   .. py:attribute:: config

      The config dict, taken from the context.

   .. py:attribute:: server

      The web server, if the application is running a web server.

   .. py:attribute:: in_browser

      Whether or not the application is running in the
      browser. Determined by whether or not the module ``js`` exists.

   .. py:method:: __init__(context)

      Create the application. Sets context, config, and in_browser.
      Server is initially None.

   .. py:method:: execute()

      Gets the command from the context, and executes the method whose
      name is the command prefixed with "com", applying it to the args from the
      context.

   .. py:method:: com_help()

      Prints out a help message.

   .. py:method:: com_build()

   Reads sys.argv and executes the command.
   It reads the WAP config file ``~/.wap``, if it exists.
   Then it instantiates WapApplication and calls its execute()
   method.


.. py:class:: Server

   The web server.
