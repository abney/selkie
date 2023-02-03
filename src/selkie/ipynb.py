##  @package seal.core.ipynb
#   Convert an ipython notebook to a simple python file.
#   Can be called:
#
#       python -m seal.core.ipynb infile [outfile]
#
#   If outfile is not provided, writes to stdout.

import json
from .com import Shift


##  Load a notebook (JSON format).

def load (fn):
    with open(fn) as f:
        return json.load(f)

##  Convert a notebook (JSON format) to simple Python.  Cells are separated by
#   empty lines.

def convert (ifn, ofn):
    top = load(ifn)
    cells = top['cells']
    first = True
    with open(ofn, 'w') as f:
        for cell in cells:
            if first: first = False
            else: f.write('\n\n')
            for s in cell['source']:
                f.write(s)

##  Call as an executable.

def main ():
    with Shift() as shift:
        ifn = shift()
        if not shift.isdone():
            ofn = shift()
        elif ifn.endswith('.ipynb'):
            ofn = ifn[:-6] + '.py'
        else:
            ofn = ifn + '.py'
        shift.done()
        print('Writing', ofn)
        convert(ifn, ofn)


if __name__ == '__main__':
    main()
