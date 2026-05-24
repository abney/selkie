
from .config import in_browser

if in_browser:
    from .ui_bootstrap import server
else:
    import webbrowser
    from .server import Server

from pathlib import Path
from importlib import import_module
from shutil import copyfile


#  Suppose we specialize WapApplication as MyApplication, in module foo.bar
#  We execute it: python -m foo.bar
#  Python -m does NOT import foo.bar, but rather loads the module into __main__
#  As far as I can determine, "python -m" does not store the module name anywhere.
#  So it must be provided explicitly, when Application is defined.

class WapApplication:

    def __init__ (self, module_name):
        cpts = module_name.split('.')

        self.module_name = module_name
        self.toplevel_module = cpts[0]
        self.name = cpts[-1]
        self.document_dir = Path('~/.cache/wap').expanduser()
        self.document_source_dir = Path(__file__).parent / 'docs'
        self.pyodide_source = None
        self.port = 8000
        self.server = None
        self.in_browser = in_browser

    async def ui (self):
        write(f'{self.name}:', 'Hello, world!')

    def _prep_document_dir (self):
        docs = self.document_dir
        src = self.document_source_dir
        if not docs.exists():
            # docs.mkdir()
            raise Exception('Not implemented: create docs directory and install pyodide')
        # TODO: if pyodide source file is not available, change the fourth line
        # of index.html to use the copy of pyodide on the web
        copyfile(src/'index.html', docs/'index.html')
        copyfile(src/'stylesheet.css', docs/'stylesheet.css')

    def _start_server (self):
        mod = import_module(self.toplevel_module)
        app_filename = Path(mod.__file__)
        if app_filename.name == '__init__.py':
            app_filename = app_filename.parent

        self.server = Server(self.module_name,
                             app_filename,
                             docs_directory=self.document_dir,
                             port=self.port)
        self.server.start()

    def _visit_start_page (self):
        webbrowser.open(f'http://localhost:{self.port}/')

    def start (self):
        if in_browser:
            raise Exception('Not available in browser')
        self._prep_document_dir()
        self._start_server()
        self._visit_start_page()

    async def quit (self):
        await server.close()
