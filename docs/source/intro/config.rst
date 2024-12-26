
Config — ``selkie``
===================

There are two items in the toplevel selkie module, outside of all
submodules.

 * ``selkie.__version__`` is a string giving version information (major.minor.patch).

 * ``selkie.config`` is a dict that is loaded from the Selkie
   configuration file. If the environment variable ``SELKIE_CONFIG`` is
   set, it will be used as the configuration file pathname. Otherwise,
   the pathname is ``~/.selkie.json``. The contents are in standard JSON
   format. They must be enclosed in braces, which is to say, they must
   define a dict.

   Various pieces of Selkie's functionality make use of settings in
   ``selkie.config.`` Each is documented separately.
