##  @package seal.cld.corpus.token
#   Represents tokenized text.
#
#   To define tokenization precisely, we require
#   three string-class functions:
#   anyletter(), anyword(), and isword().
#   There are 30 Unicode character categories,
#   which group into 7 toplevel categories:</p>
#
#     - L - Letter
#     - M - Mark, controls letter combination
#     - N - Number
#     - P - Punctuation
#     - S - Symbol
#     - Z - Separator, whitespace
#     - C - Other: control, format, surrogate, private use, unassigned
#
#   For purposes of tokenization, we reduce this list to three classes:
#
#     - Word - L, M, N, or S
#     - Punc - P or Z
#     - Indef - C
#
#   A token is defined thus: split text at whitespace to yield <b>tokens</b>.
#   If the token contains no Word character, it is a <b>miscellaneous token.</b>
#   Otherwise, it is split into <b>leading punctuation</b>,
#   <b>form</b>, and <b>trailing punctuation</b>.  The form begins and ends with
#   a Word character, and the leading and trailing punctuation contain no Word
#   characters.  If the form contains at least one L character, the token is a
#   <b>word token,</b> and otherwise it is a <b>numeric token.</b>
#
#   Tokenized file format
#
#   In the file, the text is represented in tokenized format.
#   The file is tabular, and contains four types of record,
#   distinguishable by the number of (tab-separated) fields:
#
#     - id - Start a block
#     - form lpunc rpunc - Non-lexical token
#     - form sense lpunc rpunc - Lexical token
#     - 'nxid' id - Next available ID (last line of file)


import os, unicodedata
from seal.cld.db.disk import writer, Loading
from seal.cld.db.file import File
from seal.cld.corpus.lexicon import Lexicon
from seal.cld.corpus.rom import Decoder


##  True if there is at least one word character (LMNS), and no punctuation
#   characters (PZ).

def isword (s):
    anyword = False
    for c in s:
        t = unicodedata.category(c)[0]
        if t in 'PZ': return False
        elif t in 'LMNS': anyword = True
    return anyword


##  True if there is at least one word character (LMNS).

def anyword (s):
    for c in s:
        if unicodedata.category(c)[0] in 'LMNS': return True
    return False


##  True if there is any letter character (L).

def anyletter (s):
    for c in s:
        if unicodedata.category(c)[0] == 'L': return True
    return False


#--  Tokenization  -------------------------------------------------------------

##  Creates a Tokenizer and calls it on the string, returning a list of tokens.

def tokenize (s, lw, loc=None):
    return list(Tokenizer(lw, loc)(s))


class TokenizationError (Exception): pass


##  A tokenizer.
#
#   Translates a string into a list of
#   tokens for a particular paragraph.  It takes three arguments: the
#   string to tokenize, lex, and parid.
#   When creating a temporary paragraph, lex must be a Lexicon (read-only),
#   and parid is omitted.  When creating a permanent paragraph,
#   lex must be a LexiconWriter (read-write), and parid
#   must be provided.
#
#   The input string is romanized (ASCII).
#   The tokenizer splits it at whitespace and then processes
#   each whitespace-separated token.  The token string is translated to
#   Unicode using the lexicon's orthography, while keeping a record of
#   which romanized characters produced which Unicode characters as output.
#   [BUG: should use the
#   text's orthography to decode, then recode into the lexicon's orthography.]
#
#   If the Unicode version contains at least one
#   letter, the token is a lexical token and otherwise it is a
#   non-lexical token.  Examples of non-lexical tokens are numbers,
#   money amounts, dates, and isolated punctuation.
#
#   A lexical token is analyzed as consisting
#   of leading punctuation, a form, an optional sense number,
#   and trailing punctuation.
#   The character classes are determined from the Unicode version, but the
#   token pieces are romanized strings.  The form (when translated to
#   Unicode) begins and ends with word characters, and the leading and
#   trailing punctuation strings contain no word characters.  It is
#   possible that the form contains embedded characters that are not word
#   characters.
#
#   The lexical entry for the form is fetched from the lexicon.  If the
#   lexicon is read-only and the form is not found, an error is signalled.
#   If the lexicon is read-write, a new entry is created if necessary.
#
#   The output of tokenize() is a list of Token instances.
#
#   The Tokenizer assumes that we are using the lexicon romanization.
#   A text that uses a different romanization must first be converted.
#
#   Usage:
#
#      tkz = Tokenizer(lex)
#
#   The argument lex may either be a lexicon or a lexicon lock.
#   If it is a lexicon, the token is looked up, but no reference is interned.
#
#   The tokenizer iterates over tokens:
#
#      for token in tkz(s): ...
#
#   s is split at whitespace to produce whitespace-separated blocks (wsb's).
#   Each wsb yields one token.
#
#   The romanization is taken from the lex/lock.
#   We get the parse for the transduction.
#   The parse divides wsb and unicode into aligned spans.
#   Find the first and last spans where the unicode contains word characters.
#   Spans before the first and after the last count as punctuation.
#
#   There may be a sense number (.0, .1, etc) between form and trailing punc.

