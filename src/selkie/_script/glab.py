##  \package seal.script.glab
#   Run GLab.

# importing readline magically causes input() to do line-editing
import readline

from ..cld.seal.misc import shift
from ..cld.glab.eval import interpret

##  Main function.

def main ():

    debugging = False

    while shift.isflag():
        flag = shift()
        if flag == '-g':
            debugging = True
        else:
            shift.error('Unrecognized flag: %s' % flag)

    filename = shift.ifable()
    shift.done()

    if filename is None:
        interpret.interactive(debugging=debugging)
    else:
        interpret.batch(filename, debugging=debugging)


if __name__ == '__main__':
    main()
