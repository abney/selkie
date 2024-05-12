
.. automodule:: selkie.cld.seal.misc

Types, reflexion, generic object — ``selkie.cld.seal.misc``
===========================================================

.. py:function:: string_to_module(s)

   Given a string representing a qualified module name, to get the
   module::
   
      >>> from selkie.cld.seal.misc import string_to_module
      >>> m = string_to_module('foo.bar')
   
   (This actually just calls ``importlib.load_module``.)

.. py:function:: string_to_object(s)

   Given a string representing a function, class, etc. within a qualified
   module name, to get the object::
      
      >>> from selkie.cld.seal.misc import string_to_object
      >>> f = string_to_object('foo.bar.my_function')
      >>> cls = string_to_object('foo.bar.MyClass')

.. py:class:: Object()

   Essentially, a dict that permits keys to be accessed and set using
   dot syntax as well as square-bracket syntax::

      >>> from selkie.cld.seal.misc import Object
      >>> x = Object()
      >>> x['hi'] = 10
      >>> x.bye = 20
      >>> x.hi
      10
      >>> x['bye']
      20

.. py:function:: matches(x, desc)

   *X* is an object and *desc* is a dict,
   interpreted as a description, in which the keys are attributes and the
   values are required values.  The return value is ``True`` or
   ``False``, indicating whether the object matches the description.
   
   >>> from selkie.cld.seal.misc import matches
   >>> class Point (object):
   ...     def __init__ (self, x, y):
   ...         self.x = x
   ...         self.y = y
   ...     def L1_norm (self):
   ...         return abs(self.x) + abs(self.y)
   ...
   >>> p = Point(2, -4)
   >>> matches(p, {'y': -4, 'x': 2})
   True
   >>> matches(p, {'y': 0})
   False
   >>> matches(p, {'foo': 'bar'})
   False
   
   If a value specification is a list, then the actual value can be any
   member of the list.
   
   >>> matches(p, {'x': [0,1,2]})
   True
   
   If the named attribute is a method, then it is called to get the value
   that is compared to the description's value.
   
   >>> matches(p, {'L1_norm': 6})
   True
   
   A ``None`` in the description functions as a wildcard.  It matches
   any object.
   
   >>> matches(p, {'foo': None})
   True

.. py:class:: FunctionInfo (fnc)

   A FunctionInfo object provides easy-to-use reflexion for functions.

   .. py:attribute:: args

      The names of the positional arguments (a list of strings).

   .. py:attribute:: kwargs

      A list containing pairs of optional/keyword argument and its
      default value.  Technically, these are optional arguments rather
      than true keyword arguments (which follow a ``*`` argument).

   .. py:attribute:: doc

      The lines of the doc string, eliminating any indentation
      (a list of strings).

.. py:function:: MethodInfo (method)

   Returns a FunctionInfo object.  The ``self`` argument is not
   included among the args.

.. py:class:: ListProxy

   A mix-in class.  The main class must have a method ``__list__``
   that returns an underlying list.  ListProxy
   implements the following methods by dispatching to the underlying list:
   ``__iter__``, ``__contains__``, ``__getitem__``,
   ``__len__``, ``__repr__``.

.. py:class:: MapProxy

   A mix-in class.  The main class must have a method ``__map__`` that
   returns an underlying dict.  MapProxy implements the following
   methods by dispatching to the underlying dict:
   ``__iter__``, ``__len__``, ``__contains__``, ``__getitem__``,
   ``get``, ``keys``, ``values``, ``items``, ``__repr__``.

.. py:class:: LazyList(ListProxy)

   A delayed version of ListProxy.  The initializer is called with a
   function that iterates over the members of the underlying list.
   They are then cached, and ``__list__()`` returns the cached list,
   to which the ListProxy methods dispatch.

   .. py:method:: __init__ (self, iterf):

      *Iterf* should be a callable that returns an iteration over the
      underlying list.  N.b.: if one calls ``__iter__()`` and then any
      method that dispatches to ``__list__()``, the *iterf* will be
      called multiple times.  It should return a fresh iteration each
      time.

   .. py:method:: __iter__()

      If ``__list__()`` has not previously been called, this calls the
      iteration function directly.  Otherwise, it iterates over the
      cached list.

   .. py:method:: __repr__()

      Displays as ``[...]`` if the underlying list has not been
      cached.  Dispatches to the cached list, otherwise.


.. py:class:: Index

   A dict that associates multiple values (a list) with
   each key.  For example:
   
   >>> from selkie.nlp.map import Index
   >>> index = Index()
   >>> index['hi']
   []
   >>> index.add('hi', 10)
   >>> index['hi']
   [10]
   >>> index.add('hi', 42)
   >>> index['hi']
   [10, 42]
   
   .. py:method:: count(key)

      Returns the number of items for a given key:
      
      >>> index.count('hi')
      2
   
   .. py:method:: values()

      Returns the concatenation of all the lists.
      
      >>> index.add('bye', 20)
      >>> sorted(index.values())
      [10, 20, 42]
   
   .. py:method:: itervalues()

      Iterates over all values.
   
   .. py:method:: delete(key, value)

      Deletes a value out of the list of values.
   
      >>> index.delete('hi', 10)
      >>> index['hi']
      [42]
