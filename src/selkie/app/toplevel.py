##  @package seal.app.toplevel
#   Contains toplevel calls for the CLD script and for invocation from software.

import sys, webbrowser, seal
from sys import stdout
from io import StringIO
from os import chmod, makedirs
from os.path import abspath, expanduser, exists, join
from wsgiref.handlers import CGIHandler
from seal.core.io import pprint, get_suffix, load_dict
from seal.core.misc import Shift
from seal.app.auth import LocalAuthenticator
from seal.app.config import standardize_config, print_config, config_str, ConfigFile
from seal.app.log import logger_from_config
from seal.app.auth import Authenticator
from seal.app.wsgi import WsgiApp
from seal.app.server import Server, create_cert
from seal.app.client import Client
from seal.app.resources import Resources
from seal.app.request import Request
from seal.app.response import Response


def _print_header (status, headers):
    print('HTTP/1.1', status)
    for (k,v) in headers:
        print('%s: %s' % (k, v))
    print()

def _execmode (c):
    if c == 'D': return 'desktop'
    elif c == 'W': return 'webservice'

def _int_ext (c, type):
    if c == 'X': return 'external'
    elif c == 'I': return 'internal'
    elif c == 'N': return None
    else:
        raise Exception('Bad type: %s' % type)


#--  Command  ------------------------------------------------------------------

##  A parsed command line.

class Command (object):

    ##  Constructor.

    def __init__ (self, mgr, method_name):

        ##  The Manager.  Some specializations need it.
        self.manager = mgr

        ##  Only for display.
        self.method_name = method_name

        ##  The subject.
        self.subject = mgr.__subject__

        ##  The call configuration.
        self.config = dict(mgr.__config__)

        ##  The command function.
        self.function = getattr(self, method_name)

    ##  Execute it.

    def __call__ (self, *args, **kwargs):
        return self.function(*args, **kwargs)

    ##  String representation.

    def __repr__ (self):
        return '<%s %s>' % (self.__class__.__name__, self.method_name)


#--  UsageCommand  -------------------------------------------------------------

class UsageCommand (object):
        
    def __init__ (self, shift):
        self.shift = shift

    def print_usage (self, msg, *args):
        self.shift.print_usage()



#--  RuntimeCommand  -----------------------------------------------------------

##  A runtime command.

class RuntimeCommand (Command):

    ##  Run the application.  Creates an internal server, but assumes an external
    #   client.  Runs in desktop mode by default.  Creates and enters a
    #   RuntimeContext, opens a (standard) web browser window pointed at the
    #   server (localhost:port), and waits for the server's stopped event to get
    #   activated.
    
    def run (self):
        rtc = RuntimeContext(self, 'dIX')
        with rtc:
            webbrowser.open('http://localhost:%d/' % rtc.config['server_port'])
            rtc.server.wait_for_shutdown()

    def serve (self):
        rtc = RuntimeContext(self, 'WIX')
        with rtc:
            rtc.server.wait_for_shutdown()

    ##  A toplevel command.  Assumes an external client and external server.
    #   Webservice mode by default.  Creates a RuntimeContext and runs its
    #   wsgi app within a CGIHandler.
    
    def cgi (self):
        rtc = RuntimeContext(self, 'WXX')
        with rtc:
            CGIHandler().run(rtc.wsgi)
    
    ##  A toplevel command.  Invokes an internal client and internal server.
    #   Webservice mode by default, but can be set to 'desktop' in the configuration.
    
    def call (self, *args):
        rtc = RuntimeContext(self, 'wII')
        with RTFunction(rtc) as f:
            for arg in args:
                f(arg)

    ##  A toplevel command.  Just calls the app as a function.  No client or server.
    
    def direct (self, *args):
        rtc = RuntimeContext(self, 'wNN')
        with rtc:
            for arg in args:
                req = Request(arg, rtc.config) # rtc.config is self.config
                rsp = self.manager.app(req)
                _print_header(rsp.http_status(), rsp.http_headers())
                for b in rsp:
                    stdout.write(b.decode('unicode_escape'))
    
    ##  A toplevel command.  Invokes an internal client and internal server.
    #   Unlike com_call(), it returns the RTFunction, which can then be used
    #   by the caller to process requests.  The caller should use it in a
    #   with-statement.
    
    def open (self):
        rtc = RuntimeContext(self, 'wII')
        return RTFunction(rtc)


