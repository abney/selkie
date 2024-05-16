
import sys
from os import walk, getcwd, listdir
from os.path import exists, join, abspath, normpath, dirname
from importlib import import_module

class DistChecker (object):

    def __init__ (self, fn, modname=None, installed=False):
        fn = normpath(abspath(fn))

        self.package_root = fn
        self.modules = {} # modname -> fn
        self.modname = modname
        self.installed = installed

        if modname is None:
            names = listdir(join(fn, 'src'))
            if len(names) == 1:
                self.modname = names[0]
            else:
                raise Exception(f'Cannot determine module name; src contains: {names}')

    def __call__ (self):
        n_imports = self.check_imports()
        n_docmodules = self.check_docmodules()
        return (n_imports, n_docmodules)

    def check_imports (self):
        print()
        print('Check imports')
        n_imports = 0
        root_module = import_module(self.modname)
        fn = root_module.__file__
        print(f"Filename of module '{self.modname}':", fn)
        if not fn.endswith('__init__.py'):
            raise Exception("Expecting filename to end with '__init__.py'")
        src = dirname(dirname(fn))
        if not self.installed:
            expected = join(self.package_root, 'src')
            if src != expected:
                raise Exception(f'Expecting src directory to be {expected}')

        for (fn, modname) in self.iter_imports(src):
            print('import', modname, f'[{fn}]')
            assert modname not in self.modules
            module = import_module(modname)
            if module.__file__ != fn:
                raise Exception('Module imported from wrong file: {module.__file__}')
            self.modules[modname] = fn
            n_imports += 1

        return n_imports

    def iter_imports (self, src):
        for (rp, ds, fs) in walk(join(src, self.modname)):
            modprefix = '.'.join(rp[len(src) + 1:].split('/'))
            for name in fs:
                fn = join(rp, name)
                modname = None
                if name == '__init__.py':
                    modname = modprefix
                elif name.endswith('.py'):
                    modname = modprefix + '.' + name[:-3]
                else:
                    continue
                yield (fn, modname)
    
    def check_docmodules (self):
        n_docmodules = 0
        docs = join(self.package_root, 'docs', 'source')
        print()
        print('Check docmodules', docs)
        for (fn, lno, modname) in self.iter_docmodules(docs):
            if modname in self.modules:
                n_docmodules += 1
            else:
                print(f'**Module not found:', modname, f'[{fn}:{lno}]')
        return n_docmodules
    
    def iter_docmodules (self, docs):
        for (rp, ds, fs) in walk(docs):
            for name in fs:
                fn = join(rp, name)
                if name.endswith('.rst'):
                    with open(fn) as f:
                        for (lno, line) in enumerate(f, 1):
                            for pfx in ('.. automodule:: ', '.. py:module:: '):
                                if line.startswith(pfx):
                                    modname = line[len(pfx):].strip()
                                    yield (fn, lno, modname)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        fn = sys.argv[1]
    else:
        fn = getcwd()
    check_dist = DistChecker()
    check_dist(fn)
