
import asyncio
from tornado.web import RequestHandler, StaticFileHandler, Application, url
from os.path import join, dirname, exists
from ..pyx.disk import VDisk
from ..pyx.com import BaseMain


class FileHandler (RequestHandler):

    def initialize (self, diskdir, libdir):
        self.diskdir = diskdir
        self.libdir = libdir

    def get (self, name):
        print('[FileHandler.get]', repr(name))
        if name == '' or name == 'index.html':
            fn = join(self.libdir, 'client.html')
        elif name == 'favicon.ico':
            fn = join(self.libdir, 'favicon.ico')
        elif name.startswith('.lib/'):
            fn = join(self.libdir, name[5:])
        else:
            fn = join(self.diskdir, name)
        print('fn=', repr(fn))
        if exists(fn):
            self.set_status(200)
            if fn.endswith('.css'):
                self.set_header('Content-Type', 'text/css')
            with open(fn) as f:
                for line in f:
                    self.write(line)
            self.finish()


class Server (object):

    def __init__ (self, diskdir='.', port=8000):
        self.diskdir = diskdir
        self.libdir = join(dirname(dirname(__file__)), 'cld', 'lib')
        self.port = port

    async def start (self):
        app = Application([url(r'/(.*)', FileHandler, dict(diskdir=self.diskdir, libdir=self.libdir))])
        app.listen(self.port)
        print('Running on port', self.port)
        return asyncio.Event()

    async def serve (self):
        #webbrowser.open(f'http://localhost:{port}/')
        shutdown = self.start()
        await shutdown

    def run (self):
        asyncio.run(self.serve())


class Main (BaseMain):

    def com_run (self, **kwargs):
        DiskServer(**kwargs).run()


if __name__ == '__main__':
    Main()()
