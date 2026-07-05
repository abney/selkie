##
##  This tests the version of Selkie installed in the prevailing environment.
##  To test *this* version, run it in the selkie_dev environment.
##

import unittest, doctest
from sys import stdout
from os import walk
from os.path import dirname, join, exists
from checkdist import DistChecker


class Tester:
    
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
    
    def __init__ (self):
        self.here = dirname(__file__)
        self.rootdir = dirname(self.here)
        self.docdir = join(self.rootdir, 'docs', 'source')
        self.is_dev_version = self.testing_development_version()
        self.skip = set(join(self.docdir, path) for path in self.__class__.skip)
        self.any_errors = None
    
        print('Testing development version?', self.is_dev_version)

    def testing_development_version (self):
        import selkie
        return selkie.__file__.endswith('/git/hub/selkie/src/selkie/__init__.py')
    
    def rst_files (self):
        for (root, dnames, fnames) in walk(self.docdir):
            for name in fnames:
                if name.endswith('.rst'):
                    fn = join(root, name)
                    if fn not in self.skip:
                        yield fn
    
    def local_test_files (self, dirname, prefix='', suffix=''):
        for (root, dnames, fnames) in walk(dirname):
            for name in fnames:
                if name.endswith(suffix) and name.startswith(prefix):
                    fn = join(root, name)
                    yield fn

    def unit_test_files (self):
        for fn in self.local_test_files('unittests', prefix='test_', suffix='.py'):
            cpts = fn[:-3].split('/')
            modname = '.'.join(cpts)
            print('fn=', repr(fn), 'modname=', repr(modname))
            yield (modname, fn)

    def doctest_files (self):
        yield from self.local_test_files('doctests', suffix='.doctest')
    
    
    #--  Execute  ------------------------------------------------------------------
    
    def __call__ (self, name):
        self.any_errors = False
        if name.startswith(':'):
            if name == ':all':
                self.run_all_tests()
            elif name == ':dist':
                return self.run_dist_test()
            elif name == ':rst':
                return self.run_rst_tests()
            elif name == ':unit':
                return self.run_unittests()
            elif name == ':doc':
                return self.run_doctests()
            else:
                print('Unrecognized test:', name)
    
    def run_all_tests (self):
        (n_modules, n_automodules, n_mod_errors) = self.run_dist_test()
        (n_rsttests, n_rst_errors) = self.run_rst_tests()
        (n_unittests, n_unit_errors) = self.run_unittests()
        (n_doctests, n_doc_errors) = self.run_doctests()
        results = (n_modules, n_automodules, n_rsttests, n_unittests, n_doctests)
    
        self.print_comparison(results)
    
        if self.is_dev_version:
            if n_mod_errors + n_doc_errors + n_unit_errors + n_doc_errors == 0:
                self.save_results(results)
            else:
                print('[Errors encountered, not saving results]')

    def run_dist_test (self):
        print()
        print('Test :dist')
        chk = DistChecker(self.rootdir, dev_version=self.is_dev_version)
        return chk()

    def run_rst_tests (self):
        print()
        print('Test :rst')
        return self._run_doctests(self.rst_files())

    def _run_doctests (self, fns):
        n_doctests = n_errors = 0
        for fn in fns:
            (nfails, ntests) = doctest.testfile(fn, module_relative=False)
            n_doctests += ntests
            if nfails:
                print('doctest:', f'{ntests:3d} tests', f'{nfails:3d} failures')
                n_errors += nfails
            else:
                print('doctest:', f'{ntests:3d} tests', f'[{fn}]')
        print('TOTAL:', n_doctests, 'tests', n_errors, 'errors')
        return (n_doctests, n_errors)

    def run_unittests (self):
        print()
        print('Test :unit')
    
        n_unittests = n_errors = 0
        load = unittest.defaultTestLoader.loadTestsFromName
        run = unittest.TextTestRunner().run
        for (modname, fn) in self.unit_test_files():
            print()
            print('----------------------------------------------------------------------')
            print('TEST', modname, fn)
            result = run(load(modname))
            if result.wasSuccessful():
                n_unittests += result.testsRun
            else:
                print('Unit test failed')
                n_errors += 1
        print('TOTAL:', n_unittests, 'tests', n_errors, 'errors')
        return (n_unittests, n_errors)
    
    def run_doctests (self):
        print()
        print('Test :doc')
        return self._run_doctests(self.doctest_files())

    def print_comparison (self, results):
        (n_modules, n_automodules, n_rsttests, n_unittests, n_doctests) = results
    
        if exists('previous_results'):
            with open('previous_results') as f:
                for line in f:
                    values = [int(field) for field in line.split()]
                    break
        else:
            values = (0, 0, 0, 0, 0)
    
        print()
        print( 'SUMMARY             Curr Prev')
        print(f"Imported modules:   {n_modules:4d} {values[0]:4d} {'**' if n_modules != values[0] else ''}")
        print(f"Documented modules: {n_automodules:4d} {values[1]:4d} {'**' if n_automodules != values[1] else ''}")
        print(f"RST tests:          {n_rsttests:4d} {values[2]:4d} {'**' if n_rsttests != values[2] else ''}")
        print(f"Unit tests:         {n_unittests:4d} {values[3]:4d} {'**' if n_unittests != values[3] else ''}")
        print(f"Doctests:           {n_doctests:4d} {values[4]:4d} {'**' if n_doctests != values[4] else ''}")
    
    def save_results (self, results):
        (n_modules, n_automodules, n_rsttests, n_unittests, n_doctest) = results
        print('[Updating results]')
        with open('previous_results', 'w') as f:
            print(' '.join(str(v) for v in (n_modules, n_automodules, n_rsttests, n_unittests, n_doctests)), file=f)
    
    
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
    

import sys
name = sys.argv[1] if len(sys.argv) >= 2 else ':all'
Tester()(name)
