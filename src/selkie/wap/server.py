
# This module can only be loaded server-side

import asyncio, tornado, os, sys
from threading import Thread
from pathlib import Path
from importlib import import_module
from tornado.web import Application, RequestHandler, StaticFileHandler
from urllib.parse import parse_qsl
from zipfile import ZipFile


#--  Server  -------------------------------------------------------------------

class Server:

    def __init__ (self, config):
        self.config = config
        self.wd = Path(os.getcwd())
        self.thread = None
        self.shutdown_event = None

    async def main (self):
        print('Server started')
        print('    wd     :', self.wd)
        print('    config :')
        w = max(len(k) for k in self.config) + 1
        for (k,v) in self.config.items():
            print(f'        {k:{w}}: {v}')
        handlers = [
            (r'/call/(.*)', CallHandler, {'server': self}),
            (r'/wd/(.*)', StaticFileHandler, {'path': self.wd}),
            (r'/(.*)', StaticFileHandler, {'path': self.config['document_directory'],
                                           'default_filename': 'index.html'})]
        self.tornado = Application(handlers)
        self.tornado.listen(self.config['port'])
        self.shutdown_event = asyncio.Event()
        #print('shutdown_event=', self.shutdown_event)
        await self.shutdown_event.wait()
        print('Server stopped')

    def run_loop (self):
        print('Start event loop')
        self.loop = loop = asyncio.new_event_loop()
        loop.run_until_complete(self.main())
        loop.close()
        print('End event loop')

    def start (self):
        self.thread = Thread(target=self.run_loop)
        self.thread.start()

    def stop (self):
        if self.shutdown_event and self.loop and self.loop.is_running():
            print('Shutting down')
            self.loop.call_soon_threadsafe(self.shutdown_event.set)
        else:
            print('Server not running')
            
    def status (self):
        if self.thread and self.thread.is_alive():
            print('Running')
        else:
            print('Not running')


class CallHandler (RequestHandler):

    def initialize (self, server):
        self.server = server
        self.config = server.config

    def get (self, name):
        com = 'get_' + name
        if hasattr(self, com):
            f = getattr(self, com)
            return f()
        else:
            self.set_status(404)

    def get_bootstrap (self):
        self._write_file_text(self._get_bootstrap_filename())
        self.write('\nSTART_FNC_MODULE = ')
        self.write(repr(self.config['start_fnc_module']))
        self.write('\nSTART_FNC_NAME = ')
        self.write(repr(self.config['start_fnc_name']))
        self.write('\n')

    def get_selkie (self):
        self._write_zipfile(self._get_selkie_filename())

    def get_app (self):
        self._write_zipfile(self.app_filename)

    def get_close (self):
        print('Received close message')
        self.write('Server stop')
        self.server.stop()

    def get_text (self):
        fn = self.get_query_argument('fn')
        self._write_file_text(fn)

    def _get_bootstrap_filename (self):
        # module.__file__ is __init__.py
        wapdir = Path(__file__).parent
        return wapdir / 'ui_bootstrap.py'
        
    def _write_file_text (self, fn):
        with open(fn) as f:
            self.write(f.read())
        
    def _get_selkie_filename (self):
        import selkie
        return Path(selkie.__file__).parent

    def _write_zipfile (self, sourcedir):
        name = sourcedir.name
        cache = self.config['document_directory'] / 'cache'
        if not cache.exists():
            cache.mkdir()
        zfn = cache / (name + '.zip')
        if zfn.exists():
            zfn.unlink()
        oldwd = os.getcwd()
        try:
            os.chdir(sourcedir.parent)
            with ZipFile(zfn, 'w') as zf:
                for (d, _, names) in Path(name).walk():
                    for nm in names:
                        zf.write(d / nm)
        finally:
            os.chdir(oldwd)
        with open(zfn, 'br') as f:
            self.write(f.read())


if __name__ == '__main__':
    app = sys.argv[1] if len(sys.argv) > 1 else 'no app'
    Server(app).start()
