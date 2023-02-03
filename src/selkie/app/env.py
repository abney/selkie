##  @package seal.app.env
#   Provides the digest_environ() function, which digests the environment
#   in which a CGI script is called.

import cgi
from urllib.parse import urlparse
from seal.app.config import Config
from seal.app.parse import parse_request_string


#--  Pathname  -----------------------------------------------------------------

##
#   A specialization of str, for the sake of making pathnames recognizable as such.
#
class Pathname (str):

    ##  Returns a pathname that extends this one.

    def join (self, path):
        return Pathname(self + '/' + path)


#--  Seal app wrappers  --------------------------------------------------------

##  For debugging convenience.

def make_environ (path='', qs=None, user='', rootprefix='', cookie=None, https=False, client_addr=None):
    if qs is None:
        i = path.find('?')
        if i >= 0:
            qs = path[i+1:]
            path = path[:i]
        else:
            qs = ''
    https = ('off', 'on')[https]
    env = {'HTTPS': https,
           'PATH_INFO': path,
           'QUERY_STRING': qs,
           'REQUEST_METHOD': 'GET',
           'SCRIPT_NAME': rootprefix,
           'USER': user}

    if cookie is not None:
        env['HTTP_COOKIE'] = cookie
    if client_addr is not None:
        env['REMOTE_ADDR'] = client_addr

    return env


#--  _get_form  ----------------------------------------------------------------

#
#  Takes a WSGI environ dict and returns an unconverted form.
#  "Unconverted" means that keys beginning with 'file:' or '*'
#  are still present, and values are uniformly lists.
#
def _get_form (env):
    method = env.get('REQUEST_METHOD')

    if method == 'GET':
        qs = env.get('QUERY_STRING')
        if qs: return cgi.parse_qs(qs)
        else: return {}

    elif method == 'POST' and 'wsgi.input' in env:
        header = env.get('CONTENT_TYPE')
        if header is None: return {}

        # the current cgi library seems to be buggy.
        # it expects the value of CONTENT_TYPE to be a string,
        # and extracts the boundary out of it,
        # but then it tries to concatenate b'--' with the boundary.
        # This is a workaround.

        (ctype, pdict) = cgi.parse_header(header)
        if ctype != 'multipart/form-data':
            raise Exception('Expecting multipart/form-data')

        pdict['boundary'] = bytes(pdict['boundary'], 'ascii')
        pdict['CONTENT-LENGTH'] = env.get('CONTENT_LENGTH')

        fp = env['wsgi.input']

        form = cgi.parse_multipart(fp, pdict)
        for (key, values) in form.items():
            if not key.startswith('file:') and isinstance(values[0], bytes):
                form[key] = [v.decode('utf8') for v in values]
        return form
        
    else:
        return {}


