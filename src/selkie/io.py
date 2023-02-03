##  @package seal.core.io
#   The io module contains input and output streams.

try:
    from fcntl import flock, LOCK_EX, LOCK_UN
except:
    flock = LOCK_EX = LOCK_UN = None

import sys, os, re, urllib.request, urllib.parse, urllib.error, \
    codecs, shutil, subprocess, stat, threading, datetime, random, \
    json
from glob import glob
from io import StringIO, TextIOBase
from os.path import expanduser
from pathlib import Path
from .seq import as_list
from .string import as_ascii
from .com import fg

_open = __builtins__['open']


def ispathlike (x):
    return isinstance(x, str) or hasattr(x, '__fspath__')


##  Passes '-' through unchanged; otherwise dispatches to os.path.abspath().

def abspath (fn):
    if fn == '-':
        return fn
    else:
        return os.path.abspath(os.path.expanduser(fn))


#--  srepr  --------------------------------------------------------------------

##  'Stable' repr, for use with doctest.
#   E.g., prints out the keys of a dict or members of a set in sort order.

def srepr (x):
    if isinstance(x, dict):
        pairs = ['%s: %s' % (repr(k), srepr(v))
                 for (k,v) in sorted(x.items())]
        return '{' + ', '.join(pairs) + '}'

    elif isinstance(x, set):
        elts = [srepr(e) for e in sorted(x)]
        return '{' + ', '.join(elts) + '}'

    else:
        return repr(x)


#--  Contents  -----------------------------------------------------------------

##  The contents of a file, as a string.

def contents (filename, encoding=None):
    with infile(filename, encoding) as f:
        return f.read()


#--  Tee  ----------------------------------------------------------------------

##  A tee.  Splits a stream into one going to a file and an identical copy going
#   to stdout.

class tee (object):

    ##  Constructor.

    def __init__ (self, filename):

        ##  The filename being written.
        self.filename = filename

        ##  The output stream to the file.
        self.stream = _open(filename, 'w')

    ##  Writes the given string both to the output stream and to stdout.

    def write (self, x):
        self.stream.write(x)
        sys.stdout.write(x)

    ##  Closes the output stream.

    def close (self):
        self.stream.close()
        self.stream = None
    

#--  NullStream  ---------------------------------------------------------------

##  A fake stream.

class NullStream (object):
    
    ##  No-op.

    def write (self, s):
        pass

##  An instance of NullStream.
null = NullStream()


#--  Output List  --------------------------------------------------------------

##  A specialization of list that behaves like an output stream.
#   Specifically, it provides a write() method.  Writing to it appends lines;
#   the final result is a list of lines.  The lines do not include carriage returns
#   and newlines.

class OutputList (list):

    ##  Constructor.

    def __init__ (self):

        ##  A partial line, still waiting for the newline.
        self.partial = None

    ##  Write a string.  If the string ends in carriage return and/or newline,
    #   it completes a line.  Append it to the list and clear the partial member.
    #   Otherwise, concatenate it to the partial member and wait.
    #   Caution: does not handled embedded newlines.

    def write (self, s):
        eol = False
        if s and s[-1] in '\r\n':
            eol = True
            s = s.rstrip('\r\n')
        if self.partial:
            self.partial += s
        else:
            self.partial = s
        if eol:
            self.append(self.partial)
            self.partial = None


#--  Suffixes  -----------------------------------------------------------------

##  A suffix begins with the final period, provided that it occurs in the final
#   pathname component.  Returns the pathname sans suffix.

def strip_suffix (fn):
    i = fn.rfind('.')
    if i > 0 and '/' not in fn[i+1:]:
        return fn[:i]
    else:
        return fn

##  Returns a pair: (filename sans suffix, suffix sans period).

def split_suffix (fn):
    i = fn.rfind('.')
    if i > 0 and '/' not in fn[i+1:]:
        return (fn[:i], fn[i+1:])
    else:
        return (fn, '')

##  Returns the suffix or an empty string.  The period is not included.

def get_suffix (fn):
    i = fn.rfind('.')
    if i > 0 and '/' not in fn[i+1:]:
        return fn[i+1:]
    else:
        return ''


#--  Fn  -----------------------------------------------------------------------

##  The only purpose of this object is so that we can distinguish by type
#   between a filename and the contents of a file.

class Contents (object):

    ##  Constructor.

    def __init__ (self, s):

        ##  The string.
        self.contents = s


##  A filename; a specialization of str.

class Fn (str):

    ##  Dot can be used to add a pathname component.

    def __getattr__ (self, attr):
        if os.path.isdir(self):
            return Fn(os.path.join(self, attr))
        else:
            return Fn(self + '.' + attr)

    ##  Plus can also be used to concatenate a string; no slash is inserted.

    def __add__ (self, other):
        return Fn(str.__add__(self, other))

    ##  Divide can be used to add pathname components.

    def __div__ (self, other):
        return self.join(other)

    ##  Double slash can also be used.

    def __truediv__ (self, other):
        return self.join(other)

    ##  CAUTION: this overrides str.join, with a very different semantics.
    #   Specifically, this does a pathname join.

    def join (self, *cpts):
        return Fn(os.path.join(self, *cpts))

    ##  Whether the named file exists.

    def exists (self):
        return os.path.exists(self)

    ##  True if the named file exists and is a directory.

    def isdir (self):
        return os.path.isdir(self)

    ##  The parent, obtained by stripping off the last component and deleting
    #   any trailing slashes.

    def parent (self):
        if self.endswith('/'):
            name = self.rstrip('/')
        else:
            name = self
        if name:
            return Fn(os.path.dirname(name))

    ##  Create the file.  Create any missing ancestor using os.makedirs(),
    #   then touch the file.

    def create (self, dir=False):
        if self.endswith('/'): dir = True
        if dir:
            os.makedirs(self)
        else:
            dirname = os.path.dirname(self)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            _open(self, 'w').close()

    ##  List the named file.  No-op if the file does not exist.  Returns
    #   a list of child file names, if it names an existing directory.
    #   Returns the result of os.stat(), if it names an existing regular file.

    def list (self):
        if os.path.exists(self):
            if os.path.isdir(self):
                return [Fn(f) for f in os.listdir(self)]
            else:
                return os.stat(self)

    ##  Dispatches to shutil.move().

    def rename (self, newname):
        shutil.move(self, newname)

    ##  Makes a copy.  If this is a directory, it does a deep copy.

    def copy (self, newname, symlinks=True):
        if os.path.isdir(self):
            shutil.copytree(self, newname, symlinks)
        else:
            shutil.copyfile(self, newname)

    ##  Delete the file.

    def delete (self):
        if os.path.isdir(self):
            os.rmdir(self)
        else:
            os.unlink(self)

    ##  Return the file size.

    def size (self):
        return file_size(self)

    ##  Return the modtime, in seconds since the epoch (midnight UTC, Jan 1, 1970).

    def modtime (self):
        return os.stat(self).st_mtime


# ##  The Seal python directory: the inner 'seal' directory.
# __seal__ = os.path.dirname(os.path.dirname(__file__))
# 
# ##  The Seal destination directory: the outer 'seal' directory.
# __dest__ = os.path.dirname(os.path.dirname(__seal__))
# 
# ##  The Seal destination directory.
# dest = Fn(__dest__)
# 
# ##  The Seal bin directory.
# bin = Fn(os.path.join(__dest__, 'bin'))
# 
# ##  The seal examples directory.
# ex = Fn(os.path.join(__seal__, '__examples__'))
# 
# ##  The seal data directory.
# data = Fn(os.path.join(__seal__, '__data__'))
# 
# ##  The root directory.
# root = Fn(os.path.sep)
# 
# ##  The tmp directory.
# tmp = root.tmp
# 
# ##  The current directory, as an Fn.
# here = Fn(os.path.curdir)
# 
# ##  The user's home directory, as an Fn.
# home = Fn(os.path.expanduser('~'))
# 
# ##  Nowhere (/dev/null).
# nowhere = Fn('/dev/null')


##  Allocate a tmp filename.  It automatically gets deleted when
#   the filename is deleted or garbage collected.
#   That is, one may delete the file by calling del on the filename.

def tmpfile ():
    _TmpFn.count += 1
    fn = _TmpFn('/tmp/seal_%d_%d' % (os.getpid(), _TmpFn.count))
    fn._delete_on_gc = True
    return fn

