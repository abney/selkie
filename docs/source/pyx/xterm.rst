
XTerm control-sequence strings — ``selkie.pyx.xterm``
=====================================================

Examples
--------

The functions ``red()`` and ``green()`` set the foreground color for
their argument::

   >>> from selkie.pyx.xterm import red, green, repln
   >>> print(red('hi'), green('bye'))


The function ``repln()`` causes its argument to replace the contents
of the current line.  It does a carriage return and line kill::

   >>> print('hi there')
   >>> print(repln('bye'))

Alternatively::

   >>> print(repln(), 'bye')

Module Documentation
--------------------

.. automodule:: selkie.pyx.xterm

.. py:data:: fg

   Dict mapping color names to escape strings for foreground colors.

.. py:data:: bg

   Dict mapping color names to escape strings for background colors.

.. autofunction:: black
.. autofunction:: red
.. autofunction:: green
.. autofunction:: yellow
.. autofunction:: blue
.. autofunction:: magenta
.. autofunction:: cyan
.. autofunction:: white
.. autofunction:: cursor_right
.. autofunction:: cursor_left
.. autofunction:: goto_column
