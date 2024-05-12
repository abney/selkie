
import sys
from os import walk, getcwd
from os.path import exists, join, abspath
from importlib import import_module

class DistChecker (object):

    def __init__ (self):
        self.package_filename = None
        self.modules = {} # modname -> fn
        self.src = None
        self.docs = None
        
    def __call__ (self, fn):
        self.package_filename = fn
        self.src = join(fn, 'src')
        self.docs = join(fn, 'docs', 'source')

        if not exists(self.src):
            raise Exception('Src directory does not exist:', self.src)
        if not exists(self.docs):
            raise Exception('Docs directory does not exists:', self.docs)

        n_modules = self.check_src()
        n_automodules = self.check_docs()
        return (n_modules, n_automodules)

    def iter_imports (self):
        for (rp, ds, fs) in walk(self.src):
            modprefix = '.'.join(rp[len(self.src) + 1:].split('/'))
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

    def check_src (self):
        print()
        print('Check', self.src)
        count = 0
        for (fn, modname) in self.iter_imports():
            print('import', modname, f'[{fn}]')
            import_module(modname)
            assert modname not in self.modules
            self.modules[modname] = fn
            count += 1
        return count
    
    def iter_documented_modules (self):
        for (rp, ds, fs) in walk(self.docs):
            for name in fs:
                fn = join(rp, name)
                if name.endswith('.rst'):
                    with open(fn) as f:
                        for (lno, line) in enumerate(f, 1):
                            for pfx in ('.. automodule:: ', '.. py:module:: '):
                                if line.startswith(pfx):
                                    modname = line[len(pfx):].strip()
                                    yield (fn, lno, modname)
    
    def check_docs (self):
        print()
        print('Check', self.docs)
        count = 0
        for (fn, lno, modname) in self.iter_documented_modules():
            if modname not in self.modules:
                print(f'Module not found:', modname, f'[{fn}:{lno}]')
            count += 1
        return count


if __name__ == '__main__':
    if len(sys.argv) > 1:
        fn = sys.argv[1]
    else:
        fn = getcwd()
    check_dist = DistChecker()
    check_dist(fn)
