
# This is the "prevailing environment" application
# The browser main is browser.py

import sys
from .framework import BaseServerSide


class ServerSide (BaseServerSide):

    pass


if __name__ == '__main__':
    ss = ServerSide(name='pd2', 
                    pyodide_source='~/tar/cl/src/2024/pyodide-0.26.1.tar.bz2',
                    browser_main='pd2.test_cs.ClientSide',
                    dependencies=['selkie'],
                    options=sys.argv)
    ss.run()
