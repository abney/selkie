
Command-line usage
==================

Download a snapshot from ``https://db.panlex.org/`` and unzip it.
Unzipping takes about a minute and takes up about 5.4 GB of disk
space::

   $ unzip panlex-YYYYMMDD-csv.zip
   # output: panlex-YYYYMMDD-csv

Create a target directory and cd to it::

   $ mkdir panlex-YYYYMMDD
   $ cd panlex-YYYYMMDD

Examples of commands::

   $ python -m selkie.panlex install varieties
   $ python -m selkie.panlex varieties swe
   $ python -m selkie.panlex install swe

