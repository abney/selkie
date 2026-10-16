
UI elements
===========

In addition to the framework for launching an application, the WAP
provides a library of UI elements, built on top of the elements
provided by the DOM.

Element
-------

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

When definining new specializations of Element, one may instead use
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

   
