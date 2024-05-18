##
##  This tests the version of Selkie installed in the prevailing environment.
##  To test *this* version, run it in the selkie_dev environment.
##

import unittest, doctest
from sys import stdout, argv
from os import walk
from os.path import dirname, join, exists
from checkdist import DistChecker

here = dirname(__file__)
rootdir = dirname(here)
docdir = join(rootdir, 'docs', 'source')

devflag = (len(argv) > 1 and argv[1] == 'dev')

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
        # temporarily disabled
        'pyx/table.rst',
        'pyx/xterm.rst',
        ]

skip = set(join(docdir, path) for path in skip)

def rst_files ():
    global docdir, skip
    for (root, dnames, fnames) in walk(docdir):
        for name in fnames:
            if name.endswith('.rst'):
                fn = join(root, name)
                if fn not in skip:
                    yield fn

def test_files ():
    global here
    for (root, dnames, fnames) in walk(here):
        for name in fnames:
            if name.endswith('.py') and name.startswith('test_'):
                fn = join(root, name)
                yield '.'.join(fn[len(here)+1:-3].split('/'))


#--  Execute  ------------------------------------------------------------------

def run_tests ():
    global rootdir, devflag

    # Each call signals an error if any test fails

    (n_modules, n_automodules) = DistChecker(rootdir, installed=devflag)()
    n_doctests = run_doctests()
    n_unittests = run_unittests()

    if exists('previous_results'):
        with open('previous_results') as f:
            for line in f:
                values = [int(field) for field in line.split()]
                break
    else:
        values = (0, 0, 0, 0)

    print()
    print( 'SUMMARY             Curr Prev')
    print(f"Imported modules:   {n_modules:4d} {values[0]:4d} {'**' if n_modules != values[0] else ''}")
    print(f"Documented modules: {n_automodules:4d} {values[1]:4d} {'**' if n_automodules != values[1] else ''}")
    print(f"Doctests:           {n_doctests:4d} {values[2]:4d} {'**' if n_doctests != values[2] else ''}")
    print(f"Unit tests:         {n_unittests:4d} {values[3]:4d} {'**' if n_unittests != values[3] else ''}")

    with open('previous_results', 'w') as f:
        print(' '.join(str(v) for v in (n_modules, n_automodules, n_doctests, n_unittests)), file=f)


def run_doctests ():
    print()
    print('DOCTESTS')

    n_doctests = 0
    for fn in rst_files():
        (nfails, ntests) = doctest.testfile(fn, module_relative=False)
        n_doctests += ntests
        if nfails:
            print('doctest:', f'{ntests:3d} tests', f'{nfails:3d} failures')
            raise Exception('doctest failed')
        else:
            print('doctest:', f'{ntests:3d} tests', f'[{fn}]')
    print('TOTAL:', n_doctests, 'tests')
    return n_doctests


def run_unittests ():
    print()
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
            raise Exception('Unit test failed')
    print('TOTAL:', n_unittests, 'tests')
    return n_unittests


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


run_tests()
