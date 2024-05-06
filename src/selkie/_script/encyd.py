##  \package seal.script.encyd
#   'Encyclopedia' XML notes.

import sys
from os import unlink
from os.path import exists, expanduser
from seal.core import config
from seal.app.html import *
from seal.app.toplevel import Manager
from seal.core.misc import shift
from seal.core.ency import Ency


#--  App  ----------------------------------------------------------------------

##  The web app.

class EncyApp (SealApp):

    ##  The root is not opened for special requests.

    def lib_file_pathname (self, fn):
        if fn == 'default.css':
            return config.get('ency.css')

    ##  Instantiates Ency.

    def make_root (self, cpt):
        return Ency(self.config)


##  Main function.

def main ():
    log_file = '~/.encylog'
    port = 8004
    while shift.isflag():
        flag = shift()
        if flag == '-c': log_file = '-'
        elif flag == '-p': port = int(shift())
    shift.done()

    if log_file != '-':
        log_file = expanduser(log_file)
        if exists(log_file):
            unlink(log_file)
        
    mgr = Manager(app=EncyApp, log_file=log_file, server_port=port)
    mgr.run()


if __name__ == '__main__':
    main()
