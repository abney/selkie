
PORT = 8000

try:

    import js
    root = js.document.getElementById("root")
    print('Got root:', root)

    def write (*objs):
        s = ' '.join(str(x) for x in objs)
        root.appendChild(js.document.createTextNode(s))
        root.appendChild(js.document.createElement('BR'))

    write('Loading bootstrap')

    import selkie
    write('Selkie version=', selkie.__version__, 'file=', selkie.__file__)
    
    from pyodide.http import pyfetch

    async def file_contents (fn):
        res = await pyfetch(f'http://localhost:{PORT}/' + fn)
        if res.status != 200:
            raise Exception(f'Received status {res.status}: {fn}')
        text = await res.text()
        return text

    async def file_bytes (fn):
        res = await pyfetch(f'http://localhost:{PORT}/' + fn)
        if res.status != 200:
            raise Exception(f'Received status {res.status}: {fn}')
        b = await res.bytes()
        return b

    write('Test file_contents:', repr(await file_contents('foo.py')))

    from pyodide.code import eval_code_async

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

    foo = await load('foo.py')
    write('Test load:', foo.__dict__.get('test'))

    foo.test(write)

    from pathlib import Path

    def ls (fn):
        p = Path(fn)
        if p.is_dir():
            names = [str(n) for n in p.iterdir()]
            write(f'List dir {str(fn)}:', *names)
        else:
            write('List file:', str(p))

    ls('/')
    ls('/home')
    ls('/home/web_user')

    home = Path.home()
    ls(home)

    with open(home / 'foo', 'w') as f:
        print('Test 1 2 3', file=f)

    write('Text cwd request handler:', await file_contents('cwd/testmod/foo.py'))

    from zipfile import ZipFile

    async def install (name):
        home = Path.home()
        p = (home / name).with_suffix('.zip')
        b = await file_bytes('zip/' + name)
        p.write_bytes(b)
        zf = ZipFile(p)
        zf.extractall()
        #p.unlink()

    await install('testmod')
    write('Installed testmod')

    from testmod.foo import test2
    test2(write)

    write('Bootstrap complete')

except Exception as e:
    pass
