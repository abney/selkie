
from ..pyx.com import BaseMain
from .app import exec_app


class Main (BaseMain):

    def com (self, fncname):
        exec_app(fncname, use_sys_argv=False)


Main()()

