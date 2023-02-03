##  @package seal.app.ui
#   Provides user interface components for use in defining HtmlDirectory
#   specializations.

import os, traceback
from io import StringIO
from inspect import getargspec
from seal.core.io import data, get_suffix
from seal.core.misc import trim, check_type
from seal.nlp.rom import Romanization
from seal.app.weblib import ScriptList
from seal.app.env import Pathname
from seal.app.request import Request
from seal.app.item import (Item, HtmlDirectory, HttpException, HttpSystemError,
                           HttpUserError, Page, PageNotFound, RawFile,
                           Redirect, Text)


#--  String Encoding  ----------------------------------------------------------

##  Encodes an arbitrary string as a sequence of hexadecimal digits,
#   e.g. for inclusion in a pathname.  It is used in seal.cld.ui.

def hex_encode (s):
    return s.encode('utf8').hex()

##  The inverse of hex_encode().

def hex_decode (s):
    return bytes.fromhex(s).decode('utf8')

_html_value_subs = {'&': '&amp;', '"': '&quot;'}

##  Used for HTML attribute values.
#   One does two substitutions: ampersands and double-quotes get replaced
#   with the corresponding HTML entities.
#   See escape() for a more aggressive set of substitutions.
#   See attvalue_quoted() for an even less aggressive version.

def html_value_encode (s):
    out = []
    i = 0
    n = len(s)
    while i < n:
        j = i
        while j < n and s[j] not in '&"': j += 1
        if i == 0 and j == n: return s
        if j > i: out.append(s[i:j])
        if j < n: out.append(_html_value_subs[s[j]])
        i = j+1
    return ''.join(out)
        

#--  HtmlPage  -----------------------------------------------------------------
#
#  Live Elements
#
#  A 'live' Element is associated with a script, and the script may place
#  callbacks to the element.  The Element has three relevant members:
#
#      __script__    the name of the script
#      __name__      the name of the element
#      __pages__     like for an HtmlDirectory; it maps page to method names
#
#  Suppose '/dir1/page1' reaches an HtmlPage that contains a live Element whose
#  __name__ is 'elt1'.  The HtmlPage collects the script name __script__, and
#  at the end of the body, it inserts the contents for all scripts encountered,
#  along with scripts they include.
#
#  The script for element 'elt1' may place callbacks.  The callback URLs should
#  begin 'page1:elt1:'.  For example, a callback may be placed to
#  'page1:elt1:baz.42'.
#
#  The browser generates a POST request to '/dir1/page1:elt1:baz.42'.
#
#  Browsers do not treat the colons specially, but the HtmlDirectory dispatching
#  code strips off everything after the first colon as the callback specifier.
#  It looks up the page 'dir1/page1'.  That regenerates the relevant Element.
#  When HtmlPage adds the element, it places it in the table __callback_handlers__
#  under the key 'elt1' (its __name__).
#
#  The HtmlDirectory dispatching code arrives at the page, at the end of
#  processing the URL.  Since there is a callback specifier, it looks up a
#  handler in the __callback_handlers__ table, getting the element.  It then
#  treats the element as if it were an HtmlDirectory: it looks up 'baz' in
#  the __pages__ table and calls the corresponding method with argument '42'.
#  The return value replaces page1.
#

##  A specialization of Page that allows one to build up a page from elements.

