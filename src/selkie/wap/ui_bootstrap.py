
# In-browser only

import js
from pyodide.http import pyfetch
from pyodide.code import eval_code_async

from pathlib import Path
from zipfile import ZipFile
from importlib import import_module
from asyncio import ensure_future

app_config = None
server_proxy = None


class ServerProxy:

    def __init__ (self, config):
        self.config = config

    def url (self, name, **kwargs):
        script_name = self.config['script_name']
        if kwargs:
            query = '?' + '&'.join(f'{key}={value}' for (key, value) in kwargs.items())
        else:
            query = ''
        return f'{script_name}/{name}{query}'

    async def call (self, msg, binary=False, **kwargs):
        url = self.url(msg, **kwargs)
        print('Call: url=', repr(url), 'binary=', binary)
        res = await pyfetch(url)
        if res.status != 200:
            raise Exception(f'Received status {res.status}: call {msg} {kwargs}')
        if binary:
            return await res.bytes()
        else:
            return await res.text()
    
    async def bootstrap (self):
        return await self.call('bootstrap')

    async def close (self):
        await self.call('close')

    async def get_zipfile (self, name):
        print('Get Zipfile: name=', repr(name))
        assert name in ('selkie', 'app')
        return await self.call(name, binary=True)

    async def list_dir (self):
        return await self.call('dirlist')

    async def load (self, fn):
        return await self.call('text', fn=fn)
    
    async def save (self, fn, contents):
        res = await pyfetch(self.url('text', fn=fn),
                            {'method': 'POST',
                             'body': contents})
        if res.status != 200:
            raise Exception(f'Received status {res.status}: post text {fn}')

    ##

    async def install (self, name):
        home = Path.home()
        p = (home / name).with_suffix('.zip')
        print('Install: name=', repr(name), 'p=', repr(p))
        b = await self.get_zipfile(name)
        print('Got zipfile:', len(b))
        p.write_bytes(b)
        zf = ZipFile(p)
        zf.extractall()
        #p.unlink()
        fnames = zf.namelist()
        # the name of the directory that was created
        return fnames[0].split('/')[0]

    async def start (self):
        start_fnc_module = self.config['start_fnc_module']
        start_fnc_name = self.config['start_fnc_name']
        print('server_proxy.start:', start_fnc_module, start_fnc_name)
        await self.install('selkie')
        print('Installed selkie')
        if not start_fnc_module.startswith('selkie.'):
            await self.install('app')
            print('Installed', start_fnc_module)
        mod = import_module(start_fnc_module)
        print('Instantiating Application')
        fnc = mod.__dict__[start_fnc_name]
        print('Calling', start_fnc_name)
        fnc(self)




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
    

# The server adds:
#
# app_config = {...}
# server_proxy = ServerProxy(app_config)
