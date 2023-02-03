
``selkie.webserver`` — Web server
=================================

.. py:class:: selkie.webserver.Backend

   To implement the back end of a Selkie web application,
   specialize this class.  It behaves like a dict whose keys are
   strings.  A key must begin with a forward slash.
   The portion following the initial slash is split at slashes (if
   any).  The first field is the *type* and the remaining fields are
   *arguments*.  The method whose name is ``get_`` followed by the
   type is invoked, with the arguments as arguments, to determine the
   value.  A KeyError is signalled if no such method exists.

   Setting or deleting a key behaves similarly, except that the
   invoked methods have prefix ``set_`` or ``del_``, respectively,
   instead of ``get_``.  In the case of a set method, the value is
   added as final argument.

   .. py:method:: __getitem__(uri)

      Split the uri into type and args.  Invoke ``get_`` + type on args.

   .. py:method:: __setitem__(uri, value)

      Split the uri into type and args.  Invoke ``get_`` + type on
      args + [value].

   .. py:method:: __delitem__(uri)

      Split the uri into type and args.  Invoke ``del_`` + type on
      args.
        
   .. py:method:: run(nw=False)

      Start the web server.  It will listen for websocket connections
      on port 8844.  A request is translated to a method invocation
      and the return value is sent back to the client.

      This method never returns; use ctrl-C to interrupt it.
