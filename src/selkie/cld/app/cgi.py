
import subprocess


def call_cgi_script (docroot, name, reqpath):
    docroot = docroot.rstrip('/')
    if not reqpath.startswith('/'):
        reqpath = '/' + reqpath
    scriptname = '/cgi-bin/' + name
    fn = docroot + scriptname
    uri = scriptname + reqpath

    env = {
        'CONTEXT_DOCUMENT_ROOT': docroot,
        'CONTEXT_PREFIX': '',
        'DOCUMENT_ROOT': docroot,
        'GATEWAY_INTERFACE': 'CGI/1.1',
        'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'HTTP_ACCEPT_ENCODING': 'gzip, deflate',
        'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.5',
        'HTTP_CONNECTION': 'keep-alive',
        'HTTP_DNT': '1',
        'HTTP_HOST': 'localhost:8000',
        'HTTP_UPGRADE_INSECURE_REQUESTS': '1',
        'HTTP_USER_AGENT': 'seal.app.cgi.call_cgi_script',
        'KMP_DUPLICATE_LIB_OK': 'True',
        'LC_CTYPE': 'UTF-8',
        'PATH': '/anaconda3/bin:/Users/abney/anaconda3/bin:/Users/abney/anaconda3/condabin:/Users/abney/git/spa/bin:/Users/abney/bin:/Users/abney/git/cld/bin:/Users/abney/git/seal/bin:/Users/abney/anaconda3/bin:/Users/abney/anaconda/bin:/bin:/Users/abney/cl/gnu/bin:/Users/abney/cl/bin:/usr/local/bin:/Library/TeX/texbin:/usr/X11/R6/bin:/usr/local/sbin:/opt/local/bin:/usr/share:/usr/local/share:/usr/bin:/bin:/usr/sbin:/opt/X11/bin:/usr/texbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
        'QUERY_STRING': '',
        'REMOTE_ADDR': '127.0.0.1',
        'REMOTE_PORT': '0',
        'REQUEST_METHOD': 'GET',
        'REQUEST_SCHEME': 'http',
        'REQUEST_URI': uri,
        'SCRIPT_FILENAME': fn,
        'SCRIPT_NAME': scriptname,
        'SERVER_ADDR': '127.0.0.1',
        'SERVER_ADMIN': 'you@example.com',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8000',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'SERVER_SIGNATURE': '',
        'SERVER_SOFTWARE': 'seal.app.cgi.call_cgi_script'
        }

    out = subprocess.run([fn], env=env, capture_output=True, text=True)
    print(out.stdout)
    print(out.stderr)
