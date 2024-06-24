
import re
from json import loads as json_parse, dumps as json_unparse
from io import StringIO
from os import makedirs
from os.path import expanduser, exists, dirname
from collections import OrderedDict


#--  BaseFile  -----------------------------------------------------------------

# Anything that File() should pass through unchanged

class BaseFile (object):

    def __iter__ (self): raise NotImplementedError()
    def store (self, contents, mode='w'): raise NotImplementedError()
    def exists (self): raise NotImplementedError()

    def append (self, contents):
        self.store(contents, 'a')

    def writer (self):
        return _Writer(self)

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

class _Writer (object):

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

def File (filename=None, binary=False, contents=None, **kwargs):
    if not (filename is None or contents is None):
        raise Exception('Cannot specify both filename and contents')

    if filename is None:
        if contents is None:
            raise Exception('Must specify either filename or contents')
        if binary:
            raise Exception('Not implemented')
        return StringFile(contents)

    elif filename == '-':
        return StdStream()

    elif isinstance(filename, str):
        if re.match(r'[A-Za-z]+:', filename):
            return URLStream(filename)

        elif binary:
            return BinaryFile(filename)

        else:
            return RegularFile(filename, **kwargs)

    elif isinstance(filename, BaseFile):
        return filename

    else:
        raise Exception(f'Cannot coerce to file: {repr(filename)}')


class StringFile (BaseFile):

    def __init__ (self, contents=''):
        BaseFile.__init__(self)
        self._contents = contents

    def exists (self):
        return True

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

    def exists (self):
        return True

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

    def __init__ (self, fn, mkdirs=False, **kwargs):
        BaseFile.__init__(self)
        self.filename = expanduser(fn)
        self.mkdirs = mkdirs
        self.kwargs = kwargs

    def exists (self):
        return exists(self.filename)

    def __iter__ (self):
        if exists(self.filename):
            with open(self.filename, 'r', **self.kwargs) as f:
                for line in f:
                    yield line

    def store (self, lines, mode='w'):
        if self.mkdirs:
            dn = dirname(self.filename)
            makedirs(dn, exist_ok=True)
        with open(self.filename, mode, **self.kwargs) as f:
            for line in lines:
                f.write(line)


class BinaryFile (BaseFile):

    def __init__ (self, fn):
        BaseFile.__init__(self)
        self.filename = fn

    def exists (self):
        return exists(self.filename)

    def __iter__ (self):
        with open(fn, 'rb') as f:
            for line in f:
                yield line

    def store (self, lines, mode='w'):
        with open(fn, mode + 'b') as f:
            for line in lines:
                f.write(line)


#--  _Buffered  -----------------------------------------------------------------

class _Buffered (object):

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

class Format (BaseFile):

    @classmethod
    def from_lines (self, lines):
        raise NotImplementedError()

    @classmethod
    def to_lines (self, elts):
        raise NotImplementedError()

    def __init__ (self, filename=None, binary=False, contents=None, **kwargs):
        BaseFile.__init__(self)
        self._file = File(filename, binary, contents, **kwargs)

    def exists (self):
        return self._file.exists()

    def format (self):
        return self

    def base (self):
        return self._file

    def __iter__ (self):
        return self.from_lines(iter(self._file))

    def store (self, contents, mode='w'):
        self._file.store(self.to_lines(contents), mode)


# class LoadableFormat (Format):
# 
#     pass
        

# class Lines (Format):
# 
#     @classmethod
#     def to_lines (contents):
#         return contents
#     
#     @classmethod
#     def from_lines (lines):
#         return lines


#--  Records  ------------------------------------------------------------------

class Records (Format):

    @classmethod
    def from_lines (self, lines):
        for line in lines:
            line = line.rstrip('\r\n')
            if line:
                yield line.split('\t')
            else:
                yield []
    
    @classmethod
    def to_lines (self, recs):
        for rec in recs:
            yield '\t'.join(rec) + '\n'

Tabular = Records


#--  Simples  ------------------------------------------------------------------
#
# Works with any object that consists of a mix of strings, pairs whose first
# element is a string, list-like objects, and dict-like objects.  A dict-like
# object is anything that has an items() method, and a list-like object is
# anything that has an __iter__() method but is not dict-like.
#
# When loading, the original objects are not reconstructed.  The value consists
# of strings, pairs, lists and dicts.