class HtmlPage (Page):

    ##  Overrides Page.
    content_type = 'html'

    ##  Constructor.  If stylesheet is provided, it is passed to add_stylesheet().
    #   If src is provided, it should be a filename; the file is read and
    #   the file contents are added as a string to self.contents.

    def __init__ (self, parent, title='Untitled', src=None, stylesheet='default'):

        ##  The page title.
        self.title = title # __repr__ depends on it
        Page.__init__(self, parent)

        self._stylesheets = ScriptList('css')
        self._styles = []
        self._script_inits = []
        self._script_imports = ScriptList('js')
        #self._head = []
        self._body_attributes = []
        self._listeners = []
        self._focus = None
        self._contents = []

        if stylesheet:
            self.add_stylesheet(stylesheet)

        if src:
            with open(src) as f:
                self.add(file.read())

    ##  Add a widget to the page.
    #   This does not add it to the contents.  Rather, it installs it in the
    #   __pages__ table.

    def add_widget (self, widget):
        name = widget.cpt
        if not name: raise Exception('Widget must have cpt')
        if self.__pages__ is None:
            self.__pages__ = {}
        elif self.__pages__ is self.__class__.__pages__:
            self.__pages__ = dict(self.__class__.__pages__)
        if name in self.__pages__:
            raise Exception('Page is already defined: %s in %s' % (name, self))
        self.__pages__[name] = widget

    ##  Add a known stylesheet.

    def add_stylesheet (self, name):
        if name not in self._stylesheets:
            self._stylesheets.append(name)

    ##  Add a known style.

    def add_style (self, name):
        if name not in self._styles:
            self._styles.append(name)

    ##  Add an initialization script, to be run when the page has loaded.

    def add_script (self, script):
        self._script_inits.append(script)

    ##  Add a known script, to be imported in the header.

    def add_import (self, name):
        if name not in self._script_imports:
            self._script_imports.append(name)

    ##  Set an attribute of the body.

    def add_body_attribute (self, att, value):
        self._body_attributes.append(att + '=' + repr(value))

    ##  After the page has loaded, put focus on the element with the given ID.

    def focus (self, htmlid):
        self._focus = htmlid

    ##  The HTML page.  Specifically, the following sequence is produced.
    #
    #    - Open HTML, open the head.
    #    - The title, escaped.
    #    - Pass through the stylesheets and all their dependents, ordered
    #      to put dependents first.  For each add a link to the stylesheet.
    #    - For each named style, include the contents of the named file,
    #      wrapped in a style element.
    #    - Close the head and begin the body.  Include the body attributes.
    #    - Iterate through self.contents.  Pass each to iterhtml() to get
    #      the actual strings.
    #    - If there are initialization scripts or focus is set, start a script.
    #      If focus is set, add a javascript statement to execute the focus
    #      change.  If there are initialization scripts, include their contents.
    #      Close the script.
    #    - Close the body, close HTML.

    def __iter__ (self):
        yield "<html>\r\n"
        yield "<head>\r\n"
        yield "<title>%s</title>\r\n" % escape(self.title)
        for ss in self._stylesheets.dependencies():
            fn = self.__extern__('/.lib/%s.css' % ss.name())
            yield '<link rel="stylesheet" type="text/css" href="%s" />\r\n' % fn
        for name in self._styles:
            yield '<style type="text/css">\r\n'
            for s in script_contents(name, '.css'):
                yield s
            yield '</style>\r\n'
        for s in self._script_imports.dependencies():
            yield '<script type="text/javascript" src="%s" defer></script>\n' % self.__extern__('/.lib/%s.js' % s.name())
        # for string in self._head:
        #     yield string
        yield "</head>\r\n"
        atts = ' '.join(self._body_attributes)
        if atts: atts = ' ' + atts
        yield "<body%s>\r\n" % atts
        for elt in self._contents:
            for s in iterhtml(elt):
                yield s
        if self._focus or self._script_inits:
            yield '<script>\r\n'
            yield 'window.onload = function () {\r\n'
            if self._focus:
                yield '  document.getElementById("%s").focus()\r\n' % self._focus
            for script in self._script_inits:
                for elt in script.script:
                    for s in text_strings(elt):
                        yield '  '
                        yield s
            yield '};\r\n'
            yield '</script>\r\n'
        yield '</body>\r\n'
        yield '</html>\r\n'

    ##  Add an element.  Raise an exception if it is not renderable.

    def add (self, elt):
        assert is_renderable(elt)
        self._contents.append(elt)

    ##  Convert the string using HTML() and add it to the contents.

    def write (self, s):
        self._contents.append(HTML(s))

    ##  String representation.

    def __repr__ (self):
        return '<HtmlPage %s>' % repr(self.title)


#--  script_contents  ----------------------------------------------------------

##  This is used when including the contents of a CSS file in the head.
#   It iterates over the lines of the named file.  Script may also be a list
#   of names.

def script_contents (script, type):
    state = {}
    if isinstance(script, str):
        for s in _import_script(script, type, state):
            yield s
    else:
        for name in script:
            for s in _import_script(name, type, state):
                yield s

def _import_script (name, type, state):
    key = name + type
    status = state.get(key)
    if status != 'done':
        if status == 'doing':
            raise Exception('Script cycle detected: %s %s' % (key, state))
        state[key] = 'doing'
        fn = os.path.join(data.seal, key)
        (to_import, n_header_lines) = _script_header(fn)
        for impname in to_import:
            for s in _import_script(impname, type, state):
                yield s
        yield _script_body(fn, n_header_lines)
        state[key] = 'done'

def _script_header (fn):
    n = 0
    to_import = []
    with open(fn) as f:
        for line in f:
            if line.startswith('import '):
                names = line[7:].split(',')
                for name in names:
                    to_import.append(name.strip())
            elif line.strip(): break
            n += 1
    return (to_import, n)

def _script_body (fn, n):
    with open(fn) as f:
        while n > 0:
            next(f)
            n -= 1
        return f.read()


#--  Content Items  ------------------------------------------------------------

##  A specialization of str that is used to flag a string as belonging to the
#   HTML markup.  Unlike regular strings, HTML markup will NOT be escaped
#   by iterhtml().

class HTML (str):
    pass

##  A pseudo-element that is just a literal string.

def String (parent, s):
    parent.add(s)
    return s

##  Escape a string to make it render literally when included in an HTML page.
#   The characters ampersand, less than, greater than, and double quote are
#   replaced with the corresponding HTML entities.  Regular ASCII characters
#   (printable characters, space, tab, carriage return, newline) are passed
#   through.  All other characters (other control characters, non-ASCII characters)
#   are converted to HTML character-code entities.

def escape (s):
    out = StringIO()
    for c in s:
        if c == '&': out.write('&amp;')
        elif c == '<': out.write('&lt;')
        elif c == '>': out.write('&gt;')
        elif c == '"': out.write('&quot;') # in case this is an attribute value
        else:
            n = ord(c)
            if n > 127: out.write('&#%d;' % n)
            elif n >= 32: out.write(c)
            elif c in '\t\r\n': out.write(c)
            else: raise Exception('Encountered control character: ' + hex(n))
    s = HTML(out.getvalue())
    out.close()
    return s


# def render (x, http=None):
#     if http is None: http = PseudoConnection()
#     if x is None:
#         pass
#     elif isinstance(x, Element):
#         x.render(http)
#     elif isinstance(x, list) or isinstance(x, tuple):
#         for c in x:
#             render(c, http)
#     elif isinstance(x, basestring):
#         http.write(escape(x))
#     else:
#         raise Exception, "Not renderable: " + str(x)