class Tokenizer (object):

    ##  Constructor.

    def __init__ (self, lex, loc=None):

        ##  The lexicon in which to place lexical entries.
        self.lex = lex

        ##  The PARID of the paragraph being tokenized.
        self.loc = loc

        ##  A decoder constructed from my text's romanization.
        self.decoder = lex.romanization().decoder()

    def _get_lexent (self, form, sense):
        key = (form, sense)
        if self.loc is None: return self.lex[key]
        else: return self.lex.intern(key, self.loc)

    ##  Call it on a string.  Iterates over Token instances.

    def __call__ (self, s):
        for tokstr in s.split():
            yield self.make_token(tokstr)

    ##  Create a Token.  Does the real work.

    def make_token (self, input):
        (parse, output) = self.decoder.parse(input)
        span = self._find_form(parse, output)
        if span is None:
            return Token(input, None, '', '', None)
        else:
            (i,j) = span

            lpunc = input[:parse[i][0]]
            form = input[parse[i][0]:parse[j][0]]

            if anyletter(output[parse[i][-1]:parse[j][-1]]):
                (sense, k) = self._trim_sense(parse, j, input)
                lexent = self._get_lexent(form, sense)
            else:
                sense = lexent = None

            rpunc = input[parse[k][0]:]

            return Token(form, sense, lpunc, rpunc, lexent)
        
    # trim punctuation from both ends
    # signal an error if any unit contains mixed punc/non-punc
    # units translating as '' are trimmed

    def _find_form (self, parse, output):
        first = last = None
        for i in range(0, len(parse)-1):
            s = output[parse[i][-1]:parse[i+1][-1]]
            if anyword(s):
                last = i
                if first is None: first = i
        if first is None: return None
        else: return (first, last+1)

    def _trim_sense (self, parse, j, input):
        if j+1 >= len(parse): return (0,j)
        t0 = parse[j][0]
        if input[j] != '\\': return (0,j)
        u = parse[j+1][0]
        for t in range(t0,u):
            if not input[t].isdigit(): return (0,j)
        return (int(input[t0+1:u]), j+1)


#--  Token  --------------------------------------------------------------------

##  A token.
#
#   We use simply whitespace-separated tokenization.
#   Hence a token may include leading and trailing punctuation.
#   The original token divides into lpunc, form, and rpunc.
#   The form contains word characters (letter, mark, number, or symbol);
#   the lpunc and rpunc contain punctuation and separator symbols.
#
#   A lexical token is one whose form contains at least one letter.
#
#   A lexical token is disambiguated by marking it with a sense number.
#   A non-lexical token has sense = None.
#
#   The disambiguated token is interned in the lexicon.
#   The token has a pointer to its lexical entry, and the lexical entry
#   contains a list of token locations.