##  A runtime harness for a Seal app.

class RuntimeContext (object):

    ##  Constructor.  The code indicates the manner in which the application
    #   is to be run.
    #
    #    - The first character of the code should be either 'D'
    #      or 'd' to indicate desktop mode, or 'W' or 'w' to indicate webservice
    #      mode.  If the lowercase version is used, and 'execmode' is set in the Config,
    #      the Config's value is used instead.
    #
    #    - The second and third characters indicate the type of server and client,
    #      respectively.  The choices are 'X' for external, 'I' for internal, and
    #      'N' for none.
    #
    #   Certain values get set in Config:
    #
    #    - 'execmode' gets set to 'desktop' or 'webservice'.
    #
    #    - 'server_type' and 'client_type' get set to 'external', 'internal',
    #      or None.
    #
    #    - 'log_file' gets set if it is None.  It is set to '-' if the execmode
    #      is 'desktop', and '/dev/null' otherwise.

    def __init__ (self, command, code):
        app = command.manager.app
        config = command.config

        mode = _execmode(code[0])
        if not mode:
            # uppercase modes override Config; lowercase do not
            mode = config['execmode']
            if not mode:
                mode = _execmode(code[0].upper())
                if not mode:
                    raise Exception('Bad code: %s' % code)
        config['execmode'] = mode
    
        if mode == 'desktop':
            config['rtc'] = self

        for (k,v) in zip(('server_type', 'client_type'), code[1:]):
            v = _int_ext(v, code)
            config[k] = v

        log = config.get('log')
        if log is None:
            if config.get('log_file') is None:
                k = mode + '_log_file'
                if k in config:
                    config['log_file'] = config[k]
            if config.get('logging') is None:
                k = mode + '_logging'
                if k in config:
                    config['logging'] = config[k]
            log = config['log'] = logger_from_config(config)
    
        server = wsgi = None
        server_type = config['server_type']
        if server_type == 'internal':
            server = Server(config)
        elif server_type == 'external':
            server = None
            wsgi = WsgiApp(config)
        config['server'] = server

        if config['client_type'] == 'internal':
            addr = ('localhost', config['server_port'])
            client = Client(addr)
        else:
            client = None
    
        ##  Command
        self.command = command

        ##  Config.
        self.config = config

        ##  Log.
        self.log = log

        ##  If server_type is 'internal', a Server is created from the WsgiApp.
        self.server = server

        ##  If client_type is 'internal', a Client is created.  Its address
        #   is ('localhost', server_port), the latter taken from the Config.
        self.client = client

        ##  If server_type is 'external', a Wsgi adapter is created.
        self.wsgi = wsgi


    ##  Enter.  Enters the Logger, prints the configuration to the log,
    #   and calls the server's start() method.

    def __enter__ (self):
        self.log.__enter__()
        self.log('config', config_str(self.config, indent=2))
        if self.server is not None:
            self.server.__enter__()
        return self

    ##  Exit.  Calls the server's stop() method and exits the Logger.

    def __exit__ (self, t, v, tb):
        if self.server is not None:
            self.server.__exit__(t,v,tb)
        self.log.__exit__(t,v,tb)

    ##  Can be called from within the app, in desktop mode.

    def set_application_file (self, filename):
        self.command.manager._set_application_file(filename, self.config)


##  A run-time function.

