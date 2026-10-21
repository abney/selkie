
Overview
========

Invocation
----------

The module ``selkie.editor`` is executable. It creates and
runs a wap Application, which launches the application in a browser.

Whether or not the editor is invoked from the command line, the
browser-side entry point is ``Editor(ServerConnection(servlet_name))``, or
``Editor(None)`` if no connection to the server is available.

The Editor
----------

The Editor is instantiated with a ServerConnection, and the attribute
``server`` is set to point to it. The attribute ``registry`` is set to an empty Registry, and
``selected`` is set to None. Then the registry is edited (that is, it is
passed to the Editor method ``edit()``.) The Editor's main method is:

 * **Edit.** When an item is edited, it becomes the editor's ``selected`` item,
   and its ``select()`` method is invoked. Then the HTML document is
   cleared and the Page of the item's current view is instantiated,
   passing in the current view as argument. Page is a subclass of
   ``wap.ui.Element``.

Most of the work is actually done by the subclasses of Page, which
generally inherit from StandardPage. The editor does provide some
support methods:

 * **Open corpus.** Clear the document, print a "loading" method, and
   issue a request to the server. When the corpus is loaded, it is
   passed to ``edit()``.

 * **Create corpus.** Call the registry's ``new()`` method and edit
   the resulting new corpus.