class Token (object):
    
    ##  Constructor.

    def __init__ (self, form, sense, lpunc, rpunc, lexent=None):
        self._form = form
        self._sense = sense  # int, or None for non-word token
        self._lpunc = lpunc
        self._rpunc = rpunc
        self._lexent = lexent

    ##  The form, as a romanized string.

    def form (self):
        return self._form

    ##  The sense number (int).

    def sense (self):
        return self._sense

    ##  Leading punctuation (romanized string).

    def lpunc (self):
        return self._lpunc

    ##  Trailing punctuation (romanized string).

    def rpunc (self):
        return self._rpunc

    ##  A LexicalEntry.

    def lexent (self):
        return self._lexent

    ##  Of form + sense number.

    def romanization (self):
        return self._lexent.romanization()

    ##  Of the entire token, including punctuation.
    #   Used by token.glossed_word().

    def unicode (self):
        rom = self.romanization()
        return rom.decode(self._lpunc + self._form + self._rpunc)

    ##  Romanized, includes punctuation.

    def __str__ (self):
        if self._sense: ss = '\\' + str(self._sense)
        else: ss = ''
        return self._lpunc + self._form + ss + self._rpunc


#--  TokenBlock  ---------------------------------------------------------------

##  A unit of tokenized text.
#
#   A TokenBlock may be a sentence, word, or paragraph; it is the unit
#   of translation.
#
#   It is the product of tokenizing a
#   target-language string.  It may have a PARID, which is a pair
#   <code>(<i>t</i>, <i>i</i>)</code> of a text ID and paragraph index.
#   The paragraph index is
#    permanent; the paragraph also has a current index, which may change.
#
#   A TokenBlock is the unit for editing plaintext.  The textbox in a plaintext
#   editor, and the textbox in a transcription window, both correspond to
#   TokenBlocks.
#
#   TokenBlocks are tokenized and interned in the lexicon whenever they are edited.
#   Hence TokenBlocks are the units associated with IDs (corpus locations).
#
#   At the same time, we need to know the index of a TokenBlock so that we can
#   find the previous and next blocks, given the current one.  (Needed when
#   editing IGT.)
#
#   TokenBlocks are elements of a TokenFile.
#   When one edits the textbox, the result is an ASCII string.  A TokenBlock's
#   contents are set using a Tokenizer.
#
#   We must distinguish between a newly-created block, whose tokens should be
#   interned, and a block that is loaded from disk, whose tokens have already been
#   interned.  TokenFile handles that: it uses block.set_contents() only for
#   newly-created blocks (or for modifying existing blocks).
#
#   The romanization is determined by the lexicon.
#   \\0, \\1, etc are used as sense numbers.
#   \\S is used as sentence boundary, and \\T is used as translation-unit boundary.
#
#   Plaintext and translations units are two different views of a TokenFile as
#   a list of strings - see TokenFile.
#
#   CALLS TO LEXICONWRITER
#
#   via Tokenizer:
#      romanization()
#      intern()
#
#   delete_ref()