class RTFunction (object):

    ##  Constructor.

    def __init__ (self, rtc):

        ##  The RuntimeContext.
        self.rtc = rtc

        ##  Taken from the rtc's config.  If true, the HTTP headers are included
        #   when a response is pretty-printed.
        self.print_headers = rtc.config.get('print_headers')

        ##  Taken from the rtc's config.  If true, the client handles a Redirect
        #   by issuing a new request; it does so repeatedly until something other
        #   than a Redirect is received.
        self.follow_redirects = rtc.config.get('follow_redirects')

        ##  Taken from the rtc's config.  Whether to print out the request before
        #   passing it to the client for execution.
        self.echo_on = rtc.config.get('echo_on')

    ##  Enter.  Hands off to the rtc's __enter__() method.

    def __enter__ (self):
        self.rtc.__enter__()
        return self

    ##  Exit.  Hands off to the rtc's __exit__() method.

    def __exit__ (self, t, v, tb):
        self.rtc.__exit__(t,v,tb)

    ##  The arguments collected together as a tuple constitute the request.
    #   If self.echo_on, the arguments are printed out.
    #   The client is called on the request to get a response.
    #   Finally, the response is pretty-printed.

    def __call__ (self, *args):
        client = self.rtc.client
        if self.echo_on:
            pprint()
            pprint('------', *args)
        result = client(args, follow_redirects=self.follow_redirects)
        result.pretty_print(header=self.print_headers)
        return result


##  Generic command.

# def com (type, app, config, *args, **kwargs):
# 
#     if type is None or type not in _type_codes:
#         raise Exception('Bad or missing type')
#     code = _type_codes[type]
# 
#     if code == 'C':
#         handler = config
#     elif code == 'I':
#         handler = Installer(config)
#     else:
#         handler = RTFunction(RuntimeContext(code, config))
# 
#     main = _type_coms[type]
#     return main(handler, *args, **kwargs)
# 
# 
# _type_codes = {'direct': 'wNN',
#                'run': 'dIX',
#                'call': 'wII',
#                'open': 'wII',
#                'cgi': 'wXX',
#                'create_cgi': 'I',
#                'set': 'C',
#                'unset': 'C'}
#           
# _type_coms = None


#--  Commands  -----------------------------------------------------------------

# ##  A toplevel command.  Invokes an internal client and internal server.
# #   Webservice mode by default, but can be set to 'desktop' in the configuration.
# 
# def com_call (config, *args, **kwargs):
#     config = parse_config(config, kwargs)
#     rtc = RuntimeContext('wII', config)
#     with RTFunction(rtc) as f:
#         for arg in args:
#             f(arg)
# 
# ##  A toplevel command.  Assumes an external client and external server.
# #   Webservice mode by default.  Creates a RuntimeContext and runs its
# #   wsgi app within a CGIHandler.
# 
# def com_cgi (config, **kwargs):
#     config = parse_config(config, kwargs)
#     rtc = RuntimeContext('wXX', config)
#     with rtc:
#         CGIHandler().run(rtc.wsgi)
# 
# ##  A toplevel command.  Creates an Installer and calls its create_cgi() method.
# 
# def com_create_cgi (config, cgifn=None, **kwargs):
#     config = parse_config(config)
#     Installer(config).create_cgi(cgifn, kwargs)
# 
# ##  A toplevel command.  Just calls the app as a function.  No client or server.
# 
# def com_direct (config, *args, **kwargs):
#     config = parse_config(config, kwargs)
#     rtc = RuntimeContext('wNN', config)
#     with rtc:
#         for arg in args:
#             body = rtc.wsgi(arg, _print_header)
#             for b in body:
#                 stdout.write(b.decode('unicode_escape'))
# 
# ##  A toplevel command.  Invokes an internal client and internal server.
# #   Unlike com_call(), it returns the RTFunction, which can then be used
# #   by the caller to process requests.  The caller should use it in a
# #   with-statement.
# 
# def com_open (config, **kwargs):
#     config = parse_config(config, kwargs)
#     rtc = RuntimeContext('wII', config)
#     return RTFunction(rtc)
# 
# ##  A toplevel command.  Creates an internal server, but assumes an external
# #   client.  Runs in desktop mode by default.  Creates and enters a
# #   RuntimeContext, opens a (standard) web browser window pointed at the
# #   server (localhost:port), and waits for the server's stopped event to get
# #   activated.
# 
# def com_run (config, **kwargs):
#     config = parse_config(config, kwargs)
#     rtc = RuntimeContext('dIX', config)
#     with rtc:
#         webbrowser.open('http://localhost:%d/' % rtc.config['server_port'])
#         rtc.server.stopped.wait()
# 
# 
# _type_coms = {'direct': com_direct,
#               'run': com_run,
#               'call': com_call,
#               'open': com_open,
#               'cgi': com_cgi,
#               'create_cgi': com_create_cgi}


