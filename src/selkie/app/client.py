## @package seal.app.client
#
#  Permits one to call an HTTP server from software.
#
#  An example of use:
#
#      with CLDApp('corpus.cld', port=8000):
#          client = Client('localhost', 8000)
#          resp = client('/')
#          resp.pretty_print()
#

import socket, random
from io import StringIO
from os.path import abspath, expanduser, basename
from seal.core.misc import lines, file_size
from seal.core.io import pprint
from seal.app.parse import parse_request


#--  call_app  -----------------------------------------------------------------

##
#  The app must have a <tt>server_address</tt> method, it must have __enter__
#  and __exit__ methods that start and stop a server at that address, and it
#  must have a <tt>log</tt> member that is Logger.
#  Puts the app in a with-clause, creates a client, calls the client with
#  the pathname, and pretty-prints the response.</p>
#
#  Keyword argument <tt>header</tt> controls whether the header is printed or
#  not (default False).  If keyword argument <tt>follow_redirects</tt> is True,
#  then a redirect is not returned but passed back to the app.</p>
#
#  The pathname may simply be a string, in which case a GET will be issued.
#  To cause a POST to be issued, the pathname should be a pair of form
#  (<i>pathname, kvpairs</i>).  The <i>kvpairs</i> element must be a list of pairs
#  (<i>key, value</i>).  The Seal wsgi server imposes two expectations:</p>
#  <ul>
#  <li>It is permissible for a key to appear in multiple pairs, but only if
#      the key begins with <tt>'*'</tt>.</li>
#  <li>If the key begins with <tt>'file:'</tt>, the Seal wsgi server takes
#      the value to be the binary contents of the file.  The value passed to
#      call_app should be the filename; it will be read and the value will be
#      replaced with the file contents.</li>
#  </ul>
#

def call_app (app, pathname, header=False, follow_redirects=False):
    multi_call_app(app, [pathname], header, follow_redirects)

##
#   Like call_app(), but accepts a list of pathnames rather than just one.
#

def multi_call_app (app, pathnames, header=False, follow_redirects=False):
    _check_pathnames(pathnames)
    with app.running('run', True):
        if app.log.hasvalue():
            log = app.log
        else:
            log = None
        client = Client(app.server_address(), log)
        for pathname in pathnames:
            result = client(pathname, follow_redirects=follow_redirects)
            result.pretty_print(header=header)

def _check_pathnames (pathnames):
    for pathname in pathnames:
        if isinstance(pathname, str):
            pass
        elif not isinstance(pathname, (tuple, list)):
            raise Exception('Bad pathname, must be str or tuple or list: %s' % repr(pathname))
        else:
            if not len(pathname) == 2:
                raise Exception('POST pathname must have two elements (pathname, pairs): %s' % repr(pathname))
            (pathname, pairs) = pathname
            if not isinstance(pathname, str):
                raise Exception('First pathname element must be a str: %s' % repr(pathname))
            kws = []
            for kwpair in pairs:
                if not (isinstance(kwpair, (list, tuple)) and
                        len(kwpair) == 2 and
                        isinstance(kwpair[0], str) and
                        isinstance(kwpair[1], str)):
                    raise Exception('Bad POST keyword pair: %s' % repr(kwpair))
                kw = kwpair[0]
                if kw in kws and not kw.startswith('*'):
                    raise Exception('POST keywords that appear multiple times must begin with *: %s' % repr(kw))
                kws.append(kw)


#--  HTTPResponse  -------------------------------------------------------------

##
#   Represents an HTTP response to be returned to the client.
#

class HTTPResponse (object):
    
    ##  Breaks a response (bytes) into response code, headers, and body.

    @staticmethod
    def parse (b):
        i = b.index(b'\r\n')
        status_line = b[:i]
        i += 2
        header_lines = []
        eoh = None
        while True:
            j = b.index(b'\r\n', i)
            if j == i:
                eoh = j + 2
                break
            header_lines.append(b[i:j])
            i = j + 2
        code = HTTPResponse.response_code(status_line)
        headers = HTTPResponse.parse_headers(header_lines)
        body = b[eoh:]
        return (code, headers, body)
    
    ##  Extracts the response code from the first line.

    @staticmethod
    def response_code (b):
        return int(b.split()[1])
    
    ##  Parses the header lines, returning a dict.

    @staticmethod
    def parse_headers (lines):
        out = {}
        for line in lines:
            i = line.find(b':')
            if i > 0:
                key = line[:i].decode('ascii')
                value = line[i+1:].decode('ascii').strip()
                out[key] = value
        return out

    ##  Constructor.

    def __init__ (self, b, pathname=None, redirected_from=None, traceback=None):

        ##  The original bytes-like object.
        self.raw = b

        ##  The response code (an int).
        self.code = None

        ##  The headers.  A dict mapping bytes to bytes.
        self.headers = None

        ##  The body.  A bytes-like object.
        self.body = None

        ##  The content type.
        self.content_type = None

        ##  The character encoding.
        self.encoding = None

        ##  The pathname.
        self.pathname = pathname

        ##  Set if this is the result of a redirection.
        self.redirected_from = redirected_from

        ##  Set if this is a 500 with traceback.
        self.traceback = traceback

        (self.code, self.headers, self.body) = self.parse(b)
        self._parse_content_type()

    ##  String representation.

    def __repr__ (self):
        return '<HTTPResponse %s %s>' % (self.code, self.content_type)

    def _parse_content_type (self):
        if 'Content-Type' in self.headers:
            v = self.headers['Content-Type']
            i = v.find(';')
            if i >= 0:
                self.content_type = v[:i]
                v = v[i+1:]
                if v.startswith('charset='):
                    self.encoding = v[8:]
            else:
                self.content_type = v

    ##  Just the body, as a string decoded using the character encoding.

    def string (self):
        enc = self.encoding or 'ascii'
        return self.body.decode(enc)

    ##  Breaks the value of string() into a list of lines.

    def lines (self):
        return lines(self.string())

    ##  Synonym for pretty_print(header=False).

    def describe (self):
        self.pretty_print(header=False)

    ##  Print it readably.

    def pretty_print (self, header=True):
        if header:
            self._pretty_print_header()

        if self.code == 200:
            enc = self.encoding
            if enc is None:
                pprint('Binary file, type %s, len %d' % (self.content_type, len(self.body)))
            else:
                for line in self.lines():
                    pprint(line)

        elif self.code == 303:
            pprint('Redirect:', self.headers['Location'])

        elif self.code == 500:
            pprint('Code', self.code)
            for line in self.lines():
                pprint(line)

        else:
            pprint('Code', self.code)

    def _pretty_print_header (self):
        pprint('Response')
        with pprint.indent():
            pprint('Request Pathname:', self.pathname)
            if self.redirected_from:
                for i in range(len(self.redirected_from)-1, -1, -1):
                    pprint('Redirected From: ', self.redirected_from[i])
            pprint('Code:', self.code)
            pprint('Headers:')
            with pprint.indent():
                for (k,v) in self.headers.items():
                    pprint('%s:' % k, repr(v))
            if self.traceback:
                pprint('Log:')
                with pprint.indent():
                    for line in lines(self.traceback):
                        pprint(line)
                pprint('End Log')
            pprint()