##  The things that qualify as renderable are None, strings, bytes, bytearrays,
#   Elements, Spacers, and lists or tuples of renderable things.

def is_renderable (x):
    return (x is None or
            isinstance(x, (str, bytes, bytearray, Element, Spacer)) or
            (isinstance(x, (list, tuple)) and
             all(is_renderable(e) for e in x)))

# renderable: None, str (Pathname, HTML), bytes, bytesarray, Element, Spacer,
#     or list/tuple of renderables

##  Iterates over the strings contained in x.
#
#    - If x is a string, it is passed to escape() before being yielded.
#    - If x is an instance of bytes, bytearray, Pathname, or HTML, it is passed
#      through as is.
#    - If x is a Spacer, then x.html is yielded.
#    - If x is an Element, list, or tuple, then iterhtml() is called
#      recursively on its members.
#    - Anything else causes an error to be signalled.
#

def iterhtml (x):
    if x is None:
        pass
    elif isinstance(x, (Element, list, tuple)):
        for c in x:
            for s in iterhtml(c):
                yield s
    elif isinstance(x, (Pathname, HTML, bytes, bytearray)):
        yield x
    elif isinstance(x, str):
        yield escape(x)
    elif isinstance(x, Spacer):
        yield x.html
    else:
        raise Exception("Not renderable: %s" % repr(x))


# def iterelements (x):
#     if isinstance(x, Element):
#         yield x
#     if isinstance(x, (Element, list, tuple)):
#         for c in x:
#             for d in iterelements(c):
#                 yield d

##  Renders a Text as an iteration over strings.
#   Permits the members of the Text to be either strings or embedded Texts.

def text_strings (elt):
    if isinstance(elt, str):
        yield elt
    elif isinstance(elt, Text):
        for subelt in elt:
            for s in text_strings(subelt):
                yield s
    else:
        raise Exception('Bad textual item: %s' % elt)


#--  RawHtmlPage  --------------------------------------------------------------

# class RawHtmlPage (Response):
# 
#     def __init__ (self, contents):
#         self.__contents = contents
# 
#     def render (self, http=None):
#         if http is None: http = PseudoConnection()
#         http.send_response(200)
#         http.send_header("Content-Type", "text/html;charset=utf-8")
#         http.end_headers()
#         http.write(self.__contents)
#         http.close()


#--  Elements  -----------------------------------------------------------------

##  A structural representation of an HTML element.

class Element (Item):

    ##  Constructor.  The instance adds itself to the parent.

    def __init__ (self, parent, *contents, **kwargs):
        Item.__init__(self, parent)

        ##  A list of renderables or subelements.
        self.contents = None

        ##  The HTML attributes.  These come from the keyword arguments.
        #   Keyword 'htmlclass' gets turned into attribute 'class', and
        #   keyword 'htmlid' gets turned into attribute 'id'.
        self.atts = None

        # sole argument is an iterable?
        if len(contents) == 1 \
                and hasattr(contents[0], '__iter__') \
                and not isinstance(contents[0], (str,Element)):
            self.contents = list(contents[0])

        # otherwise, contents is a tuple
        else:
            self.contents = list(contents)

        if not is_renderable(self.contents):
            raise Exception('Not renderable: %s' % repr(self.contents))

        if kwargs:
            self.atts = {}
            for (k,v) in kwargs.items():
                if k == 'htmlclass': k = 'class'
                elif k == 'htmlid': k = 'id'
                self.atts[k] = v

        parent.add(self)

    ##  Add an HTML attribute-value setting.

    def set_attribute (self, att, val):
        if self.atts is None: self.atts = {}
        if isinstance(val, str): val = html_value_encode(val)
        elif isinstance(val, int): val = str(val)
        else: raise Exception('Bad value: %s' % value)
        self.atts[att] = val

    ##  Add a renderable to the contents.

    def add (self, elt):
        assert is_renderable(elt)
        self.contents.append(elt)

    ##  Converts the string using HTML(), then adds it to the contents.

    def write (self, s):
        self.contents.append(HTML(s))

#    def render (self, http=None):
#        if http is None: http = PseudoConnection()
#        for elt in self.contents:
#            render(elt, http)

    #  Called by the page when this element or an ancestor is added to the page.

#     def bind (self, page):
#         if hasattr(self, 'javascript') and self.javascript:
#             page.add_javascript(self.javascript)
#         if hasattr(self, 'stylesheet') and self.stylesheet:
#             page.add_stylesheet(self.stylesheet)

    ##  Returns a string suitable for printing the HTML tag.

    def attstring (self):
        if self.atts:
            return ' ' + ' '.join('%s="%s"' % (k.replace('_', '-'), str(v))
                                  for (k,v) in self.atts.items())
        else:
            return ''

    ##  Iterates over the contents.

    def __iter__ (self): return self.contents.__iter__()

    ##  String version, just for debugging.

    def __str__ (self):
        output = StringIO()
        for s in iterhtml(self):
            output.write(s)
        s = output.getvalue()
        output.close()
        return s


# class Tag (Element):
# 
#     def __init__ (self, string):
#         self.string = string
# 
# #     def render (self, http=None):
# #         if http is None: http = PseudoConnection()
# #         http.write(self.string)
# 
#     def __iter__ (self):
#         yield self.string


##  A simple element.

