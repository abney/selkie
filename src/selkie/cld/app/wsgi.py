##  @package seal.app.wsgi
#   Provides WsgiApp.

import traceback, os, re, sys, threading
from .request import Request


#--  WsgiApp  ------------------------------------------------------------------

##  Converts a seal application to a wsgi application.
#   A seal application is a function that takes a Request and returns a Response.
#
#   What can be included under 'logging' in the config file:
#    - error:   Any errors that occur.
#    - server:  The lines generated by the wsgi server.   No effect if run as cgi.
#    - req:     One line per request.
#    - path:    Entails 'req'.  The resolution of the HtmlPage from the Request.
#    - trace:   Entails 'path'.  Show configuration.

class WsgiApp (object):

    ##  Constructor.  N.b., when the WsgiApp is created, the Server does not yet
    #   exist.  It is subsequently created and added to the resources.

    def __init__ (self, config):

        ##  The Config.
        self.config = config

        ##  The Seal app.
        self.app = config['app']

        ##  The Logger.
        self.log = config['log']

    ##  Called by Server

    def server_port (self): return self.config['server_port']

    ##  Main entry point.  Conforms to the WSGI protocol.

    def __call__ (self, environ, send):
        tid = str(threading.get_ident())[-4:]
        log = self.log

        try:
            req = Request(environ, self.config)
            response = self.app(req)

            status = response.http_status()
            headers = response.http_headers()
            body = response.body()

        except Exception as e:
            (t,v,tb) = sys.exc_info()
            log('traceback', ''.join(traceback.format_exception(t,v,tb)))
            status = '500 Internal Server Error'
            s = (status + '\r\n' + str(e) + '\r\n').encode('utf8')
            body = [s]
            headers = [('Content-Type', 'text/plain'),
                       ('Content-Length', str(len(s)))]

        send(status, headers)
        return body



#--  WSGI call  ----------------------------------------------------------------

##  Provides the ability to call a WsgiApp from software.

class WsgiCaller (object):

    ##  Constructor.

    def __init__ (self):

        ##  Status, from response.
        self.status = None

        ##  Headers, from response.
        self.headers = None

    ##  This is a callback for the WsgiApp.

    def send (self, status, headers):
        self.status = status
        self.headers = headers

    ##  Call the given app (a Seal app) on the given pathname.
    #   The Seal app is converted to a WsgiApp, which is called.
    #   Return value is a string or bytes, depending on whether the
    #   response page is text or binary.

    def __call__ (self, app, pathname, user='', rootprefix='', rettype=str):
        app = WsgiApp(app)
        self.status = None
        self.headers = None
        env = environ(pathname, user, rootprefix)
        body = app(env, self.send)
        if self.status is None: raise Exception('Status not set')
        if self.headers is None: raise Exception('Headers not set')
        if rettype == bytes:
            return wsgi_bytes(self.status, self.headers, body)
        elif rettype == str:
            encoding = wsgi_encoding(self.headers)
            return wsgi_string(self.status, self.headers, body, encoding)
        else:
            raise Exception('Bad value for rettype: %s' % rettype)

##  A WsgiCaller instance.
wsgi_call = WsgiCaller()

##  This is used by the WsgiCaller if the response is a binary page.

def wsgi_bytes (status, headers, body):
    out = bytearray(b'HTTP/1.1 ')
    out.extend(status.encode('ascii'))
    out.extend(b'\r\n')
    for (key,value) in headers:
        out.extend(key.encode('ascii'))
        out.extend(b': ')
        out.extend(value.encode('ascii'))
        out.extend(b'\r\n')
    out.extend(b'\r\n')
    for bs in body:
        out.extend(bs)
    return out

##  This is used by the WsgiCaller if the response is text.

def wsgi_string (status, headers, body, encoding):
    out = StringIO()
    out.write('HTTP/1.1 ')
    out.write(status)
    out.write('\n')
    for (k,v) in headers:
        out.write(k)
        out.write(': ')
        out.write(v)
        out.write('\n')
    out.write('\n') # empty line between headers and body
    if encoding is None:
        out.write('<binary contents>\n')
    else:
        for bs in body:
            out.write(bs.decode(encoding).replace('\r', ''))
    s = out.getvalue()
    out.close()
    return s

##  Determine the encoding from a set of HTTP response headers.

def wsgi_encoding (headers):
    for (k,v) in headers:
        if k.lower() == 'content-type':
            m = re.search(r';charset=([^\s]+)', v)
            if m is not None:
                return m.group(1)


#  This version is much too finicky.  Works in a standalone python, but not
#  in doctest.