##  Join two paths, provided that the second is relative.  Interprets away './'
#   and '../' components.  If the second is absolute, just return it.

def join (path1, path2):
    if path2.startswith('/'): return path2
    # we expect path1 to be an absolute pathname
    j = path1.rindex('/')
    i = 0
    while i < len(path2) and path2[i] == '.':
        if i+1 == len(path2):
            i += 1
        elif path2[i+1] == '/':
            i += 2
        elif path2[i+1] == '.':
            i += 2
            if i < len(path2):
                if path2[i] != '/':
                    raise('.. not followed by /: %s' % repr(path2))
                i += 1
            j = path1.rindex('/', 0, j)
    return path1[:j+1] + path2[i:]


##
#   Plays the role of an HTTP client.  Issues calls to the server and interprets
#   the responses.
#

class Client (object):

    ##
    #  The server_address must be a pair (<i>hostname, port</i>).
    #  If log is provided, it must have a getvalue method.
    #
    def __init__ (self, server_address):

        ##  The server address: (hostname, port).
        self.server_address = server_address

        ##  The pathname.
        self.pathname = None

        ##  Set if the request is redirected.
        self.redirected_from = None

    ##
    #   Pathname will be handed off to send_and_receive.
    #
    def __call__ (self, pathname, follow_redirects=True):
        pathname = parse_request(pathname)
        self.pathname = pathname
        self.redirected_from = None
        resp = self.send_and_receive(pathname)
        if follow_redirects and resp.code == 303:
            self.redirected_from = []
            while resp.code == 303:
                if len(self.redirected_from) > 9:
                    raise Exception('Too many redirects')
                self.redirected_from.append(pathname)
                p = resp.headers['Location']
                if p.startswith('/'):
                    pathname = p
                else:
                    pathname = join(pathname, p)
                resp = self.send_and_receive(pathname)
        return resp

    ##
    #   If pathname is a string, a GET is performed, otherwise a POST is
    #   performed.  See documentation for call_app for the syntax of pathname.
    #
    def send_and_receive (self, pathname):
        if isinstance(pathname, str):
            request = _get(pathname)
        else:
            request = _post(*pathname)
        data = []
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(self.server_address)
            for b in request:
                s.sendall(b)
            s.shutdown(socket.SHUT_WR)
            while True:
                d = s.recv(1024)
                if not d: break
                data.append(d)
        return HTTPResponse(b''.join(data),
                            pathname=pathname,
                            redirected_from=self.redirected_from)

def _get (pathname):
    yield b'GET %b HTTP/1.1\r\n\r\n' % pathname.encode('ascii')

def _post (pathname, form, cookie):
    d = random.randrange(10000000000000000000000000000,100000000000000000000000000000)
    boundary = b'---------------------------' + str(d).encode('ascii')
    yield b'POST %b HTTP/1.1\r\n' % pathname.encode('ascii')
    yield b'Content-Type: multipart/form-data; boundary=%b\r\n' % boundary
    if cookie:
        yield b'Cookie: ' + '; '.join('%s=%s' % (k,v) for (k,v) in cookie.items())
    body = list(_post_body(form, boundary))
    nb = sum(len(b) for b in body)
    yield b'Content-Length: %d\r\n' % nb
    yield b'\r\n'
    for b in body:
        yield b
    

def _post_body (form, boundary):
    for (k,vs) in form.items():
        for v in vs:
    
            yield b'--' + boundary + b'\r\n'
    
            if k.startswith('file:'):
                fn = abspath(expanduser(v))
                base = basename(fn)
    
                yield b'Content-Disposition: form-data; name="%b"; filename="%b"\r\n' % (k.encode('ascii'), base.encode('ascii'))
                yield b'Content-Length: %d\r\n' % file_size(fn)
                yield b'\r\n'
                with open(fn, 'rb') as f:
                    yield f.read()
                yield b'\r\n'
    
            else:
                yield b'Content-Disposition: form-data; name="%b"\r\n' % k.encode('ascii')
                v = v.encode('ascii')
                #yield b'Content-Length: %d\r\n' % len(v)
                yield b'\r\n'
                yield v
                yield b'\r\n'

    yield b'--' + boundary + b'--\r\n'
