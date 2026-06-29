
from .config import in_browser, tornado_available

if in_browser:
    from .ui_bootstrap import server_proxy
elif tornado_available:
    import webbrowser
    from .server import Server

import os, io, sys
from pathlib import Path
from importlib import import_module
from shutil import copyfile
from zipfile import ZipFile


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

def make_config (start_fnc, **kwargs):
    '''
    E.g., filename='/Users/abney/git/hub/selkie/src/selkie'
          module_name='selkie.editor.__main__'
          function_name='Application'
    '''

    print('make_config', 'kwargs=', kwargs)

    if isinstance(start_fnc, str):
        cpts = start_fnc.split('.')
        start_fnc_module = '.'.join(cpts[:-1])
        start_fnc_name = cpts[-1]
    else:
        start_fnc_module = start_fnc.__module__
        start_fnc_name = start_fnc.__name__

    cpts = start_fnc_module.split('.')
    topmod = import_module(cpts[0])
    app_filename = Path(topmod.__file__)
    if app_filename.name == '__init__.py':
        app_filename = app_filename.parent

    command = kwargs.get('command', 'start')

    document_directory = kwargs.get('document_directory')
    if document_directory is None:
        if command == 'install_cgi':
            document_directory = Path('.').absolute()
        else:
            document_directory = Path('~/.cache/wap').expanduser()

    zip_cache = kwargs.get('zip_cache')
    if zip_cache is None:
        zip_cache = Path('~/.cache/wap/zip').expanduser()

    port = kwargs.get('port', 8000)
    start_page = kwargs.get('start_page', 'index.html')
    script_name = kwargs.get('script_name', 'call')

    return {'app_filename': str(app_filename),
            'start_fnc_module': start_fnc_module,
            'start_fnc_name': start_fnc_name,
            'command': command,
            'document_directory': str(document_directory),
            'document_source_directory': str(Path(__file__).parent / 'docs'),
            'zip_cache': str(zip_cache),
            'port': port,
            'start_page': start_page,
            'script_name': script_name}


#  Suppose we specialize WapApplication as MyApplication, in module foo.bar
#  We execute it: python -m foo.bar
#  Python -m does NOT import foo.bar, but rather loads the module into __main__
#  As far as I can determine, "python -m" does not store the module name anywhere.
#  So it must be provided explicitly, when Application is defined.

class WapApplication:

    def __init__ (self, start_fnc, config=None, **kwargs):
        if config is None:
            config = make_config(start_fnc, **kwargs)
        else:
            config.update(kwargs)

        self.config = config
        self.server = None
        self.in_browser = in_browser

    def execute (self):
        com = self.config.get('command', 'start')
        getattr(self, com)()

    def help (self):
        print('start - start tornado web server and open start page')
        print('install_cgi - install pages for serving from a CGI script')

    def _prep_document_dir (self):
        docs = Path(self.config['document_directory'])
        src = Path(self.config['document_source_directory'])
        start_page = self.config['start_page']
        script_name = self.config['script_name']

        if not docs.exists():
            print('Creating', str(docs))
            docs.mkdir()
        # TODO: if pyodide source file is not available, change the fourth line
        # of index.html to use the copy of pyodide on the web

        fn = docs/start_page
        print('Writing', str(fn))
        with open(fn, 'w') as outfile:
            with open(src/'index.html', 'r') as infile:
                for line in infile:
                    line = line.replace('$SCRIPT_NAME', script_name)
                    outfile.write(line)

        fn = docs/'stylesheet.css'
        print('Writing', str(fn))
        copyfile(src/'stylesheet.css', fn)

    def _start_server (self):
        self.server = Server(self.config, ApplicationServlet)
        self.server.start()

    def _visit_start_page (self):
        webbrowser.open(f"http://localhost:{self.config['port']}/")

    def start (self):
        if in_browser:
            raise Exception('Not available in browser')
        self._prep_document_dir()
        self._start_server()
        self._visit_start_page()

    async def quit (self):
        await self.server.close()

    def install_cgi (self):
        self._prep_document_dir()
        docs = self.config['document_directory']
        script_name = self.config['script_name']
        start_fnc_module = self.config['start_fnc_module']
        start_fnc_name = self.config['start_fnc_name']

        fn = Path(docs)/script_name
        print('Writing', str(fn))
        with open(fn, 'w') as f:
            print(f'#!{sys.executable}', file=f)
            print(f'import sys', file=f)
            print(f'sys.path = {repr(sys.path)}', file=f)
            print(f'from selkie.wap import CGIHandler', file=f)
            print(f'from {start_fnc_module} import {start_fnc_name}', file=f)
            print(f'config = {repr(self.config)}', file=f)
            print(f"CGIHandler({start_fnc_name}, config)", file=f)


