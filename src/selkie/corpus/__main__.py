
from ..pyx.com import BaseMain
from .corpus import Corpus


class Main (BaseMain):

    def com (self, fn):
        corpus = Corpus(fn)
        print(corpus.cld_format(), end='')


# not usually wrapped, in a __main__.py file, but I do an import test,
# and I don't want it running automatically on import

if __name__ == '__main__':
    Main()()
