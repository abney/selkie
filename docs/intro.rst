
Introduction
============

Selkie is a library of functionality to support **computational
documentary and descriptive linguistics**, or, more briefly,
**language digitization**.

 * Machine learning
 * Datasets
 * User interface infrastructure
 * Computational language documentation/description
 * Executables

Installation
------------

Install it in the usual way::

    $ pip install selkie

Development
-----------

The package directory is laid out as follows.

 * ``README.md``, ``LICENSE`` — Front material.
 * ``pyproject.toml``, ``setup.cfg``, ``MANIFEST.in`` — Metadata for
   *build* and *pip*.
 * ``src`` — Python source code.
 * ``public`` — Static assets for web server.
 * ``js`` — Javascript source files.
 * ``docs`` — Documentation.
 * ``dev`` — Workspace used during build.
 * ``tests`` — Unit tests.

In addition, the following files and directories are created by tools.

 * ``dist`` — Created by build.
 * ``docs/_build`` — Created by sphinx.
 * ``dev/_env`` — Virtual environment.
 * ``dev/app``, ``dev/node_modules``, ``dev/package[-lock].json`` — Created by npm.

The following are commands used during code development.  It is
assumed that ``dev`` is the current working directory.

 * ``make`` — Create the development environment.
 * ``make docs`` — Creates or updates ../docs/_build/html.

The following is the procedure I use for web app development.

 * Start the application back end.  For example::

      >>> python -m selkie.corpus open -nw foo.lgc

 * Start the front end::

      $ cd $SELKIE/client
      $ npm start

Eventually, I need to separate out the generic client code and make it
available on npm.

Acknowledgements
----------------

The following icons in ``data/seal`` are from
``gnome-icon-theme-3.12.0``:

 * ``cog.png``
 * ``gnome/16x16/categories/applications-system.png``
