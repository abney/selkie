##  @package seal.app.response
#   Provides Response class.

from io import BytesIO


##  A response code.
OK = 200

##  A response code.
SeeOther = 303

##  A response code.
BadRequest = 400

##  A response code.
PermissionDenied = 401

##  A response code.
NotFound = 404

##  A response code.
InternalServerError = 500

##  Text renderings for each of the response codes.
ResponseMessages = {
    200: 'OK',
    303: 'See Other',
    400: 'Bad Request',
    401: 'Permission Denied',
    404: 'Not Found',
    500: 'Internal Server Error'
}

##  A key is a file suffix, and the corresponding value is a pair of
#   content type and character encoding.  The encoding is None for binary types.
ContentTypes = {
    'css': ('text/css', 'us-ascii'),
    'gif': ('image/gif', None),
    'gl': ('text/x-glab', 'utf-8'),
    'html': ('text/html', 'utf-8'),
    'jpg': ('image/jpeg', None),
    'jpeg': ('image/jpeg', None),
    'js': ('text/javascript', 'us-ascii'),
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
    #   If code is 303, provide location.
    #   Otherwise, provide content_type.

    def __init__ (self, contents=None, code=200, content_type=None, location=None, authenticator=None):

        ##  The response code.
        self.code = code

        ##  The corresponding message.
        self.message = ResponseMessages[code]

        ##  The mime type.  Content type is the pair (mime type, encoding).
        self.mime_type = None

        ##  The character encoding.
        self.encoding = None

        ##  The contents.  A list.  This is filled by iterating through
        #   the provided contents, using the encoding to convert strings to bytes.
        self.contents = []

        ##  The total number of bytes in the contents.
        self.nbytes = 0

        ##  The location, if this is a redirect.
        self.location = location

        ##  The authenticator.
        self.authenticator = authenticator

        if code == 303:
            if location is None:
                raise Exception('303 requires location')
            if not (content_type is None and contents is None):
                raise Exception('303 does not use content_type or contents')

        else:
            if location is not None:
                raise Exception('Only 303 uses location')
            if content_type is None:
                content_type = 'txt'
            
            if isinstance(content_type, (tuple,list)):
                (self.mime_type, self.encoding) = content_type
            else:
                (self.mime_type, self.encoding) = ContentTypes[content_type]

            if isinstance(contents, str): contents = [contents]
            for x in contents:
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

    ##  String representation.

    def __repr__ (self):
        if self.code == 303:
            return '<Response 303 %s>' % self.location
        else:
            if self.encoding: es = ';' + self.encoding
            else: es = ''
            return '<Response %d %s%s %d bytes>' % (self.code, self.mime_type, es, self.nbytes)

    ##  Iterates over the contents.

    def __iter__ (self): return self.contents.__iter__()

#     def __iter__ (self):
#         for s in self.contents:
#             if isinstance(s, bytes): yield s
#             elif isinstance(s, str): yield s.encode('utf8')
#             else: yield str(s).encode('utf8')

    ##  A string representing HTTP status, for WSGI.

    def http_status (self):
        return '%s %s' % (self.code, self.message)

    ##  A list of (key, value) pairs, provided for WSGI.
    #   Headers must be pairs of strings.  Poorly written code in wsgi.headers
    #   looks at type(value) instead of using isinstance(), so we simply convert
    #   everything to str.

    def http_headers (self):
        if self.code == 303:
            hdrs = [('Location', str(self.location)),
                    ('Content-Length', '0')]
        else:
            if self.encoding: enc = ';charset=' + self.encoding
            else: enc = ''
            hdrs = [('Content-Type', str(self.mime_type + enc)),
                    ('Content-Length', str(self.nbytes))]
        auth = self.authenticator
        if auth is not None:
            hdrs.extend(auth.response_headers())
        return hdrs

    ##  Returns the body of the response.  It calls __iter__() and converts to a list.

    def body (self):
        return list(self)

    ##  Calls to_string().  Provided mostly for debugging convenience.

    def __str__ (self):
        return self.to_string()

    ##  Calls to_bytes().

    def __bytes__ (self):
        return self.to_bytes()

    ##  Produce output on a byte stream.

    def write_to (self, stream, headers=True):
        if headers:
            stream.write(b'HTTP/1.1 ')
            stream.write(str(self.code).encode('ascii'))
            stream.write(b' ')
            stream.write(self.message.encode('ascii'))
            stream.write(b'\r\n')
            for (k,v) in self.http_headers():
                stream.write(k.encode('ascii'))
                stream.write(b': ')
                stream.write(v.encode('ascii'))
                stream.write(b'\r\n')
            stream.write(b'\r\n')
        for x in self.contents:
            stream.write(x)

    ##  Convert to a bytes object.

    def to_bytes (self, headers=True):
        with BytesIO() as stream:
            self.write_to(stream, headers=headers)
            return stream.getvalue()

    ##  Convert to a string.  Uses unicode_escape for decoding.

    def to_string (self, headers=True):
        return self.to_bytes(headers=headers).decode('unicode_escape')
