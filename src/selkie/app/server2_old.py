

##  If certfile is provided, this creates an SSL connection, otherwise insecure.

class ServerDaemon_Reduced (object):


    #-----------------------------------------------------------
    # class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):


    #-----------------------------------------------------------
    # class ThreadingMixIn:

    def process_request_thread(self, request, client_address):
        try:
            debug('HANDLER THREAD')
            HTTPRequestHandler(request, client_address, self)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)

    def process_request(self, request, client_address):
        """Start a new thread to process the request."""
        t = threading.Thread(target = self.process_request_thread,
                             args = (request, client_address))
        t.daemon = True
        t.start()

    #-----------------------------------------------------------
    # class HTTPServer(socketserver.TCPServer):

    def server_bind(self):
        """Override server_bind to store the server name."""

        # allow socket reuse
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        self.server_address = self.socket.getsockname()

        host, port = self.server_address[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port

    #-----------------------------------------------------------
    # class TCPServer(BaseServer):

    request_queue_size = 5

    def TCPServer__init__(self, server_address, bind_and_activate=True):
        """Constructor.  May be extended, do not override."""

        self.BaseServer__init__(server_address)
        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_STREAM)
        if bind_and_activate:
            try:
                self.server_bind()
                self.server_activate()
            except:
                self.server_close()
                raise

    def server_activate(self):
        """Called by constructor to activate the server.

        May be overridden.

        """
        self.socket.listen(self.request_queue_size)

    def server_close(self):
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

    timeout = None

    def BaseServer__init__(self, server_address):
        """Constructor.  May be extended, do not override."""
        self.server_address = server_address
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
        debug('SERVER DAEMON THREAD')
        debug('serve forever')
        self.__is_shut_down.clear()
        try:
            # XXX: Consider using another file descriptor or connecting to the
            # socket to wake this up instead of polling. Polling reduces our
            # responsiveness to a shutdown request and wastes cpu at all other
            # times.
            debug('_ServerSelector=', _ServerSelector, 'socket=', self.socket)
            with _ServerSelector() as selector:
                selector.register(self.socket, selectors.EVENT_READ)
                debug('registered')

                while not self.__shutdown_request:
                    try:
                        ready = selector.select(poll_interval)
                    except Exception as e:
                        debug('ERR', e)
                    # bpo-35017: shutdown() called during select(), exit immediately.
                    if self.__shutdown_request:
                        debug('got a shutdown request')
                        break
                    if ready:
                        self._handle_request_noblock()

                    self.service_actions()
        except Exception as e:
            debug('Exception', e)


        debug('shutting down')
        self.__shutdown_request = False
        self.__is_shut_down.set()

        debug('end serve forever')

    def shutdown(self):
        """Stops the serve_forever loop.

        Blocks until the loop has finished. This must be called while
        serve_forever() is running in another thread, or it will
        deadlock.
        """
        self.__shutdown_request = True
        self.__is_shut_down.wait()

    def wait (self):
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

    def _handle_request_noblock(self):
        """Handle one request, without blocking.

        I assume that selector.select() has returned that the socket is
        readable before this function was called, so there should be no risk of
        blocking in get_request().
        """
        debug('_handle_request_noblock')
        try:
            request, client_address = self.get_request()
            debug('got request:', request, client_address)
        except OSError:
            return

        try:
            self.process_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
            self.shutdown_request(request)
        except:
            self.shutdown_request(request)
            raise

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


    def __init__ (self, cfg):

        host = cfg.get('server_host')
        if host:
            assert isinstance(host, str)
        else:
            cfg['server_host'] = host = 'localhost'

        port = cfg.get('server_port')
        if port:
            assert isinstance(port, int)
        else:
            cfg['server_port'] = port = 8807

        certfile = cfg.get('cert_file')

        debug('MAIN THREAD')
        debug('Cfg=', cfg)
        debug('Instantiating ServerDaemon, host=', host, 'port=', port)

        #ThreadingHTTPServer.__init__(self, server_address, RequestHandlerClass)
        #TCPServer.__init__(self, server_address, RequestHandlerClass)
        self.TCPServer__init__((host, port))
        if certfile is None:
            ctx = None
        else:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            if isinstance(certfile, tuple):
                (certfile, keyfile) = certfile
            else:
                keyfile = None
            ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)

        self.config = cfg
        self.sslcontext = ctx