##  Allocates a temporary filename prefix and arranges for any file whose
#   name begins with that prefix to be
#   deleted (if any such exist) when the C{TmpFile} object gets garbage
#   collected.  The filename prefix is of form::
#
#       /tmp/seal_PID_N_
#
#   where PID is the pid of the python process and N is a
#   sequence number that is advanced each time a temporary filename is
#   allocated.

class _TmpFn (Fn):

    ##  So that we assign a unique number to each temp file.
    count = 0

    ##  When the TmpFn gets deleted, delete the file on disk.
    def __del__ (self):
        if self._delete_on_gc:
            os.system("rm -f " + self + "*")

    ##  Call this to prevent file deletion on garbage collection.
    def no_delete (self):
        self._delete_on_gc = False


#--  infile and outfile  -------------------------------------------------------

##  A readable representation; fn may be a filename, a StringIO, or a stream.

def filename_string (fn):
    if isinstance(fn, str):
        return fn
    elif isinstance(fn, StringIO):
        return '<string input>'
    else:
        return '<open file>'

##  Open a file for reading.  Filename may be '-', a string representing a
#   filename, a StringIO, a stream, or anything that has a readline() method.

def infile (filename, encoding=None):
    if isinstance(filename, str):
        if not encoding: encoding = 'utf8'
        if filename == '-':
            return sys.stdin
        elif re.match(r'[A-Za-z]+:', filename):
            bstream = urllib.request.urlopen(filename, 'r')
            reader = codecs.getreader(encoding)
            return reader(bstream)
        else:
            return _open(filename, 'r', encoding=encoding)
    elif hasattr(filename, '__fspath__'):
        return infile(filename.__fspath__())
    elif isinstance(filename, StringIO):
        return filename
    elif isinstance(filename, TextIOBase):
        return filename
    elif hasattr(filename, 'readline'):
        return filename
    else:
        raise Exception('Cannot coerce to file: %s' % filename)

##  Open a file for writing.  Fileid may be '-', a string representing
#   a filename, or None.  If None, a StringIO is returned.

def outfile (fileid=None, encoding=None):
    if fileid is None:
        return StringIO()
    elif fileid == '-':
        return sys.stdout
    else:
        if not encoding: encoding = 'utf8'
        return _open(fileid, 'w', encoding=encoding)

##  An infile containing bytes.

def byte_infile (fn):
    if fn == '-': return sys.stdin.buffer
    else: return _open(fn, 'rb')

##  An outfile writing bytes.

def byte_outfile (fn):
    if fn == '-': return sys.stdout.buffer
    else: return _open(fn, 'wb')

##  Close a file, but not if it is a StringIO or a std stream.

def close (file):
    if isinstance(file, StringIO):
        value = file.getvalue()
    else:
        value = None
    if file not in [sys.stdin, sys.stdout, sys.stderr]:
        file.close()
    return value


#--  Load/save string  ---------------------------------------------------------

##  Load a string from a file.

def load_string (filename, encoding=None):
    f = infile(filename, encoding)
    return f.read()

##  Save a string to a file.

def save_string (s, filename=None, encoding=None):
    f = outfile(filename, encoding)
    f.write(s)
    return close(f)


#--  Lines  --------------------------------------------------------------------

##  Load a list of lines from a file.  Newlines and carriage returns are not
#   included in the lines.

def load_lines (filename, encoding=None):
    return list(iter_lines(filename, encoding))

##  Iterate over a list of lines.

def iter_lines (filename, encoding=None):
    return read_lines(infile(filename, encoding))

def read_lines (f):
    for line in f:
        yield line.rstrip('\r\n')

##  Save a list of lines to a file.

def save_lines (lines, filename=None, encoding=None):
    write_lines(lines, outfile(filename, encoding))

def write_lines (lines, f):
    for line in lines:
        f.write(line)
        f.write('\n')
    return close(f)


#--  Records  ------------------------------------------------------------------

##  Load tabular records from a file.

def load_records (filename, header=None, separator='\t', encoding=None):
    return list(iter_records(filename, header, separator, encoding))

##  Iterate over tabular records.

class iter_records (object):

    ##  Constructor.

    def __init__ (self, filename, header=None, separator='\t', encoding=None):
        ##  Filename.
        self.filename = filename_string(filename)
        ##  File.
        self.file = infile(filename, encoding)
        ##  Number of lines processed so far.
        self.linecount = 0
        ##  Separator.
        self.separator = separator
        if header is not None:
            line = self.__readline()
            fileheader = line.rstrip('\r\n').split(separator)
            if fileheader != header:
                raise Exception("Bad header: got %s, expecting %s: %s" % \
                    (fileheader, header, filename))

    def __readline (self):
        self.linecount += 1
        return next(self.file)

    ##  Returns self.

    def __iter__ (self):
        return self

    ##  The iteration method.

    def __next__ (self):
        line = self.__readline()
        return line.rstrip('\r\n').split(self.separator)

    ##  Signal an error, adding the filename and line number.

    def error (self, msg):
        raise Exception("[%s line %d] %s" % (self.filename, self.linecount, msg))

##  Save a list of records to a tabular file.

def save_records (records, filename=None, header=None, separator='\t', encoding=None):
    f = outfile(filename, encoding)
    if header:
        f.write(separator.join(header))
        f.write('\n')
    for record in records:
        f.write(separator.join(record))
        f.write('\n')
    return close(f)


#--  Dict  ---------------------------------------------------------------------

##  Load a dict from a file.

def load_dict (filename, encoding=None):
    return dict((k,v) for (k,v) in load_records(filename, encoding))

##  Save a dict to a file.  The output is tabular, with keys in the first column
#   and values in the second column.

def save_dict (d, filename=None, encoding=None):
    return save_records(iter(d.items()), filename, encoding)

    
#--  NestedDict  ---------------------------------------------------------------

##  Load a nested dict from a file.
#   A nested dict permits keys containing dots.  The first part of the key
#   becomes a key in the toplevel dict, and its value is a subdict.

def load_nested_dict (fn, encoding=None):
    out = {}    
    lines = list(_open(fn, encoding=encoding))
    lno = 0
    while lno < len(lines):
        line = lines[lno].rstrip('\r\n')
        if (not line) or line.startswith('#'): continue
        (keys, v) = _nd_split(lno, line)
        (d, k) = _nd_follow_path(lno, out, keys)
        lno += 1
        if not v:
            (v, lno) = _nd_list_value(lines, lno)
        d[k] = v
    return out

def _nd_split (lno, line):
    i = 0
    while i < len(line) and not line[i].isspace():
        i += 1
    keys = line[:i].split('.')
    v = line[i:].strip()
    return (keys, v)

def _nd_follow_path (lno, d, keys):
    for k in range(len(keys)-1):
        key = keys[k]
        if key in d:
            d = d[key]
            if not isinstance(d, dict):
                s = '.'.join(keys[:k+1])
                raise Exception(f'[line {lno}] Value for {s} is not a dict')
        else:
            newd = {}
            d[key] = newd
            d = newd
    return (d, keys[-1])

def _nd_list_value (lines, lno):
    vals = []
    while lno < len(lines) and len(lines[lno]) > 0 and lines[lno][0].isspace():
        vals.append(lines[lno].strip())
        lno += 1
    return (vals, lno)
        

##  Write a dict in nested dict format.

def save_nested_dict (d, fn, encoding=None):
    f = outfile(fn, encoding)
    _write_nested_dict('', d, f)
    return close(f)

def _write_nested_dict (prefix, d, f):
    for key in d:
        if prefix: fullkey = prefix + '.' + key
        else: fullkey = key
        v = d[key]
        if isinstance(v, dict):
            _write_nested_dict(fullkey, v, f)
        else:
            f.write(fullkey)
            f.write(' ')
            v = str(v)
            if '\n' in v:
                raise Exception('Value contains newline: %s' % repr(v))
            f.write(v)
            f.write('\n')


#--  Config file  --------------------------------------------------------------

#
#  [0][d1]
#      (0, 'server', None)
#  [0 4][d1 d2]
#      (4, 'cld', None)
#  [0 4 8][d1 d2 d3]
#      (8, 'foo', '10')
#      (8, 'bar', '2')
#      (4, 'baz', '6')
#


##  Produces a nested dict, but instead of dotted keys, it uses indentation
#   Keys and values are separated by '='.
#   Hash starts a comment line.
#   Empty lines are ignored.
#
#   Example:
#
#       server
#           cld
#               foo = 10
#               bar = 2
#           baz = 6

