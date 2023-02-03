##  @package seal.app.item
#   The Item class and its specializations.

import io
from seal.core.io import Fn, outfile, null, srepr
from seal.app.env import Pathname
from seal.app.request import URLPathComponent
from seal.app.response import Response
from seal.app.wsgi import ResponseMessages


#--  Item  ---------------------------------------------------------------------

##  The root class for web directories, web pages, and page elements.

class Item (object):

    ##  A dict in which values are either strings (interpreted as method names)
    #   or Items (specifically, widgets).

    __pages__ = None

    ##  The home page name.

    __home__ = 'home'

    ##  Constructor.

    def __init__ (self, parent=None, file=None, cpt=None, context=None):

        ##  The parent web directory or page or element.
        self.parent = None

        ##  The pathname component associated with this item.
        #   The root's component is the root prefix if it exists, else None.
        self.cpt = None

        ##  The file associated with this item, if any.
        self.file = None

        ##  The context, inherited ultimately from the App.
        self.context = None

        ##  The next pathname component in line.
        self.childcpt = None

        if parent is not None:
            if not isinstance(parent, Item):
                raise Exception('Parent argument to Item must be an Item: %s' % repr(parent))
            self.parent = parent
            self.cpt = parent.childcpt
            self.file = parent.file
            self.context = parent.context

        if cpt is not None:
            if not isinstance(cpt, URLPathComponent):
                raise Exception('Not a URLPathComponent: %s' % repr(cpt))
            self.cpt = cpt

        if file is not None:
            self.file = file

        if context is not None:
            self.context = context

    ##  Conditionally print a logging message.

    def log (self, *args): self.context.log(*args)

    ##  Unconditionally print.

    def debug (self, *args): self.context.log(True, *args)

    ##  String representation.

    def __repr__ (self):
        if self.cpt:
            return '<%s %s>' % (self.__class__.__name__, self.cpt)
        else:
            return '<%s>' % self.__class__.__name__

    ##  Convert this item to a page.  The default implementation signals an error;
    #   the Page class overrides it.

    def to_page (self):
        self.log('path', 'RAISE Not a Page')
        raise Exception('Not a Page: %s' % self)

    ##  Returns a list of ancestors, from the root down.

    def __ancestors__ (self):
        rancs = []
        anc = self
        while anc is not None:
            rancs.append(anc)
            anc = anc.parent
        return reversed(rancs)

    ##  Works upward until it finds a Page or HtmlDirectory.  Returns self
    #   if self is a Page or HtmlDirectory.

    def __page__ (self):
        item = self
        while True:
            if item is None:
                raise Exception('No page!')
            if isinstance(item, (Page, HtmlDirectory)):
                return item
            item = item.parent

    ##  Works upward until it finds an HtmlDirectory.

    def __directory__ (self):
        item = self
        while True:
            if item is None:
                raise Exception('No directory!')
            if isinstance(item, HtmlDirectory):
                return item
            item = item.parent

    ##  Returns the user name from the context.

    def __user__ (self):
        return self.context.username

    ##  Invokes the server's quit() method.  The server is found in the context.

    def __quit__ (self):
        self.context.server.quit()

    ##  Returns an externalized version of a file name.
    #   Called with no arguments, returns the pathname of its cpt.

    def __extern__ (self, s=None):
        if s is None:
            return self.__page__().cpt.pathname
        elif isinstance(s, Pathname):
            return s
        # context is None if this is e.g. an HtmlPage created without a parent
        if self.context is not None:
            return self.context.extern(s)
        else:
            return Pathname(s)

    ##  Returns the child named by a given pathcpt.
    #    - If the name is the empty string, return a Redirect to the __home__
    #      child.
    #    - Get the value from the __pages__ dict.
    #    - If it is an Item, return it.
    #    - Otherwise, it is a method name.  Fetch the named method.
    #    - Set childcpt to the pathcpt.
    #    - Invoke the method on the args and kwargs from the pathcpt.call.
    #    - Unset childcpt.
    #    - Raise an exception if the method did not return anything.
    #    - Raise an exception if the name is the home name, and a directory
    #      was returned.
    #    - Otherwise, return what the method returned.

    def __getitem__ (self, pathcpt):
        name = pathcpt.call[0]
        if name == '':
            return Redirect(pathcpt.pathname + self.__home__)
        if not hasattr(self, '__pages__') or self.__pages__ is None:
            value = None
        else:
            value = self.__pages__.get(name)
        if value is None:
            self.log('path', 'ERROR: Page not found: %s in %s' % (repr(name), repr(self)))
            raise PageNotFound('%s in %s' % (repr(pathcpt), repr(self)))
        elif isinstance(value, Item):
            # a widget
            return value
        elif not hasattr(self, value):
            raise Exception('Dispatch method not defined: %s' % repr(value))
        else:
            methodname = value
            method = getattr(self, methodname)
            if self.childcpt is not None:
                raise Exception('Re-using parent')
            self.childcpt = pathcpt
            (_, args, kwargs) = pathcpt.call
            item = method(*args, **kwargs)
            self.childcpt = None
            if item is None:
                raise Exception('Page method returns None: item=%s, method=%s' % (
                        repr(self),
                        repr(methodname)))
            elif name == self.__home__ and isinstance(item, HtmlDirectory):
                raise Exception('home method returns a directory')
            return item


