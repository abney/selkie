
import sys
from os import listdir
from os.path import join, expanduser, exists
from seal.core import config
from seal.core.misc import Shift
from seal.core.ency import freeze_to


def find_lib_file (tgt_name):
    dirs = config.get('ency.libpath').split(':')
    for dir in dirs:
        dir_fn = expanduser(dir)
        if exists(dir_fn):
            for name in listdir(dir_fn):
                if (name.startswith(tgt_name) and
                    (len(tgt_name) == len(name) or
                     not name[len(tgt_name)].isdigit())):
                    print(join(dir, name))
        else:
            print('(Directory not found: %s)' % dir)


def main ():

    coms = {
        'lib': find_lib_file,
        'freeze': freeze_to
        }

    with Shift(sys.argv) as shift:
        com = shift()
        f = coms.get(com)
        if f is None:
            shift.error("Unrecognized command '%s'" % com)
        args = shift.rest()
        f(*args)


if __name__ == '__main__':
    main()
