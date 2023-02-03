##  @package seal.app.request
#   Provides the Request class and supporting functionality.

import cgi, random
from io import StringIO
from os.path import expanduser
from seal.core.io import pprint, PPrinter
from seal.app.parse import cookie_log_string
from seal.app.env import Pathname, digest_environ
from seal.app.config import create_config
from seal.app.resources import Resources
from seal.app.response import Response
from seal.app.auth import Authenticator

#  parse_request_string is in seal.app.comline


##  This is a convenience function; it hands off to parse_path().

def path_from_string (s):
    return parse_path('', s, {})

##  Hands off to parse_path(), taking the arguments from the given environment.
#   Reads the keys 'rootprefix', 'pathname', and 'form'.

def path_from_env (env):
    return parse_path(env['rootprefix'], env['pathname'], env['form'])


#--  Path parsing  -------------------------------------------------------------

##  A path is a tuple of URLPathComponents, obtained by splitting the pathname
#   at slashes.  The initial '' component (before the leading slash) is replaced with the
#   rootprefix.

def parse_path (rootprefix, pathname, form):
    if rootprefix:
        if not rootprefix.startswith('/'):
            raise Exception('Non-empty root prefix must start with /')
        if rootprefix.endswith('/'):
            raise Exception('Root prefix may not end with /')
    if pathname:
        if not pathname.startswith('/'):
            raise Exception('Non-empty pathname must start with /: %s' % repr(pathname))
    else:
        pathname = '/'
    path = pathname.split('/')
    pathname = rootprefix + pathname
    path[0] = rootprefix
    if form and len(path) < 2:
        raise Exception('Cannot handle form on root')
    n = len(rootprefix)
    for i in range(len(path)):
        cpt = URLPathComponent(path[i])
        path[i] = cpt
        if i == 0:
            cpt.call = None
        else:
            n += 1 + len(cpt)
            fields = path[i].split('.')
            if form and i == len(path)-1: kwargs = form
            else: kwargs = {}
            cpt.call = (fields[0], tuple(fields[1:]), kwargs)
        if i == 0 and n == 0:
            cpt.pathname = Pathname('/')
        else:
            cpt.pathname = Pathname(pathname[:n])
    return tuple(path)

##  A URLPathComponent is a str.  It has two additional members:</p>
#
#    - <tt>call</tt> is a tuple (name, args, kwargs).  The Request's form
#      is stored as the kwargs of the last call.
#      The <tt>call</tt> is None for the initial component.
#
#    - <tt>pathname</tt> is a string representing the full pathname
#      of the component.  It does include the rootprefix, but it does
#      not include the query string.  (In a POST request, the query string
#      is not part of the URL.)

class URLPathComponent (str):

    ##  Returns a new URLPathComponent whose pathname extends this one.

    def join (self, name):
        cpt = URLPathComponent(name)
        cpt.call = None
        cpt.pathname = Pathname(self.pathname + '/' + name)
        return cpt

#
#  Call <tt>urlparse</tt> (from urllib.parse) to parse <i>s</i> as a URL.
#  Call <tt>parse_query_string</tt>
#  to parse the URL's query string.  Call <tt>parse_path</tt> to produce a tuple
#  of URLPathComponents.
#
# def url_path (s):
#     url = urlparse(s)
#     form = parse_query_string(url.query)
#     return parse_path('', url.path, form)



#--  Request  ------------------------------------------------------------------

##  Truncate the given string/bytes if greater than length 19.  Keep first
#   8 and last 8 characters/bytes.

def maybe_truncate (s):
    if isinstance(s, str) and len(s) > 19:
        return s[:8] + '...' + s[-8:]
    elif isinstance(s, bytes) and len(s) > 19:
        return s[:8] + b'...' + s[-8:]
    else:
        return s


##  A digested HTTP request.  Also used as the context for the app while
#   accessing the page.