##  A web directory.

class HtmlDirectory (Item):

    ##  Overrides the default.  This is not a page, but can be coerced to
    #   a page, namely, a Redirect to its __home__ page.

    def to_page (self):
        self.log('path', 'RETURN Redirect: path terminates in a directory')
        pathname = self.cpt.pathname
        if not pathname.endswith('/'): pathname += '/'
        return Redirect(pathname + self.__home__)


##  A web page.

class Page (Item):

    ##  The HTTP response code.
    response_code = 200

    ##  The content type.
    content_type = None

    ##  Returns self.

    def to_page (self): return self

    ##  Must be overridden to provide page contents.  Default implementation
    #   signals an error.

    def __iter__ (self):
        raise Exception('Class must be subclassed; override __iter__')

    ##  String representation.

    def __str__ (self):
        return self.to_response(self.context).__str__()

    ##  Calls to_response(), providing the context, then calls the response's
    #   to_string() method, providing the headers flag.

    def to_string (self, headers=True):
        return self.to_response(self.context).to_string(headers=headers)

    ##  Convert to a Response instance.
    #   Response code, content_type, and contents come from this Page.
    #   Cookie comes from the request.

    def to_response (self, request=None, location=None):
        if location is None:
            content_type = self.content_type
            contents = self
        else:
            content_type = None
            contents = None
        if request is None:
            auth = None
        else:
            auth = request.authenticator

        return Response(code=self.response_code,
                        content_type=content_type,
                        contents=contents,
                        location=location,
                        authenticator=auth)


#--  Pages  --------------------------------------------------------------------
#
#  The Page class is also used by seal.server.
#
#  A UIObject is any object that represents the contents of a File.
#  Subtypes include seal.ui.HtmlDirectory and seal.ui.Element.
#

# class Page (Requestable):
# 
#     response_code = 200
#     content_type = None
# 
#     def __dispatch__ (self, key):
#         if not isinstance(key, str):
#             raise HttpUserError('Bad request, page %s does not handle request %s' % (self.__upc__.pathname, key))
#         if self.__handlers__ is None:
#             self.log('path', 'ERROR: page has no handlers')
#             raise HttpUserError("Bad request, page %s does not permit ';'" % self.__upc__.pathname)
#         item = self.__handlers__.get(key)
#         if item is None:
#             self.log('path', 'ERROR: no such handler')
#             raise HttpUserError('No handler named %s' % key)
#         return item
# 
#     def __iter__ (self):
#         raise Exception('Class must be subclassed; override __iter__')
# 
#     # Solely for debugging
# 
#     def __str__ (self):
#         return Response(self).__str__()


##  A file that is not HTML.
#   If mime type is not explicitly provided, it is taken from suffix
#   If no suffix, defaults to 'txt'

class RawFile (Page):

    ##  Constructor.

    def __init__ (self, fn, type=None):
        Page.__init__(self, None)

        ##  The filename.
        self.filename = Fn(fn)

        ##  Overrides content_type.
        self.content_type = type

        if type is None:
            i = fn.rindex('.')
            if i > 0:
                self.content_type = fn[i+1:].lower()
            else:
                self.content_type = 'txt'

    ##  Iterates over byte-like objects, reading 1024 bytes at a time.

    def __iter__ (self):
        with open(self.filename, "rb") as f:
            while True:
                bs = f.read(1024)
                if not bs: break
                yield bs