class TokenBlock (object):

    ##  Constructor.
    #   @arg parent - the TokenFile that
    #   this block belongs to.
    #   @arg loc - its location, a PARID.
    #   @arg index -  its current index in the token file, which may change as
    #   the text is edited.

    def __init__ (self, parent, loc, index):
        self._parent = parent
        self._loc = loc  # None if this is read-only
        self._index = index
        self._string = None
        self._tokens = None
        self._orig = None  # for translation unit: (i,j) in original TokenFile

    ##  Returns the unit number, which is a permanent identifier for this
    #   unit, relative to its text.

    def id (self):
        return self._loc[1]

    ##  Returns the TID, a string.

    def textid (self):
        # not ._loc[0], because that does not exist if the plaintext is a transcript
        return self._parent.textid()

    ##  Returns the PARID, a pair (TID, unit number).

    def loc (self):
        return self._loc

    ##  Returns the current index.  This may change as the text is edited.

    def index (self):
        return self._index

    ##  If this unit is created by merging "snippets" in a transcription,
    #   this contains a pair of indices, representing the slice in the transcription
    #   that this unit came from.

    def orig (self):
        return self._orig

    ##  The lexicon for the text's language.

    def lexicon (self): return self._parent.lexicon()

    ##  The romanization, from the parent text.

    def romanization (self):
        return self._parent.romanization()

    ##  The number of tokens.

    def __len__ (self):
        return self._tokens.__len__()

    ##  The <i>i</i>-th token.

    def __getitem__ (self, i):
        return self._tokens.__getitem__(i)

    ##  Iterate over tokens.

    def __iter__ (self):
        return (self._tokens or []).__iter__()

    ##  The member of the parent's translation that aligns with this unit.

    def translation (self):
        return self._parent.block_translation(self._index)

    def _editing (self):
        if self._loc is None:
            raise Exception('Attempt to edit read-only TokenBlock')
        if self._parent._writer is None:
            raise Exception('TokenBlock can only be edited in context of TokenFile writer')

    ##  Set the contents by tokenizing the given string.
    #   Tokens will be interned in the lexicon.  The lexicon will be used
    #   to create lexical entries for new
    #   tokens, and will record the location of tokens in the reference lists
    #   used to create concordances.
    #
    #   However, if this block represents a temporary sentence (as indicated
    #   by its having no location), then any
    #   tokens that lack an existing lexical entry will cause an error to
    #   be signaled.

    def set_contents (self, s):
        self._editing()
        if self._tokens: self.delete_contents()
        self._string = s
        if s:
            self._tokens = tokenize(s, self.lexicon(), self._loc)
        else:
            self._tokens = []

    ##  Replace the j-th token.

    def set_token (self, j, s):
        if any(c.isspace() for c in s):
            raise Exception('Token contains whitespace')
        self._editing()
        self._tokens[j] = Tokenizer(self.lexicon(), self._loc).make_token(s)

    ##  Deletes all tokens and also updates reference lists in the lexicon to remove
    #   references to this unit.

    def delete_contents (self):
        self._editing()
        assert self._parent._writer
        lex = self.lexicon()
        loc = self._loc
        for token in self._tokens:
            lex.delete_parid(loc, token._form, token._sense)
        self._tokens = None

    ##  Append a token.

    def append (self, token):
        self._editing()
        loc = self._loc
        lex = self.lexicon()
        key = (token.form(), token.sense())
        token.lexent = lex.intern(key, loc)
        if self._tokens is None:
            self._tokens = [token]
        else:
            self._tokens.append(token)

    ##  Append a block or list of tokens.

    def extend (self, tokens):
        if isinstance(tokens, TokenBlock):
            tokens = tokens._tokens
        for token in tokens:
            self.append(token)

    ##  Space-joined token ASCII strings; cached.

    def __str__ (self):
        # blocks loaded from disk have self._string == None
        if self._string is None:
            self._string = ' '.join(str(tok) for tok in self._tokens)
        return self._string

    ##  Same as __str__().

    def ascii (self): return self.__str__()

    ##  Decode the string.

    def unicode (self):
        s = self.__str__()
        rom = self._parent.romanization()
        return rom.decode(s)

    ##  String representation.

    def __repr__ (self):
        return '<TokenBlock %s>' % repr(self._loc)


#--  Plaintext  ----------------------------------------------------------------

##  This is a duck type.  TokenFile and TransTokenFile implement it.
#   The concordance code, for example, depends on these members and methods.
#
#   text      - the Text whose contents the plaintext represents.
#   textid()  - returns text.id()
#   by_id()   - returns a dict that maps paragraph IDs to TokenBlocks.
#   block_translation(i)
#             - returns text.trans[i], or '' if text.trans is None.


