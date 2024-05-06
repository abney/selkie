##  @package seal.app.server
#   Provides a threading web server.

from socketserver import ThreadingMixIn
from wsgiref.simple_server import make_server, WSGIServer, WSGIRequestHandler, ServerHandler
from wsgiref.handlers import BaseCGIHandler
from threading import Thread, Lock, Event, get_ident
from urllib.request import urlopen


#--  Server  -------------------------------------------------------------------

##  Just combines ThreadingMixIn with WSGIServer.

class ThreadingWSGIServer (ThreadingMixIn, WSGIServer):

    ##  This is True so that request threads die when the server is killed.
    daemon_threads = True

# socketserver.ThreadingMixIn:
#     process_request()

# simple_server.WSGIServer: .server_bind(), .setup_environ(), .get_app(), .set_app()
#     http.server.HTTPServer: .server_bind()
#         socketserver.TCPServer: .__init__(), .server_bind(), ...
#             socketserver.BaseServer:
#                 .serve_forever()
#                     ._handle_request_noblock()
#                         .process_request()

##  There is a bug in the standard ServerHandler code that causes it to hang
#   forever if the web browser stops reading a file (e.g., an audio file).
#   This overrides the run() method to fix that.

class RepairedServerHandler (ServerHandler):

    ##  @var result
    #   The value returned by the application.

    ##  Copied from python3.6/wsgiref/handlers.py.
    #   Added a BrokenPipeError catch.

    def run(self, application):
        """Invoke the application"""

        # Note to self: don't move the close()!  Asynchronous servers shouldn't
        # call close() from finish_response(), so if you close() anywhere but
        # the double-error branch here, you'll break asynchronous servers by
        # prematurely closing.  Async servers must return from 'run()' without
        # closing if there might still be output to iterate over.
        try:
            self.setup_environ()
            self.result = application(self.environ, self.start_response)
            self.finish_response()
        except BrokenPipeError:
            pass
        except:
            try:
                self.handle_error()
            except:
                # If we get an error handling an error, just give up already!
                self.close()
                raise   # ...and let the actual server figure it out.

##  Overrides the handle() method to use RepairedServerHandler instead of ServerHandler.
#   Also overrides log_message() to use the server's logger member, which we set.

class RepairedWSGIRequestHandler (WSGIRequestHandler):

    ##  @var requestline
    #   A line read from the HTTP request.

    ##  @var raw_requestline
    #   A line read from the HTTP request, before processing.

    ##  @var request_version
    #   The version portion of the request line.

    ##  @var command
    #   The command portion of the request.

    ##  Copied from python3.6/wsgiref/simple_server.py.
    #   The only edit: ServerHandler -> RepairedServerHandler.

    def handle(self):
        """Handle a single HTTP request"""

        self.raw_requestline = self.rfile.readline(65537)
        if len(self.raw_requestline) > 65536:
            self.requestline = ''
            self.request_version = ''
            self.command = ''
            self.send_error(414)
            return

        if not self.parse_request(): # An error code has been sent, just exit
            return

        handler = RepairedServerHandler(
            self.rfile, self.wfile, self.get_stderr(), self.get_environ()
        )
        handler.request_handler = self      # backpointer for logging
        handler.run(self.server.get_app())

    ##  Copied from python3.6/http/server.py.
    #   Replaced 'sys.stderr.write' with 'self.server.log'

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

        # was: sys.stderr.write("%s - - [%s] %s\n" %
        self.server.log('server', "%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format%args))


##  The web server.
#   It wraps the WSGI web server.

class Server (object):

    ##  Constructor.  App is a WsgiApp.

    def __init__ (self, app):

        ##  A WsgiApp.
        self.app = app

        ##  The server port.
        self.port = app.server_port()

        ##  The logger.
        self.log = app.log

        ##  An Event used to signal that the server has been started.
        self.started = Event()

        ##  An Event used to signal that the server has been stopped.
        self.stopped = Event()

        ##  The Thread in which the server is running.
        self.thread = None

        ##  The actual WSGI server.
        self.real_server = None

    ##  Same as start().

    def __enter__ (self):
        self.start()
        return self

    ##  Same as stop().

    def __exit__ (self, t, v, tb):
        self.stop()

    ##  Start the server.  Writes a log message, creates a thread, starts the thread,
    #   then waits for the self.start event to be activated.
    #   The (private) method that runs in the thread activates self.start just
    #   before calling the real_server's serve_forever() method.
    #   If/when the real_server is shut down, it then activates the self.stop event.

    def start (self):
        self.log('server', 'Start server, port: %d' % self.port)
        # must be a daemon, otherwise prevents shutdown
        self.thread = Thread(target=self._start_server, daemon=True)
        self.thread.start()
        self.started.wait()

    ##  Stop the server.  Call real_server's shutdown() method to request shutdown.
    #   Waits until the self.stop event is activated.

    def stop (self):
        # the user may shut down the server by calling quit from within the application
        if self.real_server is not None:
            # Sets shutdown flag.
            self.real_server.shutdown()
            # Serve_forever will terminate when all outstanding requests are finished.
            # Then my stopped flag will get set and server is set to None
            self.stopped.wait()

    def _start_server (self):
        real_server = make_server('localhost', self.port, self.app,
                                  server_class=ThreadingWSGIServer,
                                  handler_class=RepairedWSGIRequestHandler)
        if hasattr(real_server, 'log'):
            raise Exception('Overriding server.log')
        real_server.log = self.log
        self.real_server = real_server
        # The __enter__ is a no-op, but the __exit__ closes the socket
        # (and releases the address for re-use)
        with real_server:
            self.started.set()
            real_server.serve_forever()
        self.real_server = None
        self.stopped.set()

    ##  A synonym for stop().

    def quit (self):
        self.stop()