class Request (object):

    ##  Constructor.  Calls authenticate() and prints a start-up log message.

    def __init__ (self, http_request, config=None):
        if config is None:
            config = create_config()

        ##  A Config.
        self.config = config

        ##  A Logger.  If log is not provided, it is created by calling
        #   config.make_logger().
        self.log = config['log']

        ##  The web server.
        self.server = config.get('server')

        #self.log('auth', 'Raw-Cookie', repr(http_request.get('HTTP_COOKIE')))

        ##  Created by calling digest_environ().
        self.webenv = digest_environ(http_request, self.config)

        ##  Created by calling path_from_env() on the webenv.
        self.path = path_from_env(self.webenv)

        ##  An Authenticator.  This is not set until one calls authenticate().
        self.authenticator = None

        ##  The authenticated user name, or '' if authentication failed.
        self.username = ''

        ##  The root web directory, initially None.  It is set by App.
        self.root = None

        ##  The application file, initially None.  It is set by App.
        self.file = None


    ##  String representation.

    def __repr__ (self):
        words = [repr(c) for c in self.path[1:]]
        form = self.form()
        if form:
            formstr = ' ' + ','.join('%s=%s' % (k,maybe_truncate(v))
                                     for (k,v) in form.items())
        else:
            formstr = ''
        return '<Request %s%s>' % (' '.join(words), formstr)

    ##  Rootprefix, taken from self.webenv.

    def rootprefix (self): return self.webenv['rootprefix']

    ##  The form information, taken from the last URLPathComponent.

    def form (self): return self.path[-1].call[2]

    ##  Set the application filename.  Only permitted in desktop mode.

    def set_application_file (self, filename):
        if self.execmode() != 'desktop':
            raise Exception('Permitted only in desktop mode')
        self.config['rtc'].set_application_file(filename)

    ##  Provided for use of the Authenticator.  Value from the Config.
    def auth_dir (self): return self.config.get('auth_dir')

    ##  Provided for use of the Authenticator.  Value from the webenv.
    def client_addr (self): return self.webenv.get('client_addr')

    ##  Provided for use of the Authenticator.  Value from the Config.
    def desktop_user (self): return self.config.get('desktop_user')

    ##  Provided for use of the Authenticator.  Value from the Config.
    def execmode (self): return self.config.get('execmode')

    ##  Provided for use of the Authenticator.  Value from the webenv.
    def https_on (self): return self.webenv.get('https_on')

    ##  Provided for use of the Authenticator.  Value from the Config.
    def server_authentication_on (self): return self.config['server_authentication_on']

    ##  Provided for use of the Authenticator.  Value from the webenv.
    def server_username (self): return self.webenv['user']

    ##  Provided for use of the Authenticator.  Value from the webenv.
    def server_cookie (self): return self.webenv['cookie']

    ##  Whether we are doing loopback testing.
    def doing_loopback_testing (self):
        return (self.config.get('loopback_testing_on') and
                self.webenv.get('client_addr') == '127.0.0.1')

    ##  Provided for use of the Authenticator.  The value is True if HTTPS
    #   is on, or if loopback_testing_on is True and the client address is
    #   localhost (127.0.0.1).
    def connection_is_secure (self):
        return self.https_on() or self.doing_loopback_testing()

    ##  Used by Item.  If the path is absolute, prefixes it with the root prefix.
    #   Otherwise returns it unchanged.

    def extern (self, path):
        if path.startswith('/'):
            return Pathname(self.webenv['rootprefix'] + path)
        else:
            return Pathname(path)

    ##  Returns a (long) string containing information about the cookie, username,
    #   client_addr, https_on, and rootprefix.

    def runtime_configuration (self):
        webenv = self.webenv
        auth = self.authenticator
        with StringIO() as f:
            print('Runtime Configuration:', file=f)
            if auth:
                print('    auth:', file=f)
                print('        cookie:', cookie_log_string(auth.cookie), file=f)
                print('        username:', repr(auth.username), file=f)
            print('    webenv:', file=f)
            for key in ('client_addr',
                        'cookie',
                        'https_on',
                        'rootprefix',
                        'user'):
                val = webenv.get(key)
                # so that session keys are not stored in the log
                if key == 'cookie':
                    val = cookie_log_string(val)
                else:
                    val = repr(val)
                print('        %s: %s' % (key, val), file=f)
            return f.getvalue()

    ##  For debugging

    def print_environment (self, f=None):
        print('Path:', file=f)
        for (i,cpt) in enumerate(self.path):
            print('    [%d]' % i, repr(cpt), cpt.call, file=f)
        print(file=f)

        print('Config:', file=f)
        for (k,v) in sorted(self.config.items()):
            if k in ('app', 'log'):
                s = '<%s object>' % type(v).__name__
            else:
                s = repr(v)
            print('    %s: %s' % (k, s), file=f)
        print(file=f)

        print('Webenv:', file=f)
        for (k,v) in sorted(self.webenv.items()):
            if k != 'original':
                print('    %s: %s' % (k, repr(v)), file=f)
        print(file=f)
        orig = self.webenv['original']
        if isinstance(orig, dict):
            print('    original:', file=f)
            for (k,v) in sorted(orig.items()):
                print('        %s: %s' % (k, repr(v)), file=f)
        else:
            print('    original: %s' % repr(orig), file=f)

        print('Context:', file=f)
        print('    cookie:', self.server_cookie(), file=f)
        print('    username:', repr(self.username), file=f)
        print('    root:', repr(self.root), file=f)
        print('    file:', repr(self.file), file=f)


    ##  Deprecated.  Use connection_is_secure() instead.

    def is_secure (self): return self.connection_is_secure()

    ##  Authenticate the username found in the webenv.
    #   Sets self.username.  (Sets it to '' if authentication failed.)
    #   Return value is True/False indicating whether authentication succeeded.

    def authenticate (self):
        if self.authenticator is not None:
            raise Exception('Attempt to authenticate twice')
        self.authenticator = auth = Authenticator(self)
        v = auth.authenticate()
        self.username = auth.username
        return v

    ##  Log in the given user.  Returns True/False indicating whether
    #   authentication succeeded.  Sets self.username either way.

    def login (self, user, password):
        v = self.authenticator.login(user, password)
        self.username = self.authenticator.username
        return v

    ##  Log out the user.
    #   Updates self.username.

    def logout (self):
        self.authenticator.logout()
        self.username = self.authenticator.username

    ##  Change the user's password.  Returns True/False indicating whether
    #   the change succeeded.

    def change_password (self, old_password, new_password):
        return self.authenticator.change_password(old_password, new_password)
