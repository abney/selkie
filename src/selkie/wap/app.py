
from .config import in_browser

if in_browser:
    from .ui_bootstrap import server_proxy
else:
    import webbrowser
    from .server import Server

from pathlib import Path
from importlib import import_module
from shutil import copyfile


def app_config (start_fnc, **kwargs):
    '''
    E.g., filename='/Users/abney/git/hub/selkie/src/selkie'
          module_name='selkie.editor.__main__'
          function_name='Application'
    '''

    start_fnc_module = start_fnc.__module__
    start_fnc_name = start_fnc.__name__

    cpts = start_fnc_module.split('.')
    topmod = import_module(cpts[0])
    app_filename = Path(topmod.__file__)
    if app_filename.name == '__init__.py':
        app_filename = app_filename.parent

    document_directory = kwargs.get('document_directory')
    if document_directory is None:
        document_directory = Path('~/.cache/wap').expanduser()

    zip_cache = kwargs.get('zip_cache')
    if zip_cache is None:
        zip_cache = Path('~/.cache/wap/zip').expanduser()

    port = kwargs.get('port', 8000)

    return {'app_filename': app_filename,
            'start_fnc_module': start_fnc_module,
            'start_fnc_name': start_fnc_name,
            'document_directory': document_directory,
            'document_source_directory': Path(__file__).parent / 'docs',
            'zip_cache': zip_cache,
            'port': port}


#  Suppose we specialize WapApplication as MyApplication, in module foo.bar
#  We execute it: python -m foo.bar
#  Python -m does NOT import foo.bar, but rather loads the module into __main__
#  As far as I can determine, "python -m" does not store the module name anywhere.
#  So it must be provided explicitly, when Application is defined.

class WapApplication:

    def __init__ (self, start_fnc, **kwargs):
        self.config = app_config(start_fnc, **kwargs)
        self.server = None
        self.in_browser = in_browser

    def _prep_document_dir (self):
        docs = self.config['document_directory']
        src = self.config['document_source_directory']
        if not docs.exists():
            docs.mkdir()
        # TODO: if pyodide source file is not available, change the fourth line
        # of index.html to use the copy of pyodide on the web
        copyfile(src/'index.html', docs/'index.html')
        copyfile(src/'stylesheet.css', docs/'stylesheet.css')

    def _start_server (self):
        self.server = Server(self.config)
        self.server.start()

    def _visit_start_page (self):
        webbrowser.open(f'http://localhost:{self.config['port']}/')

    def start (self):
        if in_browser:
            raise Exception('Not available in browser')
        self._prep_document_dir()
        self._start_server()
        self._visit_start_page()

    async def quit (self):
        await self.server.close()


def start (fnc):
    app = WapApplication(fnc)
    app.start()
