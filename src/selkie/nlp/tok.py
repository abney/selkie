##  \package seal.nlp.tok
#   Tokenizer.

from .io import load_string


##  A token.

class Token (object):
    
    ##  Constructor.

    def __init__ (self, type, string, line, col, i, j):
        self.__type = type
        self.__string = string
        self.__line = line
        self.__column = col
        self.__start = i
        self.__end = j
        if string:
            self.__endcolumn = col + len(string)
        else:
            self.__endcolumn = col

    ##  The token type.  Possible values are: 'word', 'number',
    #   'punct', 'hyphen', 'space', 'newline'.  The 'hyphen' type represents
    #   an embedded hyphen, as distinct from a dash, which is 'punct'.
    #   The 'space' and 'newline' types appear only in temporary tokens
    #   internal to the tokenizer.

    def type (self): return self.__type

    ##  As a string.

    def string (self): return self.__string

    ##  Line number.

    def line (self): return self.__line

    ##  Column where it starts.

    def column (self): return self.__column

    ##  Column where it ends.

    def endcolumn (self): return self.__endcolumn

    ##  Start position in text.

    def start (self): return self.__start

    ##  End position in text.

    def end (self): return self.__end

    ##  String representation.

    def __repr__ (self):
        s = '<' + self.__type
        if self.__string != None: s += ' ' + repr(self.__string)
        s += '>'
        return s


##  Tokenizer.

class Tokenizer (object):
    
    ##  Constructor.

    def __init__ (self):
        
        ##  List of tokens.
        self.tokens = None

        ##  Input text.
        self.text = None

        ##  Current offset in text.
        self.offset = None

        ##  Current line number.
        self.line = None

        ##  Current column in line.
        self.column = None

    ##  Call it on a text.

    def __call__ (self, text):
        self.tokens = []
        self.text = text
        self.offset = 0
        self.line = 1
        self.column = 0

        n = len(text)
        while self.offset < n:
            t = None
            i = self.offset
            (t,j) = \
                self.word(text,i,n) or \
                self.embedded_hyphen(text,i,n) or \
                self.newline(text,i,n) or \
                self.space(text,i,n)
            if t == None: raise Exception('No token found!')
            self.advance(t,j)

        return self.tokens

    ##  Advance.  No return value, but adds a token to the tokens list (unless
    #   the current token is space or newline).  Also updates offset and column,
    #   and may update line.

    def advance (self, type, end):
        token = Token(type, self.text[self.offset:end],
                      self.line, self.column, self.offset, end)
        if not (type == 'space' or type == 'newline'):
            self.tokens.append(token)
        self.offset = token.end()
        if type == 'newline':
            self.line += 1
            self.column = 0
        else:
            self.column += len(token.string())

    ##  Scan a word if able.  Return value is either None or (t,j), where
    #   t is one of: 'word', 'number', 'punct'.

    def word (self, text, i, n):
        anyalpha = False
        anydigit = False
        j = i
        while j < n and \
                not text[j].isspace() and \
                not self.embedded_hyphen(text,j,n):
            if text[j].isalpha(): anyalpha = True
            if text[j].isdigit(): anydigit = True
            j += 1
        if j > i:
            if anyalpha: return ('word', j)
            elif anydigit: return ('number', j)
            else: return ('punct', j)
        else: return None

    ##  Scan an embedded hyphen if able.  Return value is either None or ('hyphen', j).

    def embedded_hyphen (self, text, i, n):
        if i >= n: return None
        if text[i] != '-': return None
        if i == 0: return None
        if text[i-1].isspace(): return None
        j = i + 1
        while j < n and text[j] == '-': j += 1
        if j >= n: return None
        if text[j].isspace(): return None
        return ('hyphen', j)

    ##  Scan a newline if able.  Return value is either None or ('newline', j).

    def newline (self, text, i, n):
        if text[i] == '\n': return ('newline', i+1)
        else: return None

    ##  Scan whitespace if able.  Return value is either None or ('space', j).

    def space (self, text, i, n):
        j = i
        while j < n and text[j].isspace() and text[j] != '\n':
            j += 1
        if j > i: return ('space', j)
        else: return None


##  A Tokenizer instance.  Behaves like a function that returns a list of Tokens.
tokenized = Tokenizer()


##  Test function.  Prints out tokens of a test example.

def test ():
    text = open(texts.kutenai_18).read()
    for token in tokenized(text):
        print(token.type(), repr(token.string()), \
            token.line(), token.column(), \
            token.start(), token.end())


##  Tokenize a text file.

def load_tokens (fn):
    return tokenized(load_string(fn))
