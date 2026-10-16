
UI elements
===========

In addition to the framework for launching an application, the WAP
provides a library of UI elements, built on top of the elements
provided by the DOM.

Overview
--------

All UI elements are specializations of ``Element``.
Element is instantiated with a parent element, an HTML tag, and
(optionally) keyword arguments that set attributes of the resulting
HTML node. One does not usually instantiate Element directly,
however. For predefined Element subclasses, one should use the class
name as a method of the parent. For example, to create a paragraph in
the document::

   document.P()

The parent is automatically set to ``document``, the HTML tag is set
automatically, and the paragraph is added to the list of children of
the document.

When defining new specializations of Element, one may instead use
the ``create()`` method. For example, the Button method is defined as
follows::

   def Button (self, text=None, action=None):
       return self.create(Button, text=text, action=action)

The Button class, in turn, is defined as a subclass of Element. The
init method stores the text and action for its own use, and
initializes the Element with the appropriate label and attributes::

   class Button (Element):
       def __init__ (self, parent, text=None, action=None):
           Element.__init__(self, parent, 'button', type='button')
           ...

API
---

.. py:class:: selkie.wap.ui.Element

   .. py:attribute:: parent

      The parent Element.

   .. py:attribute:: document

      The document, of class Document.

   .. py:attribute:: style

      The HTML style.

   .. py:method:: create(cls, *args, **kwargs)

      The Element whose 'create()' method is being called is the parent.
      The class *cls* is instantiated, with the parent as first
      argument. The newly created element is appended to the
      parent. The return value is the newly created element.

   .. py:method:: set_attribute(key, value)

      *Key* and *value* are both strings. Sets an attribute on the
      underlying HTML node.

   .. py:method:: add_listener(name, action)

      Adds an event listener. The *name* is a string, and the *action*
      should be a function that takes an HTML event as argument. The
      function will be suitably wrapped, so that when the wrapper is
      called in Javascript, the python action is executed.

   .. py:method:: focus()

      Focus this element.

   .. py:method:: clear()

      Delete all children of this element.

   .. py:method:: delete()

   .. py:method:: write(*objs, end='\n')

      Appends an HTML text node whose contents are the string
      representations of the given objects (using ``str()``).

   .. py:method:: br()

      Appends an HTML BR node.

   .. py:method:: Button()

      Append a button to this element. Keyword argument ``text``
      provides the text displayed on the button, and ``action``
      provides an action to be invoked when the button is pressed.

   .. py:method:: Element(label)

      Append an Element to this one.

   .. py:method:: DictEditor(dct)

      Appends a DictEditor to this element. A DictEditor takes a dict
      and an action (keyword argument ``action``). It displays the
      dict items as a table in which the values can be editted. When a
      value is editted, the dict is updated and the action is called
      with two arguments: the key and the new value.

   .. py:method:: Div()

      Appends a Div to this element.

   .. py:method:: H1(s)

      Appends a first-level heading with text *s* to this element.

   .. py:method:: H2(s)

      Appends a second-level heading with text *s* to this element.

   .. py:method:: H3(s)

      Appends a third-level heading with text *s* to this element.

   .. py:method:: H4(s)

      Appends a fourth-level heading with text *s* to this element.

   .. py:method:: LI()

      Appends a list item to this element, which should be a list.

   .. py:method:: MenuBar()

      Appends a MenuBar to this element. (See class MenuBar.)

   .. py:method:: P()

      Appends a paragraph to this element.

   .. py:method:: Row()

      Append a table row to this element (which should be a table).

   .. py:method:: Table()

      Append an HTML table to this element.

   .. py:method:: TD()

      Append a table cell to this element (which should be a table row).

   .. py:method:: TextEntry()

      Append a TextEntry object to this element. A TextEntry is a
      generalization of a text box and a text area. One can specify
      the number of rows of text using the keyword argument ``rows``;
      the default is one. A TextEntry with one row is a text box, and
      one with multiple rows is a text area. One can provide initial
      text for the entry using keyword argument ``init``. One uses the
      keyword argument ``submit`` to provide an action to execute when
      enter is pressed. It will be called with the text that has been
      entered.

   .. py:method:: TH()

      Append a header cell to this element (which should be a table row).

   .. py:method:: UL()

      Appends a bullet list to this element.

   .. py:method:: Upload(action)

      Append an Upload object to this element. Displays a "browse"
      button which can be used to select a filename. When a filename
      is selected, its contents are uploaded as an UploadedFile
      object, and passed as argument to *action*. An UploadedFile
      object has two attributes: ``name`` and ``contents``. Both have
      string values.

.. py:class:: MenuBar

   A MenuBar is a horizontally-arranged collection of menus.

   .. py:method:: Menu(title, action=None, [arg, ...])

      Appends a new Menu. It displays as a link with the given *title*
      text. Hovering over the title causes the menu items to display as a
      (temporary) vertical list. The title itself also behaves like a
      menu item, with the given *action* and *args*. Clicking on a
      menu item invokes its action on its args. A menu item with no
      action is not clickable, and its title is grayed out.

.. py:class:: Menu

   A menu in a menu bar.

   .. py:method:: MenuItem(string, action, [arg, ...])

      Appends a MenuItem to the menu.
      The menu item displays as a link with the given *string* as text. Clicking on
      the link causes the *action* to be invoked on the *args*.

