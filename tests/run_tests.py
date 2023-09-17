
import sys, unittest, doctest
from os import walk
from os.path import abspath, join

# Recursively list .rst files

def rst_files ():
    for (root, dnames, fnames) in walk('../docs/source'):
        for name in fnames:
            if name.endswith('.rst'):
                yield join(root, name)


# if 'local', make sure I'm getting the local selkie module

if len(sys.argv) > 1 and sys.argv[1] == 'local':
    src = abspath('../src')
    sys.path[0:0] = [src]
    import selkie
    assert selkie.__file__ == join(src, 'selkie', '__init__.py')
else:
    import selkie

print('Testing:', selkie.__file__)

# Run unit tests

unittest.main(argv=['unittest'], exit=False)

# Run doctests

for fn in rst_files():
    print('doctest', fn)
    doctest.testfile(fn)