def parse_command_line (argv):
    kwargs = {}
    i = 1
    if i < len(argv) and '=' not in argv[i]:
        kwargs['command'] = argv[i]
        i += 1
    for arg in argv[i:]:
        k = arg.find('=')
        if k >= 0:
            key = arg[:k]
            value = arg[k+1:]
            kwargs[key] = value
    return kwargs


def read_config_file (more_kwargs):
    config_fn = Path('.wap')
    if config_fn.exists():
        config = {}
        with open(config_fn) as f:
            for (lno, line) in enumerate(f):
                line = line.rstrip('\r\n')
                i = line.find(' ')
                if i < 0:
                    print('** Line', lno, 'in', str(config_fn), '- no space')
                else:
                    key = line[:i]
                    value = line[i+1:]
                    config[key] = value
        config.update(more_kwargs)
        return config
    else:
        return more_kwargs


def exec_app (fnc, use_sys_argv=True, more_kwargs={}):
    if use_sys_argv:
        assert not more_kwargs
        more_kwargs = parse_command_line(sys.argv)
    kwargs = read_config_file(more_kwargs)
    app = WapApplication(fnc, **kwargs)
    app.execute()


class ApplicationServlet:
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

    def get_bootstrap (self):
        self._write_file_text(self._get_bootstrap_filename())
        self.rh.write_text('\napp_config = ')
        self.rh.write_text(repr(self.config))
        self.rh.write_text('\nserver_proxy = ServerProxy(app_config)\n')

        #self.rh.write_text('\nSTART_FNC_MODULE = ')
        #self.rh.write_text(repr(self.config['start_fnc_module']))
        #self.rh.write_text('\nSTART_FNC_NAME = ')
        #self.rh.write_text(repr(self.config['start_fnc_name']))
        #self.rh.write_text('\n')

    def get_selkie (self):
        self._write_zipfile(self._get_selkie_filename())

    def get_app (self):
        self._write_zipfile(Path(self.config['app_filename']))

    def get_close (self):
        self.rh.write_text('Server stop')
        self.rh.server_stop()

    def get_dirlist (self):
        for fn in Path('.').iterdir():
            self.rh.write_text(str(fn))
            self.rh.write_text('\n')

    def get_text (self):
        fn = self.rh.get_query_argument('fn')
        self._write_file_text(fn)

    def _get_bootstrap_filename (self):
        # module.__file__ is __init__.py
        wapdir = Path(__file__).parent
        return wapdir / 'ui_bootstrap.py'
        
    def _write_file_text (self, fn):
        with open(fn) as f:
            self.rh.write_text(f.read())
        
    def _get_selkie_filename (self):
        import selkie
        return Path(selkie.__file__).parent

    def _write_zipfile (self, sourcedir):
        name = sourcedir.name
        cache = Path(self.config['zip_cache'])
        if not cache.exists():
            cache.mkdir()
        zfn = cache / (name + '.zip')
        if zfn.exists():
            zfn.unlink()
        oldwd = os.getcwd()
        try:
            os.chdir(sourcedir.parent)
            with ZipFile(zfn, 'w') as zf:
                for fn in all_files(name):
                    zf.write(fn)
#                for (d, _, names) in Path(name).walk():
#                    for nm in names:
#                        zf.write(d / nm)
        finally:
            os.chdir(oldwd)

        with open(zfn, 'br') as f:
            self.rh.write_bytes(f.read())

