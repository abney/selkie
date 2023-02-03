
import webbrowser, json
from os.path import join, dirname
import tornado.web
from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler
from tornado.ioloop import IOLoop


# static_path = join(dirname(selkie.__file__), 'static')

static_path = '/Users/abney/git/selkie/dev/_js/app/build'


class MainHandler (RequestHandler):

    def initialize (self, port=None):
        if port is None:
            raise Exception('No port')
        self.port = port

    def get (self):
        self.render('static/index.html', port=self.port)


class ConfigHandler (RequestHandler):

    def initialize (self, port=None):
        if port is None:
            raise Exception('No port')
        self.port = port

    def get (self):
        self.set_header('Content-Type', 'application/javascript')
        self.render('src/config.js', port=self.port)


class JSFileHandler (RequestHandler):

    def get (self, fn):
        self.set_header('Content-Type', 'application/javascript')
        self.render(join('src', fn))


class EchoWebSocket (WebSocketHandler):

    def open (self):
        print('Web socket opened')

    def on_message (self, msg):
        self.write_message(f'You said: {msg}')

    def on_close (self):
        print('Web socket closed')


class JsonWebSocket (WebSocketHandler):

    def initialize (self, database=None):
        self.database = database

    ###  SECURITY RISK IF NOT RUNNING LOCALLY
    
    def check_origin (self, origin):
        print('[Origin]', origin)
        return True

    def on_message (self, msg):
        try:
            req = json.loads(msg)
            method = req['method']
            if method == 'get':
                key = req['uri']
                value = self.database[key]
                resp = json.dumps({'status': 'ok', 'value': value})
                self.write_message(resp)
        except Exception as e:
            if e.args and isinstance(e.args[0], str):
                msg = e.args[0]
            else:
                msg = str(e)
            resp = json.dumps({'status': 'error', 'msg': msg})
            self.write_message(resp)


class Application (object):

    def __init__ (self, database, port=8844, open_browser=True):
        self._database = database
        self._port = port
        self._open_browser = open_browser

    def run (self):
        port = self._port
        app = tornado.web.Application([('/websocket', JsonWebSocket, dict(database=self._database))],
                                      static_url_prefix='/build/',
                                      static_path=static_path)
        app.listen(port)
        if self._open_browser:
            webbrowser.open(f'http://localhost:{port}/build/index.html')
        IOLoop.current().start()


class Backend (object):

    def _invoke (self, prefix, uri, value=None):
        if not uri.startswith('/'):
            raise KeyError(f'URI must start with /: {uri}')
        fields = uri.split('/')
        assert not fields[0]
        if not fields[1]:
            raise KeyError(f'Empty command: {uri}')
        com = fields[1]
        args = fields[2:]
        if prefix == 'set':
            args = args + [value]
        method = prefix + '_' + com
        if hasattr(self, method):
            return getattr(self, method)(*args)
        else:
            raise KeyError(f'URI not found: {uri}')

    def __getitem__ (self, uri):
        return self._invoke('get', uri)

    def __setitem__ (self, uri, value):
        self._invoke('set', uri, value)

    def __delitem__ (self, uri):
        self._invoke('del', uri)
        
    def run (self, nw=False):
        app = Application(self, open_browser=(not nw))
        app.run()


def main (port=8844):
#     app = Application([('/', MainHandler, dict(port=port)),
#                        ('/js/config.js', ConfigHandler, dict(port=port)),
#                        ('/js/(.*)', JSFileHandler),
#                        ('/websocket', EchoWebSocket)],
#                       # /static/foo -> $SRC/selkie/static/foo
#                       static_path=static_path)

    app = Application([('/websocket', JsonWebSocket, dict(database={'hi': 'there'}))],
                      static_url_prefix='/build/',
                      static_path=static_path)
    app.listen(port)
    webbrowser.open(f'http://localhost:{port}/build/index.html')
    IOLoop.current().start()


if __name__ == '__main__':
    main()