#def handle1 (app, lock, port=8000):
#    wapp = WsgiApp(app)
#    server = make_server('localhost', port, wapp)
#    lock.release()
#    server.handle_request()
#
#def call (app, pathname='', port=8000, encoding='utf8'):
#    orig_stderr = sys.stderr
#    try:
#        sys.stderr = null # suppress server log lines, but also error messages
#    
#        lock = Lock()
#        lock.acquire()
#        thread = Thread(target=handle1, args=(app, lock, port))
#        thread.start()
#        lock.acquire() # returns when handle1 has started the server
#
#        if pathname.startswith('/'): pathname = pathname[1:]
#        r = urlopen('http://localhost:%d/%s' % (port, pathname))
#        return r.read().decode(encoding)
#
#    finally:
#        sys.stderr = orig_stderr



#--  Response  -----------------------------------------------------------------

##  A Response is essentially a list of byte-strings with a response code, a
#   mime type, and a character encoding.  It needs to be a list, not an iterable,
#   because we need to know the length in bytes up front.
#
#   A Page is a more flexible object.  It has a response code and content type,
#   and is an iteration over mixed strings, Pathnames, and byte-strings.  The
#   content type determines both the mime type and the character encoding.
#
#   When converting a Page to a Response, we also provide a function that adjusts
#   pathnames.

ResponseMessages = {
    200: 'OK',
    303: 'See Other',
    400: 'Bad Request',
    401: 'Permission Denied',
    404: 'Not Found',
    500: 'Internal Server Error'
}

##  Maps file suffixes to pairs (mime-type, encoding).  For binary types,
#   encoding is None.

ContentTypes = {
    'css': ('text/css', 'us-ascii'),
    'gif': ('image/gif', None),
    'gl': ('text/x-glab', 'utf-8'),
    'html': ('text/html', 'utf-8'),
    'jpg': ('image/jpeg', None),
    'jpeg': ('image/jpeg', None),
    'js': ('application/javascript', 'us-ascii'),
    'mp3': ('audio/mp3', None),
    'mp4': ('video/mp4', None),
    'pdf': ('text/pdf', None),
    'tsv': ('text/plain', 'utf-8'),
    'txt': ('text/plain', 'utf-8'),
    'wav': ('audio/wave', None)
}

##  An HTTP response.

class Response (object):

    ##  Constructor.

    def __init__ (self, page, context):

        ##  The web page.

        self.page = page

        ##  The response code.

        self.code = page.response_code

        ##  The textual version of the response code.

        self.message = ResponseMessages[page.response_code]

        ##  The mime type.

        self.mime_type = None

        ##  The character encoding.

        self.encoding = None

        ##  The contents of the response.

        self.contents = []

        ##  The total number of bytes.

        self.nbytes = 0

        ##  The redirect location, if this is a redirect.

        self.location = None

        ##  A cookie or None.

        self.cookie = None

        if self.code == 303:
            self.location = page.uri

        else:
            t = page.content_type
            if isinstance(t, (tuple,list)):
                (self.mime_type, self.encoding) = t
            else:
                (self.mime_type, self.encoding) = ContentTypes[t]
            for x in page:
                # this misses e.g. filenames in javascript
                # if isinstance(x, Pathname):
                #     x = self.rootprefix + x
                if isinstance(x, str):
                    if self.encoding is None:
                        raise Exception('Binary page may only contain byte-strings')
                    x = x.encode(self.encoding)
                if isinstance(x, (bytes, bytearray)):
                    if x:
                        self.contents.append(x)
                        self.nbytes += len(x)
                else:
                    raise Exception('Bad object in Page: %s' % repr(x))

        if context is not None and context.cookie is not None and context.cookie.modified:
            self.cookie = context.cookie

    ##  String representation.

    def __repr__ (self):
        if self.code == 303:
            return '<Response 303 %s>' % self.location
        else:
            if self.encoding: es = ';' + self.encoding
            else: es = ''
            return '<Response %d %s%s %d bytes>' % (self.code, self.mime_type, es, self.nbytes)

    ##  Iterate over contents.

    def __iter__ (self): return self.contents.__iter__()

#     def __iter__ (self):
#         for s in self.contents:
#             if isinstance(s, bytes): yield s
#             elif isinstance(s, str): yield s.encode('utf8')
#             else: yield str(s).encode('utf8')

    ##  Required by the WSGI protocol.

    def http_status (self):
        return '%s %s' % (self.code, self.message)

    ##  Required by the WSGI protocol.

    def http_headers (self):
        if self.code == 303:
            hdrs = [('Location', self.location),
                    ('Content-Length', '0')]
        else:
            if self.encoding: enc = ';charset=' + self.encoding
            else: enc = ''
            hdrs = [('Content-Type', self.mime_type + enc),
                    ('Content-Length', str(self.nbytes))]
        if self.cookie:
            for (k,v) in self.cookie.items():
                hdrs.append(('Set-Cookie', '%s=%s;Secure;HttpOnly' % (k,v)))
        return hdrs

    ##  The body of the response.

    def body (self):
        return list(self)

    ##  This is for debugging convenience.
    #   If self.encoding is None, the body prints as "<binary data>"

    def __str__ (self):
        if self.encoding is None:
            return '<binary data>'
        else:
            ba = bytearray()
            for bs in self.body():
                ba.extend(bs)
            return ba.decode(self.encoding)