class BasicElement (Element):

    ##  Constructor.

    def __init__ (self, parent, tag, *contents, block=False, **kwargs):
        Element.__init__(self, parent, *contents, **kwargs)

        ##  The tag.
        self.tag = tag

        ##  Whether a newline should be printed after the close tag.
        self.block = block

    ##  Iterate over the contents.  Unlike with an Element, the contents
    #   should not include the start and end tags; they are added by the iterator.

    def __iter__ (self):
        s = self.tag
        yield HTML('<%s%s>' % (self.tag, self.attstring()))
        for item in self.contents:
            yield item
        yield HTML('</%s>' % self.tag)
        if self.block: yield HTML('\r\n')

    ##  String representation.

    def __repr__ (self):
        return '<BasicElement %s>' % self.tag


##  This is mixed in to Element or BasicElement.

class WidgetMixin (Item):

    ##  A table with the actions that are handled by the widget.
    __pages__ = None

    ##  Constructor.  kwargs not **kwargs on purpose.
    #   Finds the page that it belongs to and adds itself to the page's
    #   __pages__ table.  Expects a stylesheet and script to exist whose
    #   names are the class's name.

    def __init__ (self, parent, name, kwargs):
        page = parent.__page__()
        cpt = page.cpt.join(name)
        Item.__init__(self, parent, cpt=cpt)
        classname = self.__class__.__name__
        page.add_stylesheet(classname)
        page.add_import(classname)
        if self.__pages__:
            page.add_widget(self)

    ##  The pathname of this widget, relative to the lowest HtmlDirectory.

    def __relative__ (self):
        cpts = []
        item = self
        while not (item is None or isinstance(item, HtmlDirectory)):
            if item.cpt is not None:
                cpts.append(item.cpt)
            item = item.parent
        return '/'.join(reversed(cpts))


    # if the request is for the page that this widget is part of, this
    # widget's __upc__ will be None, but to be addressable it should
    # have a 'name' attribute

#    def callback_prefix (self):
#        return self.page().__upc__.name + ';' + self.atts['name'] + ';'


##  Just combines Element and WidgetMixin.

class Widget (Element, WidgetMixin):

    ##  Constructor.

    def __init__ (self, parent, name, *contents, **kwargs):
        Element.__init__(self, parent, *contents, name=name, **kwargs)
        WidgetMixin.__init__(self, parent, name, kwargs)


##  Just combines BasicElement and WidgetMixin.

class BasicWidget (BasicElement, WidgetMixin):

    ##  Constructor.

    def __init__ (self, parent, name, tag, *contents, block=False, **kwargs):
        BasicElement.__init__(self, parent, tag, *contents, block=block, name=name, **kwargs)
        WidgetMixin.__init__(self, parent, name, kwargs)


#--  Spans  --------------------------------------------------------------------

##  A BasicElement; boldface.

def B (parent, *contents, **kwargs):
    return BasicElement(parent, 'b', *contents, **kwargs)

##  A BasicElement; page heading.

def H1 (parent, *contents, **kwargs):
    return BasicElement(parent, 'h1', *contents, block=True, **kwargs)

##  A BasicElement; level-2 heading.

def H2 (parent, *contents, **kwargs):
    return BasicElement(parent, 'h2', *contents, block=True, **kwargs)

##  A BasicElement; level-3 heading.

def H3 (parent, *contents, **kwargs):
    return BasicElement(parent, 'h3', *contents, block=True, **kwargs)

##  A BasicElement; level-4 heading.

def H4 (parent, *contents, **kwargs):
    return BasicElement(parent, 'h4', *contents, block=True, **kwargs)

##  A BasicElement; level-5 heading.

def H5 (parent, *contents, **kwargs):
    return BasicElement(parent, 'h5', *contents, block=True, **kwargs)

##  A BasicElement; level-6 heading.

def H6 (parent, *contents, **kwargs):
    return BasicElement(parent, 'h6', *contents, block=True, **kwargs)

##  A BasicElement; italics.

def I (parent, *contents, **kwargs):
    return BasicElement(parent, 'i', *contents, **kwargs)

##  A BasicElement; typewriter font.

def TT (parent, *contents, **kwargs):
    return BasicElement(parent, 'tt', *contents, **kwargs)


#--  Spacers  ------------------------------------------------------------------

##  A class that includes NBSP and BR.

class Spacer (object):

    ##  Constructor.

    def __init__ (self, parent, s, n=1):

        ##  An HTML instance.
        self.html = HTML(s)

        if parent: parent.add(self)

    ##  This is here so that one can do e.g. NBSP(2) to create two of them.

    def __call__ (self, parent, n=1):
        return Spacer(parent, self.html * n)

    ##  Just returns self.html.

    def __iter__ (self):
        return self.html

    ##  String representation.

    def __str__ (self):
        return self.html


##  A non-breaking space.
NBSP = Spacer(None, '&nbsp;')

##  A line break.
BR = Spacer(None, '<br />\r\n')


#--  Blocks  -------------------------------------------------------------------

##  A BasicElement; div.

def Div (parent, *contents, **kwargs):
    return BasicElement(parent, 'div', *contents, block=True, **kwargs)

##  A BasicElement; span.

def Span (parent, *contents, **kwargs):
    return BasicElement(parent, 'span', *contents, **kwargs)

##  A BasicElement; paragraph.

def P (parent, *contents, **kwargs):
    return BasicElement(parent, 'p', *contents, block=True, **kwargs)

##  A BasicElement; pre-formatted text.

def Pre (parent, *contents, width='', htmlclass='source', **kwargs):
    return BasicElement(parent, 'pre', *contents, width=width, htmlclass=htmlclass, **kwargs)


