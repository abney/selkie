
The Request-Response abstraction
********************************

HTTP request information
------------------------

HTTP requests
.............

The information in a Request to a Seal application
originally comes from an HTTP request.
An HTTP request consists of:

 * Method — GET and POST are currently handled

 * URL

 * Headers — E.g., content-type, content-length

 * Body — For POST requests

The body is consumed in the process of digesting the HTTP request, but
it is preserved in digested form.

A URL has internal structure.
Consider the following example::

   https://abney@foo.com:8000/cgi-bin/app/foo.2.5/edit.1?x=0&y=42

It breaks into a number of pieces:

 * Scheme — https

 * User — abney

 * Host — foo.com

 * Port — 8000

 * External Pathname — /cgi-bin/app/foo.2.5/edit.1

 * Query String — x=0&y=42

When the server processes the incoming HTTP request,
it splits the external pathname into two pieces:
the **root prefix** is
the portion that addresses the CGI script, and the **internal pathname**
is the remainder.  The dividing slash is assigned to
the internal pathname, with the result that the internal pathname has the form
of an absolute pathname.  Conceptually, the internal pathname is an
address within the application's web space.

In our example URL, the external pathname subdivides into:

 * Root prefix — /cgi-bin/app

 * Internal pathname — /foo.2.5/edit.1


CGI environment
...............

When an application runs under a web server, whether it is Apache or
the python web server, the application is invoked within a CGI script,
and the server uses environment variables to pass
the HTTP request to the CGI script.  In particular, each URL piece
just mentioned is assigned to a separate environment variable.
Let us call the collection of environment
variables containing the pieces of an HTTP request
the **CGI environment.**

The convenience function make_environ() can be used to create
a CGI environment.  It is not used in normal processing but can be
useful for testing or illustration.

>>> from selkie.cld.app.env import make_environ
>>> cgienv = make_environ(rootprefix='/cgi-bin/app',
...                       path='/foo.2.5/edit.1',
...                       qs='x=0&y=42',
...                       user='abney')
...
>>> for key in sorted(cgienv):
...     print(repr(key), repr(cgienv[key]))
...
'HTTPS' 'off'
'PATH_INFO' '/foo.2.5/edit.1'
'QUERY_STRING' 'x=0&y=42'
'REQUEST_METHOD' 'GET'
'SCRIPT_NAME' '/cgi-bin/app'
'USER' 'abney'


Within Python, the CGI environment is represented as a dict-like object.
Seal makes use of the values for the following keys:

 * 'SCRIPT_NAME' —  The value is the root prefix, e.g. '/cgi-bin/app'.

 * 'PATH_INFO' —  The value is the internal pathname,
   e.g., '/foo.2.5/edit.1'.

 * 'QUERY_STRING' —  If the method is GET, this
   contains the portion of the URL following "?".

 * 'wsgi.input' —  If the method is PUT, this
   is an open file containing the data portion of the request.

 * 'REQUEST_METHOD' —  The value is 'GET' or
   'POST'.

 * 'USER' —  The user name, when the server is running locally.

 * 'REMOTE_USER' —  The user name, in the case of a
   secure connection with an authenticated user.


Digested environ
................

The Request constructor takes a CGI environment as argument, but it
digests it into a more convenient internal form, that I call
the **digested environment.**  The conversion is done by the
function digest_environ()
of selkie.cld.app.env.
The digest environment is a dict that
contains the following keys:

 * 'original' — 
   The original CGI environment that was passed to digest_environ().

 * 'rootprefix' — 
   The pathname of the CGI script itself.

 * 'pathname' — 
   The internal pathname, excluding the root prefix.

 * 'form' — 
   The digested form, a dict.  Keys have been normalized in that: (1)
   any initial "file:" has been deleted, and (2) any initial "\*" has
   been deleted.  Values are lists if there was originally a "\*", and
   single strings otherwise.

 * 'user' — 
   The alleged username.

 * 'cookie' — 
   A dict.  The empty dict if no cookie is set.

 * 'https_on' — 
   True just in case the request came by HTTPS (based on the
   environment variable 'HTTPS').

 * 'client_addr' — 
   The client address.

