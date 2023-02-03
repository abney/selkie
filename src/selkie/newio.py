
import re
from collections import namedtuple
from os.path import exists


def single (x):
    it = iter(x)
    first = next(it)
    try:
        next(it)
        raise Exception('Multiple items in iterator')
    except StopIteration:
        return first


#--  File  ---------------------------------------------------------------------
#
#  A stream is just an iterator.
#
#  A source is just a stream.
#
#  A sink is a function that accepts a stream as input and consumes it.
#
#  A filter is a function that takes a stream as input and returns a stream.


def File (filename=None, encoding='utf8', binary=False, contents=None, format=None):
    f = _file1(filename, encoding, binary, contents)
    if format is not None:
        return FormattedFile(format, f)
    else:
        return f

def _file1 (filename, encoding, binary, contents):
    if not (filename is None or contents is None):
        raise Exception('Cannot specify both filename and contents')

    if filename is None:
        if contents is None:
            raise Exception('Must specify either filename or contents')
        if binary:
            raise Exception('Not implemented')
        return FileFromString(contents)

    elif filename == '-':
        return StdStream()

    elif isinstance(filename, str):
        if re.match(r'[A-Za-z]+:', filename):
            return URLStream(filename)

        elif binary:
            return BinaryFile(filename)

        else:
            return RegularFile(filename, encoding)

    elif isinstance(filename, BaseFile):
        return filename

    else:
        raise Exception(f'Cannot coerce to file: {filename}')


# Anything that File() should pass through unchanged

class BaseFile (object):

    def __iter__ (self): raise NotImplementedError
    def store (self, contents): raise NotImplementedError

    def load (self):
        return list(iter(self))

    def save (self, contents):
        self.store(contents)


class SingletonFile (object):

    def load (self): raise NotImplementedError
    def save (self, contents): raise NotImplementedError

    def __iter__ (self):
        yield self.load()

    def store (self, contents):
        self.save(contents)


class FormattedFile (BaseFile):

    def __init__ (self, fmt, f):
        BaseFile.__init__(self)
        self._format = fmt
        self._file = f

    def __iter__ (self):
        return self._format.read(self._file)

    def store (self, contents):
        self._file.store(self._format.render(contents))


class LoadableFile (SingletonFile):

    def __init__ (self, fmt, f):
        SingletonFile.__init__(self)
        self._format = fmt
        self._file = f

    def load (self):
        return self._format.read(self._file)

    def save (self, contents):
        self._file.store(self._format.render(contents))


class FileFromString (BaseFile):

    def __init__ (self, contents=''):
        BaseFile.__init__(self)
        self._contents = contents

    def __iter__ (self):
        with StringIO(self._contents) as f:
            for line in f:
                yield line

    def store (self, lines):
        with StringIO() as f:
            for line in lines:
                f.write(line)
            self._contents = f.getvalue()
            return self._contents

    def __str__ (self):
        return self._contents


class StdStream (BaseFile):

    def __iter__ (self):
        for line in sys.stdin:
            yield line

    def store (self, lines):
        for line in lines:
            sys.stdout.write(line)


class URLStream (BaseFile):

    def __init__ (self, url):
        BaseFile.__init__(self)
        self.url = url

    def __iter__ (self):
        bstream = urllib.request.urlopen(self.url, 'r')
        reader = codecs.getreader(encoding)
        with reader(bstream) as f:
            for line in f:
                yield line

    def store (self):
        raise Exception('Cannot write to URLs')


class RegularFile (BaseFile):

    def __init__ (self, fn, encoding):
        BaseFile.__init__(self)
        self.filename = fn
        self.encoding = encoding

    def __iter__ (self):
        if exists(self.filename):
            with open(self.filename, 'r', encoding=self.encoding) as f:
                for line in f:
                    yield line

    def store (self, lines):
        with open(self.filename, 'w', encoding=self.encoding) as f:
            for line in lines:
                f.write(line)