def load_config (fn, encoding=None):
    lines = list(_iter_config_lines(fn, encoding))
    cfg = {}
    indents = [0]
    dicts = [cfg]

    for i in range(len(lines)):
        (ind, key, value) = lines[i]

        # Pop as necessary
        if ind > indents[-1]:
            raise Exception('Bad indentation')
        while ind < indents[-1]:
            if len(indents) == 1:
                raise Exception('Bad indentation in config file')
            indents.pop()
            dicts.pop()
        if ind != indents[-1]:
            raise Exception('Bad indentation in config file')            

        # Start subdict
        if value is None:
            if i+1 >= len(lines):
                raise Exception("No body for subdict '%s'" % key)
            nextind = lines[i+1][0]
            if nextind <= ind:
                raise Exception("No body for subdict '%s'" % key)
            d = {}
            dicts[-1][key] = d
            indents.append(nextind)
            dicts.append(d)

        # Set value
        else:
            dicts[-1][key] = value

    return cfg

def _iter_config_lines (fn, encoding):
    for line in infile(fn, encoding):
        line = line.rstrip('\r\n')
        if (not line) or line.startswith('#'): continue
        ind = 0
        while ind < len(line) and line[ind].isspace():
            if line[ind] != ' ':
                raise Exception('Only spaces permitted in config file')
            ind += 1
        print('ind=', ind)
        i = ind
        while True:
            if i >= len(line):
                key = line.strip()
                value = None
                break
            elif line[i] == '=':
                key = line[ind:i].strip()
                value = line[i+1:].strip()
                break
            else:
                i += 1
        yield (ind, key, value)


#--  Paragraphs  ---------------------------------------------------------------

##  Load a list of paragraphs from a file.  In the file, paragraphs are separated
#   by empty lines.  In memory, paragraphs are represented as single strings with
#   embedded newlines.

def load_paragraphs (filename, encoding=None):
    return list(iter_paragraphs(filename, encoding))

##  Iterate over paragraphs.

def iter_paragraphs (filename, encoding=None):
    file = infile(filename, encoding)
    par = []
    try:
        while True:
            line = next(file)
            if line == '\n':
                yield ''.join(par)
                par = []
            else:
                par.append(line)
    except StopIteration:
        if par:
            yield ''.join(par)

##  Write out a list of paragraphs to a file, inserting empty lines between them.

def save_paragraphs (pars, filename=None, encoding=None):
    file = outfile(filename, encoding)
    first = True
    for par in pars:
        if first:
            first = False
        else:
            file.write('\n')
        file.write(par)
    return close(file)


#--  Blocks  -------------------------------------------------------------------

##  Load a list of blocks from a file.  A block is a list of lines, sans newlines.
#   In the file, blocks are separated by empty lines.

def load_blocks (filename, encoding=None):
    return list(iter_blocks(filename, encoding))

##  Iterate over blocks.

def iter_blocks (filename, encoding=None):
    return read_blocks(infile(filename, encoding))

def read_blocks (f):
    block = []
    for line in read_lines(f):
        if line:
            block.append(line)
        else:
            if block:
                yield block
                block = []
    if block:
        yield block

##  Write a list of blocks to a file.

def save_blocks (blocks, filename=None, encoding=None):
    f = outfile(filename, encoding)
    write_blocks(blocks, f)
    return close(f)

def write_blocks (blocks, f):
    first = True
    for block in blocks:
        write_block(block, f, first=first)
        first = False

def write_block (block, f, first=False):
    if not first:
        f.write('\n')
    for line in block:
        f.write(line)
        f.write('\n')


#--  Record Blocks  ------------------------------------------------------------

##  A record is a list of field values (strings).  A record block is a list of
#   records.  A record-block file is a list of record blocks.
#   In the file, fields are separated by tab and blocks are separated by empty lines.

def load_record_blocks (filename, encoding=None):
    return list(iter_record_blocks(filename, encoding))

##  Iterate over record blocks.

def iter_record_blocks (filename, encoding=None):
    return read_record_blocks(infile(filename, encoding))

def read_record_blocks (f):
    return list(_read_record_blocks(f))

def _read_record_blocks (f):
    for block in read_blocks(f):
        yield [tuple(line.split('\t')) for line in block]

##  Save a list of record blocks to a file.

def save_record_blocks (blocks, filename=None, encoding=None):
    write_record_blocks(blocks, outfile(filename, encoding))

def write_record_blocks (blocks, f):
    first = True
    for block in blocks:
        write_record_block(block, f, first)
        first = False

def write_record_block (block, f, first=False):
    write_block(['\t'.join(r) for r in block], f, first)


#--  Tokens  -------------------------------------------------------------------

##  Quote characters: single and double quote.
QuoteChars = '"\''

##  Default special characters: parentheses, brackets, braces.
DefaultSpecialChars = '()[]{}'


##  Represents the syntax of a little language.

class Syntax (object):

    ##  Constructor.

    def __init__ (self,
                  special=DefaultSpecialChars,
                  eol=False,
                  comments=True,
                  multi=None,
                  backslash=True,
                  stringtype='word',
                  mlstrings=False,
                  digits=False):

        ##  The special characters.  True means everything except alphanumerics
        #   and whitespace.
        self.special = None

        ##  Multi-character sequences that should be recognized as tokens.
        self.multi = None

        ##  The start characters for multi-character sequences.
        self.multi_start = None

        ##  Whether to include newline as a token.
        self.eol = eol

        ##  What character/string introduces comments.  Default: '#'.
        self.comments = None

        ##  Whether to interpret backslash as escape.
        self.backslash = backslash

        ##  What token type to use for a quoted string.  Default: 'word'.
        self.stringtype = stringtype

        ##  Whether to permit strings to extend over multiple lines.  Default: False.
        self.mlstrings = mlstrings

        ##  Whether to return digit sequences as tokens.
        self.digits = digits


        if comments is True:
            self.comments = '#'
        elif not comments:
            self.comments = ''

        if special is True:
            # everything is special except alphanum and underscore
            self.special = True
        else:
            self.special = special + QuoteChars + self.comments

        self.multi = multi
        if multi:
            self.multi = sorted(multi, key=len, reverse=True)
            self.multi_start = ''.join(set(s[0] for s in multi))
        else:
            self.multi_start = ''

    ##  Convert s to a string that will scan correctly.

    def scanable_string (self, s):
        if not isinstance(s, str):
            s = str(s)
        for c in s:
            if c.isspace() or c in self.special:
                s = repr(s)
                if s[0] == 'u': return s[1:]
                else: return s
        return s

    ##  String representation.

    def __repr__ (self):
        return '<Syntax %s %s>' % (self.special, self.eol)

##  A Syntax instance.
DefaultSyntax = Syntax()

##  Convert s to a scanable string, assuming the default syntax.

def scanable_string (s):
    return DefaultSyntax.scanable_string(s)


##  A token.

class Token (str):

    ##  True if type is 'any' or equals the token's type.
    def hastype (self, type):
        if type == 'any': return self.type != 'eof'
        else: return type == self.type

    ##  Raise an exception, indicating file, line, and offset.
    def error (self, msg='syntax error'):
        raise Exception('[%s line %d char %d] %s' % \
            (self.filename, self.line, self.offset, msg))

    ##  Print a warning, indicating file, line, and offset.
    def warn (self, msg):
        sys.stderr.write('WARNING: [%s line %d char %d] %s\n' % \
                             (self.filename, self.line, self.offset, msg))


##  Tokenize a file, returning a list.

def load_tokens (filename, **kwargs):
    return list(iter_tokens(filename, **kwargs))

##  Iterate over tokens of a string.

def tokenize (s, syntax=DefaultSyntax, encoding=None):
    return iter_tokens(StringIO(s), syntax, encoding)

##  Iterator over tokens.

