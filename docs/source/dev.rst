
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
tests; each can also be executed separately. The invocations are::

   $ make dist    # tester.run_dist_test()
   $ make rst     # tester.run_rst_tests()
   $ make unit    # tester.run_unittests()
   $ make doc     # tester.run_doctests()

The test classes are as follows.

 * Distribution quality checks

    - Check imports. Make sure that every module in the src directory imports without
      error.

    - Check doc modules. Walk the documentation directory and find all
      ``.. automodule::`` and ``.. py:module::`` references. Make sure
      they are found in the src directory.

 * Documentation doctests.
   Walk the docs directory to find all ``.rst`` files, and call
   doctest on each. One can also test individual files manually by
   cd-ing to the directory in which it resides and doing ``python -m
   doctest XXX.rst``.

 * Unit tests.
   Run the unit tests in the tests directory.

 * Standalone doctests.
   Go to the subdirectory tests/doctests. Run doctest on each file
   with file suffix ``.doctest``. One can also test individual files
   manually by cd-ing to the tests/doctests directory and doing
   ``python -m doctest XXX.doctest``.
