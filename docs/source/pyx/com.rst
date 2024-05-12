
Command line — ``selkie.pyx.com``
=================================

.. automodule:: selkie.pyx.com

.. autofunction:: file_size
.. autofunction:: wget

.. py:data:: more

The function ``more()`` calls ``print`` on each item in turn,
pausing after a pageful of items has been displayed.  Hitting return
causes another page to be displayed, and hitting 'q' then enter causes
``more()`` to quit.

One can adjust the pagesize by setting ``more.pagesize``.  For
example::

   >>> from selkie.pyx.com import more
   >>> more.pagesize = 4
   >>> more(pots())       # doctest: +SKIP
   1
   2
   4
   8
   q

Shell calls
-----------

.. autofunction:: system
.. autofunction:: backtick
.. autofunction:: run_command
.. autofunction:: strip_escapes

Command-line processing
-----------------------

.. py:class:: Main

   Main provides command-line processing for a Python script.  To use it,
   subclass it and define methods whose name begins with ``com_``.  For
   example::
   
      class MyMain (Main):
   
          def com_foo (self, x, y, t=None): ...
          def com_foo_bar (self, y): ...
   
   To use it::
   
      if __name__ == '__main__':
          main = MyMain()
          main()
      
   When calling the script::
   
      python -m mymodule foo -t=42 hi bye
      python -m mymodule foo hi bye
      python -m mymodule foo bar bye
   
   In cases of ambiguity, a word is preferentially taken to be a
   continuation of the command name.  The invocations just given
   translate to the following calls::
   
      main.com_foo('hi', 'bye', t='42')
      main.com_foo('hi', 'bye')
      main.com_foo_bar('bye')
   
   
   A help command (invoked by ``-?`` or ``--help``) is automatically
   generated from the method signatures, the documentation string of the
   class, and the documentation strings of the methods.


   .. py:method:: __call__(comline)

      If *comline* is omitted, sys.argv is used.  The command line
      should have the form: *command* *flags* *args*.  A method must
      exist whose name is *command* prefixed with ``com_``.  Its
      positional arguments determine the number and interpretation of
      the *args*, and its keyword arguments determine the valid
      *flags*.  A flag must have the form ``-fKW=VAL``, where *KW* is
      a keyword argument and *VAL* is the value that it receives.
      ``=VAL`` may be omitted, in which case the value is True.

      *Comline* may also have the form ``-?`` or ``--help``, in which
      case a usage message is printed.  The usage message is assembled
      from:

       * the class documentation string (of the class specializing Main).
       * the parameter names of the command methods (those whose names
	 begin with ``com_``).
       * the documentation strings of the command methods.

.. py:class:: selkie.com.Shift

   A command-line processor that Main uses internally.  Use it in a
   with-statement::
   
      with Shift() as shift:
          ...
   
   .. py:method:: __call__(tgt)

      Returns the next argument and advances its internal pointer.
      *Tgt* is optional.  If provided, Shift advances the
      pointer and returns ``True`` if the next argument equals *tgt*,
      and does nothing and returns ``False`` otherwise.

   .. py:method:: able()

      Returns True just in case ``__call__()`` will succeed.  (Note that
      ``__call__(tgt)`` always succeeds.)

   .. py:method:: error(msg)

      Prints an error message and usage to stderr, then exits.

   .. py:method:: peek(tgt)

      Return the next argument without consuming it.  *Tgt* is
      optional and interpreted as for ``__call__()``.

   .. py:method:: isflag()

      Returns ``True`` if the next argument begins with
      ``-``.

   .. py:method:: flag()

      Returns the next argument, if it is a flag.  Returns
      ``None`` otherwise.

   .. py:method:: ifable()

      Returns the next argument, if it exists.  Returns
      ``None`` otherwise.

   .. py:method:: rest()

      Returns all remaining arguments.

   .. py:method:: isdone()

      Returns true if no arguments remain.

   .. py:method:: set_usage(msg)

      Sets the usage message.

   .. py:method:: print_usage()

      Prints out the usage message.

Timeout
-------

.. py:class:: Timeout

A ``with Timeout()`` block can be used to limit the amount of
time that some code can run::

   with Timeout(2.0):
       value = do_something()

A timer will run for 2.0 seconds, at which point the body code will be
interrupted (using a KeyboardInterrupt, equivalent to ctrl-C).  If the
body code completes before the timer goes off, the timer will be
cancelled.

One can use the effects of the body to determine whether it completed
successfully (in the example, by looking at ``value``).
Alternatively, Timeout takes a second argument, ``ontimeout``, which is a function
that will be called if the body is interrupted by the timer.

Timing
------

One can create a timer::

   >>> timer = Timer() # doctest: +SKIP

Every time one calls ``str()`` on it, one obtains a printed version
of the elapsed time since it was created::

   >>> print timer # doctest: +SKIP
   0:00:03.316634

The function that ``Timer`` uses for printing is separately
available as ``selkie.string.elapsed_time_str()``.

Progress indicator
------------------

To create a progress indicator::

   >>> from sys import stdout
   >>> from selkie.pyx.com import Progress
   >>> progress = Progress(10, file=stdout)

The value *n* is the total number of "work units" that will be necessary.
To cause a progress message to be printed, increment the indicator::

   >>> progress += 1 # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
   Progress: 1/10 (10.00%) Time remaining: ...

One may also call Progress() with no arguments, in which case the
number of ticks will be reported, with no estimate of time remaining.