Continuing our example:

>>> from selkie.cld.app.config import Config
>>> config = Config()
>>> from selkie.cld.app.env import digest_environ
>>> environ = digest_environ(cgienv, config)
>>> for key in sorted(environ):
...     if key != 'original':
...         print(repr(key), repr(environ[key]))
...
'client_addr' None
'cookie' {}
'form' {'x': '0', 'y': '42'}
'https_on' False
'pathname' '/foo.2.5/edit.1'
'rootprefix' '/cgi-bin/app'
'user' 'abney'

In the example, I skip the value for 'original' because it is
the same as the value of cgienv.

Note that digest_environ() is called by the Request
constructor; users generally have no need to call it directly.

Requests
--------

The components of a Request
...........................

The sole argument to a Seal application function is a
Request, and the
return value is a Response.  There are no side channels between
browser and application, hence all required information must be
packaged into Request and Response.  In particular, cookies used to
maintain state must be included in the Request and Response.

The Request constructor takes two arguments: a CGI environment and a
Resources instance.

A Request has the following members:

 * resources — the Resources instance given to
   the Request constructor.

 * config — a Config instance, taken from resources.

 * log — a Logger instance, taken from resources.

 * server — a Server instance, taken from resources.

 * authenticator — an Authenticator instance,
   created when one calls authenticate().

 * webenv — the digested environment, returned by digest_environ().

 * path — a tuple of URLPathComponent instances, created
   from webenv.

 * username — the authenticated user name, or '' if
   no username is provided or authentication fails.

 * root — an HttpDirectory instance representing
   the root web directory.  Initially it is None, but it is set by
   App.

 * file — the application file.  Initially it is None, but
   it is set by App.

Pathnames
.........
An application generally uses script-internal pathnames to represent locations,
inasmuch as internal pathnames are not affected if the script is moved or renamed.

However, filenames that occur in URLs, particularly in URLs appearing
in links on web pages, must be full external pathnames.
As long as we use relative pathnames, no problem arises.  However, if
we use an absolute pathname like /.lib/default.css, it will cause
the browser to request an invalid location: the browser must instead
request /cgi-bin/app/.lib/default.css.  That is,
before including an
absolute pathname in a web page, we must convert it to external form
by prepending the script location.

Some detailed issues regarding slashes introduce further
complexities.  If a browser requests /foo/bar and the returned
page contains a link to the relative path baz, the browser interprets it
as /foo/baz, whereas if the the browser requests
/foo/bar/, then baz is interpreted as /foo/bar/baz.
That is, the interpretation of a link depends on the presence or
absence of a trailing slash in the URL that the browser used to
request the page.

A Request is careful to preserve the ambiguity, to allow the
application to deal with it appropriately.  Leading and trailing slashes
are never deleted.  Rather, the URL path is split at slashes, yielding
a list of **path components.**  For example, the
path /foo/bar is interpreted as ('', 'foo', 'bar'),
whereas /foo/bar/ is interpreted as ('', 'foo', 'bar', '').

Strictly speaking, a Request should address a page, not a
directory, since only a page can be returned as an HTTP response.
The Request itself cannot determine whether the path addresses a page
or a directory; that is the responsibility of the application.
The App class deals with a
request for a directory by sending the browser a redirect to the
directory's **home page,** whose name is the empty string.  That
is, the redirect adds a trailing slash.

The empty-string component at the beginning of the path
corresponds to the **root directory.**  An empty-string path has a single
empty-string component, which addresses the root directory itself.
The path / corresponds to components ('', ''), which
address, not the root directory, but the home page of the root directory.

Note that one should <i>not</i> use os.path.join with URL pathnames.
Usually it introduces a slash between its
arguments, but not if the leading argument is the empty string:

