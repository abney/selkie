
#--  HTTPRequestHandler  -------------------------------------------------------
#  
#  This is a BaseHTTPRequestHandler that creates

class HTTPRequest (BaseHTTPRequestHandler):

    ##  WSGIRequestHandler

    def handle(self):
        """Handle a single HTTP request"""

        debug('Init handler', self.__class__)

        self.raw_requestline = self.rfile.readline(65537)
        debug('len(raw_requestline)=', len(self.raw_requestline))

        if len(self.raw_requestline) > 65536:
            self.requestline = ''
            self.request_version = ''
            self.command = ''
            self.send_error(414)
            return

        debug('enter parse_request')
        if not self.parse_request(): # An error code has been sent, just exit
            debug('failed parse_request')
            return
        debug('exited parse_request')

        # handler = ServerHandler(
        #   self.rfile, self.wfile, self.get_stderr(), self.get_environ()
        # )
        # handler.request_handler = self      # backpointer for logging
        # handler.run(self.server.get_app())

        debug('instantiating HTTPApplication')
        app = HTTPApplication(self)
        app.run()


class HTTPApplication (object):
    '''
    An HTTPApplication instance is wrapped around a Seal application
    and given to the HTTP server in lieu of a request handler class.

    When a connection is received, the server calls the HTTPApplication
    in a separate thread with arguments csock, caddr, server, which are
    what BaseHTTPRequestHandler.__init__ requires.

    When BaseHTTPRequestHandler is initialized, it sets up the socket
    and calls its own handle() method.  That is overridden in 
    HTTPRequestHandler to call back to HTTPApplication.run.
    '''

    def __init__ (self, request):
        self.request = request
        self.server = request.server
        self.resources = request.server.resources

        self.headers_sent = False
        

    ##  from BaseHandler.run
    #   called by HTTPRequestHandler.handle()

    def run(self):
        """Invoke the application"""
        # Note to self: don't move the close()!  Asynchronous servers shouldn't
        # call close() from finish_response(), so if you close() anywhere but
        # the double-error branch here, you'll break asynchronous servers by
        # prematurely closing.  Async servers must return from 'run()' without
        # closing if there might still be output to iterate over.
        try:
            debug('Start running app')
            env = self.get_environ()
            self.result = self._invoke_application(env)
            self.finish_response()
            debug('Done running app')
        except:
            debug('Got an exception while running app', sys.exc_info())
            self.log_exception(sys.exc_info())
            if not self.headers_sent:
                self.result = self.error_output(self.environ, self.start_response)
                self.finish_response()
            # XXX else: attempt advanced recovery techniques for HTML or text?

    ##  from BaseHandler
            
    def error_output(self, environ, start_response):
        start_response(self.error_status,self.error_headers[:],sys.exc_info())
        return [self.error_body]

    ##  seal.app.WsgiApp.__call__

    def _invoke_application (self, environ):
        request = Request(environ, self.resources)
        response = self.resources.app(request)
        status = response.http_status()
        headers = response.http_headers()
        body = response.body()
        self.start_response(status, headers)
        return body

    ##  BaseHTTPRequestHandler

    def log_message(self, format, *args):
        """Log an arbitrary message.

        This is used by all other logging functions.  Override
        it if you have specific logging wishes.

        The first argument, FORMAT, is a format string for the
        message to be logged.  If the format string contains
        any % escapes requiring parameters, they should be
        specified as subsequent arguments (it's just like
        printf!).

        The client ip and current date/time are prefixed to
        every message.

        """

        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.request.address_string(),
                          self.log_date_time_string(),
                          format%args))

    ##  Adapted from BaseHandler

    def finish_response(self):
        try:
            for data in self.result:
                self.write(data)
            self.finish_content()
        finally:
            self.close()

    ##  Adapted from BaseHandler

    def finish_content(self):
        """Ensure headers and content have both been sent"""
        if not self.headers_sent:
            # Only zero Content-Length if not set by the application (so
            # that HEAD requests can be satisfied properly, see #3839)
            self.headers.setdefault('Content-Length', "0")
            self.send_headers()
        else:
            pass # XXX check if content-length was too short?

    ##  Adapted from BaseHandler

    def write(self, data):
        assert type(data) is bytes, \
            "write() argument must be a bytes instance"

        if not self.status:
            raise AssertionError("write() before start_response()")

        elif not self.headers_sent:
            # Before the first output, send the stored headers
            self.bytes_sent = len(data)    # make sure we know content-length
            self.send_headers()
        else:
            self.bytes_sent += len(data)

        # XXX check Content-Length and truncate if too many bytes written?
        self._write(data)
        self._flush()

    ##  Adapted from SimpleHandler

    def _write(self,data):
        result = self.stdout.write(data)
        if result is None or result == len(data):
            return
        from warnings import warn
        warn("SimpleHandler.stdout.write() should not do partial writes",
            DeprecationWarning)
        while True:
            data = data[result:]
            if not data:
                break
            result = self.stdout.write(data)

    ##  Adapted from SimpleHandler

    def _flush(self):
        self.stdout.flush()
        self._flush = self.stdout.flush


    ##  from ServerHandler and SimpleHandler

    def close(self):
        try:
            if self.status is None:
                status = 'Error'
            else:
                status = self.status.split(' ',1)[0]
            self.request_handler.log_request(status, self.bytes_sent)
        finally:
            try:
                if hasattr(self.result,'close'):
                    self.result.close()
            finally:
                self.result = self.headers = self.status = self.environ = None
                self.bytes_sent = 0; self.headers_sent = False

    ##  from WSGIRequestHandler.get_environ and WSGIServer.setup_environ

    def get_environ(self):
        server = self.server
        request = self.request
        headers = request.headers

        env = {}
        env['SERVER_NAME'] = server.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PORT'] = str(server.server_port)
        env['REMOTE_HOST']=''
        env['CONTENT_LENGTH']=''
        env['SCRIPT_NAME'] = ''
        env['SERVER_PROTOCOL'] = 'Seal/1'
        env['SERVER_SOFTWARE'] = 'Seal/1'
        env['REQUEST_METHOD'] = request.command
        if '?' in request.path:
            (path, query) = request.path.split('?', 1)
        else:
            (path, query) = (request.path, '')

        env['PATH_INFO'] = urllib.parse.unquote(path, 'iso-8859-1')
        env['QUERY_STRING'] = query

        host = self.request.address_string()
        if host != request.client_address[0]:
            env['REMOTE_HOST'] = host
        env['REMOTE_ADDR'] = request.client_address[0]

        if headers.get('content-type') is None:
            env['CONTENT_TYPE'] = headers.get_content_type()
        else:
            env['CONTENT_TYPE'] = headers['content-type']

        length = headers.get('content-length')
        if length:
            env['CONTENT_LENGTH'] = length

        for k, v in headers.items():
            k=k.replace('-','_').upper(); v=v.strip()
            if k in env:
                continue                    # skip content length, type,etc.
            if 'HTTP_'+k in env:
                env['HTTP_'+k] += ','+v     # comma-separate multiple headers
            else:
                env['HTTP_'+k] = v
        return env

    ##  Adapted from BaseHandler

    def log_exception(self,exc_info):
        try:
            from traceback import print_exception
            print_exception(
                exc_info[0], exc_info[1], exc_info[2],
                None, # traceback_limit
                sys.stderr
            )
            sys.stderr.flush()
        finally:
            exc_info = None

    ##  from BaseHandler

    def start_response(self, status, headers,exc_info=None):
        if exc_info:
            try:
                if self.headers_sent:
                    # Re-raise original exception if headers sent
                    raise exc_info[0](exc_info[1]).with_traceback(exc_info[2])
            finally:
                exc_info = None        # avoid dangling circular ref
        elif self.headers is not None:
            raise AssertionError("Headers already set!")

        self.status = status
        self.headers = self.headers_class(headers)
        status = self._convert_string_type(status, "Status")
        assert len(status)>=4,"Status must be at least 4 characters"
        assert status[:3].isdigit(), "Status message must begin w/3-digit code"
        assert status[3]==" ", "Status message must have a space after code"

        if __debug__:
            for name, val in headers:
                name = self._convert_string_type(name, "Header name")
                val = self._convert_string_type(val, "Header value")
                assert not is_hop_by_hop(name),"Hop-by-hop headers not allowed"

        return self.write

    ##  from BaseHandler

    def _convert_string_type(self, value, title):
        """Convert/check value type."""
        if type(value) is str:
            return value
        raise AssertionError(
            "{0} must be of type str (got {1})".format(title, repr(value))
        )