class Simples (Format):

    @classmethod
    def from_lines (self, lines):
        return self._lines_to_simples(iter(lines))
    
    @classmethod
    def _lines_to_simples (self, lines, terminator=None):
        try:
            while True:
                yield self.lines_to_simple(lines, terminator)
        except StopIteration:
            pass
    
    @classmethod
    def lines_to_simple (self, lines, terminator=None):
        line = next(lines)
        j = -1 if line.endswith('\n') else len(line)
        if terminator and line == terminator:
            raise StopIteration
        elif line.startswith('|'):
            return line[1:j]
        elif line.startswith(':'):
            key = line[1:j]
            value = self.lines_to_simple(lines)
            return (key, value)
        elif line.startswith('{'):
            return self._make_dict(self._lines_to_simples(lines, '}\n'))
        elif line.startswith('['):
            return list(self._lines_to_simples(lines, ']\n'))
        else:
            raise Exception(f'Unexpected line: {repr(line)}')
    
    @classmethod
    def _make_dict (self, items):
        d = {}
        for item in items:
            if not (isinstance(item, tuple) and len(item) == 2):
                raise Exception(f'Expecting pairs: {repr(item)}')
            (k,v) = item
            d[k] = v
        return d
            
    @classmethod
    def to_lines (self, objs):
        for obj in objs:
            for line in self.simple_to_lines(obj):
                yield line
    
    @classmethod
    def simple_to_lines (self, obj):
        if isinstance(obj, str):
            yield '|' + obj + '\n'
        elif isinstance(obj, dict):
            yield '{\n'
            for (k,v) in obj.items():
                yield ':' + str(k) + '\n'
                for line in self.simple_to_lines(v):
                    yield line
            yield '}\n'
        elif isinstance(obj, tuple) and len(obj) == 2 and isinstance(obj[0], str):
            yield ':' + obj[0] + '\n'
            for line in self.simple_to_lines(obj[1]):
                yield line
        elif isinstance(obj, list):
            yield '[\n'
            for elt in obj:
                for line in self.simple_to_lines(elt):
                    yield line
            yield ']\n'
        else:
            raise Exception(f'Not a simple: {repr(obj)}')
            

#--  Blocks  -------------------------------------------------------------------

class Blocks (Format):

    @classmethod
    def from_lines (self, lines):
        return self._records_to_blocks(Records.from_lines(lines))
    
    @classmethod
    def _records_to_blocks (self, records):
        block = []
        for r in records:
            if r:
               block.append(r)
            elif block:
                yield block
                block = []
        if block:
            yield block
    
    @classmethod
    def to_lines (self, blocks):
        first = True
        for block in blocks:
            if first:
                first = False
            else:
                yield '\n'
            for record in block:
                yield '\t'.join(record) + '\n'
    
    
#--  Key-value separated by whitespace  ----------------------------------------

def kvsplit (line):
    for i in range(len(line)):
        if line[i].isspace():
            j = i+1
            while j < len(line) and line[j].isspace():
                j += 1
            return (line[:i], line[j:])
    return (line, '')
            
def spacefree (key):
    for i in range(len(key)):
        if key[i].isspace():
            return False
    return True


#--  PLists  -------------------------------------------------------------------

class PLists (Format):

    @classmethod
    def from_lines (self, lines):
        d = []
        for line in lines:
            line = line.rstrip('\r\n')
            if line:
                (key, value) = kvsplit(line)
                if not value:
                    raise Exception(f'Missing value: {repr(line)}')
                d.append((key, value))
            else:
                yield d
                d = []
        if d:
            yield d
    
    @classmethod
    def to_lines (self, plists):
        first = True
        for d in plists:
            if first: first = False
            else: yield '\n'
            for (k,v) in d:
                if not spacefree(k):
                    raise Exception(f'Bad key: {repr(key)}')
                yield k + ' ' + v


#--  Dicts  --------------------------------------------------------------------

class Dicts (Format):

    @classmethod
    def parse_value (self, value):
        return value

    @classmethod
    def unparse_value (self, value):
        return value

    @classmethod
    def from_lines (self, lines, dicttype=dict):
        d = dicttype()
        for line in lines:
            line = line.rstrip('\r\n')
            if line:
                (key, value) = kvsplit(line)
                if not value:
                    raise Exception(f'Missing value: {repr(line)}')
                if key in d:
                    raise Exception(f'Duplicate key: {key}')
                d[key] = self.parse_value(value)
            else:
                yield d
                d = dicttype()
        if d:
            yield d
    
    @classmethod
    def to_lines (self, dicts):
        first = True
        for d in dicts:
            if first: first = False
            else: yield '\n'
            for (k,v) in d.items():
                if not spacefree(k):
                    raise Exception(f'Bad key: {repr(key)}')
                yield k + ' ' + self.unparse_value(v) + '\n'
    

class OrderedDicts (Format):

    @classmethod
    def from_lines (self, lines):
        return Dicts.from_lines(lines, OrderedDict)

    @classmethod
    def to_lines (self, dicts):
        return Dicts.to_lines(dicts)


#--  ObjectTables  -------------------------------------------------------------

