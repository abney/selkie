##  \package seal.script.manifest
#   Manage manifest files.

import sys
from seal.core.misc import Shift
from seal.core.manifest import extract_sizes, list_directories, create, difference, \
    export_delta, import_delta, update_hashes

##  Main function.

def main (*args):
    fnc = None
    kwargs = {}

    with Shift(args) as shift:
        while shift.isflag():
            flag = shift()
            for c in flag[1:]:
                if c == 'H':
                    fnc = update_hashes
                    kwargs['dir'] = shift()
                elif c == 'Z':
                    fnc = extract_sizes
                    kwargs['ifile'] = shift()
                elif c == 'l':
                    fnc = list_directories
                    kwargs['ifile'] = shift()
                elif c == 'd':
                    kwargs['diff_spec'] = (shift(), shift())
                elif c == 'e':
                    fnc = export_delta
                    kwargs['ofile'] = shift()
                elif c == 'i':
                    fnc = import_delta
                    kwargs['ifile'] = shift()
                elif c in ('h', 's', 'z'):
                    fnc = create
                    kwargs['ifile'] = shift()
                    kwargs['otype'] = c
                elif c == 'c':
                    kwargs['ofile'] = '-'
                elif c == 'f':
                    kwargs['force'] = True
                elif c == 'u':
                    fnc = create
                    kwargs['update'] = True
                elif c == 'v':
                    kwargs['full'] = True
                else:
                    raise Exception('Unrecognized flag character: %s' % c)

        if fnc is None:
            if 'diff_spec' in kwargs: fnc = difference
            else: fnc = create

        if not shift.isdone():
            if fnc is create: kwargs['ifile'] = shift()
            elif fnc is export_delta: kwargs['diff_spec'] = shift()

    fnc(**kwargs)


if __name__ == '__main__':
    main(*sys.argv)
