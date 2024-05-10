
import re
from io import StringIO
from os.path import expanduser, exists


#--  BaseFile  -----------------------------------------------------------------

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

    def write (self, s):
        self.__call__(s)

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
    '''
    A file format defines *elements* of a certain sort.
    '''
    def __init__ (self, read, render):
        self.read = read
        self.render = render

    def __call__ (self, filename=None, encoding='utf8', binary=False, contents=None):
        '''
        Apply to *f*, which is an instance of ``BaseFile``.  The return
        value is a ``FormattedFile``.
        '''
        return FormattedFile(self, _file1(filename, encoding, binary, contents))


class FormattedFile (BaseFile):
    '''
    A specialization of ``BaseFile`` that is produced by applying a
    ``Format`` to a file.  It contains a base file and a
    format.  Iterating over it applies the format's ``read`` function
    to the base file.  Storing *contents* to it applies the format's
    ``render`` function to the *contents* and then stores the resulting lines
    in the base file.
    '''

    def __init__ (self, fmt, f):
        BaseFile.__init__(self)
        self._format = fmt
        self._file = f

    def format (self):
        '''
        Returns the Format.
        '''
        return self._format

    def base (self):
        '''
        Returns the BaseFile.
        '''
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
    lst = list(ilines_to_nested_list(stream, 0))
    if lst:
        yield lst

def ilines_to_nested_list (ilines, indent):
    for (ind, line) in ilines:
        if ind < indent:
            ilines.pushback((ind, line))
            break
        elif ind == indent:
            yield line
        else:
            ilines.pushback((ind, line))
            lst = list(ilines_to_nested_list(ilines, ind))
            if lst:
                yield lst
        
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