# def direct_call (app, cfg, *args, **kwargs):
#     with _TopLevel('wNN', app, cfg, kwargs) as top:
#         for arg in args:
#             body = top.wsgi(arg, _print_header)
#             for b in body:
#                 stdout.write(b.decode('unicode_escape'))
# 
# def com_run (app, cfg, **kwargs):
#     with _TopLevel('dIX', app, cfg, kwargs) as top:
#         webbrowser.open('http://localhost:%d/' % top.config['server_port'])
#         top.server.stopped.wait()
# 
# def com_call (app, cfg, *args, print_headers=False, follow_redirects=False, **kwargs):
#     with _TopLevel('wII', app, cfg, kwargs) as top:
#         for arg in args:
#             result = top.client(arg, follow_redirects=follow_redirects)
#             result.pretty_print(header=print_headers)



#--  Test app  -----------------------------------------------------------------

##  A test application.  Prints out environmental information.

def test_app (req):
    with StringIO() as f:
        req.print_environment(f)
        return Response(f.getvalue(), code=200, content_type='txt')
    

#--  AuthenticationCommand  ----------------------------------------------------

##  A target for authentication-related commands.

class AuthenticationCommand (Command):

    ##  Open a LocalAuthenticator.

    def get_auth (self):
        afn = self.config['auth_dir']
        if not afn:
            raise Exception('Configuration keyword not set: auth_dir')

        ##  A LocalAuthenticator.
        self.auth = auth = LocalAuthenticator(afn)

        print('Password file:', auth.passwords().filename)
        print('Sessions file:', auth.sessions().filename)
        print()

        return auth

    ##  List users, or print information for a given user.

    def ls (self, user=None):
        auth = self.get_auth()
        if user is None:
            auth.list_users()
        else:
            auth.print_user(user)
    
    ##  Set a password, possibly creating a new user.
    #   Explicit password is FOR TESTING ONLY!
    #   Password of None will prompt user.

    def set (self, user, password=None):
        auth = self.get_auth()
        dir = auth.auth_dir
        if not exists(dir):
            print('Creating', dir)
            makedirs(dir)
        auth.set_password(user, password)
    
    ##  Check the user's password.  Prompts for the password.

    def check (self, user):
        auth = self.get_auth()
        if exists(auth.auth_dir):
            auth.print_check(user)
        else:
            print('Directory does not exist:', auth.auth_dir)

    ##  Delete the given user.

    def delete (self, user):
        auth = self.get_auth()
        if exists(auth.auth_dir):
            auth.delete(user)


#--  CGICommand  ---------------------------------------------------------------

##  A CGI-related Command.

class CGICommand (Command):

    ##  Configuration keys that should not be hard-wired into the CGI script.
    irrelevant_keys = set(['app', 'application_file', 'config_file',
                           'desktop_log_file', 'desktop_logging', 'desktop_user',
                           'execmode', 'log', 'rootprefix', 'server', 'server_port',
                           'webservice_log_file', 'webservice_logging'])

    ##  Create a CGI script.

    def create (self, cgifn, **kwargs):
        cgifn = abspath(expanduser(cgifn))
        mgr = self.manager
        config = self.config

        # The python executable

        python_fn = sys.executable

        # The site directory

        if not seal.__file__.endswith('/seal/__init__.py'):
            raise Exception('Expecting seal.__file__ to end with /seal/__init__.py')
        site_dir = seal.__file__[:-17]

        # The manager class name

        mgr_class_name = mgr.__class__.__name__

        # The manager class module

        mgr_module_qualname = mgr.__class__.__module__

        app_file = config['application_file']

        config = {}
        config.update(self.config)
        config.update(kwargs)
        if not config.get('log_file'):
            fn = config['webservice_log_file']
            if fn: fn = abspath(fn)
            config['log_file'] = fn
        if not config.get('logging'):
            config['logging'] = config['webservice_logging']

        print('Writing', cgifn)

        with open(cgifn, 'w') as f:
            f.write('#!%s\n\n' % python_fn)
            f.write('import site\n')
            f.write("site.addsitedir('%s')\n\n" % site_dir)
            f.write('from %s import %s\n' % (mgr_module_qualname, mgr_class_name))
            f.write('mgr = %s(%s' % (mgr_class_name, repr(app_file)))
            for k in sorted(config):
                if k not in self.irrelevant_keys:
                    v = config[k]
                    if v is not None:
                        f.write(',\n        %s=%s' % (k, repr(v)))
            f.write(')\n')
            f.write('mgr.cgi()\n')

        chmod(cgifn, 0o550)