class BinaryFile (BaseFile):

    def __init__ (self, fn):
        BaseFile.__init__(self)
        self.filename = fn

    def __iter__ (self):
        with open(fn, 'rb') as f:
            for line in f:
                yield line

    def store (self, lines):
        with open(fn, 'wb') as f:
            for line in lines:
                f.write(line)


#--  Buffered  -----------------------------------------------------------------

class Buffered (object):

    def __init__ (self, stream):
        self.stream = iter(stream)
        self.buffer = []

    def __iter__ (self):
        return self
    
    def __next__ (self):
        if self.buffer:
            return self.buffer.pop()
        else:
            return next(self.stream)

    def pushback (self, item):
        self.buffer.append(item)

    def peek (self):
        try:
            item = self.__next__()
            self.pushback(item)
            return item
        except StopIteration:
            return StopIteration


#--  FileFormat  ---------------------------------------------------------------

class FileFormat (object):

    formatted_file_class = FormattedFile

    def __init__ (self, read, render):
        self.read = read
        self.render = render

    def __call__ (self, filename=None, encoding='utf8', binary=False, contents=None):
        return self.formatted_file_class(self, _file1(filename, encoding, binary, contents))


class LoadableFormat (FileFormat):

    formatted_file_class = LoadableFile
        


Lines = FileFormat(lambda x: x, lambda x: x)


#--  Records  ------------------------------------------------------------------

def lines_to_records (lines):
    for line in lines:
        line = line.rstrip('\r\n')
        if line:
            yield line.split('\t')
        else:
            yield []

def records_to_lines (recs):
    for rec in recs:
        yield '\t'.join(rec) + '\r\n'

Tabular = Records = FileFormat(lines_to_records, records_to_lines)


#--  Blocks  -------------------------------------------------------------------

def lines_to_blocks (lines):
    return _records_to_blocks(lines_to_records(lines))

def _records_to_blocks (records):
    block = []
    for r in records:
        if r:
           block.append(r)
        elif block:
            yield block
            block = []
    if block:
        yield block

def blocks_to_lines (blocks):
    first = True
    for block in blocks:
        if first:
            first = False
        else:
            yield '\n'
        for record in block:
            yield '\t'.join(record) + '\n'
    
Blocks = FileFormat(lines_to_blocks, blocks_to_lines)


#--  Dicts  --------------------------------------------------------------------

def lines_to_dicts (lines):
    for block in lines_to_blocks(lines):
        yield dict(block)

def dicts_to_lines (dicts):
    return blocks_to_lines(_dicts_to_blocks(dicts))

def _dicts_to_blocks (dicts):
    for d in dicts:
        yield list(d.items())

Dicts = FileFormat(lines_to_dicts, dicts_to_lines)


#--  ILines  -------------------------------------------------------------------

def lines_to_ilines (lines):
    for line in lines:
        line = line.rstrip('\r\n')
        i = 0
        while i < len(line) and line[i].isspace():
            i += 1
        yield (i, line[i:])

def ilines_to_lines (ilines):
    for (ind, line) in ilines:
        yield '  ' * ind + line + '\n'

ILines = FileFormat(lines_to_ilines, ilines_to_lines)


#--  Nested  -------------------------------------------------------------------

def lines_to_nested (lines):
    stream = Buffered(lines_to_ilines(lines))
    return _ilines_to_nested(stream, 0)

def _ilines_to_nested (ilines, cur_ind):
    for (ind, line) in ilines:
        if ind < cur_ind:
            ilines.pushback((ind, line))
            break
        elif ind == cur_ind:
            yield line
        else:
            ilines.pushback((ind, line))
            yield list(_ilines_to_nested(ilines, ind))
        
def nested_to_lines (lst):
    return ilines_to_lines(_nested_to_ilines(lst, 0))

def _nested_to_ilines (lines, ind):
    for line in lines:
        if isinstance(line, str):
            yield (ind, line)
        else:
            for iline in _nested_to_ilines(line, ind + 1):
                yield iline

