
``selkie.doctest`` — Extract doctest from HTML, tex
===================================================

.. program:: doctest

The script ``doctest`` provides a quick way to test python examples
in Tex documentation.  It creates a file suitable for the ``doctest``
module, and calls :py:func:`testfile` on it.

Extraction
----------

Doctest currently accepts two different input formats: html and tex.
In each case, two different kinds of test blocks are extracted, one
that is intended for printing and one that is "hidden."  Specifically, the
patterns are as follows:

.. list-table::

 * - Format
   - Start
   - End
 * - html
   - ``<pre>``
   - ``</pre>``
 * - html
   - ``<!--[python``
   - ``]-->``
 * - tex
   - ``\begin{python}``
   - ``\end{python}``
 * - tex
   - ``%[python``
   - ``%]``

In the last case (only), lines within the block begin with ``"% "`` (percent-space).
That prefix is deleted when extracting the block.

For example, suppose the file ``foo.tex`` has the following
contents::

   \documentclass{article}
   \begin{document}
   
   This is an example.
   
   \begin{python}
   >>> 2 + 2
   4
   \end{python}
   \end{document}

Calling ``doctest`` on it produces the following result::

   $ doctest foo
   1 test(s) found, all passed

If one changes the "4" to "5," the result is::

   $ doctest foo
   **********************************************************************
   File "/tmp/doctest.24869.test", line 1, in doctest.24869.test
   Failed example:
       2 + 2
   Expected:
       5
   Got:
       4
   **********************************************************************
   1 items had failures:
      1 of   1 in doctest.24869.test
   ***Test Failed*** 1 failures.

If the filename ends with ``.tex``, the suffix is stripped, so
one can run doctest on all tex files in a directory by doing::

   $ doctest *.tex