#--  TokenFile  ----------------------------------------------------------------

##  A tokenized text.
#
#   Conceptually, a TokenFile is a list of TokenBlocks.
#   Each block has an ID that is permanently assigned when it is created.
#   A block also has a current index corresponding to its position
#   in the list; that index will change if the block's position changes.
#   The TokenFile member nextid contains the ID for the next
#   paragraph to be created.
#
#   Permanent IDs are assigned as blocks are created.  If blocks are deleted, there
#   will be gaps in the sequence.  IDs of deleted blocks are not re-used.</p>'''
#
#   This is the basic (tokenized) text file.  It represents either an original
#   text or a transcript.
#
#   Conceptually, a TokenFile is a list of TokenBlocks (paragraphs, translation
#   units).  Each segment has an ID that is permanently assigned when it is created.
#
#   An OriginalText is a TokenFile with the added ability to insert segments
#   in arbitrary positions.  It does not guarantee that IDs
#   increase sequentially.  When a segment is deleted, its ID will not be
#   re-used.
#
#   FILE FORMAT
#
#   In the file, the text is represented in tokenized format.
#   The file is tabular, and contains four types of record,
#   distinguishable by the number of (tab-separated) fields:
#
#       id                        - new segment
#       form lpunc rpunc          - non-word token
#       form sense lpunc rpunc    - word token
#       'nxid' id                 - next available ID (last line of file)
#
#   The TokenFile member 'nextid' contains the id for the next paragraph to
#   be created.
#
#   PLAINTEXT
#
#   The method 'plaintext' takes the blocks to be the units, whereas
#   'translation_units' concatenates all blocks and re-splits at \\T tokens.
#   Both are read-only.
#
#   ACCESS
#
#   A TokenFile behaves like a list of TokenBlocks.  One can also access by ID.
#
#       f[i]         - Access the i-th block
#       f.by_id(id)  - Access the block with the given id
#
#   MODIFICATION
#
#   The methods for modifying a TokenFile f are:
#
#       f.insert(i,s)   - Tokenize s and insert it at position i.  Store references
#                         to the tokens in the lexicon.
#
#       f.set(i,s)      - Replace the i-th segment.  Old references are deleted,
#                         new references are inserted.
#
#       f.delete(i)     - Delete the i-th segment.  References are deleted.
#
#       f.set_length(n) - Add empty blocks to extend length to n.  Error if
#                         n is less than current length.
#
#   One may also do f[i].set_contents(s) to change the contents of an
#   existing segment.

