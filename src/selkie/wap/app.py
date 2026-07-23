
# If we're stable, index.html will micropip-install selkie in pyodide
# Otherwise, it will pyfetch it from the local dist directory

__stable__ = False

import tarfile, os, sys
from io import StringIO
from pathlib import Path
from importlib import import_module
from shutil import copyfile
from zipfile import ZipFile
from .config import in_browser, tornado_available

if tornado_available:
    import webbrowser
    from .server import Server


def all_files (dirname):
    return list(_all_files(Path(dirname)))

def _all_files (d):
    if d.is_dir():
        for child in d.iterdir():
            if child.is_dir():
                yield from _all_files(child)
            elif child.is_file():
                yield child
    elif d.is_file():
        yield d


#--  exec_app  -----------------------------------------------------------------

def exec_app (fnc, context=None):
    if context is None:
        context = Context(fnc)
    Application(context).execute()


class Context:

    def __init__ (self, fnc, argv=sys.argv):
        self.start_fnc = fnc
        self.read_config_file()
        self.parse_command_line(argv)
        self.digest_config()
    
    def read_config_file (self):
        config = self.config = {}
        fn = Path('wap.config')
        if not fn.exists():
            fn = Path('~/.wap').expanduser()
            if not fn.exists():
                return
        config['config_file'] = fn
        with open(fn) as f:
            for (lno, line) in enumerate(f):
                line = line.rstrip('\r\n')
                i = line.find(' ')
                if i < 0:
                    print('** Line', lno, 'in', str(config_fn), '- no space')
                else:
                    key = line[:i]
                    value = line[i+1:]
                    config[key] = value
    
    def parse_command_line (self, argv):
        com = 'start'
        args = []
        kwargs = {}
        i = 1
        if i < len(argv) and '=' not in argv[i]:
            com = argv[i]
            i += 1
        while i < len(argv) and '=' not in argv[i]:
            args.append(argv[i])
            i += 1
        for arg in argv[i:]:
            k = arg.find('=')
            if k >= 0:
                key = arg[:k]
                value = arg[k+1:]
                kwargs[key] = value
        if 'document_directory' not in kwargs:
            if com == 'build':
                kwargs['document_directory'] = '.'
            elif com in ('start', 'open'):
                kwargs['document_directory'] = '~/.cache/wap'
        if 'servlet' not in kwargs:
            if com == 'start':
                kwargs['servlet'] = 'tornado'
        self.com = com
        self.args = args
        self.config.update(kwargs)

    def digest_config (self):
        '''
        E.g., filename='/Users/abney/git/hub/selkie/src/selkie'
              module_name='selkie.editor.__main__'
              function_name='Application'
        '''
    
        f = self.start_fnc
        if isinstance(f, str):
            cpts = f.split('.')
            start_fnc_module = '.'.join(cpts[:-1])
            start_fnc_name = cpts[-1]
        else:
            start_fnc_module = f.__module__
            start_fnc_name = f.__name__
        start_fnc_package = start_fnc_module.split('.')[0]
    
        cpts = start_fnc_module.split('.')
        topmod = import_module(cpts[0])
        pkg_filename = Path(topmod.__file__)
        if pkg_filename.name == '__init__.py':
            pkg_filename = pkg_filename.parent
    
        cfg = self.config

        document_directory = Path(cfg['document_directory']).expanduser().absolute()
    
