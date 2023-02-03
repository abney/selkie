##  @package seal.app.core
#   The main entry point for the generic Seal web application.
#

import traceback, sys, os, io, random, _thread, webbrowser
from datetime import datetime
from io import StringIO
from time import asctime
from wsgiref.handlers import CGIHandler
from os.path import expanduser, exists

import seal
from seal.core.misc import import_class
from seal.core.io import data, pprint, PPrinter, split_suffix, abspath, load_dict, save_dict
from seal.app.auth import Authenticator
from seal.app.parse import parse_config, cookie_log_string
from seal.app.config import Config
#from seal.app.request import request_from_string
from seal.app.item import RawFile, Text, HttpException, HttpSystemError
from seal.app.server import Server
from seal.app.weblib import scripts
from seal.app.client import call_app


#--  ~/.cld file  --------------------------------------------------------------

# def desktop_config_filename ():
#     return expanduser('~/.cld')
# 
# def load_desktop_config ():
#     cfn = desktop_config_filename()
#     if exists(cfn):
#         return load_dict(cfn)
#     else:
#         return {}
# 
# def save_desktop_config (**kwargs):
#     cfn = expanduser('~/.cld')
#     if exists(cfn):
#         cfg = load_dict(cfn)
#     else:
#         cfg = {}
#     cfg.update(kwargs)
#     save_dict(cfg, cfn)


#--  App function  -------------------------------------------------------------

##  The class SealApp behaves like a Seal application function.
#   Call it on a Request.  The resulting SealApp instance behaves like a
#   Response, dispatching calls to http_status(), http_headers(), and body()
#   to the actual Response.