# 
# def _parse_multipart(fp, pdict):
#     """Parse multipart input.
# 
#     Arguments:
#     fp   : input file
#     pdict: dictionary containing other parameters of content-type header
# 
#     Returns a dictionary just like parse_qs(): keys are the field names, each
#     value is a list of values for that field.  This is easy to use but not
#     much good if you are expecting megabytes to be uploaded -- in that case,
#     use the FieldStorage class instead which is much more flexible.  Note
#     that content-type is the raw, unparsed contents of the content-type
#     header.
# 
#     XXX This does not parse nested multipart parts -- use FieldStorage for
#     that.
# 
#     XXX This should really be subsumed by FieldStorage altogether -- no
#     point in having two implementations of the same parsing algorithm.
#     Also, FieldStorage protects itself better against certain DoS attacks
#     by limiting the size of the data read in one chunk.  The API here
#     does not support that kind of protection.  This also affects parse()
#     since it can call parse_multipart().
# 
#     """
#     import http.client
# 
#     boundary = b""
#     if 'boundary' in pdict:
#         boundary = pdict['boundary']
#     if not cgi.valid_boundary(boundary):
#         raise ValueError('Invalid boundary in multipart form: %r'
#                             % (boundary,))
# 
#     nextpart = b"--" + boundary
#     lastpart = b"--" + boundary + b"--"
#     partdict = {}
#     terminator = b""
# 
#     while terminator != lastpart:
#         bytes = -1
#         data = None
#         if terminator:
#             # At start of next part.  Read headers first.
#             headers = http.client.parse_headers(fp)
#             clength = headers.get('content-length')
#             if clength:
#                 try:
#                     bytes = int(clength)
#                 except ValueError:
#                     pass
#             if bytes > 0:
#                 if maxlen and bytes > maxlen:
#                     raise ValueError('Maximum content length exceeded')
#                 data = fp.read(bytes)
#             else:
#                 data = b""
#         # Read lines until end of part.
#         lines = []
#         while 1:
#             line = fp.readline()
#             print('@@@ line=', line)
#             if not line:
#                 terminator = lastpart # End outer loop
#                 break
#             if line.startswith(b"--"):
#                 print('@@@ starts --')
#                 terminator = line.rstrip()
#                 print('@@@ terminator=', terminator)
#                 print('@@@ nextpart  =', nextpart)
#                 print('@@@ lastpart  =', lastpart)
#                 if terminator in (nextpart, lastpart):
#                     print('@@@ found terminator')
#                     break
#             lines.append(line)
#         # Done with part.
#         if data is None:
#             continue
#         if bytes < 0:
#             if lines:
#                 # Strip final line terminator
#                 line = lines[-1]
#                 if line[-2:] == b"\r\n":
#                     line = line[:-2]
#                 elif line[-1:] == b"\n":
#                     line = line[:-1]
#                 lines[-1] = line
#                 data = b"".join(lines)
#         line = headers['content-disposition']
#         if not line:
#             continue
#         key, params = cgi.parse_header(line)
#         if key != 'form-data':
#             continue
#         if 'name' in params:
#             name = params['name']
#         else:
#             continue
#         if name in partdict:
#             partdict[name].append(data)
#         else:
#             partdict[name] = [data]
# 
#     return partdict
# 


#--  _get_user etc.  -----------------------------------------------------------

# unstarred key: replace (singleton) list of values with single value
# starred key: delete the star, keep the list of values

# def _get_form (env):
#     form = _get_raw_form(env)
#     _process_star_values(form)
#     return form

def _get_user (env):
    for key in ('REDIRECT_REMOTE_USER', 'REMOTE_USER', 'USER'):
        if key in env:
            return env[key]
    return ''


def _get_rootprefix (env):
    if 'SCRIPT_NAME' in env:
        return env['SCRIPT_NAME']
    else:
        return ''

def _get_cookie (env):
    cookie = {}
    if 'HTTP_COOKIE' in env:
        s = env['HTTP_COOKIE']
        for field in s.split(';'):
            i = field.find('=')
            if i < 0:
                k = field.strip()
                v = ''
            else:
                k = field[:i].strip()
                v = field[i+1:].strip()
            cookie[k] = v
    return cookie


#--  Digest environ  -----------------------------------------------------------

##  Digests the environment of a CGI call.
#   Three types of environ argument are accepted:
#
#    - The environ dict from a WSGI call.  In this case, config is not used.
#    - A string representing a URL.  In this case, config is used to get the
#      root prefix.
#    - A string representing a pathname.  In this case, config is used to get
#      the root prefix, the scheme (http or https), and the user name.
#
#   The return value is a dict containing keys 'original', 'rootprefix',
#   'pathname', 'form', 'user', 'cookie', 'https_on', and 'client_addr'.

