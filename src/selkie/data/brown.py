##  @package seal.data.brown
#   The Brown corpus.

from nltk.corpus import brown
from nltk import ConditionalFreqDist


##  The words.

def words (fileids=None, categories=None):
    return brown.words(fileids, categories)

##  The tagged words.

def tagged_words (fileids=None, categories=None, tagset=None):
    if tagset == None or tagset == 'original':
        return brown.tagged_words(fileids, categories)
    elif tagset == 'base':
        return [(word, base(tag))
                for (word,tag) in brown.tagged_words(fileids, categories)]
    else:
        raise Exception("Unknown tagset: " + str(tagset))

##  The base form of a tag.  Strip FW-, -HL, -TL, -NC.

def base (tag):
    if tag.endswith('-HL'):
        tag = tag[:-3]
    if tag.endswith('-TL'):
        tag = tag[:-3]
    if tag.endswith('-NC'):
        tag = tag[:-3]
    # there is at least one case of -TL out of order
    if tag.endswith('-TL'):
        tag = tag[:-3]
    # these occur a few times as errors for -TL, -NC
    if tag.endswith('-T') or tag.endswith('-N'):
        tag = tag[:-2]
    if tag.startswith('FW-'):
        tag = tag[3:]
    return tag

##  Whether it is a punctuation tag.

def ispunct (tag):
    return tag in ("'", "''", '(', ')', '--', '.', ':', "``")

##  Whether it is a proper-noun tag.

def isproper (tag):
    return tag in ('NP', 'NP$', 'NPS', 'NPS$')
