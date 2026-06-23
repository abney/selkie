
# In-browser only

import js
from pyodide.http import pyfetch
from pyodide.code import eval_code_async

from pathlib import Path
from zipfile import ZipFile
from importlib import import_module

PORT = 8000
START_FNC_MODULE = None
START_FNC_NAME = None


class ServerProxy:

    async def call (self, msg, binary=False, **kwargs):
        global PORT
        words = [msg] + [f'{key}={value}' for (key, value) in kwargs.items()]
        msg = '?'.join(words)
        res = await pyfetch(f'http://localhost:{PORT}/call/{msg}')
        if res.status != 200:
            raise Exception(f'Received status {res.status}')
        if binary:
            return await res.bytes()
        else:
            return await res.text()
    
    async def bootstrap (self):
        return await self.call('bootstrap')

    async def close (self):
        await self.call('close')

    async def get_zipfile (self, name):
        assert name in ('selkie', 'app')
        return await self.call(name, binary=True)
    
    async def load (self, fn):
        return await self.call('text', fn=fn)
    
    async def save (self, fn, contents):
        global PORT
        res = await pyfetch(f'http://localhost:{PORT}/call/text?fn={fn}',
                            {'method': 'POST',
                             'body': contents})
        if res.status != 200:
            raise Exception(f'Received status {res.status}: post text {fn}')


server_proxy = ServerProxy()

# class PseudoModule:
# 
#     def __init__ (self, env):
#         self.__dict__ = env
# 
#     def __getattr__ (self, attr):
#         return self.__dict__[attr]
# 
# 
# class Context:
# 
#     async def load (self, fn):
#         env = {}
#         source = await file_contents(fn)
#         await eval_code_async(source, env)
#         return PseudoModule(env)
    

async def install (name):
    global server_proxy
    home = Path.home()
    p = (home / name).with_suffix('.zip')
    b = await server_proxy.get_zipfile(name)
    p.write_bytes(b)
    zf = ZipFile(p)
    zf.extractall()
    #p.unlink()
    fnames = zf.namelist()
    # the name of the directory that was created
    return fnames[0].split('/')[0]

async def launch_app ():
    global START_FNC_MODULE, START_FNC_NAME
    print('Launch App:', START_FNC_MODULE, START_FNC_NAME)
    await install('selkie')
    print('Installed selkie')
    if not START_FNC_MODULE.startswith('selkie.'):
        await install('app')
        print('Installed', START_FNC_MODULE)
    mod = import_module(START_FNC_MODULE)
    print('Instantiating Application')
    fnc = mod.__dict__[START_FNC_NAME]
    print('Calling', START_FNC_NAME)
    fnc()