def digest_environ (environ, config):

    if isinstance(environ, str):
        rootprefix = config.get('rootprefix') or ''
        client_addr = None

        # environ is a URL
        if environ.startswith('http:') or environ.startswith('https:'):
            url = urlparse(environ)
            https_on = (url.scheme == 'https')
            user = url.username
            cookie = {}
            pathname = url.path
            if rootprefix:
                if not pathname.startswith(rootprefix):
                    raise Exception('Path does not start with rootprefix')
                pathname = pathname[len(rootprefix):]
            if url.query:
                form = cgi.parse_qs(url.query)
            else:
                form = {}
                
        # environ is a request string
        # parse_request_string is actually meant for the Client
        else:
            https_on = (config.get('scheme') == 'https')
            user = config.get('user') or ''
            s = parse_request_string(environ)
            if isinstance(s, str):
                pathname = s
                form = {}
                cookie = {}
            else:
                (pathname, form, cookie) = s

    # environ is a WSGI environ dict
    else:
        pathname = environ.get('PATH_INFO') or ''
        rootprefix = _get_rootprefix(environ)
        form = _get_form(environ)
        user = _get_user(environ)
        cookie = _get_cookie(environ)
        https_on = (environ.get('HTTPS') == 'on')
        client_addr = environ.get('REMOTE_ADDR')

    _convert_form(form)

    return {'original': environ,
            'rootprefix': Pathname(rootprefix),
            'pathname': pathname,
            'form': form,
            'user': user,
            'cookie': cookie,
            'https_on': https_on,
            'client_addr': client_addr}

#
#  Destructive!  If the key does not begin with '*', replaces the list of
#  values with a single value.  (Signals an error if the list is not a singleton.)
#  Strips 'file:' and '*' prefixes from keys.
#
def _convert_form (form):

    for key in form:
        if not key.startswith('*'):
            values = form[key]
            if len(values) > 1: raise Exception('Multiple values for key: %s' % key)
            form[key] = values[0]

    for key in form:
        if key.startswith('*'):
            _replace_key(key, key[1:], form)
        elif key.startswith('file:'):
            _replace_key(key, key[5:], form)


def _replace_key (key, newkey, form):
    if (not newkey) or newkey.startswith('*'):
        raise Exception('Bad key: %s' % key)
    if newkey in form:
        raise Exception('Cannot have both %s and %s' % (key, newkey))
    form[newkey] = form[key]
    del form[key]


#--  Digest query string  ------------------------------------------------------
# 
# def digest_query_string (s):
#     form = cgi.parse_qs(s)
#     _convert_form(form)
#     return form
# 


# class CGIEnv (object):
# 
#     def __init__ (self, environ=None, config=None):
#         self.original = environ
#         self.pathname = None
#         self.rootprefix = None
#         self.form = None
#         self.user = None
#         self.cookie = None
#         self.https_on = None
#         self.client_addr = None
# 
#         if isinstance(environ, str):
#             if config is None: config = Config()
#             (pathname, form, cookie) = parse_request_string(environ)
#             self.pathname = pathname
#             self.rootprefix = Pathname(config['rootprefix'])
#             self.form = _convert_form(form)
#             self.user = config['user']
#             self.cookie = cookie
#             self.https_on = (config['scheme'] == 'https')
# 
#         else:
#             self.pathname = environ.get('PATH_INFO') or ''
#             self.rootprefix = Pathname(_get_rootprefix(environ))
#             self.form = _convert_form(_get_cgi_form(environ))
#             self.user = _get_user(environ)
#             self.cookie = _get_cookie(environ)
#             self.https_on = (environ.get('HTTPS') == 'on')
#             self.client_addr = environ.get('REMOTE_ADDR')
#             # Note: client port is available, too, but it varies from request to request
# 
#     def __str__ (self):
#         return 'CGIEnv:\n' + '\n'.join('    %s: %s' % (k, repr(getattr(self, k)))
#                                        for k in ('pathname', 'rootprefix', 'form', 'user', 'cookie', 'https_on', 'client_addr'))
# 
#     def __repr__ (self):
#         return '<CGIEnv u=%s r=%s p=%s>' % (repr(self.user), repr(self.rootprefix), repr(self.pathname))
