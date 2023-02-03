
.. module:: seal.script
   :synopsis: Executables

Scripts
=======



abspath.html
char.html

Executables reside in the directory ``$SEAL/bin``.  Most of them
are trivial scripts of the form::

   /bin/sh
   exec python -m seal.script.\ *name* "$@"

My general practice is to place executable modules in ``seal.script,``
but they are documented in the Developer's Guides at the place where
their functionality is discussed.

abspath.html
auth.html
char.html
cld.html
dependencies.html
doc.html
doctest.html
encyd.html
glab.html
manifest.html
panlex.html
