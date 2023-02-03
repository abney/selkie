##  \package seal.script.char
#   Print detailed information about characters.

import sys, unicodedata
from seal.core.misc import shift

##  Arguments are characters.
#   Possible formats:
#
#    - U+1234 - hex
#    - 0x1234 - hex
#    - 0123   - octal
#    - 1234   - decimal
#    - \#c     - character

def main (*args):
    shift.start(args)
    while not shift.isdone():
        arg = shift()

        if not arg: continue

        if arg.startswith('U+') or arg.startswith('0x'):
            x = int(arg[2:], 16)
            c = chr(x)
        elif arg.startswith('0'):
            x = int(arg, 8)
            c = chr(x)
        elif arg[0].isdigit():
            x = int(arg, 10)
            c = chr(x)
        elif len(arg) == 1:
            c = arg
            x = ord(c)
        elif arg[0] == '\\':
            c = arg.encode('ascii').decode('unicode_escape')
            if len(c) != 1:
                print('** Expecting a single character')
                sys.exit(1)
            x = ord(c)
        else:
            c = unicodedata.lookup(arg)
            x = ord(c)

        try:
            name = unicodedata.name(c)
        except ValueError:
            name = '(no name)'

        print('Decimal:', x)
        print('Octal:  ', '0' + oct(x)[2:])
        print('Unicode:', 'U+' + hex(x)[2:])
        print('Char:   ', repr(c))
        print('Name:   ', name)
        print('UTF-8:  ', ' '.join(hex(b)[2:] for b in c.encode('utf8')))


if __name__ == '__main__':
    main(*sys.argv[1:])
