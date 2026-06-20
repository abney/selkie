
from .config import in_browser

if in_browser:
    from .ui_bootstrap import server
else:
    import webbrowser
    from .server import Server

from pathlib import Path
from importlib import import_module
from shutil import copyfile


class AppInfo:

    def __init__ (self, module_name, function_name):
        '''
        E.g., filename='/Users/abney/git/hub/selkie/src/selkie'
              module_name='selkie.editor.__main__'
              function_name='Application'
        '''

        assert isinstance(module_name, str)
        assert isinstance(function_name, str)

        cpts = module_name.split('.')
        mod = import_module(cpts[0])
        filename = Path(mod.__file__)
        if filename.name == '__init__.py':
            filename = filename.parent

        self.filename = filename
        self.module_name = module_name
        self.function_name = function_name

    def __repr__ (self):
        return f'<AppInfo {self.filename} {self.module_name} {self.function_name}>'


#  Suppose we specialize WapApplication as MyApplication, in module foo.bar
#  We execute it: python -m foo.bar
#  Python -m does NOT import foo.bar, but rather loads the module into __main__
#  As far as I can determine, "python -m" does not store the module name anywhere.
#  So it must be provided explicitly, when Application is defined.

class WapApplication:

    def __init__ (self, module_name, function_name):
        self.module_name = module_name
        self.function_name = function_name
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
        info = AppInfo(self.module_name, self.function_name)
        self.server = Server(info,
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
