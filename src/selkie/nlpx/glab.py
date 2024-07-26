
from ..pyx.com import BaseMain
from .gdev import GDev


class SelkieMain (BaseMain):

    # GDev

    def com_sents (self, fn):
        gdev = GDev(fn)


if __name__ == '__main__':
    SelkieMain()()
