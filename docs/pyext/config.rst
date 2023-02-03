
.. py:module:: selkie.config


``selkie.config`` — Configuration
=================================

The Selkie user configuration file is ``~/.selkie``.  (One may change
the filename by setting the environment variable ``SELKIE_CONFIG``.)
Here is a fragment of an example::

   data :
      conll ~/cl/data/conll
      panlex :
         dirname |panlex-20190901-csv
         tgtdir ~/cl/data/panlex

To access it::

   >>> from selkie.config import config
   >>> config.data.conll
   '~/cl/data/conll'

The configuration file is in :ref:`kvi`.
