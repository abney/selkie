
``selkie.data`` — The data directory
====================================

.. py:function:: path(*names)

   Returns an object representing a pathname relative to the
   ``selkie.data`` directory.  It can be passed to ``open()`` as a
   filename as is, and it can be converted to a string.

.. py:function:: ex(*names)

   A shorthand for ``path('examples', *names)``.
