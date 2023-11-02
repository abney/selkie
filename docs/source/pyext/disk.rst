
``selkie.disk`` — Virtual disk
==============================

.. automodule:: selkie.disk

.. autoclass:: BaseDisk

   .. automethod:: __iter__
   .. automethod:: __contains__(name)
   .. automethod:: __getitem__(name)
   .. automethod:: __setitem__(name, value)
   .. automethod:: __delitem__(name)
   .. automethod:: iterdirectory(name)
   .. automethod:: physical_pathname(name)
   .. automethod:: __len__()
   .. automethod:: keys()
   .. automethod:: items()
   .. automethod:: values()
   .. automethod:: HEAD(fn)
   .. automethod:: GET(fn)
   .. automethod:: PUT(fn, value)
   .. automethod:: DELETE(fn)

.. autoclass:: Directory

   .. automethod:: __init__(disk, name)
   .. automethod:: physical_pathname(name=None)
   .. automethod:: __iter__(self)
   .. automethod:: __getitem__(name)