class TokenFile (File):

    ##  Constructor.  The parent should be a text; it is stored in the member
    #   text.

    def __init__ (self, *args, **kwargs):
        File.__init__(self, *args, **kwargs) # parent: Page

        ##  The text that this belongs to.
        self.text = self.parent()

        ##  The unit number that will be assigned to the next TextBlock created.
        #   Unit numbers begin with 0.
        self.nextid = None

        # set by lexicon()
        self._lexicon = None
        # set by __read__()
        self._by_id = None
        self._ntunits = None
        self._blocks = None

    ##  The <i>i</i>-th TokenBlock (by index, not ID).

    def __getitem__ (self, i):
        return self.blocks().__getitem__(i)

    ##  The number of TokenBlocks.

    def __len__ (self):
        return self.blocks().__len__()

    ##  Iterate over TokenBlocks.

    def __iter__ (self):
        return self.blocks().__iter__()

    ##  The list of TokenBlocks.

    def blocks (self):
        self.require_load()
        return self._blocks

    ##  Returns the block whose ID is <i>i</i> (an int).
    #   Signals a KeyError if there is no such block.

    def by_id (self, segid): # segid: int
        self.require_load()
        return self._by_id[segid]

    ##  The ID of my text.

    def textid (self):
        return self.text.id()

    ##  Returns None.  Overridden by TransTokenFile.

    def transcription (self): return None

    ##  Returns the lexicon's romanization.

    def romanization (self):
        return self.lexicon().romanization()

    ##  The lexicon belonging to the text's language.

    def lexicon (self):
        if self._lexicon is None:
            self._lexicon = self.env.lexicon()
        return self._lexicon

    ##  The number of units.

    def n_translation_units (self):
        self.require_load()
        return self._ntunits

    ##  Accesses the text and returns the <i>i</i>-th translation (a string).
    #   Needed when constructing concordance.

    def block_translation (self, i):
        self.require_load()
        trans = self.text.trans
        return trans[i] if trans else ''

    ##  Other Files that may get modified when modifying this one.

    def requires (self):
        yield self.lexicon()

    ##  Read contents from an open file.
    #
    #   Apart from member nextid,
    #   The contents are stored in private members.  There is a list
    #   of blocks, a map from permanent ID to block, and a variable tracking
    #   the number of translation units processed.
    #   In an audio transcript, the translation units do not necessarily align
    #   with the token blocks; rather their boundaries are marked by \\T
    #   tokens.  This is the count of translation units.  One obtains the
    #   translation units by creating a TranslationUnits object.

    def __read__ (self, f):
        lexicon = self.lexicon()
        self.nextid = 0
        self._by_id = {}
        self._ntunits = 0
        self._blocks = []
        textid = self.text.id()
        maxid = -1
        segs = self._blocks
        seg = None
        at_eot = True

        for line in f:
            line = line.rstrip('\r\n')
            fields = line.split('\t')
            nf = len(fields)

            # begin block
            if nf == 1:
                id = int(fields[0])
                if id > maxid: maxid = id
                seg = TokenBlock(self, (textid, id), len(segs))
                seg._tokens = []
                segs.append(seg)
                self._by_id[id] = seg

            # nxid
            elif nf == 2:
                if fields[0] != 'nxid':
                    raise Exception("Expecting 'nxid'")
                self.nextid = int(fields[1])
            else:

                # non-lexical
                if nf == 3:
                    (form, lpunc, rpunc) = fields
                    sense = None
                    lexent = None
                # lexical
                elif nf == 4:
                    (form, sense, lpunc, rpunc) = fields
                    sense = int(sense)
                    lexent = lexicon[form,sense]
                else:
                    raise Exception('Bad line')
                if seg is None:
                    raise Exception('Missing start of seg (ID) line')
                if form == '\\T':
                    at_eot = True
                elif at_eot:
                    at_eot = False
                    self._ntunits += 1
                seg._tokens.append(Token(form, sense, lpunc, rpunc, lexent))

        assert self.nextid > maxid

    ##  Write the contents to an open file.

    def __write__ (self, f):
        self._ntunits = 0
        at_eot = True
        for seg in self._blocks:
            f.write(str(seg.id()))
            f.write('\n')
            for token in seg:
                f.write(token._form)
                if token._sense is not None:
                    f.write('\t')
                    f.write(str(token._sense))
                f.write('\t')
                f.write(token._lpunc)
                f.write('\t')
                f.write(token._rpunc)
                f.write('\n')
                if token._form == '\\T':
                    at_eot = True
                elif at_eot:
                    at_eot = False
                    self._ntunits += 1
        f.write('nxid\t')
        f.write(str(self.nextid))
        f.write('\n')

    #--  Modification  -------------------------------------
    #
    # Calls TokenBlock methods: __init__, set_contents, delete_contents

    def _make_block (self, index, s=None):
        textid = self.text.id()
        segid = self.nextid
        self.nextid += 1
        seg = TokenBlock(self, (textid, segid), index)
        if s is not None:
            seg.set_contents(s)
        self._by_id[segid] = seg
        return seg

    ##  Allocate a new unit.

    def allocate (self):
        with writer(self):
            self.modified()
            segs = self._blocks
            seg = self._make_block(len(segs))
            segs.append(seg)
            return seg

    ##  Append a new TokenBlock with contents <i>s</i>.
    #   The argument <i>s</i> is a string to be tokenized.  New references are
    #   stored in the lexicon.

    def append (self, s):
        with writer(self):
            self.modified()
            segs = self._blocks
            seg = self._make_block(len(segs), s)
            segs.append(seg)
            return seg

    ##  Insert a new TokenBlock with contents <i>s</i> at index <i>i</i>, replacing
    #   the TokenBlock previously at that index.'''

    def insert (self, i, s):
        with writer(self):
            self.modified()
            segs = self._blocks
            seg = self._make_block(i, s)
            segs[i:i] = [seg]
            for j in range(i+1, len(segs)): segs[j]._index = j

    ##  Replace the contents of the <i>i</i>-th segment by
    #   tokenizing string <i>s</i>.  Old references are deleted, new references are inserted.
    #   One may also do <code>f[<i>i</i>].set_contents(<i>s</i>)</code> to change the contents of an
    #   existing block.

    def __setitem__ (self, i, s):
        with writer(self):
            self.modified()
            segs = self._blocks
            # updates the refs to the segment
            segs[i].set_contents(s)

    ##  Replace the j-th token of the i-th unit.

    def set_token (self, i, j, s):
        with writer(self):
            self.modified()
            self._blocks[i].set_token(j, s)

    ##  Delete the <i>i</i>-th TokenBlock.  References are deleted.

    def __delitem__ (self, i):
        with writer(self):
            self.modified()
            segs = self._blocks
            seg = segs[i]
            seg.delete_contents()
            del segs[i]
            del self._by_id[seg.id()]
            for j in range(i, len(segs)): segs[j]._index = j

    ##  The new length <i>n</i> must be greater
    #   or equal to the current length.  New empty blocks are inserted to make
    #   the length be <i>n</i>.

    def set_length (self, n):
        with writer(self):
            blocks = self._blocks
            if n < len(blocks): raise Exception('Cannot shorten')
            elif n > len(blocks):
                self.modified()
                while len(blocks) < n:
                    blocks.append(self._make_block(len(blocks), ''))

    #--  Deletion notification  --------------------------------

    ##  A callback, notifying this text that it is being deleted.

    def deleted (self):
        File.deleted(self)
        with writer(self):
            # don't bother calling modified - the file is being deleted!
            for block in self.blocks():
                block.delete_contents()


