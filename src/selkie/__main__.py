
from .pyx.com import BaseMain
from .pyx.io import xopen
from .pyx.string import unidescribe, uencode, udecode
from .nlpx.gdev import GDev
from .data.wiktionary import WiktDump, LanguageFile


class SelkieMain (BaseMain):

    # GDev

    def com_sents (self, fn):
        gdev = GDev(fn)

    def com_get (self, fn, i, j=None):
        '''Prints a range of lines of the file. Example: get foo 10 20'''
        i = int(i)
        if j is not None:
            j = int(j)
        with xopen(fn) as f:
            for (lno, line) in enumerate(f, 1):
                if j is not None and lno >= j:
                    break
                if lno >= i:
                    print(line, end='')

    def com_ud (self, fn='-'):
        '''Unicode dump.'''
        with xopen(fn) as f:
            for (lno, line) in enumerate(f, 1):
                print()
                print('Line', lno)
                print('#', line, end='')
                unidescribe(line)
                

    def com_udecode (self, fn='-'):
        '''Interpret \\Uu escapes.'''
        with xopen(fn) as f:
            for line in f:
                print(udecode(line), end='')

    def com_uencode (self, fn='-'):
        '''Insert \\Uu escapes.'''
        with xopen(fn) as f:
            for line in f:
                print(uencode(line), end='')

    def com_lno (self, fn='-'):
        '''Prefix lines with line numbers.'''
        try:
            with xopen(fn) as f:
                for (lno, line) in enumerate(f, 1):
                    print(lno, line, end='')
        except BrokenPipeError:
            pass


if __name__ == '__main__':
    SelkieMain()()