#         zip_cache = cfg.get('zip_cache')
#         if zip_cache is None:
#             zip_cache = Path(document_directory)/'zip'
    
        port = cfg.get('port', 8000)
        start_page = cfg.get('start_page', 'index.html')
        servlet = cfg.get('servlet')
        servlet_name = cfg.get('servlet_name')
        cgi = cfg.get('cgi')
        if cgi:
            servlet = 'cgi'
            servlet_name = cgi
        if servlet_name is None:
            if servlet == 'cgi':
                servlet_name = 'call.cgi'
            elif servlet == 'tornado':
                servlet_name = 'call'
        selkie_use_pypi = cfg.get('selkie_use_pypi', __stable__)
        app_use_pypi = cfg.get('use_pypi', False)
        archiver = cfg.get('archiver', 'zip')
        archiver_suffix = '.zip' if archiver == 'zip' else '.tar.gz' if archiver == 'tar' else None
        self.config = {'selkie_use_pypi': selkie_use_pypi,
                       'app_use_pypi': app_use_pypi,
                       'servlet': servlet,
                       'servlet_name': servlet_name,
                       'pkg_filename': str(pkg_filename),
                       'start_fnc_package': start_fnc_package,
                       'start_fnc_module': start_fnc_module,
                       'start_fnc_name': start_fnc_name,
                       'document_directory': str(document_directory),
                       'document_source_directory': str(Path(__file__).parent / 'docs'),
                       'port': port,
                       'start_page': start_page,
                       'archiver': archiver,
                       'archiver_suffix': archiver_suffix}
    
    def __str__ (self):
        with StringIO() as f:
            print('Context:', file=f)
            print('    start_fnc:', self.start_fnc, file=f)
            print('    com:      ', self.com, file=f)
            print('    args:     ', self.args, file=f)
            print('    config:', file=f)
            w = max(len(key) for key in self.config)
            for (key, value) in self.config.items():
                print(f'        {key:{w}s} : {value}', file=f)
            return f.getvalue()


#  Suppose we specialize WapApplication as MyApplication, in module foo.bar
#  We execute it: python -m foo.bar
#  Python -m does NOT import foo.bar, but rather loads the module into __main__
#  As far as I can determine, "python -m" does not store the module name anywhere.
#  So it must be provided explicitly, when Application is defined.

class Application:

    def __init__ (self, context):
#         if config is None:
#             config = make_config(start_fnc, **kwargs)
#         else:
#             config.update(kwargs)

        self.context = context
        self.config = context.config
        self.server = None
        self.in_browser = in_browser

    def execute (self):
        ctx = self.context
        getattr(self, 'com_' + ctx.com)(*ctx.args)

    def com_help (self):
        print('start - start tornado web server and open start page')
        print('install_cgi - install pages for serving from a CGI script')

    def com_build (self):
        print(self.context)
        servlet = self.config['servlet']
        selkie_use_pypi = self.config['selkie_use_pypi']
        app_use_pypi = self.config['app_use_pypi']
        docs = Path(self.config['document_directory'])
        start_page = self.config['start_page']
        script_name = self.config['servlet_name']

        self.maybe_create_directory(docs)
        self.create_start_page(docs/start_page)
        self.create_stylesheet(docs/'stylesheet.css')
        if servlet == 'cgi':
            self.create_cgi_script(docs/script_name)
        if not (selkie_use_pypi and app_use_pypi):
            self.create_dist(docs/'dist')

    def maybe_create_directory (self, docs):
        if not docs.exists():
            print('Creating', str(docs))
            docs.mkdir()
        # TODO: if pyodide source file is not available, change the fourth line
        # of index.html to use the copy of pyodide on the web

    def create_start_page (self, fn):
        StartPageWriter(self, fn)()

    def create_stylesheet (self, fn):
        print('Writing', str(fn))
        src = Path(self.config['document_source_directory'])
        copyfile(src/'stylesheet.css', fn)

    def create_cgi_script (self, fn):
        start_fnc_module = self.config['start_fnc_module']
        start_fnc_name = self.config['start_fnc_name']

        print('Writing', str(fn))
        with open(fn, 'w') as f:
            print(f'#!{sys.executable}', file=f)
            print(f'import sys', file=f)
            print(f'sys.path = {repr(sys.path)}', file=f)
            print(f'from selkie.wap import CGIHandler', file=f)
            print(f'from {start_fnc_module} import {start_fnc_name}', file=f)
            print(f'config = {repr(self.config)}', file=f)
            print(f"CGIHandler({start_fnc_name}, config)", file=f)

    def create_dist (self, dirname):
        if not dirname.exists():
            print('Create', dirname)
            dirname.mkdir()
        pkgfn = Path(self.config['pkg_filename'])
        name = pkgfn.name + self.config['archiver_suffix']
        archiver = self.config['archiver']
        if archiver == 'zip':
            self.create_zip_dist(dirname/name, pkgfn)
        elif archiver == 'tar':
            self.create_tar_dist(dirname/name, pkgfn)
        else:
            raise Exception(f'Unrecognized archiver: {archiver}')

    def create_tar_dist (self, fn, pkgfn):
        print('Writing', fn)
        tf = tarfile.open(fn, 'w:gz')
        tf.add(pkgfn, arcname=pkgfn.name)
        tf.close()

    def create_zip_dist (self, zfn, pkgfn):
        print('Writing', zfn)
        if zfn.exists():
            zfn.unlink()
        oldwd = os.getcwd()
        try:
            os.chdir(pkgfn.parent)
            with ZipFile(zfn, 'w') as zf:
                for fn in all_files(pkgfn.name):
                    zf.write(fn)
        finally:
            os.chdir(oldwd)

    def com_start (self):
        if in_browser:
            raise Exception('Not available in browser')
        self.com_build()
        self.start_server()
        self.visit_start_page()

    def start_server (self):
        self.server = Server(self.config, Servlet)
        self.server.start()

    def visit_start_page (self):
        webbrowser.open(f"http://localhost:{self.config['port']}/")

