
from .config import in_browser

if not in_browser:
    import webbrowser
    from .server import Server

from pathlib import Path
from importlib import import_module
from shutil import copyfile
import selkie.wap

class WapApplication:

    def __init__ (self):
        self.document_dir = Path('~/.cache/wap').expanduser()
        self.document_source_dir = Path(selkie.wap.__file__).parent / 'docs'
        self.pyodide_source = None
        self.port = 8000
        self.filename = None
        self.name = None
        self.server = None
        self.in_browser = in_browser

        mod = import_module(self.__module__)
        fn = Path(mod.__file__)
        assert fn.name == '__main__.py'
        self.filename = fn.parent
        self.name = self.filename.name

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
        self.server = Server(self.filename, docs_directory=self.document_dir, port=self.port)
        self.server.start()

    def _visit_start_page (self):
        webbrowser.open(f'http://localhost:{self.port}/')

    def start (self):
        if in_browser:
            raise Exception('Not available in browser')
        self._prep_document_dir()
        self._start_server()
        self._visit_start_page()