#--  Scripts  ------------------------------------------------------------------

##  A script element.

class Script (Element):
    
    ##  Constructor.  Finds the page to which this element belongs and calls
    #   the page's add_script() method to add
    #   itself to the list of initialization scripts.

    def __init__ (self, parent, *contents, **kwargs):
        Element.__init__(self, parent, **kwargs)

        ##  My contents, as a list.
        self.script = list(contents)

        page = self.__page__()
        page.add_script(self)

    ##  Add some javascript to this script.

    def add (self, s):
        self.script.append(s)

    ##  Same as add().

    def write (self, s):
        self.script.append(s)


#--  Lists  --------------------------------------------------------------------

##  Bullet list.

class UL (Element):

#    def render (self, http=None):
#        if http is None: http = PseudoConnection()
#        http.write('<ul>\r\n')
#        for item in self.items:
#            http.write('<li>')
#            render(item, http)
#            http.write('</li>\r\n')
#        http.write('</ul>\r\n')

    ##  Inserts the start and end tags.  The members of the contents are
    #   items.  Start and end 'li' tags are wrapped around the items.

    def __iter__ (self):
        yield HTML('<ul>\r\n')
        for item in self.contents:
            yield HTML('<li>')
            yield item
            yield HTML('</li>\r\n')
        yield HTML('</ul>\r\n')

##  This is completely optional.

class LI (Element): pass

##  Unlike a UL, this produces a vertical list with no bullets.
#   Instead, it puts a line break between each pair of adjacent items.

class Stack (Element):

#    def render (self, http=None):
#        if http is None: http = PseudoConnection()
#        if self.contents:
#            render(self.contents[0], http)
#            for elt in self.contents[1:]:
#                http.write('<br />\r\n')
#                render(elt, http)

    ##  Iterate, inserting line breaks.

    def __iter__ (self):
        if self.contents:
            yield self.contents[0]
            for elt in self.contents[1:]:
                yield BR
                yield elt


#--  Table  --------------------------------------------------------------------

##  A cell in a table.  A BasicElement.

class Cell (BasicElement):

    ##  Constructor.

    def __init__ (self, parent, *contents, rowspan=1, colspan=1, **kwargs):
        assert isinstance(rowspan, int)
        assert isinstance(colspan, int)
        if rowspan > 1: kwargs['rowspan'] = str(rowspan)
        if colspan > 1: kwargs['colspan'] = str(colspan)
        if isinstance(parent, Header): tag = 'th'
        else: tag = 'td'
        BasicElement.__init__(self, parent, tag, *contents, **kwargs)

#    def render (self, http=None):
#        if http is None: http = PseudoConnection()
#        http.write('<td rowspan=%d colspan=%d>' % (self.rowspan, self.colspan))
#        render(self.contents, http)
#        http.write('</td>')

#     def __iter__ (self):
#         yield HTML('<td %s>' % self.attstring())
#         for item in self.contents: yield item
#         yield HTML('</td>')


##  A row in a table.

class Row (Element):

    ##  Constructor.

    def __init__ (self, parent, *cells, **kwargs):
        Element.__init__(self, parent, *cells, **kwargs)

        ##  What tag to use for cells.  By default it is 'td'.
        #   To get 'th' cells, use a Header instead of a plain Row.
        self.celltag = 'td'

#    def render (self, http=None):
#        if http is None: http = PseudoConnection()
#        http.write('<tr>')
#        for cell in self.contents:
#            if isinstance(cell, Cell):
#                cell.render(http)
#            else:
#                http.write('<td>')
#                render(cell, http)
#                http.write('</td>')
#        http.write('</tr>\r\n')

    ##  Iterate.  Prints the start and end 'tr' tags.
    #   If an element is a Cell instance, rendering its start and end
    #   tags is left to the cell.  Otherwise, self.celltag is used.

    def __iter__ (self):
        yield HTML('<tr%s>' % self.attstring())
        for cell in self.contents:
            if isinstance(cell, Cell):
                yield cell
            else:
                yield HTML('<%s>' % self.celltag)
                yield cell
                yield HTML('</%s>' % self.celltag)
        yield HTML('</tr>\r\n')


##  A row containing 'th' tags instead of 'td'.

class Header (Row):

    ##  Constructor.

    def __init__ (self, parent, *cells):
        Row.__init__(self, parent, *cells)

        ##  Which tag to use for cells, inherited from Row.
        self.celltag = 'th'


##  A table.

class Table (Element):

    ##  The table start and end tags are inserted.
    #   If the table does not have an overt 'class' attribute,
    #   class="display" is used.
    #   The members are rows.  If a member is not an instance of
    #   Row, a Row is created out of it.

    def __iter__ (self):
        if not (self.atts and 'class' in self.atts):
            self.set_attribute('class', 'display')
        yield HTML('<table%s>\r\n' % self.attstring())
        for elt in self.contents:
            if isinstance(elt, Row): yield elt
            else: yield Row(elt)
        yield HTML('</table>\r\n')


#--  Navigation  ---------------------------------------------------------------

##  A hyperlink.

class Link (Element):

    ##  Constructor.

    def __init__ (self, parent, text, url, target=None, **kwargs):
        Element.__init__(self, parent, text, **kwargs)
        if url is None: raise Exception('URL is required')

        ##  The url is passed to self.__extern__() and stored here.
        self.url = self.__extern__(url)

        ##  E.g., 'top'.  Most commonly, None.
        self.target = target

