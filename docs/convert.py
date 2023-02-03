#
#  python convert.py foo
#
#     Reads foo.html and writes foo.rst
#

import sys
from os.path import exists
from selkie.xml import load_xml

def convert (basename):
    infn = basename + '.html'
    if not exists(infn):
        print('** File not found:', infn)
        return
    outfn = basename + '.rst'
    if exists(outfn):
        print('** File exists:', outfn)
        return
    print('Reading', infn, 'writing', outfn)
    xml = load_xml(basename + '.html', entities=False)
    with open(outfn, 'w') as f:
        for s in convert_node(xml):
            f.write(s)

def convert_children (node):
    if node.children:
        for child in node.children:
            for s in convert_node(child):
                yield s

def convert_node (node):
    cat = node.cat

    if cat == '#CDATA':
        yield node.word

    elif cat in ('head',):
        pass

    elif cat in ('h1', 'h2', 'h3', 'h4'):
        title = ''.join(s for s in convert_children(node))
        yield title
        yield '\n'
        if cat == 'h1': c = '='
        elif cat == 'h2': c = '-'
        elif cat == 'h3': c = '^'
        else: c = '"'
        yield c * len(title)
        yield '\n'

    elif cat in ('i', 'b', 'tt'):
        if cat == 'i': c = '*'
        elif cat == 'b': c = '**'
        else: c = '``'
        yield c
        for s in convert_children(node):
            yield s
        yield c

    elif cat == 'table':
        yield '\n.. list-table::\n\n'
        for row in node.children:
            if row.cat == 'tr':
                pfx = '   * - '
                for cell in row.children:
                    if cell.cat == 'td':
                        yield pfx
                        for s in convert_children(cell):
                            yield s
                        yield '\n'
                        pfx = '     - '

    else:
        for s in convert_children(node):
            yield s


if __name__ == '__main__':
    convert(sys.argv[1])
