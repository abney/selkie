
Request processing
******************

The process of handling a web-page request was described briefly
above, in the secton 'App as function'.
In this section, I give more detail.

Descending through the web space
--------------------------------

Calling App
...........

A request is essentially a sequence
of **pathname components** (class URLPathComponent) describing a path through a **web space**.
There is a fixed **root web directory** at which the app begins,
whose pathname in the web space is called the **root prefix**.
Then each (subsequent) component of the pathname is used to access an
item in the current directory.  If the component sequence is
exhausted, the retrieved item should be
a web page, and if there are more components to process, the
retrieved item should be a subdirectory, which becomes the new current
directory.

Let us walk through a concrete example.  A call to App begins with a
request.  We can create a Request instance as follows::

   >>> from selkie.cld.app import request_from_string
   >>> req = request_from_string('/seal/index.html')
   >>> req.path
   ('', 'seal', 'index.html')

The App first does some set-up.

 * It wraps the request in a Context.  Contexts are discussed in
   a later section.
   They provide logging and
   authentication services, and may also be used by the application to
   store global web resources::

      >>> context = ency.make_context(req)
      >>> context
      <selkie.cld.app.Context object at 0x10284ada0>

 * It opens the application file.  (The ency app does not actually
   have an application file; it uses the default
   open_file method implementation, which simply returns None.)::

      >>> file = ency.open_file(ency.filename, context)

 * It instantiates the root web directory::

      >>> dir = ency.make_root(req.path[0], file, context)
      >>> dir
      <seal.ency.Ency object at 0x10284ae10>

The first component of the request path is the root prefix, which
provides the web pathname for the root directory.

Once the set-up has been completed, the App follows the sequence of
names remaining in the request path.  In our examples, two names
remain: 'seal' and 'index.html'.  The first one
gives us a subdirectory::

   >>> req.path[1]
   'seal'
   >>> dir[_]
   <Directory seal>
   >>> dir = _

The subdirectory becomes the new current directory.  The App accesses
it using the next pathname component::

   >>> req.path[2]
   'index.html'
   >>> dir[_]
   <EncyFile 'index' 'html' '/Users/abney/git/seal/doc/html/index.html'>
   >>> item = _

Since this is the last component, we expect it to give us a web page,
or rather, something that can be converted to a web page.  This is the
point at which the follow method returns::

   >>> ency.follow(req)
   <EncyFile 'index' 'html' '/Users/abney/git/seal/doc/html/index.html'>

Postprocessing
..............

The final item found in the descent through the web space may be
an HtmlDirectory, a Page, or a Widget.  The App's return value should
be a Response.  The conversion from final item to Response
proceeds in two steps.

First, the final item's to_page method is called to
convert it to a Page::

   >>> page = item.to_page()
   >>> page
   <selkie.cld.app.RawFile object at 0x10288aa20>

(If the item a Page, its to_page method simply
returns the same item again.)

Second, the Page's to_response method is called to convert it
to a Response, which is returned to the caller.

Web objects
-----------

The web object hierarchy
........................

Recall that the App descends through the web space
by calling the __getitem__ method of one web object to get the next
one in line, starting from the root web directory.  When the path is
exhausted, the App calls the last item's to_page method to
convert it to a web page.
In this section, we flesh out the details.

**Web objects** are the objects that the App visits when processing
a request.
The following is the upper hierarchy of web objects:

 * Item
    
     * HtmlDirectory

     * Page
        
         * HtmlPage

         * RawFile

         * Data

         * Text

         * Redirect

         * HttpException
            
             * PermissionDenied

             * PageNotFound

             * HttpUserError

             * HttpSystemError

     * Element
        
         * Widget

An **addressable** web object is one that is associated with a path
through the web space.  These are the ones that the App can reach by
following a request.  They include HtmlDirectories, Pages, and
Widgets.

Let us further distinguish
between **nonterminal** and **terminal** items.  Specifically,
define a nonterminal item to be one that returns values for at least
some calls to __getitem__, and define a terminal item to be one that
returns itself when when to_page is requested.

There are four important cases:

 * HtmlDirectories are nonterminal addressable items.

 * Page and its specializations are terminal addressable items.

 * Widget is also a terminal addressable item.

 * An HtmlPage that contains widgets is simultaneously terminal and
   nonterminal.

Item
....

The following members of Item are significant for
traversing the web space:

 * __pages__ — By default None.  Directory-like Items
   must set __pages__ to a dict.  "Directory-like Items" includes
   both HtmlDirectories and HtmlPages that contain Widgets.
   In the case of HtmlDirectories, the dict maps component names to
   page-method names, and in the case of HtmlPages, the dict maps
   component names to Widgets.

 * __home__ — The name of the home page.  By default, 'home'.

 * parent — The parent HtmlDirectory.

 * file — The file associated with this web object,
   if any.

 * cpt — The URLPathComponent associated with this page.

 * context — The Context.

The __init__ method of Item takes four
arguments, which set the corresponding
members: *parent,* *file,* *cpt,* *context.*
If *parent* is provided, the other three are initialized from the
parent.  (Just during the call to the method that fetches the child,
the child's cpt is stored in the parent's childcpt member.)
Even if *parent* is provided, the other three may be used to
override the values from the parent.

Method __getitem__
..................

The Item.__getitem__ method is the one that App uses to get a child of
an HtmlDirectory.  The sole argument to __getitem__ is *pathcpt.*
It does the following:

 * Let (*name*, \* *args*, \** *kwargs*) be the elements of *pathcpt*.call.

 * If the *name* is the empty string, return a Redirect to
   the home page, obtained by joining the value of __home__ to this
   page's pathname.

 * Look up *name* in the __pages__ dict.

 * If the value is an Item, return it.

 * Otherwise, the value is a method name.  Get the named method
   and call it on \* *args* \** *kwargs*.  Signal an error if the return
   value is None, or if the name is __home__ and the return value is
   an HtmlDirectory.  Otherwise, return the value.

Method to_page
..............

If the requested path leads the App to an HtmlDirectory, and the
HtmlDirectory has a to_page method, the App
calls to_page to convert the directory to a page.  Several
classes have a to_page implementation:

 * Item: signals an error.

 * HtmlDirectory: returns a Redirect to the pathname
   obtained by joining __home__ to the directory's pathname.

 * Page: returns itself.

Method to_response
..................

Page and its specializations provide a method to_response
that takes a Context and returns a Response.
The Context is used only for access to the cookie, if any.
The Response constructor
gets the page's response_code
and it uses the the page's content_type to determine
a Mime type and character encoding.  Then
it iterates over the Page and stores the results
in its own contents member.
In the process, it
converts any strings to byte-strings using the encoding determined by
the page's content-type.  If the page has binary contents (that is, if
encoding is None), only byte-strings are permitted.
As byte-strings are added to contents, a running count of bytes
is kept in the member nbytes.
Note that a page's iterator will be used only once; there is no need
for it to be reusable.

Script library
--------------

Defining an HtmlDirectory
-------------------------

