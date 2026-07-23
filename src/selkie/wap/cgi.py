
import os, sys, io
from traceback import format_exc
from urllib.parse import parse_qs
from .app import Servlet


class CGIHandler:

    responses = {200: '200 OK',
                 404: '404 Not Found',
                 500: '500 Internal Server Error'}

    def __init__ (self, fnc, config):
        try:
            self.config = config
            self.method = os.environ['REQUEST_METHOD']
            self.status = 200
            self.response_type = 'text'
            self.wap = Servlet(self)
            self.text_output = io.StringIO()
            self.binary_output = None

            self.handle_request()
            self.generate_response()

        except:
            self.status = 500
            self.error_output = ''.join(format_exc())
            self.generate_response()

    def handle_request (self):
        name = 'root'
        if 'PATH_INFO' in os.environ:
            name = os.environ['PATH_INFO']
            if name.startswith('/'):
                name = name[1:]
        if self.method == 'GET':
            qs = parse_qs(os.environ['QUERY_STRING'])
            kwargs = {k:v[0] for (k,v) in qs.items()}
        else:
            kwargs = {}
        self.wap.call(self.method, name, kwargs)

    def generate_response (self):
        if self.status == 200:

            if self.response_type == 'text':
                output = self.text_output.getvalue()
                print('Content-Type: text/plain; charset=us-ascii')
                print('Content-Length: ', len(output))
                print()
                print(output)

            elif self.response_type == 'bytes':
                output = self.binary_output
                f = sys.stdout.buffer
                f.write(b'Content-Type: application/zip\r\n')
                f.write(b'Content-Length: ')
                f.write(str(len(output)).encode('ascii'))
                f.write(b'\r\n')
                f.write(b'\r\n')
                f.write(output)

        elif self.status == 500:
            output = self.error_output
            print('Content-Type: text/plain; charset=us-ascii')
            print('Content-Length: ', len(output))
            print()
            print(output)

    def get_query_argument (self, key):
        return self.qs[key][0]

    def set_status (self, status):
        self.status = status

    def write_text (self, msg):
        self.text_output.write(msg)

    def write_bytes (self, msg):
        self.response_type = 'bytes'
        self.binary_output = msg

    def server_stop (self):
        pass
