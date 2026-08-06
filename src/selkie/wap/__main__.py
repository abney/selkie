
from ..pyx.com import BaseMain
from .app import exec_app


class Main (BaseMain):

    def com (self, fncname):
        exec_app(fncname, use_sys_argv=False)


# not usually wrapped, in a __main__.py file, but I do an import test,
# and I don't want it running automatically on import

if __name__ == '__main__':
    Main()()

