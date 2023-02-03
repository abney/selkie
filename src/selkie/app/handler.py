
#
#  WSGIRequestHandler        ~/anaconda3/lib/python3.7/wsgiref/simple_server.py
#    BaseHTTPRequestHandler  ~/anaconda3/lib/python3.7/http/server.py
#      StreamRequestHandler  ~/anaconda3/lib/python3.7/socketserver.py
#        BaseRequestHandler  "
#
#  A WSGIRequestHandler creates a ServerHandler to do its actual work.
#
#  ServerHandler     ~/anaconda3/lib/python3.7/wsgiref/simple_server.py
#    SimpleHandler   ~/anaconda3/lib/python3.7/wsgiref/handlers.py
#      BaseHandler   "
#

import sys, socket, threading, selectors, ssl, urllib, time
from socketserver import _ServerSelector
from http.server import BaseHTTPRequestHandler
from threading import Thread
from traceback import print_exc

from wsgiref.handlers import read_environ, format_date_time
from wsgiref.headers import Headers
from wsgiref.util import is_hop_by_hop

from seal.app.resources import Resources
from seal.app.request import Request
from seal.app.dualserver import DualServer, debug


#--  HTTPRequestHandler  -------------------------------------------------------
#  
#  This is a BaseHTTPRequestHandler that creates an ApplicationCaller to do
#  its work.
#

class HTTPRequestHandler (BaseHTTPRequestHandler):

    def do_GET (self):
        ApplicationCaller(self).run()

    def do_POST (self):
        ApplicationCaller(self).run()

    def log_message(self, format, *args):
        log = self.server.config['log']
        log('server', "%s - - [%s] %s\n" %
            (self.address_string(),
             self.log_date_time_string(),
             format%args))


