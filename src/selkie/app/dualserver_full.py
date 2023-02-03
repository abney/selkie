
import socket


#  Inheritance:
#
#      ThreadingHTTPServer
#          ThreadingMixIn
#          HTTPServer
#              TCPServer
#                  BaseServer
#


##  If certfile is provided, this creates an SSL connection, otherwise insecure.

class DualServer (object):

    #-----------------------------------------------------------
    # class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):

    daemon_threads = True



    #-----------------------------------------------------------
    # class ThreadingMixIn:

    # If true, server_close() waits until all non-daemonic threads terminate.
    block_on_close = True

    # For non-daemonic threads, list of threading.Threading objects
    # used by server_close() to wait for all threads completion.
    _threads = None

    def process_request_thread(self, request, client_address):
        """Same as in BaseServer but as a thread.

        In addition, exception handling is done here.

        """
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)

    def process_request(self, request, client_address):
        """Start a new thread to process the request."""
        t = threading.Thread(target = self.process_request_thread,
                             args = (request, client_address))
        t.daemon = self.daemon_threads
        if not t.daemon and self.block_on_close:
            if self._threads is None:
                self._threads = []
            self._threads.append(t)
        t.start()

    # ThreadingMixIn

    def server_close(self):
        #super().server_close()
        self.TCPServer_server_close()
        if self.block_on_close:
            threads = self._threads
            self._threads = None
            if threads:
                for thread in threads:
                    thread.join()


    #-----------------------------------------------------------
    # class HTTPServer(socketserver.TCPServer):

    allow_reuse_address = 1    # Seems to make sense in testing environment

    def server_bind(self):
        """Override server_bind to store the server name."""
        #socketserver.TCPServer.server_bind(self)
        self.TCPServer_server_bind()
        host, port = self.server_address[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port


    #-----------------------------------------------------------

    # class TCPServer(BaseServer):

#  """Base class for various socket-based server classes.
# 
#     Defaults to synchronous IP stream (i.e., TCP).
# 
#     Methods for the caller:
# 
#     - __init__(server_address, RequestHandlerClass, bind_and_activate=True)
#     - serve_forever(poll_interval=0.5)
#     - shutdown()
#     - handle_request()  # if you don't use serve_forever()
#     - fileno() -> int   # for selector
# 
#     Methods that may be overridden:
# 
#     - server_bind()
#     - server_activate()
#     - get_request() -> request, client_address
#     - handle_timeout()
#     - verify_request(request, client_address)
#     - process_request(request, client_address)
#     - shutdown_request(request)
#     - close_request(request)
#     - handle_error()
# 
#     Methods for derived classes:
# 
#     - finish_request(request, client_address)
# 
#     Class variables that may be overridden by derived classes or
#     instances:
# 
#     - timeout
#     - address_family
#     - socket_type
#     - request_queue_size (only for stream sockets)
#     - allow_reuse_address
# 
#     Instance variables:
# 
#     - server_address
#     - RequestHandlerClass
#     - socket
# 
#     """

    address_family = socket.AF_INET

    socket_type = socket.SOCK_STREAM

    request_queue_size = 5

    allow_reuse_address = False

    def TCPServer__init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        """Constructor.  May be extended, do not override."""
        # BaseServer.__init__(self, server_address, RequestHandlerClass)
        self.BaseServer__init__(server_address, RequestHandlerClass)
        self.socket = socket.socket(self.address_family,
                                    self.socket_type)
        if bind_and_activate:
            try:
                self.server_bind()
                self.server_activate()
            except:
                self.server_close()
                raise

    def TCPServer_server_bind(self):
        """Called by constructor to bind the socket.

        May be overridden.

        """
        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        self.server_address = self.socket.getsockname()

    def server_activate(self):
        """Called by constructor to activate the server.

        May be overridden.

        """
        self.socket.listen(self.request_queue_size)

    def TCPServer_server_close(self):
        """Called to clean-up the server.

        May be overridden.

        """
        self.socket.close()

    def fileno(self):
        """Return socket file number.

        Interface required by selector.

        """
        return self.socket.fileno()

    def get_request(self):
        """Get the request and client address from the socket.

        May be overridden.

        """
        return self.socket.accept()

    def shutdown_request(self, request):
        """Called to shutdown and close an individual request."""
        try:
            #explicitly shutdown.  socket.close() merely releases
            #the socket and waits for GC to perform the actual close.
            request.shutdown(socket.SHUT_WR)
        except OSError:
            pass #some platforms may raise ENOTCONN here
        self.close_request(request)

    def close_request(self, request):
        """Called to clean up an individual request."""
        request.close()

    #-----------------------------------------------------------
    # class BaseServer:

#     """Base class for server classes.
# 
#     Methods for the caller:
# 
#     - __init__(server_address, RequestHandlerClass)
#     - serve_forever(poll_interval=0.5)
#     - shutdown()
#     - handle_request()  # if you do not use serve_forever()
#     - fileno() -> int   # for selector
# 
#     Methods that may be overridden:
# 
#     - server_bind()
#     - server_activate()
#     - get_request() -> request, client_address
#     - handle_timeout()
#     - verify_request(request, client_address)
#     - server_close()
#     - process_request(request, client_address)
#     - shutdown_request(request)
#     - close_request(request)
#     - service_actions()
#     - handle_error()
# 
#     Methods for derived classes:
# 
#     - finish_request(request, client_address)
# 
#     Class variables that may be overridden by derived classes or
#     instances:
# 
#     - timeout
#     - address_family
#     - socket_type
#     - allow_reuse_address
# 
#     Instance variables:
# 
#     - RequestHandlerClass
#     - socket
# 
#     """

    timeout = None

    def BaseServer__init__(self, server_address, RequestHandlerClass):
        """Constructor.  May be extended, do not override."""
        self.server_address = server_address
        self.RequestHandlerClass = RequestHandlerClass
        self.__is_shut_down = threading.Event()
        self.__shutdown_request = False

    def BaseServer_server_activate(self):
        """Called by constructor to activate the server.

        May be overridden.

        """
        pass

    def serve_forever(self, poll_interval=0.5):
        """Handle one request at a time until shutdown.

        Polls for shutdown every poll_interval seconds. Ignores
        self.timeout. If you need to do periodic tasks, do them in
        another thread.
        """
        self.__is_shut_down.clear()
        try:
            # XXX: Consider using another file descriptor or connecting to the
            # socket to wake this up instead of polling. Polling reduces our
            # responsiveness to a shutdown request and wastes cpu at all other
            # times.
            with _ServerSelector() as selector:
                selector.register(self, selectors.EVENT_READ)

                while not self.__shutdown_request:
                    ready = selector.select(poll_interval)
                    # bpo-35017: shutdown() called during select(), exit immediately.
                    if self.__shutdown_request:
                        break
                    if ready:
                        self._handle_request_noblock()

                    self.service_actions()
        finally:
            self.__shutdown_request = False
            self.__is_shut_down.set()

    def shutdown(self):
        """Stops the serve_forever loop.

        Blocks until the loop has finished. This must be called while
        serve_forever() is running in another thread, or it will
        deadlock.
        """
        self.__shutdown_request = True
        self.__is_shut_down.wait()

    def service_actions(self):
        """Called by the serve_forever() loop.

        May be overridden by a subclass / Mixin to implement any code that
        needs to be run during the loop.
        """
        pass

    # The distinction between handling, getting, processing and finishing a
    # request is fairly arbitrary.  Remember:
    #
    # - handle_request() is the top-level call.  It calls selector.select(),
    #   get_request(), verify_request() and process_request()
    # - get_request() is different for stream or datagram sockets
    # - process_request() is the place that may fork a new process or create a
    #   new thread to finish the request
    # - finish_request() instantiates the request handler class; this
    #   constructor will handle the request all by itself

    def handle_request(self):
        """Handle one request, possibly blocking.

        Respects self.timeout.
        """
        # Support people who used socket.settimeout() to escape
        # handle_request before self.timeout was available.
        timeout = self.socket.gettimeout()
        if timeout is None:
            timeout = self.timeout
        elif self.timeout is not None:
            timeout = min(timeout, self.timeout)
        if timeout is not None:
            deadline = time() + timeout

        # Wait until a request arrives or the timeout expires - the loop is
        # necessary to accommodate early wakeups due to EINTR.
        with _ServerSelector() as selector:
            selector.register(self, selectors.EVENT_READ)

            while True:
                ready = selector.select(timeout)
                if ready:
                    return self._handle_request_noblock()
                else:
                    if timeout is not None:
                        timeout = deadline - time()
                        if timeout < 0:
                            return self.handle_timeout()

    def _handle_request_noblock(self):
        """Handle one request, without blocking.

        I assume that selector.select() has returned that the socket is
        readable before this function was called, so there should be no risk of
        blocking in get_request().
        """
        try:
            request, client_address = self.get_request()
        except OSError:
            return
        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)
            except Exception:
                self.handle_error(request, client_address)
                self.shutdown_request(request)
            except:
                self.shutdown_request(request)
                raise
        else:
            self.shutdown_request(request)

    def handle_timeout(self):
        """Called if no new request arrives within self.timeout.

        Overridden by ForkingMixIn.
        """
        pass

    def verify_request(self, request, client_address):
        """Verify the request.  May be overridden.

        Return True if we should proceed with this request.

        """
        return True

    def BaseServer_process_request(self, request, client_address):
        """Call finish_request.

        Overridden by ForkingMixIn and ThreadingMixIn.

        """
        self.finish_request(request, client_address)
        self.shutdown_request(request)

    def BaseServer_server_close(self):
        """Called to clean-up the server.

        May be overridden.

        """
        pass

    def finish_request(self, request, client_address):
        """Finish one request by instantiating RequestHandlerClass."""
        self.RequestHandlerClass(request, client_address, self)

    def BaseServer_shutdown_request(self, request):
        """Called to shutdown and close an individual request."""
        self.close_request(request)

    def BaseServer_close_request(self, request):
        """Called to clean up an individual request."""
        pass

    def handle_error(self, request, client_address):
        """Handle an error gracefully.  May be overridden.

        The default is to print a traceback and continue.

        """
        print('-'*40, file=sys.stderr)
        print('Exception happened during processing of request from',
            client_address, file=sys.stderr)
        import traceback
        traceback.print_exc()
        print('-'*40, file=sys.stderr)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.server_close()

    #-----------------------------------------------------------


    def __init__ (self, server_address, RequestHandlerClass, certfile=None, resources=None):
        #ThreadingHTTPServer.__init__(self, server_address, RequestHandlerClass)
        #TCPServer.__init__(self, server_address, RequestHandlerClass)
        self.TCPServer__init__(server_address, RequestHandlerClass)
        if certfile is None:
            ctx = None
        else:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            if isinstance(certfile, tuple):
                (certfile, keyfile) = certfile
            else:
                keyfile = None
            ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
        self.sslcontext = ctx
        self.resources = resources

    ##  From TCPServer.__init__

