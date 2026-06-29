
from ..pyx.com import BaseMain
from .corpus import Corpus


class Main (BaseMain):

    def com (self, fn):
        corpus = Corpus(fn)
        print(corpus.cld_format(), end='')


Main()()
