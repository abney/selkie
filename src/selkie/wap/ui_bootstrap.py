
# In-browser only

import js
from pyodide.http import pyfetch
from pyodide.code import eval_code_async

from pathlib import Path
from zipfile import ZipFile
from importlib import import_module

PORT = 8000

def write (*objs):
    s = ' '.join(str(x) for x in objs)
    root = js.document.getElementById("root")
    root.appendChild(js.document.createTextNode(s))
    root.appendChild(js.document.createElement('BR'))

async def call (msg):
    res = await pyfetch(f'http://localhost:{PORT}/{msg}')
    if res.status != 200:
        raise Exception(f'Received status {res.status}: {fn}')
    return res

async def file_contents (fn):
    res = await call(fn)
    text = await res.text()
    return text

async def file_bytes (fn):
    res = await call(fn)
    b = await res.bytes()
    return b

class PseudoModule:

    def __init__ (self, env):
        self.__dict__ = env

    def __getattr__ (self, attr):
        return self.__dict__[attr]

async def load (fn):
    env = {}
    source = await file_contents(fn)
    await eval_code_async(source, env)
    return PseudoModule(env)

def ls (fn='.'):
    p = Path(fn)
    if p.is_dir():
        names = [str(n) for n in p.iterdir()]
        write(f'List dir {str(p)}:', *names)
    elif p.exists():
        write('List file:', str(p))
    else:
        write('No such file:', str(p))

async def install (name):
    home = Path.home()
    p = (home / name).with_suffix('.zip')
    b = await file_bytes('call/' + name)
    p.write_bytes(b)
    zf = ZipFile(p)
    zf.extractall()
    #p.unlink()
    fnames = zf.namelist()
    # the actual module name
    return fnames[0].split('/')[0]

async def launch_app ():
    await install('selkie')
    app_name = await install('app')
    ls()
    mod = import_module(app_name + '.__main__')
    app = mod.Application()
    await app.ui()
