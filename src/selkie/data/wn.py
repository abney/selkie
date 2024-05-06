##  @package seal.data.wn
#   Imported from NLTK, with a couple of added functions.

from nltk.corpus import wordnet

##  Same as synsets.

def word_senses (word, pos=None):
    return wordnet.synsets(word,pos)

##  The list of lemma names for words whose meaning is the given concept.

def words_expressing (sense):
    return [lem.name for lem in sense.lemmas]

##  The synset of the input word.

def sense (s):
    return wordnet.synset(s)

##  A list of names for the given concept, of form WORD.POS.I, indicating
#   that this is the i-th concept with the given part of speech in the synsets
#   of the given word.

def sense_names (sense):
    words = words_expressing(sense)
    names = []
    for w in words:
        senses = word_senses(w, sense.pos)
        i = senses.index(sense)
        names.append('%s.%s.%02d' % (w, sense.pos, i+1))
    return names