#    def render (self, http=None):
#        if http is None: http = PseudoConnection()
#        if self.target:
#            http.write('<a href="%s" target="%s">' % (self.url, self.target))
#        else:
#            http.write('<a href="%s">' % self.url)
#        render(self.text, http)
#        http.write('</a>')

    ##  Iterate.  Produces an 'a' element whose href is the url.  A 'target'
    #   attribute is added if self.target is not boolean false.  As with any
    #   element, arbitrary attributes may also be specified.  The contents form
    #   the body of the 'a' element.

    def __iter__ (self):
        yield HTML('<a href="')
        if ':' in self.url: yield self.url
        else: yield Pathname(self.url)
        if self.target:
            yield HTML('" target="%s"' % self.target)
        else:
            yield HTML('"')
        yield HTML('%s>' % self.attstring())
        for s in self.contents:
            yield s
        yield HTML('</a>')

##  A menu bar.

class MenuBar (Element):

    ##  Iterate.  It renders as a div with class "menubar".  Members are
    #   separated by NBSP.

    def __iter__ (self):
        yield HTML('<div class="menubar">\r\n')
        first = True
        for button in self.contents:
            if first: first = False
            else: yield NBSP
            yield button
        yield HTML('</div>\r\n')


##  The navigation chain of ancestors at the top of the web page, corresponding
#   to the components of this page's URL pathname.  Renders as a div with class
#   "path" in which each path component provides a Link, separated by literal
#   greater-than characters.  (The last component is not a link, however, as it
#   names the current page.)

def Path (page):
    path = BasicElement(page, 'div', block=True, htmlclass='path')
    names = [anc.cpt for anc in page.__ancestors__() if anc.cpt is not None]
    if not names:
        raise Exception('No path components')

    last = len(names) - 1
    for i in range(len(names)):
        name = names[i]
        pathname = name.pathname
        if name == '':
            if i == 0: name = 'Top'
            else: name = '(null)'
        elif '/' in name:
            k = name.rindex('/')
            name = name[k+1:]
        if len(name) > 8:
            name = name[:8] + '..'
        if i == last:
            String(path, name)
        else:
            Link(path, name, pathname)
            String(path, ' > ')

    return path

##  The same, but add a 'Login' button against the right margin.

def PathWithLogin (page):
    path = Path(page)
    ctx = page.context
    if ctx.connection_is_secure() and not ctx.server_authentication_on():
        name = page.context.username
        if name:
            tgtname = 'logout'
        else:
            name = 'Login'
            tgtname = 'login'
        caller = hex_encode(page.cpt.pathname)
        tgt = '/%s.%s' % (tgtname, caller)
        Link(path, name, tgt, htmlclass='login_button')
    return path


#--  Forms  --------------------------------------------------------------------

##  A button.

class Button (Element):

    ##  Constructor.

    def __init__ (self, parent, text, url=None, target=None, **kwargs):
        Element.__init__(self, parent, **kwargs)
        if url is not None: url = self.__extern__(url)

        ##  The button text.
        self.text = text

        ##  The URL that is visited when the button is clicked.
        self.url = url

        ##  As for a Link.
        self.target = target

        self.set_attribute('type', 'button')
        self.set_attribute('value', text)

    ##  Iterate.  Renders as an input element with type button, whose value
    #   is the text.  If there is a target, it has an onclick method that calls
    #   window.open(url,tgt).  If there is a URL but no target, it sets
    #   window.location to the URL.  If there is no URL, the button is grayed out.

    def __iter__ (self):
        atts = self.attstring()
        if self.url is not None and self.target:
            yield HTML('<input %s onclick="window.open(\'' % atts)
            yield self.url
            yield HTML("','%s')\"/>" % self.target)
        elif self.url is not None:
            yield HTML('<input %s onclick="window.location=\'' % atts)
            yield self.url
            yield HTML("'\"/>")
        else:
            yield HTML('''<input %s disabled/>''' % atts)


##  A check box.  Key and value are for the form.  Checked determines whether
#   it is initially checked or not.

def CheckBox (parent, key=None, value=False, checked=False, htmlclass=None, htmlid=None, disabled=False):
    atts = [('type', 'checkbox')]
    if key: atts.append(('name', key))
    if value: atts.append(('value', value))
    if checked: atts.append(('checked', 'true'))
    if htmlclass: atts.append(('class', htmlclass))
    if htmlid: atts.append(('id', htmlid))
    if disabled: atts.append(('disabled', 'true'))
    elt = HTML('<input %s/>\r\n' % ' '.join('%s="%s"' % (a,v) for (a,v) in atts))
    parent.add(elt)
    return elt
        

##  A collection of check boxes, any number of which can be checked.

class CheckBoxes (Element):

    ##  Constructor.

    def __init__ (self, parent, key, values, selected=[], separator=' '):
        Element.__init__(self, parent)
        assert not key.endswith('*')
        if not (isinstance(values, list) or isinstance(values, tuple)):
            raise Exception("Values must be a list or tuple")
        if isinstance(selected, str): selected = [selected]

        ##  The key for the form.
        self.key = key

        ##  The values for the form.  Each is rendered as a separate check box.
        #   Note that a star will be added in the actual form, indicating that
        #   it may have multiple values.
        self.values = values

        ##  Which values are selected.  This should be a list containing values.
        self.selected = selected

        ##  What to use as a separator between check boxes.  By default, a space.
        self.separator = separator

