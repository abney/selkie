
# importing readline magically causes input() to do line-editing
import readline

from ..com import shift
from .eval import interpret

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
