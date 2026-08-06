
Development
===========

Testing
-------

To run all tests, do::

   $ cd tests
   $ make

This runs the python file ``run_tests.py``. That file consists of a
class definition for ``Tester``; running the file instantiates Tester
and calls it with argument ``:all``. This executes four varieties of
tests; each can also be executed separately:

 * Distribution quality checks (``:dist``, method ``run_dist_test()``).

    - Check imports. Make sure that every module in the src directory imports without
      error.

    - Check doc modules. Walk the documentation directory and find all
      ``.. automodule::`` and ``.. py:module::`` references. Make sure
      they are found in the src directory.

 * Documentation doctests (``:rst``, method ``run_rst_tests()``).
   Walk the docs directory to find all ``.rst`` files, and call
   doctest on each.

 * Unit tests (``:unit``, method ``run_unittests()``).
   Run the unit tests in the tests directory.

 * Standalone doctests (``:doc``, method ``run_doctests()``).
   Go to the subdirectory tests/doctests. Run doctest on each file
   with file suffix ``.doctest``.

