
import re, urllib, sys
from io import StringIO
from collections import namedtuple
from os.path import exists, expanduser
from .object import MapProxy, ListProxy


def single (x):
    it = iter(x)
    first = next(it)
    try:
        next(it)
        raise Exception('Multiple items in iterator')
    except StopIteration:
        return first


# Anything that File() should pass through unchanged

class BaseFile (object):

    def __iter__ (self): raise NotImplementedError
    def store (self, contents, mode='w'): raise NotImplementedError

    def append (self, contents):
        self.store(contents, 'a')

    def writer (self):
        return Writer(self)

    def __str__ (self):
        bol = True
        with StringIO() as f:
            for elt in self:
                if not bol:
                    f.write('\n')
                    bol = True
                s = str(elt)
                f.write(s)
                if s and s[-1] != '\n':
                    bol = False
            return f.getvalue()


# This collects all items into a list, then passes the entire list
# the File's store() method.
#
# The alternative would be to run store() in a separate thread, but
# that would reduce space needs at the cost of increased time overhead.

class Writer (object):

    def __init__ (self, f, mode='w'):
        self._file = f
        self._mode = mode
        self._contents = []

    def __enter__ (self):
        return self

    def __call__ (self, elt):
        self._contents.append(elt)

    def __exit__ (self, t, v, tb):
        self._file.store(self._contents, self._mode)


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
        raise Exception(f'Cannot coerce to file: {repr(filename)}')


class FileFromString (BaseFile):

    def __init__ (self, contents=''):
        BaseFile.__init__(self)
        self._contents = contents

    def __iter__ (self):
        with StringIO(self._contents) as f:
            for line in f:
                yield line

    def store (self, lines, mode='w'):
        with StringIO() as f:
            if mode == 'a':
                f.write(self._contents)
            for line in lines:
                f.write(line)
            self._contents = f.getvalue()

    def __str__ (self):
        return self._contents


class StdStream (BaseFile):

    def __iter__ (self):
        for line in sys.stdin:
            yield line

    def store (self, lines, mode='w'):
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

    def store (self, lines, mode='w'):
        raise Exception('Cannot write to URLs')
    

class RegularFile (BaseFile):

    def __init__ (self, fn, encoding):
        BaseFile.__init__(self)
        self.filename = expanduser(fn)
        self.encoding = encoding

    def __iter__ (self):
        if exists(self.filename):
            with open(self.filename, 'r', encoding=self.encoding) as f:
                for line in f:
                    yield line

    def store (self, lines, mode='w'):
        with open(self.filename, mode, encoding=self.encoding) as f:
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

    def store (self, lines, mode='w'):
        with open(fn, mode + 'b') as f:
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


#--  Format  ---------------------------------------------------------------

class Format (object):

    def __init__ (self, read, render):
        self.read = read
        self.render = render

    def __call__ (self, filename=None, encoding='utf8', binary=False, contents=None):
        return FormattedFile(self, _file1(filename, encoding, binary, contents))


class FormattedFile (BaseFile):

    def __init__ (self, fmt, f):
        BaseFile.__init__(self)
        self._format = fmt
        self._file = f

    def format (self):
        return self._format

    def base (self):
        return self._file

    def __iter__ (self):
        return self._format.read(iter(self._file))

    def store (self, contents, mode='w'):
        self._file.store(self._format.render(contents), mode)


# class LoadableFormat (Format):
# 
#     pass
        


Lines = Format(lambda x: x, lambda x: x)


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

Tabular = Records = Format(lines_to_records, records_to_lines)


#--  Simples  ------------------------------------------------------------------
#
# Works with any object that consists of a mix of strings, pairs whose first
# element is a string, list-like objects, and dict-like objects.  A dict-like
# object is anything that has an items() method, and a list-like object is
# anything that has an __iter__() method but is not dict-like.
#
# When loading, the original objects are not reconstructed.  The value consists
# of strings, pairs, lists and dicts.

def lines_to_simples (lines):
    return _lines_to_simples(iter(lines))