class iter_tokens (object):

    ##  Constructor.

    def __init__ (self, filename, syntax=DefaultSyntax, encoding=None):

        ##  A Syntax instance.
        self.syntax = syntax

        ##  Stack, for (possibly nested) temporary syntax changes.
        self.stack = []

        ##  Filename string; set even for streams not associated with files.
        self.filename = filename_string(filename)

        ##  The lines of the file.
        self.lines = load_lines(filename, encoding)  # no newlines in lines

        ##  The current line.
        self.line = None

        ##  Current line number.
        self.linecount = 1

        ##  Current character offset on the line.
        self.offset = 0

        ##  Previous linecount.
        self.old_linecount = 1

        ##  Previous offset.
        self.old_offset = 0

        self.__token = None

        if self.lines: self.line = self.lines[0]
        else: self.line = ''

    ##  Returns self.

    def __iter__ (self):
        return self

    ##  Whether we are at EOF.

    def __bool__ (self):
        return self.token().type != 'eof'

    def __readline (self):
        if self.linecount < len(self.lines):
            self.line = self.lines[self.linecount]
            self.linecount += 1
        elif self.linecount == len(self.lines):
            self.line = ''
            self.linecount += 1
        else:
            raise Exception('Readline after EOF')
        self.offset = 0

    def __at_eof (self):
        return self.linecount > len(self.lines)

    def __empty_line (self):
        for c in self.line:
            if c in self.syntax.comments: return True
            elif not c.isspace(): return False
        return True

    def __is_special (self, c):
        if self.syntax.special is True:
            return not (c.isalnum() or c == '_')
        else:
            return c in self.syntax.special

    ##  Advance, if necessary, then return the current token.

    def token (self):
        if self.__token is None: self.__advance()
        return self.__token

    def __skip_eol (self):
        if self.offset >= len(self.line):
            if self.syntax.eol and not self.__empty_line():
                self.__set_token('\n', self.offset, string='\n')
                self.__readline()
            else:
                while self.offset >= len(self.line):
                    if self.__at_eof():
                        self.__set_token('eof', self.offset)
                        break
                    self.__readline()

    def __advance (self):
        self.old_linecount = self.linecount
        self.old_offset = self.offset
        self.__token = None
        try:
            while self.__token is None:
                self.__skip_eol()
                if self.__token is not None: return
                c = self.line[self.offset]

                if c in self.syntax.multi_start and self.__scan_multi(): pass
                elif c in self.syntax.comments: self.offset = len(self.line)
                elif c == "'" or c == '"': self.__scan_quoted()
                elif c.isspace(): self.offset += 1
                elif self.__is_special(c): self.__scan_special()
                elif self.syntax.digits and self.__is_digit(c): self.__scan_digit()
                else: self.__scan_word()

        except StopIteration:
            raise Exception('[%s line %d offset %d] Unexpected eof' % \
                (self.filename, self.linecount, self.offset))

    def __retreat (self):
        self.__token = None
        self.linecount = self.old_linecount
        self.offset = self.old_offset
        if self.linecount > 0:
            self.line = self.lines[self.linecount-1]
        else:
            self.line = None

    def __set_token (self, type, start, line=None, string=None, quotes=None):
        if line is None:
            line = self.linecount
        if string is None:
            string = self.line[start:self.offset]
        self.__token = Token(string)
        self.__token.type = type
        self.__token.filename = self.filename
        self.__token.line = line
        self.__token.offset = start
        self.__token.quotes = quotes

    def __is_digit (self, c):
        if c.isdigit(): return True
        i = self.offset + 1
        return c == '-' and i < len(self.line) and self.line[i].isdigit()

    def __scan_digit (self):
        start = self.offset
        if self.line[self.offset] == '-': self.offset += 1
        while self.offset < len(self.line) and self.line[self.offset].isdigit():
            self.offset += 1
        self.__set_token('digit', start)

    def __scan_word (self):
        start = self.offset
        while self.offset < len(self.line):
            c = self.line[self.offset]
            if c.isspace() or self.__is_special(c): break
            self.offset += 1
        self.__set_token('word', start)

    def __error (self, start, msg):
        raise Exception('[%s line %d char %d] %s' % \
            (self.filename, self.linecount, start, msg))

    def __scan_quoted (self):
        delim = self.line[self.offset]
        self.offset += 1
        start = self.offset
        restart = self.offset
        frags = []
        while True:
            while self.offset >= len(self.line):
                if self.syntax.mlstrings:
                    if restart < len(self.line):
                        frags.append(self.line[restart:])
                    frags.append('\n')
                    self.__readline()
                    restart = self.offset
                    if self.__at_eof():
                        self.__error(start, 'Unterminated string at EOF')
                else:
                    self.__error(start, 'End of line in string')
            c = self.line[self.offset]
            if c == delim:
                frags.append(self.line[restart:self.offset])
                self.offset += 1
                break
            elif c == '\\' and self.syntax.backslash:
                frags.append(self.line[restart:self.offset])
                frags.append(self.__scan_escape_sequence())
                restart = self.offset
            else:
                self.offset += 1
        self.__set_token(self.syntax.stringtype, start, self.linecount, ''.join(frags), delim)

    def __scan_escape_sequence (self):
        # self.line[self.offset] is backslash
        self.offset += 1
        if self.offset >= len(self.line): self.__error('Bad escape sequence')
        c = self.line[self.offset]
        self.offset += 1
        if c == '\\' or c == '"' or c == "'": return c
        elif c == 'a': return '\a'
        elif c == 'b': return '\b'
        elif c == 'f': return '\f'
        elif c == 'n': return '\n'
        elif c == 'r': return '\r'
        elif c == 't': return '\t'
        elif c == 'u':
            i = self.offset
            self.offset += 4
            if self.offset > len(self.line): self.__error('Bad escape sequence')
            return chr(int(self.line[i:self.offset], 16))
        elif c == 'U':
            self.__error('\\U escapes not implemented')
        elif c == 'v': return '\v'
        elif '0' <= c <= '7':
            i = self.offset
            self.offset += 1
            n = 1
            while n < 3 and self.offset < len(self.line) and \
                    '0' <= self.line[self.offset] <= '7':
                self.offset += 1
                n += 1
            return chr(int(self.line[i:self.offset], 8))
        elif c == 'x':
            i = self.offset
            self.offset += 1
            if self.offset < len(self.line) and \
                    ('0' <= self.line[self.offset] <= '9' or \
                     'a' <= self.line[self.offset] <= 'f' or \
                     'A' <= self.line[self.offset] <= 'F'):
                self.offset += 1
            d = int(self.line[i:self.offset], 16)
            if d < 0x100: return chr(d)
            else: return chr(d)

    def __scan_special (self):
        start = self.offset
        self.offset += 1
        self.__set_token(self.line[start], start)

    def __looking_at (self, word):
        for i in range(len(word)):
            t = self.offset + i
            if t >= len(self.line): return False
            if self.line[t] != word[i]: return False
        return True

    def __scan_multi (self):
        for word in self.syntax.multi:
            if self.__looking_at(word):
                start = self.offset
                self.offset += len(word)
                self.__set_token(self.line[start:self.offset], start)
                return True

    ##  Whether the next token is something other than EOF.
    #   If type or string is provided, the value indicates whether the next
    #   token has the given type and/or string.

    def has_next (self, type=None, string=None):
        if string:
            if type: raise Exception("Provide only one argument")
            return self.token() == string
        elif type:
            return self.token().hastype(type)
        else:
            return self.token().type != 'eof'

    ##  Iterator method.

    def __next__ (self):
        token = self.token()
        if token.type == 'eof': raise StopIteration
        self.__token = None
        self.old_linecount = self.linecount
        self.old_offset = self.offset
        return token

    ##  If the next token matches the given type and/or string, return it
    #   and advance.  Otherwise, return None.

    def accept (self, type=None, string=None):
        token = self.token()
        if type and not token.hastype(type):
            return None
        if string and not (token == string):
            return None
        return next(self)

    ##  If the next token has the given type and/or string, return it
    #   and advance.  Otherwise, signal an error.  Returns None at EOF.

    def require (self, type=None, string=None):
        token = self.token()
        if type and not token.hastype(type):
            token.error('Expecting ' + repr(type))
        if string and not (token == string):
            token.error('Expecting ' + repr(string))
        if type == 'eof': return None
        else: return next(self)

    ##  Signal an error, indicating filename and line number.

    def error (self, msg=None):
        token = self.token()
        token.error(msg)

    ##  Print a warning, showing filename and line number.

    def warn (self, msg=None):
        token = self.token()
        token.warn(msg)

    ##  Push the current syntax on the stack and switch to the given syntax.

    def push_syntax (self, syntax):
        self.stack.append(self.syntax)
        self.syntax = syntax
        self.__retreat()

    ##  Restore the previous syntax from the stack.

    def pop_syntax (self):
        if not self.stack: raise Exception('Empty stack')
        self.syntax = self.stack.pop()
        self.__retreat()


#--  Indenter  -----------------------------------------------------------------

