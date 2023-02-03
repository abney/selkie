##  \package seal.nlp.stemmer
#   Stemmer.

import os
from .data import path


##  True for aeiou.

def is_vowel (c):
    if not c: return False
    return c in 'aeiou'

##  True if not vowel.

def is_consonant (c):
    if not c: return False
    return c not in 'aeiou'

##  Counts y as a vowel if it is not adjacent to a vowel.
#   Counts u as a consonant if it follows q.
#   Otherwise, true for aeiou.

def is_vowel_at (s, i):
    if s[i] == 'y':
        if (i == 0 or is_consonant(s[i-1])) and (i+1 == len(s) or is_consonant(s[i+1])):
            return True
        else:
            return False
    if s[i] == 'u' and i > 0 and s[i-1] == 'q': return False
    return s[i] in 'aeiou'

##  True unless it contains more than one vowels-at.

def is_monosyllable (s):
    vowel = 0
    for i in range(len(s)):
        if is_vowel_at(s,i):
            vowel += 1
            if vowel > 1: return False
    return True

##  True if s[i:j] consists entirely of consonants.

def is_consonant_cluster (s, i, j):
    for k in range(i,j):
        if is_vowel_at(s, k): return False
    return True

##  Returns a 4-tuple containing the last four characters of s
#   in reverse order.  If s is shorter than four characters, it is padded
#   with None.

def last_four (s):
    n = len(s)
    if n == 0: return (None, None, None, None)
    elif n == 1: return (s[-1], None, None, None)
    elif n == 2: return (s[-1], s[-2], None, None)
    elif n == 3: return (s[-1], s[-2], s[-3], None)
    else: return (s[-1], s[-2], s[-3], s[-4])


##  The stemmer.