class ApplicationCaller (object):

    def __init__ (self, handler):
        self.handler = handler
        self.stdin = handler.rfile
        self.stdout = handler.wfile
        self.server = handler.server
        self.config = handler.server.config

        self.headers = None
        self.headers_sent = False
        self.bytes_sent = 0
        
        self.environ = self.get_environ() # my get_envirion(), below

    ##  from BaseHandler.run
    #   called by HTTPRequestHandler.do_X

    def run(self):
        """Invoke the application"""
        # Note to self: don't move the close()!  Asynchronous servers shouldn't
        # call close() from finish_response(), so if you close() anywhere but
        # the double-error branch here, you'll break asynchronous servers by
        # prematurely closing.  Async servers must return from 'run()' without
        # closing if there might still be output to iterate over.
        try:
            #debug('Start running app')
            self.result = self._invoke_application(self.environ)
            self.finish_response()
            #debug('Done running app')
        except:
            try:
                info = sys.exc_info()
                #debug('Got an exception while running app', sys.exc_info())
                self.log_exception(info)
                if not self.headers_sent:
                    self.result = self.error_output(self.environ, self.start_response)
                    self.finish_response()
                # XXX else: attempt advanced recovery techniques for HTML or text?
            except:
                sys.stderr.write('** Exception during exception\n')
                (t,v,tb) = info
                sys.stderr.write('**     Original: %s %s\n' % (t,v))
                (t,v,tb) = sys.exc_info()
                sys.stderr.write('**     In handling: %s %s\n' % (t,v))

    ##  from BaseHandler
            
    def error_output(self, environ, start_response):
        start_response("500 Internal Server Error",
                       [('Content-Type','text/plain')],
                       sys.exc_info())
        return [
            b"A server error occurred.  Please contact the administrator."
            ]

    ##  seal.app.WsgiApp.__call__

    def _invoke_application (self, environ):
        app = self.config.get('app')
        if app is not None:
            request = Request(environ, self.config)
            response = app(request)
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
            self.handler.log_request(status, self.bytes_sent)
        finally:
            try:
                if hasattr(self.result,'close'):
                    self.result.close()
            finally:
                self.result = self.headers = self.status = None
                self.bytes_sent = 0; self.headers_sent = False


    ##  Environment
    #
    #   BaseHandler.run() originally called self.setup_environ() to set
    #   the member environ.
    #
    #   The class variable os_environ was set using read_environ().
    #   A copy was made and stored in environ.
    #   Then add_cgi_vars() was called.
    #
    #   Add_cgi_vars() updated the environ from the member base_env, which was
    #   set when SimpleHandler was instantiated, which was done in
    #   WSGIRequestHandler.handle().  It called its get_environ() method
    #   to create the dict that was stored in base_env.
    #
    #   The WSGIRequestHandler.get_environ() method started with a copy of the
    #   server's base_environ.  The server in question was of class WSGIServer,
    #   and its base_environ was set by WSGIServer.setup_environ().

    ##  from WSGIRequestHandler.get_environ and WSGIServer.setup_environ

    def get_environ(self):
        server = self.server
        handler = self.handler
        headers = handler.headers

        env = {}

        ##  from BaseHandler.setup_environ()

        env['wsgi.input'] = self.stdin

        ##  from WSGIServer.setup_environ()

        env['SERVER_NAME'] = server.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PORT'] = str(server.server_port)
        env['REMOTE_HOST']=''
        env['CONTENT_LENGTH']=''
        env['SCRIPT_NAME'] = ''

        ##  from WSGIRequestHandler.get_environ()

        env['SERVER_PROTOCOL'] = 'Seal/1'
        env['SERVER_SOFTWARE'] = 'Seal/1'
        env['REQUEST_METHOD'] = handler.command
        if '?' in handler.path:
            (path, query) = handler.path.split('?', 1)
        else:
            (path, query) = (handler.path, '')

        env['PATH_INFO'] = urllib.parse.unquote(path, 'iso-8859-1')
        env['QUERY_STRING'] = query

        host = self.handler.address_string()
        if host != handler.client_address[0]:
            env['REMOTE_HOST'] = host
        env['REMOTE_ADDR'] = handler.client_address[0]

        if headers.get('content-type') is None:
            env['CONTENT_TYPE'] = headers.get_content_type()
        else:
            env['CONTENT_TYPE'] = headers['content-type']

        length = headers.get('content-length')
        if length:
            env['CONTENT_LENGTH'] = length

        ##  Secure connection?

        env['HTTPS'] = 'on' if self.server.sslcontext else 'off'

        ##  Any key beginning with 'HTTP_' is copied from the HTTP request!
        #   HTTP_COOKIE is the most important one.

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
        self.headers = Headers(headers)
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

    origin_server = True    # We are transmitting direct to client

    ##  from BaseHandler

    def send_headers(self):
        """Transmit headers to the client, via self._write()"""
        self.cleanup_headers()
        self.headers_sent = True
        if not self.origin_server or self.client_is_modern():
            self.send_preamble()
            self._write(bytes(self.headers))

    ##  from BaseHandler

    def cleanup_headers(self):
        """Make any necessary header changes or defaults

        Subclasses can extend this to add other defaults.
        """
        if 'Content-Length' not in self.headers:
            self.set_content_length()

    ##  from BaseHandler

    def client_is_modern(self):
        """True if client can accept status and headers"""
        return self.environ['SERVER_PROTOCOL'].upper() != 'HTTP/0.9'

    ##  from BaseHandler

    def set_content_length(self):
        """Compute Content-Length or switch to chunked encoding if possible"""
        try:
            blocks = len(self.result)
        except (TypeError,AttributeError,NotImplementedError):
            pass
        else:
            if blocks==1:
                self.headers['Content-Length'] = str(self.bytes_sent)
                return
        # XXX Try for chunked encoding if origin server and client is 1.1

    http_version  = "1.0"   # Version that should be used for response

    ##  from BaseHandler

    def send_preamble(self):
        """Transmit version/status/date/server, via self._write()"""
        if self.origin_server:
            if self.client_is_modern():
                self._write(('HTTP/%s %s\r\n' % (self.http_version,self.status)).encode('iso-8859-1'))
                if 'Date' not in self.headers:
                    self._write(
                        ('Date: %s\r\n' % format_date_time(time.time())).encode('iso-8859-1')
                    )
                # if self.server_software and 'Server' not in self.headers:
                #     self._write(('Server: %s\r\n' % self.server_software).encode('iso-8859-1'))
        else:
            self._write(('Status: %s\r\n' % self.status).encode('iso-8859-1'))
