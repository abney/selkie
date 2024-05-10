
Command line — ``selkie.pyx.com``
=================================

.. automodule:: selkie.pyx.com

.. autofunction:: file_size
.. autofunction:: wget

.. py:data:: more

The function ``more()`` calls ``print`` on each item in turn,
pausing after a pageful of items has been displayed.  Hitting return
causes another page to be displayed, and hitting 'q' then enter causes
``more()`` to quit.

One can adjust the pagesize by setting ``more.pagesize``.  For
example::

   >>> from selkie.pyx.com import more
   >>> more.pagesize = 4
   >>> more(pots())       # doctest: +SKIP
   1
   2
   4
   8
   q

Shell calls
-----------

.. autofunction:: system
.. autofunction:: backtick
.. autofunction:: run_command
.. autofunction:: strip_escapes

Command-line processing
-----------------------

.. autoclass:: Shift
.. autoclass:: Main