class Stemmer (object):

    ##  Constructor.

    def __init__ (self, wordsfn, stemsfn):

        ##  A dict whose keys are entire words.
        self.word_exceptions = dict()

        for line in open(wordsfn):
            (key, value) = line.strip().split('\t')
            if ' ' in value:
                (stem, suffix) = value.split(' ')
            else:
                stem = value
                suffix = None
            self.word_exceptions[key] = (stem, suffix)

        ##  A dict whose keys are stems.
        self.stem_exceptions = dict()

        for line in open(stemsfn):
            (key, value) = line.strip().split('\t')
            self.stem_exceptions[key] = value


    ##  Call it on a word.

    def __call__ (self, word):

        word = word.lower()

        if word in self.word_exceptions:
            return self.word_exceptions[word]

        n = len(word)
        (c1,c2,c3,c4) = last_four(word)
    
        if c1 == 's':
    
            # -ss
            if c2 == 's': return (word, None)
    
            elif is_consonant_cluster(word, 0, n-2): return (word, None)
    
            elif c2 == 'e':
    
                # -[oiS]es
                if c3 in 'oiszxh': return (self.change(word[:-2]), '-s')
    
                # -es
                else: return (word[:-1], '-s')
    
            elif c2 == 'u':
    
                # -eaus
                if c4 == 'e' and c3 == 'a': return (word[:-1], '-s')
    
                # -us
                else: return (word, None)
    
            # -is
            elif c2 == 'i': return (word, None)
    
            # -s
            else: return (word[:-1], '-s')
    
        elif c1 == 'd':
    
            if c2 != 'e': return (word, None)
    
            # -Ked
            elif is_consonant_cluster(word, 0, n-2): return (word, None)
    
            # -eed
            elif c3 == 'e': return (word, None)
    
            # -Cred
            elif is_consonant(c4) and c4 != 'r' and c3=='r': return (word, None)
    
            # -ed
            else: return (self.change(word[:-2]), '-ed')
    
        elif c1 == 'g':
    
            if not (c3 == 'i' and c2 == 'n'): return (word, None)
    
            # crying, drying, etc.
            elif n > 4 and c4 == 'y': return (self.change(word[:-3]), '-ing')
    
            # -King
            elif is_consonant_cluster(word, 0, n-3): return (word, None)
    
            # -Cring
            elif n > 4 and c4 == 'r' and word[-5] != 'r' and is_consonant(word[-5]):
                return (word, None)
    
            # -ing
            else: return (self.change(word[:-3]), '-ing')
    
        elif c1 == 'n':
    
            # -men
            if c3 == 'm' and c2 == 'e': return (word[:-3]+'man', '-s')
    
            else: return (word, None)
    
        else: return (word, None)
    
    ##  Determine which stem change to use for the given stem.
    #   If the stem is listed in stem-exceptions, the corresponding value is
    #   returned, short-circuiting the rest.
    
    def change (self, stem):

        if stem in self.stem_exceptions:
            return self.stem_exceptions[stem]
        
        n = len(stem)
        (c1, c2, c3, c4) = last_four(stem)
    
        if c1 == 'i': return stem[:-1] + 'y'
        elif c1 == 'u': return stem + 'e'
        elif c1 in 'aeo': return stem
    
        elif c1 == 'x':
            # xx-
            if c2 == 'x': return stem[:-1]
            else: return stem
    
        elif c1 == 'z':
            # tz-, zz-
            if c2 == 't' or c2=='z': return stem
            else: return stem + 'e'
    
        elif c1 == 's':
            # ss-
            if c2 == 's': return stem
            else: return stem + 'e'
    
        elif c1 == 't':
    
            # et-, it-
            if c2 == 'e' or c2 == 'i': return stem
    
            # else drop through
    
        elif c1 in 'vgc':
    
            # vv-, gg-, cc-
            if c1 == c2: return stem[:-1]
    
            else: return stem + 'e'
    
        elif c1 == 'f':
    
            # ff-
            if c2 == 'f': return stem
    
            # else drop through
    
        elif c1 == 'l':
            # wl, rl, el, Mll, ual, ial
            if c2 == 'w' or c2 == 'r' or c2 == 'e' or \
                    (c2 == 'a' and c3 in 'ui'):
                    # Removed following condition b/c of bug -- Terry:
                    # (c2 == 'l' and is_monosyllable(stem, 0, n)) or \
                return stem
    
            # ll-
            elif c2 == 'l': return stem[:-1]
    
            # Cl-
            elif is_consonant(c2): return stem + 'e'
    
            # else drop through
    
        elif c1 == 'r':
    
            # rr-
            if c2 == 'r': return stem[:-1]
    
            # Cr-
            elif is_consonant(c2): return stem + 'e'
    
            # else drop through
    
        elif c1 == 'h':
    
            # th-
            if c2 == 't': return stem + 'e'
    
            # else drop through
    
        elif c1 == 'y' or c1 == 'w':
    
            # ^.y, ^.w
            if n == 2: return stem + 'e'
    
            else: return stem
    
        elif c1 == 'k':
    
            # VCick- VCCick-
            if n >= 5 and c2 == 'c' and c3 == 'i' and is_consonant(c4) and \
                    (is_vowel(stem[-5]) or
                     n > 5 and is_vowel(stem[-6])):
                return stem[:-1]
    
            # else drop through
    
        # else drop through
    
    
        # ... drop through to here.  last letter is a consonant
    
    
        if is_consonant(c2):
    
            # XX
            if c1 == c2: return stem[:-1]
    
            # CyC
            if c2 == 'y' and is_consonant(c3): return stem + 'e'
    
            # CC
            else: return stem
    
    
        ###  VC
    
        # iaC, uaC, uiC, uoC
        elif (c3 == 'i' and c2 == 'a') or (c3 == 'u' and c2 in 'aio'):
            return stem + 'e'
    
        # VVC
        elif is_vowel(c2) and is_vowel(c3): return stem
    
    
        ###  CVC
    
        # em, om, en, on, er, or */
        elif c2 in 'eo' and c1 in 'mnr': return stem
    
        # CVC
        else: return stem + 'e'


##  Instantiate a stemmer using stemmer_words and stemmer_stems from the seal
#   data directory.

def make_default_stemmer ():
    return Stemmer(path('selkie', 'stemmer_words'), path('selkie', 'stemmer_stems'))

##  The default stemmer.
stemmer = make_default_stemmer()


##  Test the default stemmer on a few words, printing out the results.

def test ():
    for word in ['dogs', 'caught', 'beached', 'starting', 'staring', 
                 'receiving', 'picnicking', 'backed', 'baked']:
        print(word, stemmer(word))
