
from .pyx.com import Main
from .nlpx.gdev import GDev
from .data.wiktionary import WiktDump, LanguageFile


class SelkieMain (Main):

    # GDev

    def com_sents (self, fn):
        gdev = GDev(fn)


if __name__ == '__main__':
    SelkieMain()()
