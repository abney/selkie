
Overview
********

CLD builds on three main substrate components: a server framework, a
persistent-object database, and a content framework.

 * The **Server Framework** provides a web server that
   can be called either stand-alone, to
   provide a web service, or as the engine of a desktop application that
   uses a web browser as user interface.
   In the server framework, the application is a
   function that takes a Request (which is a digested version of an HTTP
   request), reads or updates files on disk, 
   and returns a Response (which can be rendered as an HTTP response).

   The nature of the HTTP protocol imposes some strong constraints on the
   application function.  The protocol is stateless apart from what is written to
   disk, and it centers around processing individual requests.  
   When it receives a request from a client (that is, a web browser), the
   web server launches a request handler in a separate thread.  Multiple
   requests may be processed simultaneously; thus all processing must be
   thread-safe.

 * The **Persistent-Object Database** provides a database that
   is represented by Python objects whose contents are backed by
   local files.  It is designed for multiple users; it includes a
   permission system and is thread-safe.

 * The **Content Framework** provides an application that is
   built on web directories and web pages, represented as Python
   objects.

Substrate
---------

The Server Framework
....................

The Server Framework consists of the web server and surrounding
classes.  The key components are the following:

 * **Manager** (seal.app.toplevel).  Provides command-line processing.
   It can be used to
   run the server in desktop mode or web mode, or to call the
   application from within a CGI or WSGI script.  It also provides
   functionality for managing config files and databases.

 * Configuration and logging

    * **Environment dict.**  This is a standard Python dict
      that contains configuration parameters
      for all components, including the application function, the Server,
      the Logger, and the Authenticator.
  
    * **ConfigFile** (seal.app.config).  This stores
      environment dict information on disk.
  
    * **Logger** (seal.app.log).  Allows logging information
      to be written to console or file, to be selected conditionally,
      and to do thread-safe interleaving of log messages.

 * Requests and responses

    * **Request** (seal.app.request).  The input to an
      application function; it represents a digested HTTP request.
      It also provides global resources to the
      application function.
  
    * **Response** (seal.app.response).  Returned by the
      application function.  Is rendered by the server (or by a WSGI
      adapter) to produce an HTTP response.
  
    * **Authenticator** (seal.app.auth).  In some cases,
      authentication is handled 
      by a third-party web server, and the application may trust the user
      information in the Request to be authentic.  In other cases, the
      application itself must handle authentication, in which case
      the Authenticator sets session information in a Cookie.  That
      information is passed back to the browser when the Response is
      rendered as an HTTP response.  The Authenticator also provides the
      application with an interface for login requests.

 * Server

    * **Server** (seal.app.server).  The web server itself.
      An easy-to-use version of the python web server.

    * **Client** (seal.app.client).  Can be used to call the
      server from software, in lieu of using a web browser.
      Creates an HTTP request and
      sends it to a server.  Receives an HTTP response and packages it
      up as an HTTPResponse object.

 * **WsgiAapp** (seal.app.wsgi).  An adapter that allows an
   application function to be run within a WSGI or CGI script.
   It receives an HTTP request, converts
   it to a Request object, passes the Request to the application
   function, receives a Response,
   and translates the Response to an HTTP response, which it returns to
   the server in accordance with the WSGI protocol.

Persistent-Object Database
..........................

The database provides a hierarchical structure represented by
persistent objects in Python.

The Content Framework
.....................

The Content Framework provides support for implementing an
application that runs within the Server Framework.
In this framework, the pathname portion of a request addresses **web directories,**
with the final component addressing a **web page.**  Web
directories are instantiated as the pathname is processed; the
complete hierarchy is not instantiated.  Subdirectories and pages
correspond to methods of the web directory; different web directories
correspond to different subclasses.

State is not stored in the application function but rather on disk,
within the database.  As a general matter, the web and disk
hierarchies are independent of
one another: the disk hierarchy represents the structure of the data,
whereas the web hierarchy represents the structure of workflows that
apply to the data.  There may well be correspondences, but there may
well also be differences between the two hierarchies.

The main components of the Content Framework are:

 * A **web directory** that can be used to process the pathname
   and post/query parameters of a request.

 * **Page** objects for ease of constructing HTML pages.

 * A **SealApp** class that can be subclassed to define an
   application function.  The subclass itself is the application function: its
   __init__ method is called on a Request, and the resulting instance
   behaves like a Response.  The subclass can provide: (1) a
   method for creating the web-directory at the root of the pathname
   hierarchy, (2) a method for opening the database file.

In addition, selkie.cld.lib contains a collection of Javascript files
that implement client-side behavior. These are not currently documented.