class SealApp (object):

    ##  Call the application function.

    def __init__ (self, request):

        ##  The context is the request being processed.
        #   N.b., the application may make destructive changes to the request.
        #   Its file and root members may get set, and its cookie may get updated.

        self.context = request

        ##  A logging function; taken from the request.

        self.log = request.log

        ##  The configuration; taken from the request.

        self.config = request.config

        ##  The response; the SealApp instance dispatches to it.

        self._response = None

        ##  Whether the request has been executed or not.

        self._executed = False


    ##  Return the response, executing if necessary.

    def response (self):
        if not self._executed:
            self.run()
        return self._response


    ##  Call the handler.
    #
    #    - The key 'application_file' is accessed to get the application file name,
    #      and that is passed to open_file() to get the application file.
    #    - The application file is stored in context.file.
    #    - The first component of the path is passed to make_root() to create
    #      the root web directory.  It is stored in context.root.
    #    - A descent is done through the remainder of the path, passing each
    #      component in turn to the current web directory to get the next one.
    #      The final result should have a page() method that returns a web page.
    #
    #   If the Request path starts with '.', it is handled specially.  .lib and
    #   .debug are currently recognized.

    def run (self):
        request = self.context
        self._response = None
        try:
            self.log('req', '[%s]' % asctime(), ('HTTP','HTTPS')[request.https_on()], repr(request))
            with self.log.indent():
                request.authenticate()
                self.log('config', request.runtime_configuration())
                item = self.follow()
                if hasattr(item, 'to_page'):
                    orig = item
                    item = orig.to_page()
                    if item is not orig:
                        self.log('path', repr(orig), 'to_page ->', repr(item))
            if not is_page(item):
                raise Exception('Not a web page: %s' % repr(item))
        except HttpException as e:
            item = e
    
        # This needs the context for the sake of the cookie
        # We can't depend on the item containing the context: it might be
        # a Text or Redirect
        self._response = rsp = item.to_response(request)
        self._executed = True
        self.log('resp', repr(rsp), cookie_log_string(rsp.authenticator.cookie))

    ##  Duck-type Response method.

    def http_status (self):
        return self.response().http_status()

    ##  Duck-type Response method.

    def http_headers (self):
        return self.response().http_headers()

    ##  Duck-type Response method.

    def body (self):
        return self.response().body()

    ##  Duck-type Reponse method.

    def __str__ (self):
        return self.response().__str__()


    ##  When called on a Request, this is called to open and return the application
    #   file.  Specializations may override.  The default implementation is a no-op.

    def open_file (self, filename):
        pass

    ##  When called on a Request, this is called to create the root web directory.
    #   Specializations may override.  The default implementation is a no-op.

    def make_root (self, cpt):
        pass

    ##  Can be called for testing.  It is also called by run(), which is called
    #   in response().

    def follow (self):
        path = self.context.path
        if len(path) > 1 and path[1].startswith('.'):
            return self._handle_special_request(path[1], path[2:])
        else:
            fn = self.config.get('application_file')
            if fn:
                file = self.open_file(fn)
                self.context.file = file
            item = self.make_root(path[0])
            self.context.root = item
    
            for pathcpt in path[1:]:
                item = self._next(item, pathcpt)
    
            return item

    def _next (self, item, pathcpt):
        parent = item
        try:
            item = parent[pathcpt]
            self.log('path', repr(parent), repr(pathcpt), '->', repr(item))
            if item is None:
                self.log('error', 'getitem returns None', repr(parent), repr(pathcpt))
                raise Exception('__getitem__ returns None')
        except HttpException as e:
            self.log('path', repr(parent), repr(pathcpt), '->', repr(e))
            raise e
        except Exception as e:
            self.log('error', 'Exception', repr(parent), repr(pathcpt), e)
            self.log('traceback')
            raise HttpSystemError()
        return item
    
    def _handle_special_request (self, name, rest):
        if name == '.lib':
            return self._handle_lib_request(rest)
        elif name == '.debug':
            return self._handle_debug_request(rest)
        else:
            raise HttpException('Unrecognized special request: %s' % name)
    
    def _handle_lib_request (self, rest):
        if len(rest) != 1:
            raise HttpException('Bad lib request: %s' % self.context.path)
        name = rest[0]
        if not name:
            self.log('path', '.lib', 'No lib file name given')
            raise HttpException('No lib file name given')
        page = self.load_lib_file(name)
        if page is None:
            self.log('path', 'Lib file not found:', name)
            raise PageNotFound(name)
        else:
            self.log('path', 'Lib file', repr(name), '->', repr(page))
            return page
    
    # Returns PageNotFound unless debugging is enabled
    def _handle_debug_request (self, rest):
        request = self.context
        if not self.config['debug_on']:
            raise PageNotFound(request.path)
        if len(rest) != 1:
            raise HttpException('Bad debug request')
        name = rest[0]
        if name == 'environ':
            webenv = request.webenv
            if webenv is None:
                s = '(no CGI environment)'
            else:
                s = '\n'.join(k + ' ' + repr(v) for (k,v) in webenv.items())
            return Text(s)
        # elif name == 'set_cookie':
        #     request.cookie['foo'] = 'bar'
        #     request['user'] = 'joe'
        #     return Text('OK', context=self.context)
        # elif cpt == 'unset_cookie':
        #     request.cookie['foo'] = ''
        #     request.cookie['user'] = ''
        #     return Text('OK', context=self.context)
        else:
            return HttpException("Unrecognized debug command: %s" % name)
    
    ##  Load a lib file; used when handling a .lib request.
    #
    #   .css, .js
    #   implements "import foo"
    #   Scripts must reside in data/seal
    #
    #   This is a method (not a function)
    #   for the benefit of an App specialization that wants to override it.
    #
    #   If lib_file_pathname() returns a boolean false value, the scripts
    #   table (from seal.app.weblib) is used, in the case of a name ending in
    #   .css or .js; otherwise the data.seal directory is assumed.
    
    def load_lib_file (self, name):
        key = split_suffix(name)
        suffix = key[1]
        fn = self.lib_file_pathname(name)
        if suffix in ('css', 'js'):
            if fn:
                with open(abspath(fn)) as f:
                    contents = f.read()
                return Text(contents, suffix=suffix)
            elif key in scripts:
                return Text(scripts[key].contents(), suffix=suffix)
        else:
            if fn:
                return RawFile(fn)
            else:
                filename = os.path.join(data.seal, name)
                if os.path.exists(filename):
                    return RawFile(filename)
    
    ##  Returns a lib file pathname, given a logical file name.
    #   Specializations may override.  The default is a no-op.

    def lib_file_pathname (self, fn):
        return None


#--  is_page  ------------------------------------------------------------------

##  Returns true just in case x looks like a web page.  Specifically:
#    - It is iterable.
#    - It has a response_code member.
#    - If its response_code is 303, it has a uri member.
#    - If its response_code is not 303, it has a content_type member.

def is_page (x):
    return ( hasattr(x, '__iter__') and
             hasattr(x, 'response_code') and
             ( (x.response_code == 303 and hasattr(x, 'uri')) or
               (x.response_code != 303 and hasattr(x, 'content_type')) ) )

