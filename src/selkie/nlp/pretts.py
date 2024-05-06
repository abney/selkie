##  \package seal.nlp.orth
#   Orthography.

from .data import path
from .seq import Queue

##  Load abbreviations table.

def load_abbreviations ():
    table = {}
    with open(path('selkie', 'abbreviations')) as f:
        for line in f:
            line = line.rstrip('\r\n')
            fields = line.split('\t')
            key = fields[0]
            values = tuple(fields[1:])
            table[key] = values
    return table


##  A specialization of str.

class Token (str):
    pass

_magnitudes = ['', 'thousand', 'million', 'billion', 'trillion',
               'quadrillion', 'quintillion', 'sextillion', 'septillion',
               'octillion', 'nonillion', 'decillion', 'undecillion',
               'duodecillion', 'tredecillion']

_teens = ['ten', 'eleven', 'twelve', 'thirteen', 'fourteen',
          'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen']

_enties = ['', '', 'twenty', 'thirty', 'forty',
           'fifty', 'sixty', 'seventy', 'eighty', 'ninety']

_digits = ['', 'one', 'two', 'three', 'four',
           'five', 'six', 'seven', 'eight', 'nine']


##  A normalizer spells out numbers, abbreviations, etc. to
#   produce word forms that can be looked up in a pronunciation
#   dictionary.

class Normalizer (object):

    ##  Constructor.

    def __init__ (self, s):

        ##  The input string.
        self.string = None

        ##  Current position in the input.
        self.offset = 0

        ##  An abbreviations table.
        self.abbrevs = load_abbreviations()

        ##  Queue of words that have been processed but not yet returned by __next__().
        self.queue = Queue()

        ##  Offset of the current number.
        self.number_offset = None

    ##  Returns self.

    def __iter__ (self): return self

    ##  The iteration method.

    def __next__ (self):
        while not self.queue:
            if self.offset >= len(self.string): raise StopIteration
            self.advance()
        return self.queue.read()

    ##  Scan the next word.

    def advance (self):
        s = self.string
        c = s[self.offset]
        if c.isspace():
            self.offset += 1
        elif c.isalpha():
            w = self._scan_word()
            if self._abbrev(w):
                pass
            else:
                self.queue.write(w.lower())
        elif c.isdigit():
            self._number()
        elif self._is_dollar_amt():
            self._dollar_amt()
        else:
            self._punc()

    def _scan_word (self):
        s = self.string
        i = self.offset
        while self.offset < len(s) and s[self.offset].isalpha():
            self.offset += 1
        return s[i:self.offset]

    def _abbrev (self, w):
        if self.offset >= len(self.string): return False
        if self.string[self.offset] != '.': return False
        key = w.lower()
        if key not in self.abbrevs: return False
        self.offset += 1
        values = self.abbrevs[key]
        # needs to be updated to produce lattice
        self.queue.write(values[0])
        return True

    def _number (self):
        s = self.string
        i = self.offset
        j = self.offset + 1
        while j < len(s) and s[j].isdigit(): j += 1
        self.offset = j
        if all(s[k] == '0' for k in range(i,j)):
            self.queue.write('zero')
        elif j - i <= 3:
            while i < j and s[i] == '0': i += 1
            blocks = [(i,j)]
            while self._extend_number(blocks): pass
            self._pronounce_blocks(blocks)
        else:
            self._pronounce_nonzero(i,j)

    def _pronounce_nonzero (self, i, j):
        s = self.string
        while i < j and s[i] == '0': i += 1
        n = j - i

        if n > 4:
            k = i + n % 3
            if k == i: k = i + 3
            blocks = [(i, k)]
            while k < j:
                blocks.append((k, k+3))
                k += 3
            self._pronounce_blocks(blocks)

        elif n == 4:
            if all(s[k] == '0' for k in range(i+1, j)):
                self.queue.write(_digits[int(s[i])])
                self.queue.write('thousand')
            else:
                self._pronounce_nonzero(i, i+2)
                self.queue.write('hundred')
                self._pronounce_nonzero(i+2, j)

        elif n == 3:
            self.queue.write(_digits[int(s[i])])
            self.queue.write('hundred')
            self._pronounce_nonzero(i+1, j)

        elif n == 2:
            if s[i] == '1':
                self.queue.write(_teens[int(s[i:j]) - 10])
            else:
                w = _enties[int(s[i])]
                if not w: raise Exception('Empty n-ty')
                self.queue.write(w)
                self._pronounce_nonzero(i+1, j)

        elif n == 1:
            w = _digits[int(s[i])]
            if w: self.queue.write(w)

    def _extend_number (self, blocks):
        s = self.string
        i = self.offset
        if i < len(s) and s[i] == ',':
            i += 1
            j = i
            while j < len(s) and s[j].isdigit(): j += 1
            if j - i == 3:
                blocks.append((i,j))
                self.offset = j
                return True
        return False

    def _pronounce_blocks (self, blocks):
        if len(blocks) > len(_magnitudes):
            raise Exception('Number is too big')
        for i in range(len(blocks)):
            m = _magnitudes[len(blocks) - 1 - i]
            self._pronounce_block(blocks[i], m)

    def _pronounce_block (self, block, m):
        s = self.string
        (i,j) = block
        if not all(s[k] == '0' for k in range(i,j)):
            self._pronounce_nonzero(i,j)
            if m: self.queue.write(m)

    def _punc (self):
        s = self.string
        i = self.offset
        c = s[i]
        if c == "`" and i+1 < len(s) and s[i+1] == "`":
            self.offset += 2
            return "``"
        elif c == "'" and i+1 < len(s) and s[i+1] == "'":
            self.offset += 2
            return "''"
        else:
            self.offset += 1
            return c

    def _is_dollar_amt (self):
        self.number_offset = None
        s = self.string
        i = self.offset
        c = s[i]
        if c != '$': return False
        i += 1
        while i < len(s) and s[i].isspace(): i += 1
        if i < len(s) and s[i].isdigit():
            self.number_offset = i
            return True
        else:
            return False

    def _dollar_amt (self):
        if self.number_offset is None:
            raise Exception('No number offset')
        self.offset = self.number_offset
        self.number_offset = None
        n = len(self.queue)
        self._number()
        new_n = len(self.queue)
        if new_n == n + 1 and self.queue[0] == 'one':
            self.queue.write('dollar')
        else:
            self.queue.write('dollars')