def _lines_to_simples (lines, terminator=None):
    try:
        while True:
            yield lines_to_simple(lines, terminator)
    except StopIteration:
        pass

def lines_to_simple (lines, terminator=None):
    line = next(lines)
    j = -1 if line.endswith('\n') else len(line)
    if terminator and line == terminator:
        raise StopIteration
    elif line.startswith('|'):
        return line[1:j]
    elif line.startswith(':'):
        key = line[1:j]
        value = lines_to_simple(lines)
        return (key, value)
    elif line.startswith('{'):
        return _make_dict(_lines_to_simples(lines, '}\n'))
    elif line.startswith('['):
        return list(_lines_to_simples(lines, ']\n'))
    else:
        raise Exception(f'Unexpected line: {repr(line)}')

def _make_dict (items):
    d = {}
    for item in items:
        if not (isinstance(item, tuple) and len(item) == 2):
            raise Exception(f'Expecting pairs: {repr(item)}')
        (k,v) = item
        d[k] = v
    return d
        
def simples_to_lines (objs):
    for obj in objs:
        for line in simple_to_lines(obj):
            yield line

def simple_to_lines (obj):
    if isinstance(obj, str):
        yield '|' + obj + '\n'
    elif isinstance(obj, dict):
        yield '{\n'
        for (k,v) in obj.items():
            yield ':' + str(k) + '\n'
            for line in simple_to_lines(v):
                yield line
        yield '}\n'
    elif isinstance(obj, tuple) and len(obj) == 2 and isinstance(obj[0], str):
        yield ':' + obj[0] + '\n'
        for line in simple_to_lines(obj[1]):
            yield line
    elif isinstance(obj, list):
        yield '[\n'
        for elt in obj:
            for line in simple_to_lines(elt):
                yield line
        yield ']\n'
    else:
        raise Exception(f'Not a simple: {repr(obj)}')
            
Simples = Format(lines_to_simples, simples_to_lines)


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
    
Blocks = Format(lines_to_blocks, blocks_to_lines)


#--  Dicts  --------------------------------------------------------------------

def lines_to_dicts (lines):
    d = {}
    for line in lines:
        line = line.rstrip('\r\n')
        if line:
            i = _first_space(line)
            if i is None:
                raise Exception(f'Missing value: {repr(line)}')
            key = line[:i]
            value = line[i+1:]
            if key in d:
                raise Exception(f'Duplicate key: {key}')
            d[key] = value
        else:
            yield d
            d = {}
    if d:
        yield d

def _first_space (line):
    for i in range(len(line)):
        if line[i].isspace():
            return i

def dicts_to_lines (dicts):
    first = True
    for d in dicts:
        if first: first = False
        else: yield '\n'
        for (k,v) in d.items():
            if not _spacefree(k):
                raise Exception(f'Bad key: {repr(key)}')
            yield k + ' ' + v
        
def _spacefree (key):
    for i in range(len(key)):
        if key[i].isspace():
            return False
    return True

Dicts = Format(lines_to_dicts, dicts_to_lines)


#--  ILines  -------------------------------------------------------------------

def lines_to_ilines (lines):
    for line in lines:
        line = line.rstrip('\r\n')
        i = 0
        while i < len(line) and line[i] == ' ':
            i += 1
        yield (i, line[i:])

def ilines_to_lines (ilines):
    for (ind, line) in ilines:
        yield '  ' * ind + line + '\n'

ILines = Format(lines_to_ilines, ilines_to_lines)


#--  NestedLists  --------------------------------------------------------------
#
# A block at indentation level i consists of a mix of lines at indentation i+1
# and subblocks at indentation i+1.
#
# The toplevel elements are the elements of the (nonexistent) block at level -1.

def lines_to_nested_lists (lines):
    stream = Buffered(lines_to_ilines(lines))
    yield ilines_to_nested_list(stream, 0)

def ilines_to_nested_list (ilines, indent):
    return list(_ilines_to_nested_list(ilines, indent))

