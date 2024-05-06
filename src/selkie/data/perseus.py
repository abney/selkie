##  @package seal.data.perseus
#   Perseus Latin and Greek treebanks.

import xml.dom.minidom
from seal.core.config import perseus as perseus_home
from seal.nlp.dep import make_sentence

#from seal.stemma import Dependent, Stemma

##  The subdirectory containing the Latin treebank.
latin_data_dir  = perseus_home/'latin/1.5/data'

##  The filename of the Latin treebank.
latin_data_file = latin_data_dir/'ldt-1.5.xml'

##  The subdirectory containing the Greek treebank.
greek_data_dir  = perseus_home/'greek/1.1/data'

##  The filename of the Greek treebank.
greek_data_file = greek_data_dir/'agdt-1.1.xml'



##  Input: 1-based string version and ID for "root".
#   Output: 0-based int, or the root ID.

def fix_govr (head, n):
    g = int(head) - 1
    if g < 0: return n
    else: return g


##  Treebank.

class Treebank (object):

    ##  Constructor.

    def __init__ (self, fn):
        self._fn = fn
        self._doc = None
        self._sents = None

    ##  List of sentences.

    def sentence_elts (self):
        if not self._sents:
            self._doc = xml.dom.minidom.parse(self._fn)
            self._sents = self._doc.getElementsByTagName('sentence')
        return self._sents

    ##  A StemmaIter.

    def stemmas (self):
        return StemmaIter(self)

    ##  Close.

    def close (self):
        self._doc.unlink()
        self._doc = None
        self._sents = []


##  Iterator for stemmas.

class StemmaIter (object):

    ##  Constructor.

    def __init__ (self, tb):
        self._sents = tb.sentence_elts()
        self._ptr = 0

    ##  Iterator method.

    def __next__ (self):
        if self._ptr >= len(self._sents):
            raise StopIteration

        sent = self._sents[self._ptr]
        self._ptr += 1
        
        words = sent.getElementsByTagName('word')
        n = len(words)
        newsent = make_sentence(n)

        for i in range(n):
            id = int(words[i].getAttribute('id'))
            if id != i + 1:
                raise Exception("Bad ID")
            word = words[i]
            newword = newsent[id]
            newword.form = word.getAttribute('form')
            newword.govr = fix_govr(word.getAttribute('head'), n)
            newword.cat = word.getAttribute('postag')
            newword.lemma = word.getAttribute('lemma')
            newword.role = word.getAttribute('relation')

        return newsent

    ##  Returns self.

    def __iter__ (self):
        return self


##  The Latin treebank.
latin = Treebank(latin_data_file)
##  The Greek treebank.
greek = Treebank(greek_data_file)
