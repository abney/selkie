##  \package seal.script.abspath
#   Convert a relative path to absolute.  Expands tilde.

import sys
from os.path import expanduser, abspath
from seal.core.misc import Shift


##  Convert a relative path to absolute.  Expands tilde.

def main (args):
    with Shift(args) as shift:
        fn = shift()
    print(abspath(expanduser(fn)))


if __name__ == '__main__':
    main(sys.argv[1:])