def _ilines_to_nested_list (ilines, indent):
    for (ind, line) in ilines:
        if ind < indent:
            ilines.pushback((ind, line))
            break
        elif ind == indent:
            yield line
        else:
            ilines.pushback((ind, line))
            yield ilines_to_nested_list(ilines, ind)
        
def nested_lists_to_lines (lst):
    return ilines_to_lines(_nested_list_to_ilines(lst, 0))

def _nested_list_to_ilines (lines, ind):
    for line in lines:
        if isinstance(line, str):
            yield (ind, line)
        else:
            for iline in _nested_list_to_ilines(line, ind + 2):
                yield iline

NestedLists = Format(lines_to_nested_lists, nested_lists_to_lines)


#--  Containers  ---------------------------------------------------------------

def lines_to_containers (lines):
    return nested_lists_to_containers(lines_to_nested_lists(lines))

def nested_lists_to_containers (lists):
    for lst in lists:
        yield nested_list_to_container(list(lst))

def nested_list_to_container (lst):
    out = None
    i = 0
    while i < len(lst):
        if isinstance(lst[i], list):
            raise Exception('Embedded dict without a key')
        elif i+1 < len(lst) and isinstance(lst[i+1], list):
            out = _insert_item(lst[i], nested_list_to_container(lst[i+1]), dict, out)
            i += 2
        else:
            line = lst[i].strip()
            k = _first_space(line)
            if k is None:
                out = _insert_item(None, line, list, out)
            else:
                out = _insert_item(line[:k], line[k+1:].strip(), dict, out)
            i += 1
    return out

def _insert_item (key, value, typ, out):
    if out is None:
        out = typ()
    elif not isinstance(out, typ):
        raise Exception(f'Inconsistent with {type(out)}: {key} {value}')
    if key is None:
        out.append(value)
    elif key in out:
        raise Exception(f'Duplicate key: {key}')
    else:
        out[key] = value
    return out

def containers_to_lines (conts):
    for cont in conts:
        for line in container_to_lines(cont):
            yield line

def container_to_lines (cont):
    return ilines_to_lines(container_to_ilines(cont, 0))

def container_to_ilines (cont, indent):
    if isinstance(cont, dict):
        for (k, v) in cont.items():
            if isinstance(v, str):
                yield (indent, k + ' ' + v)
            elif isinstance(v, dict):
                yield (indent, k)
                for iline in container_to_ilines(v, indent+2):
                    yield iline
            else:
                raise Exception(f'Unexpected value type: {repr(v)}')
    elif isinstance(cont, list):
        for v in cont:
            if isinstance(v, str):
                yield (indent, v)
            else:
                raise Exception('Lists may only contain strings')


Containers = Format(lines_to_containers, containers_to_lines)

# 
# #--  NestedDict  ---------------------------------------------------------------
# 
# def first_space (line):
#     for (i, c) in enumerate(line):
#         if c.isspace():
#             return i
#     return -1
# 
# # It would be more readable if this transformed the output of lines_to_nested_items,
# # but maybe this way is more efficient
# 
# def lines_to_nested_dicts (lines):
#     yield nested_items_to_nested_dict(lines_to_nested_items(lines))
# 
# def nested_items_to_nested_dict (items):
#     if isinstance(items, str):
#         return items
#     elif isinstance(items, list):
#         d = {}
#         for (k1, v1) in nested_items_to_nested_dicts(v):
#             if k1 in d:
#                 raise Exception(f'Duplicate key: {repr(k1)}')
#             d[k1] = v1
#         return d
# 
# # Warning: if you convert multiple dicts to lines and then convert them
# # back to dicts, you will get a single dict containing all items
# 
# def nested_dicts_to_lines (dicts):
#     for d in dicts:
#         for line in nested_dict_to_lines(d):
#             yield line
# 
# def nested_dict_to_lines (d):
#     return nested_items_to_lines(nested_dict_to_nested_items(d))
# 
# def nested_dict_to_nested_items (d):
#     for (k, v) in d.items():
#         if isinstance(v, str):
#             yield (k, v)
#         elif isinstance(v, dict):
#             yield (k, list(nested_dict_to_nested_items(v)))
#         else:
#             raise Exception(f'Unexpected value type: {repr(v)}')
# 
# NestedDicts = Format(lines_to_nested_dicts, nested_dicts_to_lines)


