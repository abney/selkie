##  \package seal.script.panlex
#   Panlex.

import sys
from seal.core.misc import shift
from seal.core.io import pprint
from seal.data.panlex import PanLex


##  Main function.

def main (*args):

    panlex = PanLex()

    shift.start(args)
    com = shift.ifable()

    if not com:
        print('Commands: zip compile var dict')

    elif com == 'zip':
        zf = panlex.zipfile()

        com = shift.ifable()
        
        if not com:
            print('Commands: list head cat table')

        elif com == 'list':
            for name in zf.filenames():
                print(name)

        elif com == 'head':
            fn = shift.ifable()
            shift.done()
            if not fn:
                print('For a list of filenames, do: panlex zip list')
            else:
                zf.head(fn)

        elif com == 'cat':
            fn = shift.ifable()
            shift.done()
            if not fn:
                print('For a list of filenames, do: panlex zip list')
            else:
                zf.cat(fn)

        elif com == 'table':
            fn = shift.ifable()
            key = shift.ifable()
            val = shift.ifable()
            shift.done()
            if not fn:
                print('For a list of filenames, do: panlex zip list')
            else:
                table = zf.table(fn)
                if key is None:
                    table.dump()
                else:
                    table.where(key, val).dump()

        else:
            shift.error('Valid zip commands: list, head, cat, table')

    elif com == 'compile':
        what = shift.ifable()
        shift.done()
        panlex.compile(what)

    elif com == 'var':
        id = shift.ifable()
        shift.done()
        catalog = panlex.catalog()
        varieties = catalog.varieties
        if id:
            pprint(varieties.byuid[id])
        else:
            for key in sorted(varieties):
                print(key)

    elif com == 'lang':
        id = shift.ifable()
        shift.done()
        catalog = panlex.catalog()
        langs = catalog.languages
        if id:
            for v in sorted(langs[id], key=lambda v: v.uid):
                print(v.uid, v.name)
        else:
            for key in sorted(langs):
                print(key)

    elif com == 'dict':
        id = shift.ifable()
        shift.done()
        catalog = panlex.catalog()
        if id:
            pprint(catalog.dicts[id])
        else:
            for id in sorted(catalog):
                print(id)

    else:
        print('** Unrecognized command: %s' % com, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main(*sys.argv[1:])