##  An in-memory binary file.

class Data (Page, io.IOBase):

    ##  Constructor.

    def __init__ (self, parent, type):
        Page.__init__(self, parent)

        ##  Overrides content_type.
        self.content_type = type

        ##  Contents is a list of byte-like objects.
        self.contents = []

    ##  Iterates over the contents list.

    def __iter__ (self): return self.contents.__iter__()
    
    ##  Adds data to the contents.  Data must be bytes or bytearray.

    def write (self, data):
        assert isinstance(data, (bytes, bytearray))
        self.contents.append(data)


# def nonascii (c):
#     n = ord(c)
#     return n > 127 or (n < 32 and n != '\n' and n != '\r')
# 
# def htmlencode (s):
#     if any(nonascii(c) for c in s):
#         out = StringIO()
#         for c in s:
#             n = ord(c)
#             if n > 127: out.write('&#%d;' % n)
#             elif n >= 32: out.write(c)
#             elif c in '\r\n': out.write(c)
#             else: raise Exception('Encountered control character: ' + hex(n))
#         v = out.getvalue()
#         out.close()
#         return v
#     else:
#         return s


##  Plain text.
#   This is typically used for an Ajax response.
#   Suffix is .txt by default, but could be e.g. .css or .js.

class Text (Page):

    ##  Constructor.

    def __init__ (self, contents=None, suffix='txt', context=None):
        Page.__init__(self, context=context)

        ##  Overrides Page.
        self.content_type = suffix
        
        ##  List of contents.
        self.contents = []

        if contents is None:
            pass
        elif isinstance(contents, str):
            self.write(contents)
        else:
            for x in contents:
                self.write(x)

    ##  Add a string, bytes, or bytearray to the contents.
    #   Simply hands off to write().

    def add (self, s):
        self.write(s)

    ##  Add a string or bytes or bytearray to the contents.

    def write (self, s):
        if isinstance(s, (str, bytes, bytearray)):
            self.contents.append(s)
        else:
            raise Exception('Attempt to add non-text %s to %s' % (repr(s), repr(self)))

    ##  Iterate over the contents list.

    def __iter__ (self):
        return self.contents.__iter__()

    ##  String representation.

    def __repr__ (self):
        return '<Text %s>' % self.content_type


##  A redirect.

class Redirect (Page):

    ##  Response code for a redirect.
    response_code = 303

    ##  Constructor.

    def __init__ (self, uri):
        Page.__init__(self, None)
        if uri is None: uri = '/'

        ##  The URI to redirect to.
        self.uri = uri

    ##  Returns self.
    def __iter__ (self): return self

    ##  Immediately raises StopIteration: empty contents.
    def __next__ (self): raise StopIteration

    ##  String representation.
    def __repr__ (self): return '<Redirect %s>' % repr(self.uri)

    ##  Calls Page.to_response() with location set to self.uri.

    def to_response (self, request=None):
        return Page.to_response(self, request=request, location=self.uri)


##  An HTTP exception.

class HttpException (Exception, Page):

    ##  Overrides Item.
    response_code = 400

    ##  Overrides Item.
    content_type = 'txt'

    ##  Constructor.
    def __init__ (self, msg=''):
        Exception.__init__(self, msg)
        Page.__init__(self)

    ##  Body is just the response code and a text rendering of it.

    def __iter__ (self):
        yield '%d %s\n' % (self.response_code, ResponseMessages[self.response_code])
        yield str(self) + '\n'


##  Permission denied.

class PermissionDenied (HttpException):

    ##  Response code for 'permission denied'.

    response_code = 401


##  Page not found.

class PageNotFound (HttpException):

    ##  Response code for 'page not found'.

    response_code = 404


##  HTTP user error.  Used when the request is ill-formed.

class HttpUserError (HttpException): pass


##  HTTP system error.  Used when an unexpected exception happens when processing
#   the request.

class HttpSystemError (HttpException):

    ##  Response code for a generic system error.

    response_code = 500


