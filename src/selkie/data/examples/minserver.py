#
#  $ python minserver.py
#
#  Visit http://localhost:8000/{u,a,ur,ar}
#  You can view the response using firefox (web console > network)
#

from http.server import HTTPServer, BaseHTTPRequestHandler

ascii_msg = ['<html>',
             '<head><title>Hello</title></head>',
             '<body>',
             '<p>Hello, World!</p>',
             '</body>',
             '</html>']

unicode_msg = ['<html>',
               '<head><title>Hello</title></head>',
               '<body>',
               '<p>Hello, W\u00f8rl\u00f0!</p>',
               '</body>',
               '</html>']


class RequestHandler (BaseHTTPRequestHandler):

    def print_info (self):
        print('HTTP Request')
        print('    Client address:', repr(self.client_address))
        print('    Server:')
        print('        server.server_address:', repr(self.server.server_address))
        print('        server.server_name:', repr(self.server.server_name))
        print('    Request:')
        print('        requestline:', repr(self.requestline))
        print('        command:', repr(self.command))
        print('        path:', repr(self.path))
        print('        request_version:', repr(self.request_version))
        print('    Headers:')
        for key in self.headers:
            print("       %s:" % repr(key), repr(self.headers[key]))

    def do_GET (self): self.doit()
    def do_POST (self): self.doit()

    def doit (self):
        self.print_info()
        if self.path == '/a': self.write_response(ascii_msg)
        elif self.path == '/u': self.write_response(unicode_msg)
        elif self.path == '/ar': self.write_response_raw(ascii_msg)
        elif self.path == '/ur': self.write_response_raw(unicode_msg)


    def write_response (self, lines):
        blines = []
        for line in lines:
            blines.append(line.encode('utf-8'))
        
        nb = sum(len(b) + 2 for b in blines)

        print('Responding, nb=', nb)

        self.send_response(200, 'OK')
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(nb))
        self.end_headers()

        for b in blines:
            if b: self.wfile.write(b)
            self.wfile.write(b'\r\n')


    def write_response_raw (self, lines):
        blines = []
        for line in lines:
            blines.append(line.encode('utf-8'))
        
        nb = sum(len(b) + 2 for b in blines)

        print('Responding, nb=', nb)

        self.wfile.write(b'HTTP/1.1 200 OK\r\n')
        self.wfile.write(b'Content-Type: text/html; charset=utf-8\r\n')
        self.wfile.write(b'Content-Length: ')
        self.wfile.write(str(nb).encode('ascii'))
        self.wfile.write(b'\r\n')
        self.wfile.write(b'\r\n')

        for b in blines:
            if b: self.wfile.write(b)
            self.wfile.write(b'\r\n')


class Server (HTTPServer):

    def __init__ (self):
        HTTPServer.__init__(self, ('', 8000), RequestHandler)

        while True:
            self.handle_request()


Server()