##  Indenter.
#   The main facility a formatter provides is automatic indentation.
#   There is a prevailing indentation level, and indentation spaces are
#   automatically inserted after each newline that is written to the
#   formatter.  The level of indentation is increased
#   using begin_indent() and decreased
#   using end_indent().  It is initially zero.
#
#   A formatter may be turned off, in which case writing commands are
#   accepted but generate no output.  The formatter is initially on.

class Indenter:

    ##  Constructor.

    def __init__ (self, filename=None, encoding=None):
        self.__out = outfile(filename, encoding)

        ##  Whether it is enabled.
        self.enabled = True

        self.__at_bol = True
        self.__indent_level = 0
        self.__indent_string = ""

        ##  How many spaces to indent by each time.
        self.indent_step = 3

    ##  Flush any pending output.
        
    def flush (self):
        if self.__out: self.__out.flush()

    ##  Close the file.

    def close (self):
        if self.__out:
            self.__out.close()
            self.__out = None

    ##  Turn the indenter on.

    def on (self):
        self.enabled = True

    ##  Turn the indenter off.

    def off (self):
        self.enabled = False

    ##  Write str(x) to the output, inserting indentation at the beginning
    #   of each line.

    def write (self, x):
        string = str(x)
        if self.enabled and string:
            lines = string.split("\n")
            self.__write(lines[0])
            for i in range(1, len(lines)):
                self.newline()
                self.__write(lines[i])

    def __write (self, string):
        if string:
            if self.__at_bol: self.__out.write(self.__indent_string)
            self.__out.write(string)
            self.__at_bol = False

    ##  Equivalent to write('\n').

    def newline (self):
        self.__out.write("\n")
        self.__at_bol = True

    ##  Increase the indentation level by one.

    def begin_indent (self):
        self.__indent_level += 1
        self.__indent_string = " " * (self.indent_step * self.__indent_level)

    ##  Decrease the indentation level by one.

    def end_indent (self):
        self.__indent_level -= 1
        if self.__indent_level < 0: raise Exception("No indentation to end")
        self.__indent_string = " " * (self.indent_step * self.__indent_level)

    ##  Set the indentation level to zero.

    def reset (self):
        self.__indent_level = 0

    ##  If the internal stream is a StringIO, fetch its value.

    def getvalue (self):
        return self.__out.getvalue()


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


#--  tabular  ------------------------------------------------------------------

def __getcell (row, j, tostring):
    if len(row) > j: return tostring(row[j])
    else: return ''

def __compute_width (rows, j, tostring):
    return max(len(__getcell(r,j,tostring)) for r in rows)

def colalign (rows, header=None, indent='', tostring=str, hlines=True):
    tmp = []
    if header: tmp.append(header)
    tmp.extend(rows)
    rows = tmp
    ncols = max(len(r) for r in rows)
    widths = [__compute_width(rows,j,tostring) for j in range(ncols)]
    for i in range(len(rows)):
        line = indent
        for j in range(ncols):
            if j: line += ' '
            line += '%-*s' % (widths[j], __getcell(rows[i], j, tostring))
        rows[i] = line
    if hlines:
        linewidth = sum(widths) + ncols - 1
        hline = '-' * linewidth
        if header:
            rows[1:1] = [hline]
        rows[-1:-1] = [hline]
    return rows

##  Produces a string representation of a table with aligned columns,
#   suitable for printing.

def tabular (rows, header=None, indent='', tostring=str, hlines=True):
    return '\n'.join(colalign(rows, header, indent, tostring, hlines))


#--  wget  ---------------------------------------------------------------------

##  Simple interface to urlretrieve().

def wget (url):
    return urllib.request.urlretrieve(url)[0]


#--  OutputRedirected  ---------------------------------------------------------

##  Does the actual output redirection.
class _Redirect (object):

    ##  Constructor.
    def __init__ (self):
        ##  The output file.
        self.output = None

    ##  Call it.
    def __call__ (self, f=None, mode=None):
        if f is None:
            return Redirection(StringIO(), True, self)
        elif mode:
            return Redirection(_open(f, mode), True)
        elif isinstance(f, str):
            mode = 'w'
            return Redirection(_open(f, mode), True)            
        else:
            return Redirection(f)


##  Output redirection.  One should not generally instantiate this class
#   directly.  Rather, use the redirect() function.

class Redirection (object):

    ##  Constructor.

    def __init__ (self, file, toclose=False, caller=None):

        ##  The file redirected to.
        self.file = file

        ##  Whether it should be closed when done.
        self.toclose = toclose

        ##  If caller is set, then caller.output gets set to file.getvalue() on exit.
        self.caller = caller

        ##  To save the old value of stdout.
        self.stdout = None

        ##  To save the old value of stderr.
        self.stderr = None

    ##  Enter.  Stdout and stderr are set to my file.

    def __enter__ (self):
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self.file
        sys.stderr = self.file
        return self

    ##  Exit.  If there is a caller, set caller.output to file.getvalue().
    #   If toclose is True, close the file.  Restore stdout and stderr.

    def __exit__ (self, etype, evalue, traceback):
        if self.caller is not None: self.caller.output = self.file.getvalue()
        if self.toclose: self.file.close()
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    ##  Write a string to the file.

    def write (self, s):
        self.file.write(s)

    ##  Flush the file.

    def flush (self):
        self.file.flush()


##  Returns a Redirection, for use in a with-statement.
#   Arguments: filename and mode.
#   Call it with no arguments to get redirection to a string.
#   For example:
#
#       with redirect() as f:
#           f.write(...)
#           out = f.output
#

redirect = _Redirect()


#--  Location  -----------------------------------------------------------------

##  Affects some Location methods.
DryRun = False


##  Generalizes over local files and remote files represented by URL.

