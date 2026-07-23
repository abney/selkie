
# This module can only be loaded server-side

import asyncio, tornado, os, sys
from threading import Thread
from pathlib import Path
from importlib import import_module
from tornado.web import Application, RequestHandler, StaticFileHandler


#--  Server  -------------------------------------------------------------------

class Server:

    def __init__ (self, config, app_servlet):
        self.config = config
        self.app_servlet = app_servlet
        self.wd = Path(os.getcwd())
        self.thread = None
        self.shutdown_event = None

    async def main (self):
        print('Server: started')
        print('    wd:', self.wd)
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
        print('Server: stopped')

    def run_loop (self):
        print('Server: start event loop')
        self.loop = loop = asyncio.new_event_loop()
        loop.run_until_complete(self.main())
        loop.close()
        print('Server: end event loop')

    def start (self):
        self.thread = Thread(target=self.run_loop)
        self.thread.start()

    def stop (self):
        if self.shutdown_event and self.loop and self.loop.is_running():
            print('Server: Shutting down')
            self.loop.call_soon_threadsafe(self.shutdown_event.set)
        else:
            print('Server: not running')
            
    def status (self):
        if self.thread and self.thread.is_alive():
            print('Running')
        else:
            print('Not running')


class CallHandler (RequestHandler):

    def initialize (self, server):
        self.server = server
        self.config = server.config
        self.wap = server.app_servlet(self)

    def get (self, name):
        self.wap.call('get', name, {})

    def write_text (self, msg):
        self.write(msg)

    def write_bytes (self, msg):
        self.write(msg)

    def server_stop (self):
        print('CallHandler: received stop')
        self.server.stop()


if __name__ == '__main__':
    app = sys.argv[1] if len(sys.argv) > 1 else 'no app'
    Server(app).start()