#--  Single  -------------------------------------------------------------------

class Single (object):

    def __init__ (self, f):
        self._file = f

    def load (self):
        for elt in self._file:
            return elt

    def save (self, obj):
        self._file.store([obj])


def Simple (f):
    return Single(Simples(f))


#--  Container  ----------------------------------------------------------------

class Container (object):

    def __init__ (self, f):
        self._file = Containers(f)
        self._editing = False
        self._contents = None
        self.load()
        if self._contents is None:
            raise Exception('Implementation error: loading failed to set _contents')

    # Returns the first element without checking whether there are more

    def load (self):
        for elt in self._file:
            self._contents = elt
            break

    def save (self):
        if not self._editing:
            self._file.store([self._contents])

    def edit (self):
        return BatchEdit(self)

    def __setitem__ (self, key, value):
        self._contents[key] = value
        self.save()

    def __delitem__ (self, key):
        del self._contents[key]
        self.save()

    def __getitem__ (self, att):
        return self._contents[att]

    def append (self, value):
        self._contents.append(value)
        self.save()

    def __repr__ (self):
        return repr(self._contents)


class BatchEdit (object):

    def __init__ (self, tgt):
        self._tgt = tgt

    def __enter__ (self):
        self._tgt._editing = True
        return self

    def __exit__ (self, t, v, tb):
        self._tgt._editing = False
        if not t:
            self._tgt.save()


# 
# class Cell (object):
# 
#     def __init__ (self, array, i=0):
#         if isinstance(array, BaseFile):
#             array = Array(array)
# 
#         self._array = array
#         self._i = i
# 
#     def get (self):
#         return self._array[self._i]
# 
#     def set(self, value):
#         self._array[self._i] = value
# 
#     def save (self):
#         self._array.save()
# 
#     def __enter__ (self):
#         return self
# 
#     def __exit__ (self, t, v, tb):
#         if not t:
#             self._array.save()
# 

# class SingletonFile (object):
# 
#     def load (self): raise NotImplementedError
#     def save (self, contents): raise NotImplementedError
# 
#     def __iter__ (self):
#         yield self.load()
# 
#     def store (self, contents):
#         self.save(contents)
# 
# 
# class LoadableFile (SingletonFile):
# 
#     def __init__ (self, fmt, f):
#         SingletonFile.__init__(self)
#         self._format = fmt
#         self._file = f
# 
#     def load (self):
#         return self._format.read(self._file)
# 
#     def save (self, contents):
#         self._file.store(self._format.render(contents))


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



#--  pprint  -------------------------------------------------------------------

##  A PPrinter instance.
pprint = None


##  Indentation for a PPrinter.

class PPrintIndent (object):

    ##  Constructor.

    def __init__ (self, pprinter, n):

        ##  The pprinter.
        self.pprinter = pprinter

        ##  The number of spaces indented by.
        self.n = n

    ##  Enter.

    def __enter__ (self):
        self.pprinter._indent += self.n

    ##  Exit.

    def __exit__ (self, t, v, tb):
        self.pprinter._indent -= self.n
        

##  A color for a PPrinter.

class PPrintColor (object):

    ##  Constructor.

    def __init__ (self, pprinter, color):

        ##  The pprinter.
        self.pprinter = pprinter

        ##  The color.
        self.color = color

        ##  Saves the previous color.
        self.prevcolor = None

    def _set_color (self, color):
        self.pprinter._color = color
        sys.stdout.write(fg[color])
        sys.stdout.flush()

    ##  Enter.

    def __enter__ (self):
        self.prevcolor = self.pprinter._color or 'default'
        self._set_color(self.color)

    ##  Exit.

    def __exit__ (self, t, v, tb):
        self._set_color(self.prevcolor)


