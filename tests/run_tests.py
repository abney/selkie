##
##  This tests the version of Selkie installed in the prevailing environment.
##  To test *this* version, run it in the selkie_dev environment.
##

import unittest, doctest
from sys import stdout
from os import walk
from os.path import dirname, join
from checkdist import DistChecker

here = dirname(__file__)
rootdir = dirname(here)
docdir = join(rootdir, 'docs', 'source')

skip = ['nlp/glab.rst',
        'nlp/fst.rst',
        'nlp/dp/parser.rst',
        'nlp/dp/eval.rst',
        'nlp/dp/mst.rst',
        'nlp/dp/features.rst',
        'nlp/dp/nnproj.rst',
        'nlp/dp/nivre.rst',
        'nlp/dp/ml/cluster.rst',
        'data/corpora.rst',
        'data/wiktionary.rst',
        'data/panlex/panlex2.rst',
        'data/panlex/panlex_module.rst',
        'editor/corpus/corpus.rst',
        'editor/server/disk.rst',
        'cld/imp/content/requests.rst',
        'cld/imp/content/elt.rst',
        'cld/imp/content/framework.rst',
        'cld/imp/content/responses.rst',
        'cld/imp/server/server.rst',
        'cld/imp/server/wsgi.rst',
        'cld/imp/server/app_toplevel.rst',
        'cld/imp/server/resources.rst',
        'cld/imp/server/python_servers.rst',
        'cld/imp/db/database.rst',
        'cld/imp/db/db_toplevel.rst',
        'cld/corpus/token.rst',
        'cld/corpus/corpus.rst',
        'cld/corpus/langdb.rst',
        'cld/corpus/language.rst',
        'cld/corpus/text.rst',
        'cld/corpus/media.rst',
        'cld/pyext/fs.rst',
        'cld/pyext/config.rst',
        'cld/pyext/io.rst',
        'cld/pyext/com.rst',
        'cld/pyext/misc.rst',
        'pyx/table.rst',
        'pyx/xterm.rst',
        ]

skip = set(join(docdir, path) for path in skip)

def rst_files ():
    for (root, dnames, fnames) in walk(docdir):
        for name in fnames:
            if name.endswith('.rst'):
                fn = join(root, name)
                if fn not in skip:
                    yield fn

def test_files ():
    for (root, dnames, fnames) in walk(here):
        for name in fnames:
            if name.endswith('.py') and name.startswith('test_'):
                fn = join(root, name)
                yield '.'.join(fn[len(here)+1:-3].split('/'))


#--  Execute  ------------------------------------------------------------------

# Signals an error if any module fails to import
(n_modules, n_automodules) = DistChecker()(rootdir)

print()

anyfail = False

# Run doctests
print('DOCTESTS')
n_doctests = 0
for fn in rst_files():
    (nfails, ntests) = doctest.testfile(fn, module_relative=False)
    n_doctests += ntests
    if nfails:
        print(fn, ':', ntests, 'tests', nfails, 'failures')
        anyfail = True
        break
    else:
        print(fn, ':', ntests, 'tests', 'OK')
if not anyfail:
    print('TOTAL:', n_doctests, 'tests')

print()

# Run unit tests
print('UNIT TESTS')
n_unittests = 0
load = unittest.defaultTestLoader.loadTestsFromName
run = unittest.TextTestRunner().run
for modname in test_files():
    print()
    print('----------------------------------------------------------------------')
    print('TEST', modname)
    result = run(load(modname))
    if result.wasSuccessful():
        n_unittests += result.testsRun
    else:
        anyfail = True
        break
if not anyfail:
    print('TOTAL:', n_unittests, 'tests')

# Summary

print()
print('SUMMARY')
print('Imported modules:  ', n_modules)
print('Documented modules:', n_automodules)
print('Doctests:          ', n_doctests)
print('Unit tests:        ', n_unittests)


# def test_suite ():
#     loader = unittest.TestLoader()
#     suite = unittest.TestSuite()
#     for fn in rst_files():
#         suite.addTests(doctest.DocFileSuite(fn, module_relative=False))
#     suite.addTests(loader.discover(start_dir=here))
#     return suite
    
# if __name__ == '__main__':
#     runner = unittest.TextTestRunner(verbosity=2)
#     runner.run(test_suite())

