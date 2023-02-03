
``selkie.object`` — Types, reflexion, generic object
====================================================

.. py:function:: string_to_module(s)

   Given a string representing a qualified module name, to get the
   module::
   
      >>> from selkie.object import string_to_module
      >>> m = string_to_module('foo.bar')
   
   (This actually just calls ``importlib.load_module``.)

.. py:function:: string_to_object(s)

   Given a string representing a function, class, etc. within a qualified
   module name, to get the object::
      
      >>> from selkie.object import string_to_object
      >>> f = string_to_object('foo.bar.my_function')
      >>> cls = string_to_object('foo.bar.MyClass')

.. py:class:: Object()

   Essentially, a dict that permits keys to be accessed and set using
   dot syntax as well as square-bracket syntax::

      >>> from selkie.object import Object
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
   
   >>> from selkie.object import matches
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