class Location (object):

    ##  Constructor.  The filename may contain a * wildcard.  It will be
    #   expanded out as the filename of an existing file.

    def __init__ (self, fn=None, user=None, host=None, pathname=None):

        ##  May include ~ and *
        self.orig_pathname = pathname

        if fn is None:

            ##  The specified user name, None for a local file.
            self.user = user

            ##  The specified host, None for a local file.
            self.host = host

            ##  The pathname, converted to absolute form.
            self.pathname = pathname

        else:
            if user or host or pathname:
                raise Exception('Specify either fn or user-host-pathname')

            i = fn.find('@')
            j = fn.find(':')
    
            # No colon: local file
            if j < 0:
                if i >= 0:
                    raise Exception('At-sign but no colon: ' + fn)
                self.user = None
                self.host = None
                self.pathname = fn
    
            # Remote file
            else:
    
                # User not specified: use current user
                if i < 0:
                    self.user = getpass.getuser()
                    self.host = fn[:j]
                else:
                    self.user = fn[:i]
                    self.host = fn[i+1:j]
                self.pathname = fn[j+1:]

        if self.host is None:
            if self.pathname.startswith('~'):
                fn = os.path.expanduser(self.pathname)
            else:
                fn = os.path.abspath(self.pathname)
            self.pathname = instantiate_pathname(fn)

    ##  String representation.

    def __repr__ (self):
        if self.user is None: u = ''
        elif isinstance(self.user, str): u = self.user + '@'
        else: u = '<BAD USER>@'
        if self.host is None: h = ''
        elif isinstance(self.host, str): h = self.host + ':'
        else: h = '<BAD HOST>:'
        if self.pathname is None: p = '<NO PATHNAME>'
        elif isinstance(self.pathname, str): p = self.pathname
        else: p = '<BAD PATHNAME>'
        return u + h + p

    ##  Join a component to create a new Location.

    def join (self, cpt):
        return Location(user=self.user, host=self.host, pathname=os.path.join(self.pathname, cpt))

    ##  Slash is a synonym for join().

    def __truediv__ (self, cpt):
        return self.join(cpt)

    ##  Creates a new Location by concatenating the given string to the pathname.
    #   Unlike join(), does not insert a slash.

    def __add__ (self, suffix):
        return Location(user=self.user, host=self.host, pathname=self.pathname+suffix)

    ##  Whether this Location is for a remote file.  Boolean not of is_local().

    def is_remote (self):
        return bool(self.host)

    ##  Whether this Location is for a local file.

    def is_local (self):
        return not self.host

    ##  Raise an exception unless this Location is a local file.

    def require_local (self):
        if self.is_remote(): raise Exception('Not a local file: %s' % self)

    ##  Signals an error if not local.
    #   Return is not guaranteed to be an *existing* file.

    def to_filename (self):
        self.require_local()
        return self.pathname

    ##  Open the file.

    def open (self, mode='r', encoding=None, makedirs=False):
        fn = self.to_filename()
        if makedirs:
            if not mode.startswith('w'):
                raise Exception('Makedirs=True but mode is not w')
            dir = os.path.dirname(fn)
            if not os.path.exists(dir):
                os.makedirs(dir)
        return _open(fn, mode, encoding=encoding)

    ##  Read the file.  Set encoding to 'bytes' to read a binary file.

    def read (self, encoding=None):
        if encoding == 'bytes':
            mode = 'rb'
            encoding = None
        else:
            mode = 'r'
        with self.open(mode, encoding) as f:
            return f.read()

    ##  Returns a TabularFile.

    def tabular (self, mode='r', encoding=None, separator='\t'):
        return TabularFile(self, mode, encoding, separator)

    ##  Calls load_dict() on the file.

    def dict (self):
        return load_dict(str(self))

    ##  Like dirname(), but returns a Location.

    def parent (self):
        if (not self.pathname) or self.pathname == '/':
            return None
        else:
            return Location(user=self.user, host=self.host,
                            pathname=os.path.dirname(self.pathname))

    ##  Like basename().  Returns a string.

    def name (self):
        return os.path.basename(self.pathname)

    ##  Returns (parent, name) pair.  The parent is a Location, the name
    #   is a string.

    def split (self):
        (dirname, name) = os.path.split(self.pathname)
        return (Location(user=self.user, host=self.host, pathname=dirname),
                name)

    ##  Whether the file exists.

    def exists (self):
        return os.path.exists(self.to_filename())

    ##  Whether the file is '/'.

    def is_root (self):
        return self.pathname == '/'

    ##  Mac-specific.  If the filename begins with '/Volumes', check whether
    #   the subdirectory within /Volumes exists.

    def is_mounted (self):
        if self.is_remote(): raise Exception('Not a local file')
        f0 = self
        f1 = f2 = None
        while not f0.is_root():
            f2 = f1
            f1 = f0
            f0 = f0.parent()
            if f0 is None: return True
        if f1.pathname == '/Volumes':
            return f2 is not None and f2.exists()
        else:
            return True

    ##  Whether the file is a symbolic link.

    def islink (self):
        os.path.islink(self.to_filename())

    ##  Whether the file is a directory.

    def isdir (self):
        return os.path.isdir(self.to_filename())

    ##  Return an iteration over file names in this directory.
    #   Raises an exception if this is a regular file.

    def listdir (self):
        dir = self.to_filename()
        if not os.path.exists(dir):
            return iter([])
        elif not os.path.isdir(dir):
            raise Exception('Not a directory: %s' % self)
        else:
            return iter(os.listdir(dir))

    ##  Like listdir(), but iterates over (name, loc) pairs.

    def items (self):
        for name in self.listdir():
            yield (name, self.join(name))

    ##  Returns the size of the file, in bytes.

    def size (self):
        return os.stat(self.to_filename()).st_size

    ##  Returns the modification time of the file, in seconds since the epoch.

    def modtime (self):
        return os.stat(self.to_filename()).st_mtime

    ##  Returns the current user's relation to the file: 'owner', 'group', or 'other'.

    def my_relation (self):
        return self._my_relation1(os.stat(self.to_filename()))

    def _my_relation1 (self, s):
        if s.st_uid == os.getuid(): return 'owner'
        elif s.st_gid in os.getgroups(): return 'group'
        else: return 'other'

    def _Xable (self, forwhom, u, g, o):
        s = os.stat(self.to_filename())
        m = s.st_mode
        if forwhom == 'me': forwhom = self._my_relation1(s)
        if forwhom == 'owner': return m & u
        elif forwhom == 'group': return m & g
        elif forwhom == 'other': return m & o
        else: raise Exception('Bad forwhom: %s' % forwhom)

    ##  Whether the file is readable.

    def readable (self, forwhom='me'):
        return self._Xable(forwhom, stat.S_IRUSR, stat.S_IRGRP, stat.S_IROTH)

    ##  Whether it is writable.

    def writable (self, forwhom='me'):
        return self._Xable(forwhom, stat.S_IWUSR, stat.S_IWGRP, stat.S_IWOTH)

    ##  Whether it is executable.

    def executable (self, forwhom='me'):
        return self._Xable(forwhom, stat.S_IXUSR, stat.S_IXGRP, stat.S_IXOTH)

    ##  The permissions value: an int representing a 3-digit octal number.

    def permissions (self):
        return stat.filemode(os.stat(self.to_filename()).st_mode)

    ##  The MD5 hash of the file.

    def md5 (self, silent=False):
        if not silent: print('Computing md5 hash for', self, '...', end='')
        sys.stdout.flush()
        s = subprocess.getoutput('openssl md5 < ' + self.to_filename())
        if s.startswith('(stdin)= '):
            s = s[9:]
        if not silent: print(' ok')
        return s

    ##  Whether the file has dir as an ancestor.

    def is_under (self, dir):
        return (self.host == dir.host and
                self.user == dir.user and
                self.pathname.startswith(dir.pathname))

    ##  Execute the file using os.system().

    def __call__ (self):
        return os.system(self.to_filename()) == 0


    #--  Modifications  --------------------

    def _actionmask (self, s, action, forwhom):
        w = 0
        if isinstance(forwhom, str): forwhom = [forwhom]
        for name in forwhom:
            if name == 'me': name = self._my_relation1(s)
            if name == 'all': w |= (stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            elif name == 'owner': w |= stat.S_IRWXU
            elif name == 'group': w |= stat.S_IRWXG
            elif name == 'other': w |= stat.S_IRWXO
            else: raise Exception('Bad name: %s' % name)
        a = 0
        if 'r' in action:
            a |= (stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        if 'w' in action:
            a |= (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
        if 'x' in action:
            a |= (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return w & a

    ##  Change permissions to allow the given action: 'r', 'w', 'x'.
    #   @arg forwhom - may be 'me', 'owner', 'group', 'other', or 'all'.

    def permit (self, action, forwhom='me', recurse=False, silent=False):
        return self._chmod('permit', action, forwhom, recurse, silent)

    ##  Change permissions to disallow the given action.

    def deny (self, action, forwhom='all', recurse=False, silent=False):
        return self._chmod('deny', action, forwhom, recurse, silent)

    def _chmod (self, change, action, forwhom, recurse, silent):
        if not silent: pprint(change.title(), self, action, forwhom)
        fn = self.to_filename()
        s = os.stat(fn, follow_symlinks=False)
        mask = self._actionmask(s, action, forwhom)

        # specifying 'me' on a recursive call chooses owner/group/other
        # based on ownership of top file; may be wrong if lower files have
        # different owners

        if recurse and self.isdir():
            for (dir, subdirs, files) in os.walk(fn):
                self._chmod1(change, dir, mask)
                for name in files:
                    fn = os.path.join(dir, name)
                    self._chmod1(change, fn, mask)
        else:
            self._chmod1(change, fn, mask, s)
        
    def _chmod1 (self, change, fn, mask, s=None):
        if s is None: s = os.stat(fn, follow_symlinks=False)
        if change == 'permit': mode = (s.st_mode | mask)
        elif change == 'deny': mode = (s.st_mode & ~mask)
        else: raise Exception('Bad change: %s' % change)
        os.chmod(fn, mode, follow_symlinks=False)

    ##  Create any missing directories above this file.

    def assure_parent (self):
        dir = os.path.dirname(self.to_filename())
        if not os.path.exists(dir):
            os.makedirs(dir)

    ##  Create this directory, including any missing directories above it.
    #   Prints out a message.  Can get just the message and not the action
    #   by setting DryRun = True.

    def make_directory (self, silent=False):
        global DryRun
        if not self.exists():
            if not silent: pprint('Make Directory', self)
            fn = self.to_filename()
            if DryRun: return
            os.makedirs(fn)

    ##  Copy this file to the target.  Can be disabled by DryRun.

    def copy_to (self, tgt, silent=False):
        global DryRun
        if not silent: pprint('Copy File', self, tgt)
        if self.is_remote() and tgt.is_remote():
            raise Exception('Not implemented: copying remote to remote')
        if DryRun: return
        if self.is_remote():
            server = _intern_server(self.host, self.user)
            server.get(self.pathname, local=tgt.to_filename())
        elif tgt.is_remote():
            server = _intern_server(tgt.host, tgt.user)
            server.put(self.to_filename(), remote=tgt.pathname)
        else:
            shutil.copyfile(self.to_filename(), tgt.to_filename())

    ##  Copy the source file to this one.  Can be disabled by DryRun.

    def copy_from (self, src, silent=False):
        src.copy_to(self, silent)
    
    ##  Rename this file.  Can be disabled by DryRun.

    def move_to (self, tgt, silent=False):
        global DryRun
        if not silent: pprint('Move File', self, tgt)
        if self.is_remote() or tgt.is_remote():
            raise Exception('Only local moves are possible')
        if DryRun: return
        shutil.move(self.to_filename(), tgt.to_filename())

    ##  Delete this file.  Can be disabled by DryRun.

    def delete_file (self, silent=False):
        if not silent: pprint('Delete File', self)
        if DryRun: return
        if self.is_remote():
            server = _intern_server(self.host, self.user)
            server('rm ' + self.pathname)
        else:
            os.unlink(self.to_filename())
    
    ##  Delete this directory, if it is empty, error otherwise.  Can be disabled
    #   by DryRun.

    def delete_empty_directory (self, silent=False):
        if not silent: pprint('Delete Empty Directory', self)
        if DryRun: return
        if self.is_remote():
            server = _intern_server(self.host, self.user)
            server('rmdir ' + self.pathname)
        else:
            os.unlink(self.to_filename())
    
    ##  Delete the directory hierarchy rooted here.
    #   Use with caution!
    
    def delete_hierarchy (self, silent=False):
        if self.is_remote():
            raise Exception('Not implemented: remote delete hierarchy')
        if not silent: pprint('Delete Hierarchy', self)
        top = self.to_filename()
    
        if DryRun: return
    
        if os.path.islink(top):
            os.unlink(top)
    
        elif os.path.isdir(top):
            for (dir, subdirs, files) in os.walk(top, topdown=False):
                for name in files:
                    fn = os.path.join(dir, name)
                    os.unlink(fn)
                # symbolic links to dirs show up here
                for name in subdirs:
                    fn = os.path.join(dir, name)
                    if os.path.islink(fn):
                        os.unlink(fn)
                os.rmdir(dir)

        else:
            os.unlink(top)

    ##  Same as delete_hierarchy(), but no error if the directory has already
    #   been deleted.  Also, refuses to delete the root directory.

    def clear (self, silent=False):
        if self.is_local() and self.exists():
            if not self.pathname or self.pathname == '/':
                raise Exception('Attempt to delete root')
            if self.isdir():
                self.delete_hierarchy(silent)
            else:
                self.delete_file(silent)

    ##  Same as clear(), but will even change the file permissions to override
    #   the lack of write permission.  Use with extreme caution.

    def nuke (self, silent=False):
        self.permit('w', 'me', recurse=True, silent=silent)
        self.parent().permit('w', 'me', silent=silent)
        self.clear(silent=silent)


##  Expand out a wildcard (*) by looking for an existing file matching the pattern.

def instantiate_pathname (orig):

    # if the * is in a directory name, we want the unique directory, even
    #     if the full pathname does not exist
    # from the end, in case there are multiple wildcards
        
    i = orig.rfind('*')
    if i < 0:
        return orig
    else:
        j = orig.find('/', i+1)
        if j > 0:
            suffix = orig[j:]
            fn = orig[:j]
        else:
            suffix = ''
            fn = orig
        alts = glob(fn)
        if len(alts) != 1:
            return orig
        return alts[0] + suffix

##  Returns the first pathname component.

def first_component (fn):
    i = fn.find('/')
    if i < 0: return fn
    else: return fn[:i]

def _make_writable (self, fn):
    if not os.path.islink(fn):
        mode = os.lstat(fn).st_mode
        os.chmod(fn, mode | 0o200)

            
##  Shorthand for Location.
def L (s): return Location(s)

# ##  The Seal destination directory, as a Location.
# Dest = L(__dest__)
# 
# ##  The Seal python directory, as a Location.
# Seal = L(__seal__)
# 
# ##  The Seal bin directory, a Location.
# Bin = Dest/'bin'
# 
# ##  The Seal examples directory, a Location.
# Examples = L(ex)
# 
# ##  The Seal data directory, a Location.
# Data = L(data)

##  The /tmp directory, as a Location.
Tmp = L('/tmp')


#--  TabularFile  --------------------------------------------------------------

##  A tabular file.

class TabularFile (object):

    ##  Constructor.
    #   Separator of None means any whitespace on read, single space on write.

    def __init__ (self, loc, mode='r', encoding=None, separator='\t'):

        ##  Location.
        self.location = loc

        ##  Mode.
        self.mode = mode

        ##  Character encoding.
        self.encoding = encoding

        ##  Field separator.
        self.separator = separator

        ##  Stream.
        self.file = None

    ##  Enter.

    def __enter__ (self):
        self.file = self.location.open(self.mode)
        return self

    ##  Exit.

    def __exit__ (self, t, v, tr):
        self.file.close()
        self.file = None

    ##  Returns self.

    def __iter__ (self):
        return self

    ##  Iterator method.

    def __next__ (self):
        return next(self.file).rstrip('\r\n').split(self.separator)

    ##  Like print().

    def write (self, *args):
        sep = self.separator or ' '
        last = len(args) - 1
        for (i, arg) in enumerate(args):
            self.file.write(str(arg))
            if i == last: self.file.write('\n')
            else: self.file.write(sep)


#--  Open  ---------------------------------------------------------------------

##  Wraps around stdin or stdout.

class PseudoFile (object):

    ##  Constructor.

    def __init__ (self, file):
        ##  File.
        self.file = file

    ##  Write to the file.

    def write (self, s):
        self.file.write(s)

    ##  Returns self.

    def __iter__ (self):
        return self

    ##  Iterator method.

    def __next__ (self):
        return self.file.__next__()

    ##  Enter.

    def __enter__ (self):
        return self

    ##  Exit.

    def __exit__ (self, t, v, tr):
        pass


##  Accepts '-' as filename, representing stdin/stdout.

def open (fn, mode='r', **kwargs):
    if fn == '-':
        if mode.startswith('r'): return PseudoFile(sys.stdin)
        else: return PseudoFile(sys.stdout)
    else:
        return _open(fn, mode, **kwargs)


#--  BackingSave  --------------------------------------------------------------

##  Handles locking (only).

class BackingAdmin (object):

    ##  Constructor.

    def __init__ (self, fn):

        ##  The filename.
        self.filename = fn

        ##  The lock, when locked.
        self.lock = None

    ##  Lock the file.

    def __enter__ (self):
        self.lock = open(fn + '.lock', 'w')
        flock(self.lock, LOCK_EX)
        return self

    ##  Release the lock.

    def __exit__ (self, type, value, tb):
        self.lock.close()
    
    ##  Replace the file with the backup version.

    def undo (self):
        bakfn = self.filename + '.bak'
        if not os.path.exists(bakfn):
            raise Exception('No undo information available: %s' % fn)
        if os.path.exists(self.filename):
            os.replace(self.filename, self.filename + '.redo')
        os.replace(bakfn, self.filename)

    ##  Restore the old version after an undo.

    def redo (self):
        redofn = self.filename + '.redo'
        if not os.path.exists(redofn):
            raise Exception('No redo information available')
        bakfn = self.filename + '.bak'
        if os.path.exists(self.filename):
            if os.path.exists(bakfn):
                os.unlink(bakfn)
            os.replace(self.filename, bakfn)
        os.replace(redofn, self.filename)


##  Handles backup and locking.

class BackingSave (object):

    ##  Constructor.

    def __init__ (self, fn, binary=False, makedirs=False):

        ##  Filename.
        self.filename = fn

        ##  The file.
        self.file = None

        ##  Whether to create missing directories.
        self.makedirs = makedirs

        ##  Whether it is a binary file.
        self.binary = binary

        ##  Write to a temp file, only touch the protected file if all writes
        #   complete successfully.
        self.tmp = fn + '.tmp'

        ##  The lock, while locked.
        self.lock = None

    ##  Enter.  Create any missing directories.  Lock the file.
    #   Open the temp file.  Return the temp file.

    def __enter__ (self):
        dir = os.path.dirname(self.filename)
        # if filename contains no slash, dir is ''
        if dir and not os.path.exists(dir):
            if self.makedirs:
                os.makedirs(dir)
            else:
                raise Exception('Directory does not exist: %s' % dir)
        self.lock = open(self.filename + '.lock', 'w')
        flock(self.lock, LOCK_EX)
        if self.binary: mode = 'wb'
        else: mode = 'w'
        self.file = open(self.tmp, mode)
        return self.file

    ##  Close the temp file.  If no error occurred, move the current
    #   file to backup and move the temp file into its place.
    #   If an error occurred, just delete the temp file.
    #   Release the lock.

    def __exit__ (self, type, value, traceback):
        self.file.close()
        if type is None:
            bak = self.filename + '.bak'
            if os.path.exists(bak):
                os.unlink(bak)
            if os.path.exists(self.filename):
                shutil.move(self.filename, bak)
            shutil.move(self.tmp, self.filename)
        else:
            if os.path.exists(self.tmp):
                os.unlink(self.tmp)
        self.lock.close()


#--  Indented lines  -----------------------------------------------------------

def _split_indent (line):
    i = 0
    while i < len(line) and line[i] == ' ':
        i += 1
    return (i, line[i:] if i > 0 else line)

def indented_lines (f):
    for line in f:
        line = line.strip('\r\n')
        yield _split_indent(line)


#--  KV format  ----------------------------------------------------------------
#
#  Values:
#      |    String, to end of line.
#      NUM  float or int; begins with +, -, or digit.
#      :    Object or list.  The type is determined by the first record.
#      {}   Empty object.
#      []   Empty list.
#      
#  An object consists of key-value pairs.
#  A list consists of values.
#
#  At beginning of file, or after a record whose value is ':', we are in "first-child" mode.
#  If the record begins with a key, the parent is an object.
#  If the file begins with a value, the parent is a list.
#  Otherwise, error.
#
#  Parent is the object that we are working on.
#  Parent_indent is parent's indentation.
#  Current_indent is the indentation for the current parent's *children*.
#  For the first child, current_indent is None.
#
#  If the parent is an object, the current record must be key-value.
#  If the parent is a list, the current record must be a value.
#
#  When the value is in ':', create a new parent.
#  Push the old parent and its indentation on the stack.
#

class KVISyntaxError (Exception): pass

def _kvexception (loc, msg):
    (fn, lno) = loc
    return KVISyntaxError(f'[{fn}:{lno}] {msg}')

def _kverror (loc, msg):
    raise _kvexception(loc, msg)
    
def _split_key_value (line):
    if not line[0].isalpha():
        return (None, line)
    i = 1
    while not (i >= len(line) or line[i].isspace()):
        i += 1
    if i == len(line):
        return (line, '')
    key = line[:i]
    while i < len(line) and line[i].isspace():
        i += 1
    return (key, line[i:])

def _parse_value (loc, value, parentpath):
    if not value:
        _kverror(loc, 'Empty value')
    elif value[0].isspace():
        _kverror(loc, 'Indentation must consist of spaces only')
    elif value[0] == '|':
        return value[1:]
    elif value == ':T':
        return True
    elif value == ':F':
        return False
    elif value == '-':
        return None
    elif value in ('{}', '{}:'):
        return {}
    elif value in ('[]', '[]:'):
        return []
    elif value == ':':
        return None
    elif value[0] in '/.~':
        if not (value.startswith('/') or
                value.startswith('./') or
                value.startswith('../') or
                value.startswith('~/') or
                value in ('.', '..', '~')):
            _kverror(loc, 'Illegal pathname')
        return value
    else:
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except:
            raise _kvexception(loc, 'Illegal numeric value') from None

def read_kvi (f, filename=None):
    path = Path(filename).parent if filename else Path('.')
    roots = [None]
    stack = []
    parent_loc = (roots, 0)
    parent = None
    parent_indent = -1
    current_indent = None

    for (lno, (indent, line)) in enumerate(indented_lines(f), 1):
        loc = (filename, lno)
        if not line or line.startswith('#'):
            continue

        (key, value) = _split_key_value(line)

        # first child?
        if parent is None:
            parent = [] if key is None else {}
            (gp,k) = parent_loc
            gp[k] = parent

        if current_indent is None:
            if indent <= parent_indent:
                _kverror(loc, 'Illegal indentation: <= parent_indent')
            current_indent = indent
            
        # end of parent
        while indent < current_indent:
            if not stack:
                _kverror(loc, 'Illegal indentation: empty stack')
            current_indent = parent_indent
            (parent, parent_indent) = stack.pop()

        if indent != current_indent:
            _kverror(loc, 'Illegal indentation: > current_indent')

        # process record
        if key is None:
            if not isinstance(parent, list):
                _kverror(loc, 'Expecting a key-value pair')
            key = len(parent)
            parent.append(None)
        else:
            if not isinstance(parent, dict):
                _kverror(loc, 'Expecting a simple value')
            if key in parent:
                _kverror(loc, f'Key {key} is not unique')

        if not value:
            _kverror(loc, 'Missing value')

        parent[key] = parsed_value = _parse_value(loc, value, path)

        # push
        if value in (':', '[]:', '{}:'):
            parent_loc = (parent, key)
            stack.append((parent, parent_indent))
            parent = parsed_value
            parent_indent = current_indent
            current_indent = None

    return roots[0]

def load_kvi (fn, **kwargs):
    with open(fn, **kwargs) as f:
        return read_kvi(f, filename=fn)

def isdictlike (x):
    return hasattr(x, 'items')

def islistlike (x):
    return hasattr(x, '__iter__') and not isdictlike(x)

def write_kvi (x, f):
    if isdictlike(x):
        _write_dict_contents(x, f, 0)
    elif islistlike(x):
        _write_list_contents(x, f, 0)
    else:
        raise Exception('Contents of KVI must be a dict or list')

def _write_dict_contents (x, f, indent):
    for (k,v) in x.items():
        f.write(' ' * indent)
        f.write(k)
        f.write(' ')
        _write_value(v, f, indent)

def _write_list_contents (x, f, indent):
    for v in x:
        f.write(' ' * indent)
        _write_value(v, f, indent)

def _write_value (x, f, indent):
    if isinstance(x, dict):
        if len(x) == 0:
            f.write('{}\n')
        else:
            f.write('{}:\n')
            _write_dict_contents(x, f, indent + 2)
    elif isinstance(x, (list, tuple)):
        if len(x) == 0:
            f.write('[]\n')
        else:
            f.write('[]:\n')
            _write_list_contents(x, f, indent + 2)
    elif isinstance(x, str):
        if '\n' in x:
            raise Exception('Value may not contain newline')
        f.write('|')
        f.write(x)
        f.write('\n')
    elif isinstance(x, bool):
        f.write(':T\n' if x else ':F\n')
    elif isinstance(x, (int, float)):
        f.write(str(x))
        f.write('\n')
    elif x == None:
        f.write('-\n')
    else:
        raise Exception('Illegal object type for KVI')

def save_kvi (x, fn, **kwargs):
    with open(fn, 'w', **kwargs) as f:
        write_kvi(x, f)


#--  File Formats  -------------------------------------------------------------

class FileFormat (object):

    def __init__ (self, name=None, read=None, write=None, encoding=None):
        self.name = name
        self.read = read
        self.write = write
        self.encoding = encoding

    def load (self, fn):
        if self.encoding is False:
            mode = 'rb'
            enc = None
        else:
            mode = 'r'
            enc = self.encoding
        with open(fn, mode, encoding=enc) as f:
            return self.read(f)
            
    def parse (self, s):
        with StringIO(s) as f:
            return self.read(f)

    def save (self, x, fn):
        if self.encoding is False:
            mode = 'wb'
            enc = None
        else:
            mode = 'w'
            enc = self.encoding
        with open(fn, mode, encoding=enc) as f:
            self.write(x, f)


def _read_lines (f):
    return [line.rstrip('\r\n') for line in f]

def _write_lines (lines, f):
    for line in lines:
        f.write(line)
        f.write('\n')

def _read_tabular (f):
    return [line.rstrip('\r\n').split('\t') for line in f]

def _write_tabular (recs, f):
    for rec in recs:
        f.write('\t'.join(rec))
        f.write('\n')

LineFormat = FileFormat('lines', _read_lines, _write_lines)
TabularFormat = FileFormat('tabular', _read_tabular, _write_tabular)
KVIFormat = FileFormat('kvi', read_kvi, write_kvi)
JsonFormat = FileFormat('json', json.load, json.dump)
BlockFormat = FileFormat('blocks', read_record_blocks, write_record_blocks)