#     def com_open (self):
#         if in_browser:
#             raise Exception('Not available in browser')
#         self.com_build('browser-dev')
#         self.visit_start_page()

#     async def quit (self):
#         await self.server.close()


class StartPageWriter:

    def __init__ (self, app, fn):
        self.config = app.config
        self.filename = fn
        self.micropip_installs = None
        self.local_installs = None
        
    def __call__ (self):
        self.compute_installs()
        self.write_page()

    def compute_installs (self):
        self.micropip_installs = []
        self.local_installs = []
        app_package = self.config['start_fnc_package']
        if app_package != 'selkie':
            if self.config['selkie_use_pypi']:
                dev = selkie.__version__.split('.')[-1].startswith('dev')
                if dev:
                    pkg = 'selkie==' + selkie.__version__
                else:
                    pkg = 'selkie'
                self.add_micropip_install(pkg)
            else:
                self._add_local_install('selkie-' + selkie.__version__)
        if self.config['app_use_pypi']:
            self.add_micropip_install(app_package)
        else:
            self.add_local_install(app_package)

    def add_micropip_install (self, pkg):
        self.micropip_installs.append(f'''
    	    await micropip.install('{pkg}');
	    console.log('{pkg} installed');
        ''')

    def add_local_install (self, pkg):
        suffix = self.config['archiver_suffix']
        self.local_installs.append(f'''
              response = await pyfetch('dist/{pkg}{suffix}')
              await response.unpack_archive()
        ''')

    def write_page (self):
        fn = self.filename
        print('Writing', str(fn))
        src = Path(self.config['document_source_directory'])
        with open(fn, 'w') as outfile:
            with open(src/'index.html', 'r') as infile:
                for line in infile:
                    if line == '$PIP_INSTALL\n':
                        self.write_micropip_installs(outfile)
                    elif line == '$BODY\n':
                        self.write_local_installs(outfile)
                        self.write_body(outfile)
                        outfile.write('\n')
                    else:
                        outfile.write(line)

    def write_micropip_installs (self, outfile):
        if self.micropip_installs:
            outfile.write('''
	        await pyodide.loadPackage('micropip');
	        const micropip = pyodide.pyimport('micropip');
            ''')
            for text in self.micropip_installs:
                outfile.write(text)

    def write_local_installs (self, outfile):
        if self.local_installs:
            outfile.write('''
              from pyodide.http import pyfetch
              import sys
            ''')
        for text in self.local_installs:
            outfile.write(text)

    def write_body (self, outfile):
        start_fnc_module = self.config['start_fnc_module']
        start_fnc_name = self.config['start_fnc_name']
        servlet = self.config['servlet']
        servlet_name = self.config['servlet_name']
        if servlet:
            arg = f'ServerConnection({repr(servlet_name)})'
            outfile.write('''
              from selkie.wap import ServerConnection
            ''')
        else:
            arg = 'None'
        outfile.write(f'''
              from {start_fnc_module} import {start_fnc_name}
              {start_fnc_name}({arg})
        ''')



