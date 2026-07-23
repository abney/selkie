
The WAP API — ``selkie.wap``
============================

.. py:module:: selkie.wap

.. py:function:: exec_app(f)

   Reads sys.argv and executes the command.
   It reads the WAP config file ``~/.wap``, if it exists.
   Then it instantiates WapApplication and calls its execute()
   method.

.. py:class:: WapApplication

   