##  A pretty-printer.

class PPrinter (object):

    ##  Constructor.

    def __init__ (self, file=None):
        self._color = None
        self._indent = 0
        self._atbol = True
        self._brflag = False
        self._file = file
    
    ##  String representation.

    def __repr__ (self):
        return '<PPrinter %s>' % repr(self._file)

    ##  The protected file.

    def file (self):
        if self._file is None: return sys.stdout
        else: return self._file

    ##  Returns an indentation.  Calling this in a with-statement causes the
    #   indentation to be active within the body.

    def indent (self, n=2):
        return PPrintIndent(self, n)

    ##  Start an indentation.  One should usually do "with pp.indent()" instead.

    def start_indent (self, n=2):
        self._indent += n
    
    ##  End an indentation.

    def end_indent (self, n=2):
        self._indent -= n
        if self._indent < 0: self._indent = 0
    
    ##  Freshline.

    def br (self):
        self._brflag = True

    ##  Returns a color.  Calling this in a with-statement causes the color
    #   to be used in the body.

    def color (self, c):
        return PPrintColor(self, c)

    ##  Like print().  Handles embedded newlines correctly.

    def __call__ (self, *args, end=None, color=None):
        if color is None:
            self._call1(args, end)
        else:
            with self.color(color):
                self._call1(args, end)
                
    def _call1 (self, args, end):
        if end is None and (len(args) == 0 or not hasattr(args[-1], '__pprint__')):
            end = '\n'
        first = True
        for arg in args:
            if first: first = False
            else: self.file().write(' ')
            self._printarg(arg)
        if end:
            self._printarg(end)

    def _printarg (self, arg):
        if hasattr(arg, '__pprint__'):
            arg.__pprint__()
        else:
            self.write(str(arg))

    ##  Write a string.

    def write (self, s):
        f = self.file()
        i = 0
        n = len(s)
        while i < n:
            j = s.find('\n', i)
            if j < 0: j = n
            # it is possible that s[0] == '\n'
            if i < j:
                if self._brflag and not self._atbol:
                    f.write('\n')
                    self._atbol = True
                if self._atbol:
                    f.write(' ' * self._indent)
                f.write(s[i:j].replace('\x1b', '\\x1b'))
                self._atbol = False
            # if j < n then s[j] == '\n'
            if j < n:
                f.write('\n')
                j += 1
                self._atbol = True
            i = j
    
    ##  Emit a newline, unless the last character printed was a newline.

    def freshline (self):
        if not self._atbol:
            self.write('\n')

    ##  Print and immediately flush.

    def now (self, *args, end=''):
        self.__call__(*args, end)
        self.file().flush()
    
    ##  Flush the output.

    def flush (self):
        self.file().flush()


pprint = PPrinter()


#--  redirect  -----------------------------------------------------------------
#
# with redirect() as f:
#     pprint('foo')
#     with pprint.indent():
#         pprint('bar')
#     return str(f)
#

class redirect (object):

    def __init__ (self, filename=None, mode='w', stderr=False):
        self.filename = filename
        self.mode = mode
        self._redirect_stderr = stderr
        self._file = None
        self._old_stdout = None
        self._old_stderr = None

    def __enter__ (self):
        if self.filename is None:
            self._file = StringIO()
        else:
            self._file = open(self.filename, self.mode)
        self._file.__enter__()
        self._old_stdout = sys.stdout
        sys.stdout = self._file
        if self._redirect_stderr:
            self._old_stderr = sys.stderr
            sys.stderr = self._file
        return self

    def __str__ (self):
        if self.filename is None and self._file is not None:
            return self._file.getvalue()
        else:
            return f'redirect({self.filename}, {self.mode})'
            
    def __exit__ (self, t, v, tb):
        sys.stdout = self._old_stdout
        if self._redirect_stderr:
            sys.stderr = self._old_stderr
        return self._file.__exit__(t, v, tb)