Nested = FileFormat(lines_to_nested, nested_to_lines)


#--  NestedDict  ---------------------------------------------------------------

def first_space (line):
    for (i, c) in enumerate(line):
        if c.isspace():
            return i
    return -1

def lines_to_nested_dict (lines, recurse=True):
    return dict(_nested_to_items(lines_to_nested(lines), recurse))

def _nested_to_items (lines, recurse):
    key = None
    for line in lines:
        if isinstance(line, str):
            if key is not None:
                yield (key, {} if recurse else [])
            i = first_space(line)
            if i < 0:
                key = line
            else:
                key = line[:i]
                value = line[i+1:]
                yield (key, value)
                key = None
        else:
            if key is None:
                raise Exception('Unexpected indented block')
            value = line
            if recurse:
                value = dict(_nested_to_items(value, recurse))
            yield (key, value)
            key = None
    if key is not None:
        yield (key, {} if recurse else [])

def nested_dict_to_lines (tab, recurse=True):
    return nested_to_lines(_items_to_nested(tab.items(), recurse))

def _items_to_nested (items, recurse):
    for (key, value) in items:
        if isinstance(value, str):
            yield key + '\t' + value
        else:
            yield key
            if recurse:
                value = _items_to_nested(value.items(), recurse)
            yield value

NestedDict = LoadableFormat(lines_to_nested_dict, nested_dict_to_lines)


#--  Tokens  -------------------------------------------------------------------