# def exec_app (fnc, use_sys_argv=True, com=None, args=[], more_kwargs={}):
#     if use_sys_argv:
#         assert not (com or args or more_kwargs)
#         (com, args, more_kwargs) = parse_command_line(sys.argv)
#     kwargs = read_config_file(more_kwargs)
#     app = WapApplication(fnc, **kwargs)
#     app.execute(com, *args)


class Servlet:
    '''
    The call handler must support:

    rh.config
    rh.get_query_argument(str)
    rh.write_text(str)
    rh.write_bytes(bytes)
    rh.set_status(int)
    rh.server_stop()
    '''

    def __init__ (self, rh):
        self.rh = rh
        self.config = rh.config

    def call (self, method, name, kwargs):
        methname = method.lower() + '_' + name
        if hasattr(self, methname):
            fnc = getattr(self, methname)
            fnc(**kwargs)
        else:
            self.rh.set_status(404)

#    def get_bootstrap (self):
#        self._write_file_text(self._get_bootstrap_filename())
#        self.rh.write_text('\napp_config = ')
#        self.rh.write_text(repr(self.config))
#        self.rh.write_text('\nserver_proxy = ServerProxy(app_config)\n')

        #self.rh.write_text('\nSTART_FNC_MODULE = ')
        #self.rh.write_text(repr(self.config['start_fnc_module']))
        #self.rh.write_text('\nSTART_FNC_NAME = ')
        #self.rh.write_text(repr(self.config['start_fnc_name']))
        #self.rh.write_text('\n')

#    def get_selkie (self):
#        self._write_zipfile(self._get_selkie_filename())
#
#    def get_app (self):
#        self._write_zipfile(Path(self.config['pkg_filename']))

    def get_close (self):
        print("Servlet: received 'close'")
        self.rh.write_text('Server stop')
        self.rh.server_stop()

    def get_dirlist (self):
        print("Servlet: received 'dirlist'")
        for fn in Path('.').iterdir():
            self.rh.write_text(str(fn))
            self.rh.write_text('\n')

    def get_text (self):
        fn = self.rh.get_query_argument('fn')
        print(f"Servlet: received 'text {fn}'")
        self._write_file_text(fn)

    def _get_bootstrap_filename (self):
        # module.__file__ is __init__.py
        wapdir = Path(__file__).parent
        return wapdir / 'ui_bootstrap.py'
        
    def _write_file_text (self, fn):
        with open(fn) as f:
            self.rh.write_text(f.read())
        
#    def _get_selkie_filename (self):
#        import selkie
#        return Path(selkie.__file__).parent

#     def _write_zipfile (self, sourcedir):
#         name = sourcedir.name
#         cache = Path(self.config['zip_cache'])
#         if not cache.exists():
#             cache.mkdir()
#         zfn = cache / (name + '.zip')
#         if zfn.exists():
#             zfn.unlink()
#         oldwd = os.getcwd()
#         try:
#             os.chdir(sourcedir.parent)
#             with ZipFile(zfn, 'w') as zf:
#                 for fn in all_files(name):
#                     zf.write(fn)

#                for (d, _, names) in Path(name).walk():
#                    for nm in names:
#                        zf.write(d / nm)

#         finally:
#             os.chdir(oldwd)
# 
#         with open(zfn, 'br') as f:
#             self.rh.write_bytes(f.read())