#--  ConfigCommand  ------------------------------------------------------------

##  A Command that has to do with configuration.

class ConfigCommand (Command):

    ##  Returns a Config that is loaded directly from file.

    def config_file (self):
        return ConfigFile(self.config['config_file'])

    ##  Print out configuration information.
    
    def print_config (self):
        print_config(self.config)

    ##  Set a value.

    def set (self, *settings):
        self.config_file().com_set(*settings)

    ##  Unset keys.

    def unset (self, *keys):
        self.config_file().com_unset(*keys)


#--  MiscCommand  --------------------------------------------------------------

class MiscCommand (Command):

    def create_cert (self, cert_file=None):
        if cert_file is None:
            cert_file = self.config.get('cert_file')
            if cert_file is None:
                raise Exception('No cert file specified')
        create_cert(cert_file)


#--  Manager  ------------------------------------------------------------------

##  An application manager.

class Manager (object):

    ##  Default values for configuration keys.
    
    __defaults__ = dict(application_file = None,
                        auth_dir = None,
                        cgi_file = None,
                        client_type = None,
                        config_file = None,
                        debug_on = False,
                        # used by auth only in desktop mode
                        desktop_log_file = '-',
                        desktop_logging = 'all',
                        desktop_user = '_root_',
                        execmode = None,
                        log_file = None,
                        logging = None,
                        loopback_testing_on = False,
                        rootprefix = '',
                        server_authentication_on = False,
                        server_port = 8000,
                        server_type = None,
                        webservice_log_file = 'log',
                        webservice_logging = 'req,auth,traceback')

    ##  A usage message.
    __usage__ = 'Invoke the application'

    ##  Command methods and syntax.
    #  !  obligatory argument
    #  ?  optional argument; will not accept -FLAG or KEY=VALUE
    #  *  list of remaining arguments
    #  =  list of KEY=VALUE assignments
    #  @  app configuration keyword arguments (KEY=VALUE)
    __commands__ = dict(auth_ls = (AuthenticationCommand, 'ls', '?'),
                        auth_set = (AuthenticationCommand, 'set', '!?'),
                        auth_check = (AuthenticationCommand, 'check', '!'),
                        auth_delete = (AuthenticationCommand, 'delete', '!'),
                        call = (RuntimeCommand, 'call', '*'),
                        cfg = (ConfigCommand, 'print_config', ''),
                        cgi = (RuntimeCommand, 'cgi', ''),
                        config = (ConfigCommand, 'print_config', ''),
                        # an omitted cgifn will be supplied from .seal, but that may be going away
                        create_cgi = (CGICommand, 'create', '?@'),
                        direct = (RuntimeCommand, 'direct', '*'),
                        open = (RuntimeCommand, 'open', ''),
                        run = (RuntimeCommand, 'run', ''),
                        serve = (RuntimeCommand, 'serve', ''),
                        set = (ConfigCommand, 'set', '='),
                        unset = (ConfigCommand, 'unset', '*'))

    ##  Flags accepted; each is shorthand for a keyword argument.
    __flags__ = {'-u': ('desktop_user',),
                 '-M': ('media_dir',),
                 '-p': ('server_port'),
                 '-w': (('execmode', 'webserver'),
                        ('log_file', '-'),
                        ('logging', 'all'),
                        ('loopback_testing_on', 'True')),
                 '-A': ('auth_dir',)}

    @classmethod
    def __main__ (self, argv):
        (cmd, args, kwargs) = self.__parse__(argv)
        return cmd(*args, **kwargs)

    @classmethod
    def _items (self, shift):
        while True:
            arg = shift.peek()
            if arg is None:
                break
            elif '=' in arg:
                shift()
                yield arg.split('=')
            elif arg.startswith('-'):
                shift()
                if arg not in self.__flags__:
                    raise Exception('Unrecognized flag: %s' % arg)
                specs = self.__flags__[arg]
                if isinstance(specs[-1], str):
                    v = shift()
                else:
                    v = True
                yield (arg, v)
            else:
                break

    @classmethod
    def _dict (self, shift):
        return dict(self._items(shift))

    ##  Convert an argv into a Command.

    @classmethod
    def __parse__ (self, args):

        with Shift(args) as shift:
        
            shift.set_usage(self.__usage__)
            
            # config and command
            subject = command = None

            if not shift.isdone():
                arg = shift.peek()
                if not (arg.startswith('-') or '=' in arg) and '.' in arg:
                    subject = shift()

            settings = dict(self._items(shift))

            if shift.isdone():
                command = 'run'
            else:
                command = shift()

            if command == 'help':
                return (UsageCommand(shift), tuple(), {})
            elif command not in self.__commands__:
                shift.error('Unrecognized command: %s' % repr(command))

            (cls, method_name, argnames) = self.__commands__[command]

            # args and kwargs
            args = []
            kwargs = {}

            for c in argnames:
                if c == '!':
                    if shift.able():
                        arg = shift()
                        if (arg.startswith('-') and arg != '-') or '=' in arg:
                            shift.error('Flag or keyword, expecting required argument: %s' % arg)
                        args.append(arg)
                    else:
                        shift.error('Missing obligatory argument: %s %s' % (command, argnames))
                elif c == '?':
                    arg = shift.peek()
                    if arg and not arg.startswith('-') and '=' not in arg:
                        args.append(shift())
                elif c == '=':
                    args.extend(self._items(shift))
                elif c == '@':
                    kwargs.update(self._items(shift))
                elif c == '*':
                    args.extend(shift.rest())
                else:
                    shift.error('Bad argument spec: %s' % repr(c))
    
            # Create the Command
            mgr = self(subject, **settings)
            return (cls(mgr, method_name), args, kwargs)


    ##  Constructor.

    def __init__ (self, _subject=None, _config=None, **kwargs):

        # Created by parsing a command line
        if _config is None:
            cfg = dict(self.__defaults__)

            # 'config_file' and 'application_file' are reserved keys
            for k in ('config_file', 'application_file'):
                if cfg.get(k) or kwargs.get(k):
                    raise Exception('Illegal key: %s' % repr(k))

            self._set_application_file(_subject, cfg, kwargs)

        # Created by cloning an old manager
        else:
            assert _subject is None
            cfg = dict(_config)
            cfg.update(kwargs)
            standardize_config(cfg)

        self.__subject__ = cfg['application_file'] # standardization absolutizes path
        self.__config__ = cfg

    ##  Load config file.

    def _set_application_file (self, subject, cfg, kwargs=None):

        # Maybe load subject config file
        cfn = None
        if subject:
            cfn = self.__configfile__(subject)
            if cfn is not None and exists(cfn):
                for (k,v) in load_dict(cfn).items():
                    if k in ('config_file', 'application_file'):
                        raise Exception('Illegal key: %s' % repr(k))
                    cfg[k] = v

        # Install any keyword args
        if kwargs:
            cfg.update(kwargs)

        cfg['config_file'] = cfn
        cfg['application_file'] = subject

        standardize_config(cfg)

    ##  Clone.

    def __call__ (self, **kwargs):
        return self.__class__(_config=self.__config__,
                              **kwargs)

    ##  Get the config file name.  Called by __init__.

    def __configfile__ (self, subject):
        if subject.endswith('.cfg'):
            return subject
        else:
            return join(subject, '_config')

    ##  Returns a command instance.

    def __getattr__ (self, com):
        if com in self.__commands__:
            (cls, methname, _) = self.__commands__[com]
            return cls(self, methname)
