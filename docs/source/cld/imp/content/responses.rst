
Constructing a Page
*******************

As described in the overview,
calling the App produces a Page, which is converted to a Response.
The Page is combined with some
contextual information to create a Response
instance, which is returned.

Pages
-----

Specializations of Page
.......................

The following are specializations of Page.

**HtmlPage.**  The commonest kind of Page.  It is discussed in
detail below.

**RawFile.**  The constructor takes a filename.  The MIME
type of the file is determined from the filename suffix, or it may be
explicitly specified by providing keyword argument type.
If there is no suffix, it defaults to 'txt'.

**Data.**  Unlike RawFile, this is not data that is associated with
a file.  When constructed, it represents an empty byte sequence.  One
adds data by calling write(bs), where *bs* is a byte
array.

**Text.**  Like Data, except that one may write strings to it.  One
may also pass a string to the constructor to set the contents.

**Redirect.**  The constructor takes a URI.

**HttpException.**  The constructor takes a message.  Subclasses
are: PermissionDenied, PageNotFound, HttpUserError, and HttpSystemError.

Page to Response
................

A Response instance packages up a Page along with cookie information
taken from the Context.  It has methods that make it suitable for use
within a WSGI application.  See 'Translating responses'.

The following members of Page are relevant for producing WSGI output:

 * response_code — An HTTP status code.  The default
   value is 200.

 * content_type — A filename suffix.

 * __iter__() —
   An iteration containing a mixture of strings and byte-strings.

 * uri — This member is present only if the
   response_code is 303 (a redirect).
   It contains the location to redirect to.

The available specializations of Page are as follows.

 * HtmlPage — A regular HTML page.  This class is not directly
   instantiatable; it must be subclassed.  Content type: html.

 * RawFile — Initialized with parent and filename.  Content
   type is taken from the filename suffix, or txt if there is no suffix.

 * Data — Initialized with parent and content-type.  Contents
   are set by calling its write method, which accepts bytes.

 * Text — Typically used for an Ajax response; no parent.
   Initializer takes contents and content-type.
   Contents are set by calling the write method, which accepts
   strings.  The add method is a synonym for write.

 * Redirect — Initializer takes URI as argument, no parent.
   Caution: do not use '' as the target of a redirect; browsers
   interpret it as '/'.  Instead, use '.'
   Response code: 303.

 * HttpException — Response code
   400, content type txt.  Superclass for the following.

 * PageNotFound — Response code 404.

 * HttpUserError — Illegal request, reponse code 400.

 * HttpSystemError — Response code 500.

HtmlPage
--------

Creating a web page
...................

One creates a web page by instantiating HtmlPage.
The HtmlPage constructor has one
obligatory argument, *parent,* which is usually an
HtmlDirectory, though we use None in the following example to keep things simple.
A commonly-used optional parameter is title::

   >>> page = HtmlPage(None, title='Test Page')

One then adds UI elements to the page.  Creating an element with the
page as parent automatically adds it to the page::

   >>> par = P(page)

Strings can be added using the function String::

   >>> String(par, 'This is a ')
   'This is a '
   >>> B(par, 'test')
   <BasicElement b>
   >>> String(par, '.')
   '.'

Printing the page shows the contents that will be sent to the client::

   >>> print(page, end='')
   <html>
   <head>
   <title>Test Page</title>
   <link rel="stylesheet" type="text/css" href="/.lib/default.css" />
   </head>
   <body>
   <p>This is a <b>test</b>.</p>
   </body>
   </html>

Methods
.......

There are two lowlevel methods for adding material to an
HtmlPage: add, for adding elements, and write(),
for writing raw HTML.  Usually one does not
call these methods directly.  Rather, one adds a new element as in the
previous example: simply by
creating an element and passing it the page, or an element already on
the page, as its parent.

Other methods are provided for adding information to the page that is
rendered in the head or foot.  Several of these methods access script or
stylesheet files; all such files reside in the Seal subdirectory data/seal.

 * add_stylesheet(*n*) — Add a stylesheet by name.  The
   stylesheet file is *n*.css.

 * add_style(*n*) — Embed the contents of a stylesheet as a
   <style> element.  The source file is *n*.css.

 * add_body_attribute(*k,* *v*) — Add
   *k*=*v* to the body element.

 * focus(*id*) — Add a focus call in a <script> element in
   the foot.  The argument *id* is the HTML ID of the element to be focussed.  This will be the first thing in the script.

 * add_import(*n*) — Embed the contents of the file
   *n*.js in the <script> element in the foot.

 * add_script(*s*) — The argument *s* is a Script element.
   Its member *s*.script contains a list of strings; embed them
   in the <script> element in the foot.  Script elements are
   added in the order they are encountered on the page, but they follow
   all imports.

 * add_widget(*w*) — Registers a widget *w* in the
   __pages__ dict, creating it if necessary.


Contents
........

Adding an item to an HtmlPage simply adds it to the page's contents.
When rendering the page,
the function iterhtml is called on each item in the contents
to convert it into strings or bytes.  In particular:

 * Objects of type Element, list, or tuple are
   iterated over, and iterhtml is called recursively on each
   item they contain.

 * Bytes and bytearrays are passed through as is.

 * Strings belonging to the subclasses HTML or Pathname
   are passed through as is.  Regular strings are
   first passed through the function escape, which replaces
   '<', '>', '&amp;', and '&quot;' with their HTML entities,
   and replaces all non-ASCII characters with &amp;#...; entities.
   The return value from escape is of type HTML.

 * Spacer instances are replaced with the value of their
   html members (which are strings of class HTML).

 * None is ignored.

Convenience module: html
------------------------
