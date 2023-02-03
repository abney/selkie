
.. module:: selkie.ssh
   :synopsis: SSH

``selkie.ssh`` — Secure Shell (SSH)
===================================

Usage
-----

The module ``selkie.ssh`` provides a python interface to secure
shell calls.  The main entry point is the function ``connection()``::

   >>> from ssh import connection
   >>> ssh = connection('host123', 'me')

.. py:function:: connection(host, user)

   Three keyword arguments are available that affect the behavior of
   the connection:

   show_progress
      If true, progress information is printed about what the
      connection is doing.  Default: ``True``.

   show_responses
      If true, responses from the server are
      printed as they are received.  Default: ``True``.

   return_responses
      If true, responses are collected and returned as a single string
      when the call completes.  Default: ``True``.

The ssh module maintains a table of remote SSH servers, each represented
locally by a Server instance.  The password is stored in the Server
instance, so that one only needs to enter it once, the first time one
connects to the server.
The information provided to ``connection()`` as keywords (degree of
verbosity and what to return) is stored
in the Connection rather than the Server.
A server is identified by
host and user name.  User name may be omitted if it is the same as
one's user name on the local machine.  Servers are cached in a table
so that a new connection to the same host uses the same server instance.

One may invoke the connection as a function to issue a shell command on
the remote machine.  An SSH connection is created, the function is
called, and the SSH connection is closed, but the Connection object
persists::
   
   >>> s = ssh('ls')
   [SSH: Fork completed, child pid=23496]
   [SSH: Authenticate]
   [SSH: Reading]
   [SSH: Read b'Password: ']
   Password: [SSH: Password request]
   [SSH: Getting password from user]
   Password for abney@login.itd.umich.edu: 
   [SSH: Sending password]
   [SSH: Checking response, first read]
   [SSH: Read b'\r\n']
   
   [SSH: Checking response, second read]
   [SSH: Read b'AppleVolumes\r\nbot\r\n...]
   AppleVolumes
   bot
   cl
   ...
   seal
   Shared
   [SSH: Push back]
   [SSH: Authentication complete]
   [SSH: Reading response block]
   [SSH: Reading response block]
   [SSH: EOF]
   [SSH: Response complete]

The trace messages "[SSH: ...]" are displayed in magenta, and
the strings read from the server are displayed in cyan.
The return value does not include the prompt for the password::
   
   >>> s[:12]
   'AppleVolumes'

API
---

The ``connection()`` function is actually an instance of ServerTable.

.. py:class:: ServerTable()

   A table mapping a host name to a server that connects to that
   host.

   .. py:method:: __call__(host[, user][, show_progress][, show_responses][, return_responses])

      Fetch a server (creating it if it does not already exist), and
      return a new Connection with the given settings.

.. py:class:: selkie.ssh.Server(host, [user])

   If user is None or not provided, it defaults to getpass.getuser().

   .. py:attribute:: user

      The user name (a string).

   .. py:attribute:: host

      The remote hostname (a string).

   .. py:attribute:: password

      The user will be prompted once for this, no matter how many
      times calls are placed to the server.

   .. py:method:: hoststring()

      Has the form "user@host".

   .. py:method:: hostpath(path)

      Has the form "user@host:path".

   .. py:method:: connection([show_progress] [,show_responses] [,return_responses])

      Returns a new Connection.  Creating a Connection does not
      actually send anything to the server; it just stores the
      settings.  By default, all are on.

.. py:class:: selkie.ssh.Connection(server [,show_progress] [,show_responses] [,return_responses])

   .. py:attribute:: server

      The SSH Server.

   .. py:attribute:: show_progress

      Whether to show progress.

   .. py:attribute:: show_responses

      Whether to show responses from the server.

   .. py:attribute:: return_responses

      Whether to return responses.

   .. py:attribute:: child_pid

      The child process PID, when a request is in progress.

   .. py:method:: hoststring()

      Dispatches to the server.

   .. py:method:: hostpath(path)

      Dispatches to the server.

   .. py:method:: __call__(cmd)

      Execute a remote command and return the value.
      It spawns a subprocess in which it logs in, sends the command,
      and gets the response.  It cleans up the subprocess and returns
      the response.