#--  TranslationUnits  ---------------------------------------------------------

##  Deprecated.  A TranslationUnits object provides a view of a token file in
#   which the tokens are reapportioned into TokenBlocks separated by
#   \\T tokens.  The blocks are temporary blocks.
#
#   A TokenFile behaves like a list of TokenBlocks.
#
#  Alternatively, translation units are blocks formed by splitting
#  the original blocks at \\T tokens.
#
#  We need to be able to go from a translation unit back to the original
#  transcript fragments.  To do that, we add member _origblocks =
#  (origblockindex of first token, origblockindex of last token)

class TranslationUnits (object):

    ##  Constructor.

    def __init__ (self, tokfile):
        self._tokfile = tokfile
        # Cheap start-up; blocks are created on demand
        self._blocks = None

    ##  The units.

    def blocks (self):
        if self._blocks is None:
            self._blocks = tuple(self._iter_translation_units())
        return self._blocks

    def _iter_translation_units (self):
        nblocks = 0
        tokens = []
        i0 = None
        i = -1
        for block in self._tokfile.blocks():
            i += 1
            for token in block:
                if i0 is None: i0 = i
                if token._form == '\\T':
                    yield self._make_block(nblocks, i0, i, tokens)
                    i0 = None
                    nblocks += 1
                    tokens = []
                else:
                    tokens.append(token)
        if tokens:
            if i0 is None: i0 = i
            yield self._make_block(nblocks, i0, i, tokens)

    def _make_block (self, index, i0, i, tokens):
        block = TokenBlock(self, None, index)
        block._tokens = tokens
        block._orig = (i0,i+1)
        return block

    ##  Return the <i>i</i>-th block.

    def __getitem__ (self, i):
        return self.blocks()[i]

    ##  The number of blocks.

    def __len__ (self):
        return self.blocks().__len__()

    ##  An iteration over the blocks.

    def __iter__ (self):
        return self.blocks().__iter__()

    ##  The romanization, from the token file.

    def romanization (self):
        return self._tokfile.romanization()

    ##  Whether the action is permitted.

    def permitted (self, action, user=None):
        if action == 'write': return False
        else: return self._tokfile.permitted(action, user)