>>> import os
>>> os.path.join('foo', 'bar')
'foo/bar'
>>> os.path.join('foo', '')
'foo/'
>>> os.path.join('', 'foo')
'foo'

The result we desire is /foo, not foo.

URLPathComponent
................

A pathname component is represented by the class URLPathComponent.
It is a specialization of str, but it also has a record of the full
external pathname corresponding to the component.  One may use
a URLPathComponent's join method to extend the path,
instead of using os.path.join.

In the example introduced above, the request's path consists of three
components:

 * path[0] — '/cgi-bin/app' — '/cgi-bin/app'

 * path[1] — 'foo.2.5' — '/cgi-bin/app/foo.2.5'

 * path[2] — 'edit.1' — '/cgi-bin/app/foo.2.5/edit.1'

The first component represents the root; its pathname is the script location.
Each subsequent pathname is obtained by adding a slash and the next
component's string value.

The Request constructor calls path_from_env() to convert the
digested environment into a path.  To continue our previous example
for the sake of illustration:

>>> from selkie.cld.app.request import path_from_env
>>> path = path_from_env(environ)
>>> for (i, cpt) in enumerate(path):
...     print('[%d]' % i, repr(cpt), repr(cpt.pathname))
...
[0] '/cgi-bin/app' '/cgi-bin/app'
[1] 'foo.2.5' '/cgi-bin/app/foo.2.5'
[2] 'edit.1' '/cgi-bin/app/foo.2.5/edit.1'


Forms
.....

A form is a set of key-value assignments.  Where it
comes from depends on the HTTP request method.
In the case of a GET request, the form comes from the query string in
the URL, and in the case of a POST request, the form comes from the
body of the HTTP request.

The form is translated to a dict of
keyword arguments attached to the final URLPathComponent.
For example, the final URLPathComponent generated from the
URL '/foo.2/edit.1?x=hi&y=there'
has the form dict::

   {'x': 'hi', 'y': 'there'}

There is one nonstandard aspect to my treatment of form information.
I permit variable names to be prefixed with an asterisk, making them
**list-valued.**  For example, the query string
'\*x=2&\*x=5&\*y=hi&z=lo' produces the form dict::

   {'x': ['2', '5'], 'y': ['hi'], 'z': 'lo'}

Calls
.....

A path component is parsed into a **call** by splitting it at
dots.  The first element is the **component name,** and the
remaining elements are positional arguments.  The call also contains a
keyword-arguments dict.  For the last component, it consists of the
form information, and for other components, it is an empty dict.

For example:

>>> for (i, cpt) in enumerate(path):
...     print('[%d]' % i, cpt.call)
...
[0] None
[1] ('foo', ('2', '5'), {})
[2] ('edit', ('1',), {'x': '0', 'y': '42'})

There is no call for the first path component.  The first component
is associated with the root directory, and each call addresses
a child (subdirectory or page) of the previous component.

Miscellany
..........

In addition to the path and form, the request extracts two further
pieces of information from the URL:

 * user - The name of the user, as provided in the URL or environment.

 * is_secure - True if the scheme is https, False otherwise.

Two further pieces of information are included in an HTTP request, but
are not part of the URL:

 * cookie - A string containing key-value pairs.  Key and
   value are separated by '=', and pairs are separated
   by ';'.

 * client_addr - The address of the client.

Response
--------

A Response packages up the information needed to produce an HTTP
response.  There are two cases: regular responses and redirect
responses.

Regular responses
.................

A regular response is created by providing
the contents and optionally
a code, content_type, and authenticator.

 * contents - An iteration that may contain strings, bytes,
   and byte-arrays.

 * code - The legal values are part of the HTTP
   specification.  A subset is currently supported, given in the table
   below.  The default value is 200 (OK).

 * content_type - A filename suffix.  The table of supported
   values is given below.  The default value is 'txt'.

 * authenticator - Created when one authenticates a
   Request.

Redirect responses
..................

A redirect is created by providing code=303, in which case
one must also provide the keyword argument location to
specify which URI to redirect to.  No other arguments are
permitted.

