
#
#  ~/anaconda3/lib/python3.7/http/server.py   ThreadingHTTPServer, HTTPServer
#  ~/anaconda3/lib/python3.7/socketserver.py  ThreadingMixIn, TCPServer, BaseServer
#
#  Inheritance:
#
#      ThreadingHTTPServer
#          ThreadingMixIn
#          HTTPServer
#              TCPServer
#                  BaseServer
#

import sys, socket, threading, selectors, ssl, urllib, os, subprocess
from socketserver import _ServerSelector
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from traceback import print_exc
from seal.app.resources import Resources
from seal.app.request import Request
from seal.app.handler import HTTPRequestHandler
from seal.app.item import Text


#--  Utilities  ----------------------------------------------------------------

def debug (*msgs):
    print('**%04d' % (threading.get_ident() % 8191), *msgs)


_ReqTemplate = '''[ req ]
default_bits	= 1024
default_keyfile	= %s
distinguished_name	= req_distinguished_name
prompt	= no

[ req_distinguished_name ]
C	= US
ST	= MI
L	= Ann Arbor
O	= Seal
OU	= Seal
CN	= localhost
emailAddress	= nobody@nowhere.com
'''

def create_cert (fn):
    tmp = '/tmp/cert.cfg'
    try:
        with open(tmp, 'w') as f:
            f.write(_ReqTemplate % fn)
        subprocess.run(('openssl',
                        'req',
                        '-new',
                        '-x509',
                        '-config', tmp,
                        '-days', '365',
                        '-nodes',
                        '-out', fn),
                       check=True)
    finally:
        os.unlink(tmp)


#--  EchoApp  ------------------------------------------------------------------

def EchoApp (request):
    print('EchoApp: Received request:', request)
    print('  config:')
    for (k, v) in request.config.items():
        print('    %s:' % k, repr(v))
    print('  log:', repr(request.log))
    print('  server:', repr(request.server))
    print('  authenticator:', repr(request.authenticator))
    print('  webenv:')
    for (k, v) in request.webenv.items():
        if isinstance(v, dict):
            print('    %s:' % k)
            for (k2, v2) in v.items():
                print('      %s:' % k2, repr(v2))
        else:
            print('    %s:' % k, repr(v))
    print('  path:', repr(request.path))
    print('  username:', repr(request.username))
    print('  root:', repr(request.root))
    print('  file:', repr(request.file))

    return Text('Hello, world').to_response()


#--  Server  -------------------------------------------------------------------

class Server (object):

    def __init__ (self, cfg):
        self.server = ServerDaemon(cfg)

    def __enter__ (self):
        server = self.server
        addr = server.server_address
        name = server.server_name
        port = server.server_port

        thread = Thread(target=server.run)
        thread.start()
        #debug('Server started:', repr(addr), repr(name), port)
        return self

    def wait_for_shutdown (self):
        self.server.wait()

    def __exit__ (self, t, v, tb):
        self.server.shutdown()
        #debug('Server stopped')


#--  ServerDaemon  -------------------------------------------------------------

class ServerDaemon (ThreadingHTTPServer):

    def __init__ (self, cfg):
        self.config = cfg
        self.sslcontext = None

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

        #debug('MAIN THREAD')
        #debug('Cfg=', cfg)
        #debug('Instantiating ServerDaemon, host=', host, 'port=', port, 'certfile=', certfile)

        ThreadingHTTPServer.__init__(self, (host, port), HTTPRequestHandler)

        if certfile is not None:
            self.sslcontext = ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            if isinstance(certfile, tuple):
                (certfile, keyfile) = certfile
            else:
                keyfile = None
            ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
            #print('** Loaded cert chain')


    # http.server.HTTPServer
    #
    #    def server_bind(self):
    #        """Override server_bind to store the server name."""
    #        socketserver.TCPServer.server_bind(self)
    #        host, port = self.server_address[:2]
    #        self.server_name = socket.getfqdn(host)
    #        self.server_port = port

    # socketserver.TCPServer
    #
    #    def server_bind(self):
    #        """Called by constructor to bind the socket.
    #
    #        May be overridden.
    #
    #        """
    #        if self.allow_reuse_address:
    #            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #        self.socket.bind(self.server_address)
    #        self.server_address = self.socket.getsockname()

    # TCPServer.get_request just does: return self.socket.accept()

    def get_request (self):
        #debug('get_request')
        (csock, caddr) = self.socket.accept()
        if self.sslcontext is not None:
            csock = self.sslcontext.wrap_socket(csock, server_side=True)
            #debug('Wrapped socket')
        return (csock, caddr)

    def run (self):
        #debug('SERVER DAEMON THREAD')
        self.serve_forever()

    def wait (self):
        self._BaseServer__is_shut_down.wait()

