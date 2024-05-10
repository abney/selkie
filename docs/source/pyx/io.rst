
Input/output — ``selkie.pyx.io``
================================

.. automodule:: selkie.pyx.io

Filename suffixes
-----------------

.. autofunction:: ispathlike
.. autofunction:: strip_suffix
.. autofunction:: split_suffix
.. autofunction:: get_suffix

Syntax
------

.. autoclass:: Token
.. autoclass:: Syntax

Special streams
---------------

.. function:: pprint(*strs)
.. autofunction:: tabular

.. py:function:: redirect()

   Example::
   
      with redirect() as s:
          pprint('foo')
          with pprint.indent():
              pprint('bar')
          return str(s)

.. autoclass:: BackingSave