Code and suffix tables
......................

The following table lists the HTTP status codes that are currently used,
along with the corresponding messages:

 * 200 — OK

 * 303 — See Other

 * 400 — Bad Request

 * 404 — Not Found

 * 500 — Internal Server Error

The following table lists the currently recognized filename suffixes,
along with the corresponding Mime type and character encoding.
An encoding of None indicates binary data.

 * css — text/css — us-ascii

 * gl — text/x-glab — utf-8

 * html — text/html — utf-8

 * js — application/javascript — us-ascii

 * pdf — text/pdf — None

 * txt — text/plain — utf-8

 * wav — audio/wave — None

Authentication
--------------

Authenticator
.............

The locus of authentication is the class Authenticator (selkie.cld.app.auth).
Authentication is done separately for each Request; an
Authenticator is instantiated when one calls the
request's *authenticate* method.  Request.authenticate dispatches
to Authenticator.authenticate, and the result
is a username, which is stored both in the Authenticator and in the
Request.  On authentication failure, the username is the empty string.

The application function may interact with the authenticator by
calling the following methods of Request:

 * authenticate() - Do authentication; sets <i>username.</i>

 * login(user, password) - Log in; sets <i>username</i> on either
   success or failure.

 * logout() - Log out; sets <i>username</i> to the empty string.

 * change_password(old,new) - Updates the user's password, if the old
   password is correct.

Those methods of Request hand off to methods of Authenticator, listed below.

Changes in the username must be passed back to the client in the form
of a cookie.  That happens in the method Response.http_headers, which
calls Authenticator.response_headers() and includes the resulting
headers (if any) among the headers that are passed back to the
client.

There is one last connection needed to close the loop.  When creating
the Response, one must pass the Authenticator to the Response
constructor.  If one defines the application function using the App
framework described below (Chapters 13-16), a web page is a
specialization of Item, and maintains an internal pointer to the
Request in its *context* member.  The Response constructor is
called in the Item method to_response,
which takes the Authenticator from the request and passes it to the
Response constructor.  The to_response method is called in
App.__call__.

The members and methods of Authenticator are:

 * auth — 
   The Authenticator, but only if the request comes
   over a secure connection.

 * username — 
   The name of the user, if authenticated.

 * cookie — 
   When the user logs in, a session token is
   created and is stored client-side in a cookie.  Whenever the cookie
   is modified, the updated information is sent back to the client by
   the Response instance.

 * authenticate() — 
   This method is automatically called when
   the Context is created.  If the client passes a cookie along with
   the request, and the authenticator checks that the token matches the session key stored for the
   user in the session file, and that the session key has not expired.
   The session key expires after a certain period, but each time the
   key is used, the clock restarts.

 * login(user, password) — 
   Uses the authenticator to log in the user.  On success, the
   username is set and the cookie is updated.  The authenticator also
   creates a new session key, overwriting any previous one.

 * logout() — 
   The session key is deleted, but only if the current user has a
   valid token.  In any case, the cookie is cleared.

 * change_password(oldpass, newpass) — 
   The user's password is changed to *newpass*, but only
   if *oldpass* authenticates.  Changing the password does not in
   itself terminate the current session, even though it was starting
   using the old password.  But any subsequent calls to login() or
   change_password() will need to use the new password.

 * response_headers() —
   Called by Response's *http_headers* method.  This returns an
   iteration over 'Cookie' headers that pass username and token
   information back to the web client.

The Auth script
...............

The auth script is used to manage authentication files.
There are two files that the authenticator makes use
of, users.txt and sessions.txt, both located in the
directory config['auth_dir'].

The auth script assumes that the current working directory is the
authentication directory, and it uses or modifies ./users.txt
and ./sessions.txt.
The following provide examples of usage::

    $ auth ls            # lists the users
    $ auth set uname     # prompts for password, saves it
    $ auth check uname   # prompts for password, checks it
    $ auth delete uname

