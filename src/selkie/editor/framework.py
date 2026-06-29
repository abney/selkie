
# DEFUNCT

# This module runs in the prevailing environment

import json, webbrowser
from os.path import join
from os import symlink
from pathlib import Path
from importlib import import_module
from .sh import (cd, norm_filename, exists, mkdir, join, wget, tar, rm, basename, dirname,
                 CurrentDirectory, sh, ln, walk, modtime, suffix)


class BaseServerSide (object):
    '''This runs server-side.'''

    def __init__ (self, **config):
        self.config = config

    def run (self):
        launcher = Launcher(self, self.config)
        self.debug = launcher.debug
        self.server = launcher.run()
        self.server.thread.join()


class Launcher (object):

    pyodide_release = '0.27.3'
    legal_keys = {'name', 'pypi', 'dependencies', 'browser_main',
                  'pyodide_source', 'options'}

    def __init__ (self, uss, config):
        bad_keys = [key for key in config if key not in self.legal_keys]
        assert not bad_keys, f'Bad key(s): {' '.join(bad_keys)}'
        assert 'name' in config, 'Must provide name'
        name = config['name']
        assert '.' not in name, 'Package must be a toplevel module'
        assert 'browser_main' in config, 'Must provide browser_main'
        config['pyodide_release'] = self.pyodide_release

        self.options = config.get('options', {})
        if isinstance(self.options, list):
            # sys.argv
            self.options = dict(arg.split('=') for arg in self.options[1:] if '=' in arg)
        if 'options' in config:
            del config['options']

        self.config = config
        self.uss = uss  # user server-side code
        self.name = name
        self.pypi = self.config.get('pypi', False)
        self.dependencies = self.config.get('dependencies', [])
        self.debug = self.options.get('debug', False)

        # This is a dotted name
        self.browser_main = self.config['browser_main']

        self.source = self.compute_source()
        self.docs_directory = norm_filename('~/.cache/pd2')
        self.build_directory = join(self.docs_directory, 'build')
        self.config_file = join(self.build_directory, 'Pd2Config')
        self.wheel_file = join(self.build_directory, 'dist', f'{name}-0.1.0-py3-none-any.whl')

        self.changed_params = set(self.iter_changed_params())

        if self.debug:
            print('Config:')
            print('  browser_main=', self.browser_main)
            print('  source=', self.source)
            print('  docs_directory=', self.docs_directory)
            print('  build_directory=', self.build_directory)
            

    def compute_source (self):
        mod = import_module(self.name)
        fn = mod.__file__
        if basename(fn) == '__init__.py':
            fn = dirname(fn)
        return fn

    def iter_changed_params (self):
        if not exists(self.config_file):
            yield from self.legal_keys
        else:
            old = self.read_config()
            for key in self.legal_keys:
                if (key in old) != (key in self.config):
                    yield key
                elif key in old and old[key] != self.config[key]:
                    yield key

    def write_config (self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

    def read_config (self):
        with open(self.config_file) as f:
            return json.load(f)

    def run (self):
        self.create_docs_directory()
        self.create_pyodide_directory()
        self.create_build()
        self.create_index_html()
        self.create_stylesheet()
        self.write_config()
        self.start_tornado()
        self.open_start_page()
        return self.server

    def create_docs_directory (self):
        if not exists(self.docs_directory):
            mkdir(self.docs_directory)

    def create_pyodide_directory (self):
        if not exists(join(self.docs_directory, 'pyodide')):
            if 'pyodide_source' in self.config:
                self._install_pyodide_from_source()
            else:
                self._install_pyodide_from_web()
        elif 'pyodide_release' in self.changed_params:
            self._install_pyodide_from_web()

    def _install_pyodide_from_source (self):
        fn = norm_filename(self.config['pyodide_source'])
        cd(self.docs_directory)
        print('Unpacking pyodide')
        tar('x', fn)

    def _install_pyodide_from_web (self):
        cd(self.docs_directory)
        n = self.pyodide_release
        release = f'https://github.com/pyodide/pyodide/releases/download/{n}/pyodide-{n}.tar.bz2'
        print('Downloading pyodide')
        fn = wget(release)
        print('Unpacking pyodide')
        tar('x', fn)
        rm(fn)

    def needs_build (self):
        if self.pypi:
            (value, reason) = (False, 'From pypi')
        elif not exists(self.wheel_file):
            (value, reason) = (True, f'Wheel file does not exist: {self.wheel_file}')
        elif 'name' in self.changed_params:
            (value, reason) = (True, 'Name changed')
        elif self.source_is_newer():
            (value, reason) = (True, f'Source is newer than wheel: {self.newest_src_file}')
        else:
            (value, reason) = (False, 'All good')
        if self.debug:
            print('Rebuild:' if value else 'No rebuild:', reason)
        return value

    def _newest_source_file (self):
        maxmt = None
        maxfn = None
        for fn in walk(join(self.build_directory, 'src')):
            if '__pycache__' not in fn:
                mt = modtime(fn)
                if maxmt is None or mt > maxmt:
                    maxmt = mt
                    maxfn = fn
        return (maxmt, maxfn)

    def source_is_newer (self):
        (self.src_modtime, self.newest_src_file) = self._newest_source_file()
        self.wheel_modtime = modtime(self.wheel_file)
        return self.src_modtime >= self.wheel_modtime
    
    def create_build (self):
        if self.needs_build():
            print('Creating wheel file')
            if not exists(self.build_directory):
                mkdir(self.build_directory)
            with CurrentDirectory(self.build_directory):
                if not exists('src'):
                    mkdir('src')
                # we don't check whether source location has changed - fix
                if not exists(join('src', self.name)):
                    ln(self.source, join('src', self.name), 's')
                self.maybe_write_file('pyproject.toml', self.pyproject_toml())
                self.maybe_write_file('setup.cfg', self.setup_cfg())
                sh('python -m build')

    def maybe_write_file (self, fn, lines):
        reason = None
        if not exists(fn):
            reason = 'file does not exist'
        elif modtime(__file__) >= modtime(fn):
            reason = f'{__file__} has been modified'
        elif self.changed_params:
            reason = 'changed params'
        if reason:
            print(f'Writing {fn}:', reason)
            with open(fn, 'w') as f:
                for line in lines:
                    f.write(line)
                    f.write('\n')

    def create_index_html (self):
        with CurrentDirectory(self.docs_directory):
            self.maybe_write_file('index.html', self.index_html())

    def create_stylesheet (self):
        with CurrentDirectory(self.docs_directory):
            fn = Path('stylesheet.css')
            if not fn.exists():
                print('Creating', fn)
                symlink(Path(self.source)/'stylesheet.css', 'stylesheet.css')

    def start_tornado (self):
        self.server = Server(uss=self.uss, docs_directory=self.docs_directory, debug=self.debug)
        self.server.start()
    
    def open_start_page (self):
        webbrowser.open(f'http://localhost:8000/')

    def pyproject_toml (self):
        yield '[build-system]'
        yield 'requires = [ "hatchling" ]'
        yield 'build-backend = "hatchling.build"'
        yield ''
        yield '[project]'
        yield f'name = "{self.name}"'
        yield 'version = "0.1.0"'
        yield 'authors = ['
        yield '    { name="Anonymous", email="noone@nowhere.com" }'
        yield ']'
        yield 'requires-python = ">=3.7"'
        yield 'classifiers = ['
        yield '    "Programming Language :: Python :: 3",'
        yield '    "License :: Other/Proprietary License",'
        yield '    "Operating System :: OS Independent",'
        yield ']'

    def setup_cfg (self):
        yield '[metadata]'
        yield f'name = {self.name}'
        yield 'version = 0.1.0'
        yield 'author = Anonymous'
        yield 'author_email = noone@nowhere.com'
        yield 'description = No description'
        yield 'classifiers ='
        yield '    Programming Language :: Python :: 3'
        yield '    License :: Other/Proprietary License'
        yield '    Operating System :: OS Independent'
        yield ''
        yield '[options]'
        yield 'package_dir ='
        yield '    = src'
        yield 'packages = find:'
        yield 'include_package_data = True'
        yield 'python_requires = >=3.7'
        yield ''
        yield '[options.packages.find]'
        yield 'where = src'

    def index_html (self):
        yield '<!doctype html>'
        yield '<html>'
        yield '  <head>'
        yield '    <script src="http://localhost:8000/pyodide/pyodide.js"></script>'
        yield '    <link rel="stylesheet" type="text/css" href="stylesheet.css"/>'
        yield '  </head>'
        yield '  <body>'
        yield '    <div id="splash"><h1>Loading...</h1></div>'
        yield '    <div id="root"></div>'
        yield '    <script type="text/javascript">'
        yield '      async function main(){'
        yield '        let pyodide = await loadPyodide();'
        yield '        console.log("Pyodide loaded");'
        yield '        await pyodide.loadPackage("micropip");'
        yield '        const micropip = pyodide.pyimport("micropip");'
        if self.pypi:
            yield f'        await micropip.install("{self.name}");'
            yield f'        console.log("{self.name} installed");'
        for dep in self.dependencies:
            yield f'        await micropip.install("{dep}");'
            yield f'        console.log("{dep} installed");'
        if not self.pypi:
            yield f'        await micropip.install("http://localhost:8000/build/dist/{self.name}-0.1.0-py3-none-any.whl");'
            yield f'        console.log("{self.name} installed");'
            yield  '        document.getElementById("splash").remove();'
        path = self.browser_main.split('.')
        func = path[-1]
        module = '.'.join(path[:-1])
        yield f'        pyodide.runPythonAsync("from {module} import {func}; {func}()");'
        yield '      }'
        yield '      main();'
        yield '    </script>'
        yield '  </body>'
        yield '</html>'