# class Tokenizer (object):
# 
#     ##  Constructor.  Filename only for printing error messages; need not be genuine filename.
# 
#     def __init__ (self, filename, lines, syntax=DefaultSyntax):
# 
#         ##  A Syntax instance.
#         self.syntax = syntax
# 
#         ##  Stack, for (possibly nested) temporary syntax changes.
#         self.stack = []
# 
#         ##  Filename string; set even for streams not associated with files.
#         self.filename = filename
# 
#         ##  The lines of the file.
#         self.lines = lines
# 
#         ##  The current line.
#         self.line = None
# 
#         ##  Current line number.
#         self.linecount = 1
# 
#         ##  Current character offset on the line.
#         self.offset = 0
# 
#         ##  Previous linecount.
#         self.old_linecount = 1
# 
#         ##  Previous offset.
#         self.old_offset = 0
# 
#         self.__token = None
# 
#         if self.lines: self.line = self.lines[0]
#         else: self.line = ''
# 
#     ##  Returns self.
# 
#     def __iter__ (self):
#         return self
# 
#     ##  Whether we are at EOF.
# 
#     def __bool__ (self):
#         return self.token().type != 'eof'
# 
#     def __readline (self):
#         if self.linecount < len(self.lines):
#             self.line = self.lines[self.linecount]
#             self.linecount += 1
#         elif self.linecount == len(self.lines):
#             self.line = ''
#             self.linecount += 1
#         else:
#             raise Exception('Readline after EOF')
#         self.offset = 0
# 
#     def __at_eof (self):
#         return self.linecount > len(self.lines)
# 
#     def __empty_line (self):
#         for c in self.line:
#             if c in self.syntax.comments: return True
#             elif not c.isspace(): return False
#         return True
# 
#     def __is_special (self, c):
#         if self.syntax.special is True:
#             return not (c.isalnum() or c == '_')
#         else:
#             return c in self.syntax.special
# 
#     ##  Advance, if necessary, then return the current token.
# 
#     def token (self):
#         if self.__token is None: self.__advance()
#         return self.__token
# 
#     def __skip_eol (self):
#         if self.offset >= len(self.line):
#             if self.syntax.eol and not self.__empty_line():
#                 self.__set_token('\n', self.offset, string='\n')
#                 self.__readline()
#             else:
#                 while self.offset >= len(self.line):
#                     if self.__at_eof():
#                         self.__set_token('eof', self.offset)
#                         break
#                     self.__readline()
# 
#     def __advance (self):
#         self.old_linecount = self.linecount
#         self.old_offset = self.offset
#         self.__token = None
#         try:
#             while self.__token is None:
#                 self.__skip_eol()
#                 if self.__token is not None: return
#                 c = self.line[self.offset]
# 
#                 if c in self.syntax.multi_start and self.__scan_multi(): pass
#                 elif c in self.syntax.comments: self.offset = len(self.line)
#                 elif c == "'" or c == '"': self.__scan_quoted()
#                 elif c.isspace(): self.offset += 1
#                 elif self.__is_special(c): self.__scan_special()
#                 elif self.syntax.digits and self.__is_digit(c): self.__scan_digit()
#                 else: self.__scan_word()
# 
#         except StopIteration:
#             raise Exception('[%s line %d offset %d] Unexpected eof' % \
#                 (self.filename, self.linecount, self.offset))
# 
#     def __retreat (self):
#         self.__token = None
#         self.linecount = self.old_linecount
#         self.offset = self.old_offset
#         if self.linecount > 0:
#             self.line = self.lines[self.linecount-1]
#         else:
#             self.line = None
# 
#     def __set_token (self, type, start, line=None, string=None, quotes=None):
#         if line is None:
#             line = self.linecount
#         if string is None:
#             string = self.line[start:self.offset]
#         self.__token = Token(string)
#         self.__token.type = type
#         self.__token.filename = self.filename
#         self.__token.line = line
#         self.__token.offset = start
#         self.__token.quotes = quotes
# 
#     def __is_digit (self, c):
#         if c.isdigit(): return True
#         i = self.offset + 1
#         return c == '-' and i < len(self.line) and self.line[i].isdigit()
# 
#     def __scan_digit (self):
#         start = self.offset
#         if self.line[self.offset] == '-': self.offset += 1
#         while self.offset < len(self.line) and self.line[self.offset].isdigit():
#             self.offset += 1
#         self.__set_token('digit', start)
# 
#     def __scan_word (self):
#         start = self.offset
#         while self.offset < len(self.line):
#             c = self.line[self.offset]
#             if c.isspace() or self.__is_special(c): break
#             self.offset += 1
#         self.__set_token('word', start)
# 
#     def __error (self, start, msg):
#         raise Exception('[%s line %d char %d] %s' % \
#             (self.filename, self.linecount, start, msg))
# 
#     def __scan_quoted (self):
#         delim = self.line[self.offset]
#         self.offset += 1
#         start = self.offset
#         restart = self.offset
#         frags = []
#         while True:
#             while self.offset >= len(self.line):
#                 if self.syntax.mlstrings:
#                     if restart < len(self.line):
#                         frags.append(self.line[restart:])
#                     frags.append('\n')
#                     self.__readline()
#                     restart = self.offset
#                     if self.__at_eof():
#                         self.__error(start, 'Unterminated string at EOF')
#                 else:
#                     self.__error(start, 'End of line in string')
#             c = self.line[self.offset]
#             if c == delim:
#                 frags.append(self.line[restart:self.offset])
#                 self.offset += 1
#                 break
#             elif c == '\\' and self.syntax.backslash:
#                 frags.append(self.line[restart:self.offset])
#                 frags.append(self.__scan_escape_sequence())
#                 restart = self.offset
#             else:
#                 self.offset += 1
#         self.__set_token(self.syntax.stringtype, start, self.linecount, ''.join(frags), delim)
# 
#     def __scan_escape_sequence (self):
#         # self.line[self.offset] is backslash
#         self.offset += 1
#         if self.offset >= len(self.line): self.__error('Bad escape sequence')
#         c = self.line[self.offset]
#         self.offset += 1
#         if c == '\\' or c == '"' or c == "'": return c
#         elif c == 'a': return '\a'
#         elif c == 'b': return '\b'
#         elif c == 'f': return '\f'
#         elif c == 'n': return '\n'
#         elif c == 'r': return '\r'
#         elif c == 't': return '\t'
#         elif c == 'u':
#             i = self.offset
#             self.offset += 4
#             if self.offset > len(self.line): self.__error('Bad escape sequence')
#             return chr(int(self.line[i:self.offset], 16))
#         elif c == 'U':
#             self.__error('\\U escapes not implemented')
#         elif c == 'v': return '\v'
#         elif '0' <= c <= '7':
#             i = self.offset
#             self.offset += 1
#             n = 1
#             while n < 3 and self.offset < len(self.line) and \
#                     '0' <= self.line[self.offset] <= '7':
#                 self.offset += 1
#                 n += 1
#             return chr(int(self.line[i:self.offset], 8))
#         elif c == 'x':
#             i = self.offset
#             self.offset += 1
#             if self.offset < len(self.line) and \
#                     ('0' <= self.line[self.offset] <= '9' or \
#                      'a' <= self.line[self.offset] <= 'f' or \
#                      'A' <= self.line[self.offset] <= 'F'):
#                 self.offset += 1
#             d = int(self.line[i:self.offset], 16)
#             if d < 0x100: return chr(d)
#             else: return chr(d)
# 
#     def __scan_special (self):
#         start = self.offset
#         self.offset += 1
#         self.__set_token(self.line[start], start)
# 
#     def __looking_at (self, word):
#         for i in range(len(word)):
#             t = self.offset + i
#             if t >= len(self.line): return False
#             if self.line[t] != word[i]: return False
#         return True
# 
#     def __scan_multi (self):
#         for word in self.syntax.multi:
#             if self.__looking_at(word):
#                 start = self.offset
#                 self.offset += len(word)
#                 self.__set_token(self.line[start:self.offset], start)
#                 return True
# 
#     ##  Whether the next token is something other than EOF.
#     #   If type or string is provided, the value indicates whether the next
#     #   token has the given type and/or string.
# 
#     def has_next (self, type=None, string=None):
#         if string:
#             if type: raise Exception("Provide only one argument")
#             return self.token() == string
#         elif type:
#             return self.token().hastype(type)
#         else:
#             return self.token().type != 'eof'
# 
#     ##  Iterator method.
# 
#     def __next__ (self):
#         token = self.token()
#         if token.type == 'eof': raise StopIteration
#         self.__token = None
#         self.old_linecount = self.linecount
#         self.old_offset = self.offset
#         return token
# 
#     ##  If the next token matches the given type and/or string, return it
#     #   and advance.  Otherwise, return None.
# 
#     def accept (self, type=None, string=None):
#         token = self.token()
#         if type and not token.hastype(type):
#             return None
#         if string and not (token == string):
#             return None
#         return next(self)
# 
#     ##  If the next token has the given type and/or string, return it
#     #   and advance.  Otherwise, signal an error.  Returns None at EOF.
# 
#     def require (self, type=None, string=None):
#         token = self.token()
#         if type and not token.hastype(type):
#             token.error('Expecting ' + repr(type))
#         if string and not (token == string):
#             token.error('Expecting ' + repr(string))
#         if type == 'eof': return None
#         else: return next(self)
# 
#     ##  Signal an error, indicating filename and line number.
# 
#     def error (self, msg=None):
#         token = self.token()
#         token.error(msg)
# 
#     ##  Print a warning, showing filename and line number.
# 
#     def warn (self, msg=None):
#         token = self.token()
#         token.warn(msg)
# 
#     ##  Push the current syntax on the stack and switch to the given syntax.
# 
#     def push_syntax (self, syntax):
#         self.stack.append(self.syntax)
#         self.syntax = syntax
#         self.__retreat()
# 
#     ##  Restore the previous syntax from the stack.
# 
#     def pop_syntax (self):
#         if not self.stack: raise Exception('Empty stack')
#         self.syntax = self.stack.pop()
#         self.__retreat()