#    def render (self, http=None):
#        if http is None: http = PseudoConnection()
#        first = True
#        for v in self.values:
#            if first: first = False
#            else: http.write(self.separator)
#
#            if v in self.selected: sel = ' checked'
#            else: sel = ''
#
#            http.write('<input type="checkbox"%s name="%s*" value="%s">%s</input>\r\n' % \
#                           (sel, self.key, v, v))

    ##  Iterate.

    def __iter__ (self):
        first = True
        for v in self.values:
            if first: first = False
            else: yield self.separator

            if v in self.selected: sel = ' checked'
            else: sel = ''

            yield HTML('<input type="checkbox"%s name="%s*" value="%s">%s</input>\r\n' % \
                (sel, self.key, v, v))


##  A drop-down menu.

class DropDown (Element):

    ##  Constructor.

    def __init__ (self, parent, key, values, selected=None, disabled=False, **kwargs):
        Element.__init__(self, parent, **kwargs)
        assert not key.endswith('*')
        if not (isinstance(values, list) or isinstance(values, tuple)):
            raise Exception("Values must be a list or tuple")
        self.set_attribute('name', key)
        if disabled:
            self.set_attribute('disabled', 'true')

        if selected is None:
            selected = values[0]

        ##  The key, for the form.
        self.key = key

        ##  The list of values.
        self.values = values

        ##  Which value is initially selected.  By default, it is the first value.
        self.selected = selected

#    def render (self, http=None):
#        if http is None: http = PseudoConnection()
#        http.write('<select name="%s">' % self.key)
#        for v in self.values:
#            if v == self.selected: sel = ' selected="true"'
#            else: sel = ''
#            http.write('<option%s value="%s">%s</option>\r\n' % (sel,v,v))
#        http.write('</select>')

    ##  Iterate.

    def __iter__ (self):
        yield HTML('<select%s>' % self.attstring())
        for v in self.values:
            if v == self.selected: sel = ' selected'
            else: sel = ''
            yield HTML('<option%s value="%s">%s</option>\r\n' % (sel,v,v))
        yield HTML('</select>')

##  Browse button.  For choosing the name of an existing file.

def BrowseButton (parent, key):
    assert not key.startswith('*')
    elt = HTML('<input type="file" name="file:%s"/>\r\n' % key)
    parent.add(elt)
    return elt

##  Form.

class Form (Element):

    ##  Constructor.

    def __init__ (self, parent, callback, name=None):
        Element.__init__(self, parent)

        ##  The URL that the form should call back to.
        self.callback = callback

        ##  The name of the form.
        self.name = name

#    def render (self, http=None):
#        if http is None: http = PseudoConnection()
#        http.write('<form enctype="multipart/form-data" action="%s" method="post">\r\n' % self.callback)
#        for elt in self.contents:
#            render(elt, http)
#        http.write('</form>\r\n')

    ##  Iterate.  Produces the form start tag, with enctype "multipart/form-data"
    #   and action equal to the callback, method "post".  The contents provide
    #   the body of the form.

    def __iter__ (self):
        
        yield HTML('<form enctype="multipart/form-data" action="')
        yield Pathname(self.callback)
        yield HTML('" method="post"')
        if self.name: yield HTML(' name="%s"' % self.name)
        yield HTML('>\r\n')
        for elt in self.contents:
            yield elt
        yield HTML('</form>\r\n')

##  A hidden key-value pair in a form.

def Hidden (parent, key, value, **kwargs):
    assert not key.endswith('*')
    atts = [('name', key), ('value', value)]
    atts.extend(kwargs.items())
    elt = HTML('<input type="hidden" %s/>\r\n' % ' '.join('%s="%s"' % (a,v) for (a,v) in atts))
    parent.add(elt)
    return elt
    
##  Essentially the same as Hidden.

def NotEditable (parent, key, value):
    assert not key.endswith('*')
    if value is None: value = ''
    elt = HTML('<input type="hidden" name="%s" value="%s"/>%s\r\n' % (key, value, value))
    parent.add(elt)
    return elt

##  A password-input element.

def Password (parent, key):
    assert not key.endswith('*')
    elt = HTML('<input type="password" name="%s"/>' % key)
    parent.add(elt)
    return elt


##  A radio button.

def RadioButton (parent, key, value, checked=False, htmlclass=None, htmlid=None, disabled=False):
    atts = [('type', 'radio'), ('name', key), ('value', value)]
    if checked: atts.append(('checked', 'true'))
    if htmlclass: atts.append(('class', htmlclass))
    if htmlid: atts.append(('id', htmlid))
    if disabled: atts.append(('disabled', 'true'))
    elt = HTML('<input %s/>\r\n' % ' '.join('%s="%s"' % (a,v) for (a,v) in atts))
    parent.add(elt)
    return elt
        
##  A collection of radio buttons, only one of which can be selected.

class RadioButtons (Element):

    ##  Constructor.

    def __init__ (self, parent, key, values, selected=None, separator=' '):
        Element.__init__(self, parent)
        assert not key.endswith('*')
        if not (isinstance(values, list) or isinstance(values, tuple)):
            raise Exception("Values must be a list or tuple")

        ##  The key for the form.
        self.key = key

        ##  The list of values, one for each radio button.
        self.values = values

        ##  The selected value, possibly None.
        self.selected = selected

        ##  The separator to put between adjacent buttons.
        self.separator = separator

