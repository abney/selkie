##  @package seal.data.idp
#   The Internet Dictionary Project files.

from seal.core.config import idp as idp_dir


##  The lexicons.
Lexicons = {}

##  Info: (filename, key is English?).  English is always in the first field.
Info = {'fra': ('French.txt', True),
        'deu': ('German.txt', True),
        'ita': ('Italian.txt', True),
        'lat': ('Latin.txt', False),
        'por': ('Portuguese.txt', True),
        'spa': ('Spanish.txt', True)}

##  Look up a word.

def lookup (word, lang):
    return lexicon(lang).get(word)

##  Get a lexicon (dict).  Loads the Lexicon if necessary.

def lexicon (name):
    if name not in Lexicons:
        Lexicons[name] = load(name)
    return Lexicons[name]

##  Load a lexicon.

def load (name, warnings=False):
    if name not in Info:
        raise Exception('No dictionary for "%s"' % name)
    (fn, key_is_english) = Info[name]
    fn = idp_dir/fn
    lexicon = {}
    with open(fn, encoding='latin1') as f:
        for (i, line) in enumerate(f):
            if not line.startswith('#'):
                try:
                    (eng,tgt) = line.strip().split('\t')
                    if key_is_english:
                        lexicon[eng] = tgt
                    else:
                        lexicon[tgt] = eng
                except Exception as e:
                    if warnings:
                        print('Warning: line %d: %s' % (i+1, str(e)))
    return lexicon