#     def tcpserver_init (self, server_address, RequestHandlerClass, bind_and_activate=True):
#         """Constructor.  May be extended, do not override."""
#         BaseServer.__init__(self, server_address, RequestHandlerClass)
#         print('** Set socket')
#         self.socket = socket.socket(self.address_family,
#                                     self.socket_type)
#         if bind_and_activate:
#             try:
#                 self.server_bind()
#                 self.server_activate()
#             except:
#                 print('** Error, server close')
#                 self.server_close()
#                 raise



#     def get_request (self):
#         (csock, caddr) = self.socket.accept()
#         if self.sslcontext is not None:
#             csock = self.sslcontext.wrap_socket(csock, server_side=True)
#         return (csock, caddr)


    ##  From BaseServer

#     def _handle_request_noblock(self):
#         """Handle one request, without blocking.
# 
#         I assume that selector.select() has returned that the socket is
#         readable before this function was called, so there should be no risk of
#         blocking in get_request().
#         """
#         try:
#             print('** Calling get_request')
#             request, client_address = self.get_request()
#             print('** Got request')
#         except OSError:
#             return
#         if self.verify_request(request, client_address):
#             try:
#                 self.process_request(request, client_address)
#             except Exception:
#                 self.handle_error(request, client_address)
#                 self.shutdown_request(request)
#             except:
#                 self.shutdown_request(request)
#                 raise
#         else:
#             self.shutdown_request(request)


    ##  From TCPServer.server_bind

#     def tcpserver_bind(self):
#         """Called by constructor to bind the socket.
# 
#         May be overridden.
# 
#         """
#         print('** bind')
#         if self.allow_reuse_address:
#             print('** Set reuse address')
#             self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self.socket.bind(self.server_address)
#         self.server_address = self.socket.getsockname()

    ##  From HTTPServer

#     def server_bind(self):
#         """Override server_bind to store the server name."""
#         print('** bind')
#         self.tcpserver_bind()
#         host, port = self.server_address[:2]
#         self.server_name = socket.getfqdn(host)
#         self.server_port = port


    ##  From TCPServer

#     def server_activate(self):
#         """Called by constructor to activate the server.
# 
#         May be overridden.
# 
#         """
#         print('** activate')
#         self.socket.listen(self.request_queue_size)


