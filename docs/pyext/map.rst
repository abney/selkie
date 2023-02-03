
``selkie.map`` — The Index class
================================

.. py:class:: selkie.map.Index

   A dict that associates multiple values (a list) with
   each key.  For example:
   
   >>> from selkie.map import Index
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

.. py:class:: selkie.map.Object

   Generic object whose members can be freely set.