class ObjectTables (Format):

    # The first key in an object is the primary key. Every object must begin
    # with the primary key, and every object must have a unique value for
    # the primary key.
    #
    # The table's keys are primary keys, and its values are the objects (dicts).
    # A File's contents are always a list containing exactly one table.

    @classmethod
    def from_lines (self, lines):
        tab = {}
        primary_key = None
        for obj in OrderedDicts.from_lines(lines):
            for (pkey, pvalue) in obj.items(): break
            if primary_key is None: primary_key = pkey
            elif primary_key != pkey:
                raise Exception(f'Object does not begin with the primary key: {obj}')
            tab[pvalue] = obj
        yield tab

    @classmethod
    def to_lines (self, tables):
        if tables:
            return OrderedDicts.to_lines(tables[0].values())


#--  ILines  -------------------------------------------------------------------

class ILines (Format):

    @classmethod
    def from_lines (self, lines):
        for line in lines:
            line = line.rstrip('\r\n')
            i = 0
            while i < len(line) and line[i] == ' ':
                i += 1
            yield (i, line[i:])
    
    @classmethod
    def to_lines (self, ilines):
        for (ind, line) in ilines:
            yield '  ' * ind + line + '\n'


#--  NestedLists  --------------------------------------------------------------
#
# A block at indentation level i consists of a mix of lines at indentation i+1
# and subblocks at indentation i+1.
#
# The toplevel elements are the elements of the (nonexistent) block at level -1.

class NestedLists (Format):

    @classmethod
    def from_lines (self, lines):
        stream = _Buffered(ILines.from_lines(lines))
        lst = list(self.ilines_to_nested_list(stream, 0))
        if lst:
            yield lst
    
    @classmethod
    def ilines_to_nested_list (self, ilines, indent):
        for (ind, line) in ilines:
            if ind < indent:
                ilines.pushback((ind, line))
                break
            elif ind == indent:
                yield line
            else:
                ilines.pushback((ind, line))
                lst = list(self.ilines_to_nested_list(ilines, ind))
                if lst:
                    yield lst
            
    @classmethod
    def to_lines (self, lsts):
        for lst in lsts:
            for line in ILines.to_lines(self._nested_list_to_ilines(lst, 0)):
                yield line
    
    @classmethod
    def _nested_list_to_ilines (self, lines, ind):
        for line in lines:
            if isinstance(line, str):
                yield (ind, line)
            else:
                for iline in self._nested_list_to_ilines(line, ind + 2):
                    yield iline


#--  NestedDicts  ---------------------------------------------------------------

class NestedDicts (Format):

    @classmethod
    def from_lines (self, lines):
        return self.from_nested_lists(NestedLists.from_lines(lines))
    
    @classmethod
    def from_nested_lists (self, lists):
        for lst in lists:
            yield self.nested_list_to_container(list(lst))
    
    @classmethod
    def nested_list_to_container (lst):
        out = None
        i = 0
        while i < len(lst):
            if isinstance(lst[i], list):
                raise Exception('Embedded dict without a key')
            elif i+1 < len(lst) and isinstance(lst[i+1], list):
                out = self._insert_item(lst[i], self.nested_list_to_container(lst[i+1]), dict, out)
                i += 2
            else:
                line = lst[i].strip()
                (key, value) = kvsplit(line)
                if not value:
                    out = self._insert_item(None, key, list, out)
                else:
                    out = self._insert_item(key, value, dict, out)
                i += 1
        return out
    
    @classmethod
    def _insert_item (self, key, value, typ, out):
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
    
    @classmethod
    def to_lines (self, conts):
        for cont in conts:
            for line in self.container_to_lines(cont):
                yield line
    
    @classmethod
    def container_to_lines (self, cont):
        return ILines.to_lines(self.container_to_ilines(cont, 0))
    
    @classmethod
    def container_to_ilines (self, cont, indent):
        if isinstance(cont, dict):
            for (k, v) in cont.items():
                if isinstance(v, str):
                    yield (indent, k + ' ' + v)
                elif isinstance(v, dict):
                    yield (indent, k)
                    for iline in self.container_to_ilines(v, indent+2):
                        yield iline
                else:
                    raise Exception(f'Unexpected value type: {repr(v)}')
        elif isinstance(cont, list):
            for v in cont:
                if isinstance(v, str):
                    yield (indent, v)
                else:
                    raise Exception('Lists may only contain strings')

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

class Json (Format):

    @classmethod
    def from_lines (self, lines):
        yield json_parse(''.join(lines))

    @classmethod
    def to_lines (self, objs):
        first = True
        for obj in objs:
            if not first:
                raise Exception('Only one object can be stored in a Json file')
            first = False
            yield json_unparse(obj)