#--  TransTokenFile  -----------------------------------------------------------

##  The plaintext units derived from a transcription.
#   The transcription contains a TokenFile consisting of "snippets,"
#   and an array of flags indicating which snippets start new translation units.
#   A unit in the TransTokenFile corresponds to a slice of the original,
#   starting with an initial snippet and continuing with subsequent non-initial
#   snippets.
#   The units it contains are "temporary," meaning that they do not have PARIDs.

class TransTokenFile (object):

    ##  Constructor.

    def __init__ (self, trans):
        self._transcription = trans
        self._by_id = None
        # Cheap start-up; blocks are created on demand
        self._blocks = None

        ##  The text, which is the parent of the transcription.
        self.text = trans.parent()

    ##  Return the ID of the text that contains the transcription.

    def textid (self):
        return self.text.id()

    ##  The underlying transcription.

    def transcription (self):
        return self._transcription

    ##  The translation of the i-th paragraph.

    def block_translation (self, i):
        trans = self.text.trans
        return trans[i] if trans else ''

    ##  The units.

    def blocks (self):
        if self._blocks is None:
            self._blocks = tuple(self._iter_blocks())
        return self._blocks

    def _iter_blocks (self):
        tokfile = self._transcription.transcript
        oblocks = tokfile.blocks()
        paras = self._transcription.paras
        tokens = []
        index = 0
        b0 = 0
        for b1 in range(len(oblocks)):
            if b1 > b0 and paras[b1] == 'S':
                yield self._make_block(index, b0, b1, tokens)
                index += 1
                b0 = b1
                tokens = []
            tokens.extend(oblocks[b1])
        b1 = len(oblocks)
        if b1 > b0:
            yield self._make_block(index, b0, b1, tokens)

    def _make_block (self, index, b0, b1, tokens):
        block = TokenBlock(self, None, index)
        block._tokens = tokens
        block._orig = (b0,b1)
        return block

    def _make_index (self):
        tab = {}
        oblocks = self._transcription.transcript.blocks()
        for block in self.blocks():
            (b0,b1) = block._orig
            for b in range(b0, b1):
                sn = oblocks[b].id()
                if sn in tab: raise Exception('Duplicate sequence numbers!')
                tab[sn] = block
        return tab

    ##  Fetch a unit by its permanent unit number.

    def by_id (self, sn):
        if self._by_id is None:
            self._by_id = self._make_index()
        return self._by_id[sn]

    ##  Return the <i>i</i>-th block.

    def __getitem__ (self, i):
        return self.blocks()[i]

    ##  The number of blocks.

    def __len__ (self):
        return self.blocks().__len__()

    ##  An iteration over the blocks.

    def __iter__ (self):
        return self.blocks().__iter__()

    ##  The romanization, from the token file.

    def romanization (self):
        return self._transcription.romanization()

    ##  Use the transcription's environment rather than my own.

    def require_rom (self, name): return self._transcription.env.require_rom(name)

    ##  Use the transcription's permissions, rather than those of my text.

    def permitted (self, action, user=None):
        if action == 'write': return False
        else: return self._transcription.permitted(action, user)