#    def render (self, http=None):
#        if http is None: http = PseudoConnection()
#        first = True
#        for v in self.values:
#            if first: first = False
#            else: http.write(self.separator)
#
#            if v == self.selected: sel = ' checked'
#            else: sel = ''
#
#            http.write('<input type="radio"%s name="%s" value="%s">%s</input>\r\n' % \
#                           (sel, self.key, v, v))

    ##  Iterate.  Contents is ignored; iterates over values.

    def __iter__ (self):
        first = True
        for v in self.values:
            if first: first = False
            else: yield self.separator

            if v == self.selected: sel = ' checked'
            else: sel = ''

            yield HTML('<input type="radio"%s name="%s" value="%s">%s</input>\r\n' % \
                (sel, self.key, v, v))

##  A submit button.

def Submit (parent, value='Submit', name='submit', htmlclass=None, htmlid=None, disabled=False):
    atts = [('type', 'submit'), ('name', name), ('value', value)]
    if htmlclass: atts.append(('class', htmlclass))
    if htmlid: atts.append(('id', htmlid))
    if disabled: atts.append(('disabled', 'true'))
    elt = HTML('<input %s/>\r\n' % ' '.join('%s="%s"' % (a,v) for (a,v) in atts))
    parent.add(elt)
    return elt

##  A text area.

def TextArea (parent, key, value='', size=(3,60), htmlid=None, trigger=False, disabled=False):
    classatt = idatt = ''
    if htmlid:
        idatt = ' id="%s"' % htmlid
    if trigger:
        classatt = ' class="sealTrigger"'
    if disabled: disabled = ' disabled="true"'
    else: disabled = ''
    elt = HTML('<textarea rows="%d" cols="%d" name="%s"%s%s%s>%s</textarea>\r\n' % \
                   (size[0], size[1], key, classatt, idatt, disabled, value))
    parent.add(elt)
    return elt

##  Replaces only double quotes with the corresponding HTML entity.
#   See also html_value_encode() and escape().

def attvalue_quoted (s):
    return s.replace('"', '&quot;')

##  A text box.

def TextBox (parent, key, value='', size=60, htmlid=None, disabled=False):
    assert not key.endswith('*')
    if value is None: value = ''
    if htmlid: htmlid = ' id="%s"' % htmlid
    else: htmlid = ''
    if disabled: disabled = ' disabled="true"'
    else: disabled = ''
    elt = HTML('<input%s type="text" size="%s" name="%s" value="%s"%s/>\r\n' % \
                   (htmlid, size, key, attvalue_quoted(value), disabled))
    parent.add(elt)
    return elt


#--  Audio/Video  --------------------------------------------------------------

##  An audio player.  It has controls.  The type is "audio/X" where X is the
#   suffix of the filename (src).

class Audio (Element):

    ##  Constructor.

    def __init__ (self, parent, src, **kwargs):
        Element.__init__(self, parent, **kwargs)

        ##  The source URL.
        self.src = src

    def __iter__ (self):
        yield HTML('<audio controls%s>' % self.attstring())
        yield HTML('<source src="%s" type="audio/%s">' % (self.src, get_suffix(self.src)))
        yield HTML('</audio>')


##  A video player.  Type is "video/mp4".  Has controls.

class Video (Element):

    ##  Constructor.

    def __init__ (self, parent, src, type='video/mp4', **kwargs):
        Element.__init__(self, parent, **kwargs)

        ##  The URL of the video file.
        self.src = src

        ##  The mime type.
        self.type = type

    ##  Contents.

    def __iter__ (self):
        yield HTML('<video controls%s src="%s" type="%s">' % (self.attstring(), self.src, self.type))
        yield HTML('</video>')


#--  Editable  -----------------------------------------------------------------

##  An editable paragraph.  The HTML class is "editable," but it does not include
#   the javascript code to make it work.  That is in PlainTextPanel.js.
#   There is one callback from PlainTextPanel.js, namely: edit_par(op, i, j, text).

class EditableParagraph (BasicElement):

    ##  Constructor.  The contents should be romanized text.

    def __init__ (self, parent, ascii, rom):
        check_type(rom, ('Romanization', 'ReadOnlyRomanization'))
        BasicElement.__init__(self, parent, 'p', htmlclass='editable')

        ##  The ascii version.  Is passed through html_value_encode() and
        #   becomes the value of the attribute "data-value".  The contents
        #   of the paragraph are produced by using the rom to decode the
        #   ASCII version.
        self.ascii = ascii

        try:
            value = html_value_encode(ascii)
            pretty = rom.decode(ascii)
        except:
            value = pretty = '(Bad text)'

        self.set_attribute('data-value', value)
        String(self, pretty)


##  An editable text.  Has attributes "data-roms" and "data-url."
#   Needs PlainTextPanel.js to work.

class EditableText (BasicWidget):

    ##  Constructor.

    def __init__ (self, parent, name, roms, url, columns, htmlclass=None):
        cls = 'editorTable'
        if htmlclass: cls = cls + ' ' + htmlclass

        BasicWidget.__init__(self, parent, name, 'div', htmlclass=cls)
        self.add_attribute('data-roms', ','.join(roms))
        self.add_attribute('data-url', self.cpt) # callback_prefix())

        for rom in roms:
            assert isinstance(rom, Romanization)

        table = Table(self, htmlclass=cls)
        for i in range(len(columns[0])):
            row = Row(table)
            for j in range(len(columns)):
                s = columns[j][i]
                cell = Cell(table)
                EditableParagraph(cell, s, roms[j])
