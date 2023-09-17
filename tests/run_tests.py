##
##  This tests the version of Selkie installed in the prevailing environment.
##  To test *this* version, run it in the selkie_dev environment.
##

import sys, unittest, doctest
from os import walk
from os.path import abspath, join

# Recursively list .rst files

def rst_files ():
    for (root, dnames, fnames) in walk('../docs/source'):
        for name in fnames:
            if name.endswith('.rst'):
                yield join(root, name)


import selkie
print('Testing:', selkie.__file__)

# Run unit tests

unittest.main(argv=['unittest'], exit=False)

# Run doctests

for fn in rst_files():
    print('doctest', fn)
    doctest.testfile(fn)
