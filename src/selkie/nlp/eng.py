##  @package seal.nlp.eng
#   English.

import os
from seal.core import io
from seal.data import census
from nltk.corpus import wordnet as wn


##  The data directory.
directory = os.path.join(io.data, 'eng')

##  English names (from the census).

def names ():
    fn = os.path.join(directory, 'names.lex')
    print('Write', fn)
    f = open(fn, 'w')
    print('%Lexicon', file=f)
    for name in census.names():
        if name.male.rank or name.female.rank:
            print(name.string.lower(), 'fname', file=f)
        if name.last.rank:
            print(name.string.lower(), 'lname', file=f)
               
##  Wordnet.

def wordnet ():
    wordnet_pos('n', 'n[sg]')
    wordnet_pos('a', 'adj')
    wordnet_pos('s', 'adj')
    wordnet_pos('r', 'adv')

##  Wordnet parts of speech.

def wordnet_pos (pos, cat):
    global directory
    fn = os.path.join(directory, 'wn-%s.lex' % pos)
    print('Write', fn)
    f = open(fn, 'w')
    print('%Lexicon', file=f)
    for word in wn.all_lemma_names(pos):
        if word.isalpha():
            print(word, cat, file=f)
    f.close()

##  Executable.

def main ():
    if not os.path.exists(directory):
        os.makedirs(directory)
    names()
    wordnet()


if __name__ == '__main__':
    main()
