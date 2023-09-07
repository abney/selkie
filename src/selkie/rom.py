##  \package seal.nlp.rom
#   Romanizers.
#
#   Romanized text can always contain the following escapes:
# 
#       \\(xxx xxx)  Unicode characters
#       \\\          Literal backslash
#       \\c=aaa      Define c as a code for romanization aaa.  c must be UNDEFINED.
#       \\c          Set romanization to the one with code c.  c must be defined.
#       \\!          Unset romanization.
#       \\:          Silently ignored, can be used to terminate aaa
#       \\<EOF>      Silently ignored
#       \\Z          Silently ignored
#      
#    - c   - any single lowercase character.
#    - aaa - any characters except backslash, space, or newline.
#    - xxx - any number of hexadecimal digits.
#    - Z   - any single character other than lowercase letter, left paren, backslash, or colon.
#
#   N.b., \\c=aaa is interpreted as \\c followed by literal =aaa if c is defined.
#
#   DECODING
#
#   A romanization consists of a list of key-value pairs.  Keys may not
#   contain backslash, but may contain any other ASCII characters.
#   At each point in the input:
#
#     - If the next character is \\, it is interpreted as an escape.  It
#       is silently discarded if the following characters do not yield
#       a valid escape sequence.
#
#     - If a key matches, the longest matching key is replaced with its
#       value.
#
#     - Otherwise, a single character is passed unchanged to the output.
#
#   ENCODING
#
#   The input potentially contains non-ASCII characters, and the ouput
#   should contain only ASCII characters, such that decoding will yield
#   the input.  At each point in the input:
#
#     - If a value matches, the longest matching value is replaced with
#       the corresponding key.  However, if some prefix of the key when
#       combined with the suffix of the previous output would give an
#       overlapping key, then \\: is output before outputting the key.
#      
#     - If the next character is backslash, it is replaced with \\\\.
#
#     - If the next character is not ASCII, it is replaced with a numeric
#       code.
#
#     - Otherwise the next character is passed through unchanged.  However,
#       if combining the character with the suffix of the previous output
#       completes a key, \\: is output first.
#
#   ROMANIZATION
#
#   A romanization is internalized as a state sequence.  States are
#   accessed using single ASCII characters, and the return value is
#   a new state or None.  A state may also be associated with an output
#   value.
#

import os, codecs
from os.path import exists
from io import StringIO
from codecs import CodecInfo
from .io import ispathlike, byte_infile, byte_outfile, contents, FileFormat
from .com import shift
from .data import path as datapath
from . import config

default_registry = None


#--  Romanization file  --------------------------------------------------------

def load_romfile (fn):
    with open(fn, 'rb') as f:
        return read_romfile(f)

# Since this is returned from inside 'with open', it should not be a generator
# that requires the file to be open

def read_romfile (f):
    return list(_read_romfile_1(f))

def _read_romfile_1 (f):
    for line in f:
        line = line.rstrip(b'\r\n')
        if line.startswith(b'#') or not line:
            continue
        (key, value) = line.split(b'\t')
        yield (key, value)


#--  Romanization  -------------------------------------------------------------

##  State in the romanization dictionary.

class State (dict):

    ##  Constructor.

    def __init__ (self):
        dict.__init__(self)

        ##  Non-null if this state corresponds to a valid code.
        self.value = None


##  A romanization.

class Romanization (object):

    ##  Constructor.

    def __init__ (self, name=None, fn=None):

        ##  Its name.
        self.name = name

        ##  Filename.
        self.filename = fn

        ##  Start state.
        self.start = None

        if fn: self.load(fn)

    ##  Load from file.  Called by the constructor.

    def load (self, fn):
        decode = Decoder()
        for (key, value) in load_romfile(fn):
            self[key] = decode(value)

    ##  Store an association.

    def __setitem__ (self, key, value):
        if not key: raise Exception('Empty key')
        if value is None: raise Exception('Null value')
        if self.start is None: self.start = State()
        q = self.start
        i = 0
        for c in key:
            if c < 0x20 or c > 0x7f:
                raise Exception('Control or non-ASCII character in key: %s' % key)
            if c == 0x5c:
                raise Exception('Backslash in key: %s' % key)
            if c in q:
                q = q[c]
            else:
                next = State()
                q[c] = next
                q = next
        if q.value is None:
            q.value = value
        else:
            raise Exception('Duplicate key: %s' % key)

    def items (self):
        return load_romfile(self.filename)

    def __str__ (self):
        return contents(self.filename)

    ##  Print out the state graph.

    def print_graph (self):
        todo = [self.start]
        stateno = {id(self.start): 1}
        while todo:
            q = todo[0]
            del todo[0]
            print(stateno[id(q)])
            for c in sorted(q):
                next = q[c]
                j = id(next)
                if j not in stateno:
                    stateno[j] = len(stateno)+1
                    todo.append(next)
                print("   %d ('%s')" % (c, chr(c)), stateno[j])
            if q.value:
                print('    value=', repr(q.value))

    ##  Match an input.  Returns a pair (j, value).

    def match (self, input, i=0):
        q = self.start
        value = None
        j = None

        while i < len(input) and q is not None and input[i] in q:
            q = q[input[i]]
            i += 1
            if q.value is not None:
                value = q.value
                j = i

        return (j, value)
    
    ##  Decode an input.

    def decode (self, input, output=None, errors='strict', registry=None):
        try:
            decoder = Decoder(rom=self, registry=registry)
            return decoder(input, output)
        except Exception as e:
            if errors == 'strict':
                raise UnicodeDecodeError(str(e))
            elif errors == 'ignore':
                pass
            else:
                raise Exception('Bad value for errors: %s' % errors)

    ##  Decode in the form expected by CodecInfo.

    def std_decoder (self, input, errors='strict'):
        s = self.decode(input, errors=errors)
        return (s, len(input))


#--  as_bytes  -----------------------------------------------------------------

##  If the input is a string,
#   convert it to bytes using the ASCII codec.
#   Otherwise, assume it is bytes and leave it alone.
#   (Python sometimes passes memory objects that are not instances of
#   bytes or bytesarray; no easy way to distinguish that from a bad argument.)

def as_bytes (s):
    if isinstance(s, str):
        return s.encode('ascii')
    else:
        return s

##  Return the i-th character, or -1 if i is beyond the end of the string.

def peek (s, i):
    if i < len(s): return s[i]
    else: return -1


#--  Decoder  ------------------------------------------------------------------

##  A decoder.  The main entry points are __call__() and match_escape().

class Decoder (object):

    ##  Constructor.

    def __init__ (self, rom=None, registry=None):
        global default_registry
        if registry is None:
            registry = default_registry
        if isinstance(rom, str):
            rom = registry[rom]
        assert rom is None or isinstance(rom, Romanization)

        ##  The registry, needed if the romanization is given by name,
        #   and for romanization changes in the input.
        self.registry = registry

        ##  The current romanization, may be None.
        self.rom = rom

        ##  Table of romanizations.  Keys are single-character codes.
        self.roms = {}

        ##  1 if inside \( ... ), 0 otherwise.
        self.state = 0

    ##  Main entry point.
    #   \arg input:  a byte-like object or an ASCII string.  Non-ascii characters
    #         will cause an encoding error to be raised.
    #   \arg rom:    a romanization or a string naming a romanization.
    #   \arg output: an output stream or None.  If None, a string will be returned.

    def __call__ (self, input, output=None):
        input = as_bytes(input)
        if output is None:
            with StringIO() as output:
                self.transduce(input, output)
                return output.getvalue()
        else:
            self.transduce(input, output)

    ##  Transduce input to output.

    def transduce (self, input, output):
        i = 0
        while i < len(input):
            (j, s) = self.match(input, i)
            i = j
            output.write(s)

    ##  Parse the input.  Returns two values: a list of points marking the beginnings of
    #   matched tokens, and the output string.

    def parse (self, input):
        input = as_bytes(input)
        i = 0
        t = 0
        points = [(0,0)]
        with StringIO() as output:
            while i < len(input):
                (i, s) = self.match(input, i)
                output.write(s)
                t += len(s)
                points.append((i,t))
            if self.state != 0: self.error(input, i, 'Incomplete input')
            return (points, output.getvalue())

    ##  Get the longest match at position i.

    def match (self, input, i):
        c = input[i]

        # in the middle of \( ... )?
        if self.state == 1:

            # if space, there's another code point
            if c == 0x20:
                i += 1
                return self.scan_code_point(input, i)

            # if right paren, we're done
            elif c == 0x29: # right paren
                self.state = 0
                return (i+1, '')

            else:
                self.error(input, i, 'Expected space or right paren')

        # if c is a backslash, decode an escape sequence
        elif c == 0x5c:
            return self.match_escape(input, i)

        else:
            j = None
            if self.rom: (j, s) = self.rom.match(input, i)

            # the rom matched
            if j is not None: return (j, s)

            # no rom, or no match; pass through the input character
            else: return (i+1, chr(c))

    ##  Print an error message, including input position, and raise an exception.

    def error (self, input, i, msg):
        print('**', msg)
        print('Input:', repr(input[0:i]), repr(input[i:]))
        print('i=', i)
        raise Exception(msg)

    ##  Scan a backslash escape.  Advance i, write to out.
    #   May change rom.

    def match_escape (self, input, i):
        i += 1 # the triggering backslash

        # will be -1 at EOF
        c = peek(input, i)

        # \<EOF>
        if c < 0:
            return (i, '')

        # escaped backslash
        elif c == 0x5c:
            return (i+1, '\\')

        # \:
        elif c == 0x3a: # colon
            return (i+1, '')

        # \(
        elif c == 0x28: # left paren
            i += 1
            self.state = 1
            return self.scan_code_point(input, i)

        # \0
        elif c == 0x30:
            self.rom = self.registry.get('default') or Romanization()
            return (i+1, '')

        # \c or \c=aaa.
        elif c >= 0x61 and c <= 0x7a: # in range a-z
            code = c
            i += 1

            # \c is defined, use it.
            if code in self.roms:
                self.rom = self.roms[code]
                return (i, '')

            # \c is not defined, define it.
            else:
                c = peek(input, i)
                if c != 0x3d: self.error('Expecting =')
                i += 1
                # terminated by backslash, space, or nl
                (i, name) = self.scan_name(input, i)
                # consume the space or newline
                if peek(input, i) != 0x5c: i += 1
                rom = self.registry.get(name)
                if rom is None: self.error(input, i, 'No such romanization: %s' % name)
                self.roms[code] = rom
                return (i, '')
    
        # anything else is silently ignored
        else:
            return (i+1, '')

    ##  Called following \\(.
    #   Reads a block of hex digits, translates to character.

    def scan_code_point (self, input, i):
        j = i
        c = peek(input, j)
        # digit, A-F, a-f
        while ((c >= 0x30 and c <= 0x39) or
               (c >= 0x41 and c <= 0x46) or
               (c >= 0x61 and c <= 0x66)):
            j += 1
            c = peek(input, j)
        if j == i: self.error(input, i, 'Empty code point')
        return (j, chr(int(input[i:j], base=16)))

    ##  Scan the aaa following c=aaa.
    #   Returns a string.

    def scan_name (self, input, i):
        # name terminated by backslash, space, newline
        j = i
        while (j < len(input) and
               input[j] not in [0x20, 0x5c, 0x0a]):
            j += 1
        if i == j: self.error(input, i, 'Empty name')
        return (j, input[i:j].decode('ascii'))


##  Decode input.  Instantiates Decoder and calls it.

def decode (input, rom=None, output=None, registry=None):
    d = Decoder(rom, registry)
    return d(input, output)


#--  To Html  ------------------------------------------------------------------

##  Convert to a bytes object.  Printable ASCII characters, tab, newline, and
#   carriage return are passed through.  All other characters are replaced with
#   HTML character entities of form &#...;
#   Returns a pair: the bytes object and the length of the input string.

def to_html_1 (s):
    out = bytearray()
    for c in s:
        n = ord(c)
        # 0x09 = tab, 0x0a = newline, 0x0d = cr
        if (n >= 0x20 and n <= 0x7e) or n in [0x09, 0x0a, 0x0d]:
            out.append(n)
        else:
            out.extend(ord(c) for c in ('&#%d;' % n))
    return (bytes(out), len(s))

##  Calls to_html_1() and returns just the bytes object.

def to_html (s):
    (b,n) = to_html_1(s)
    return b


#--  Registry  -----------------------------------------------------------------

##  A table of romanizations.
#   Romanization and Decoder only use the methods get() and __getitem__().
#   They are expected to return Romanizations.

class Registry (object):

    ##  Constructor.

    def __init__ (self, path):
        # backwards compatibility
        if isinstance(path, str):
            path = [path]

        for d in path:
            assert ispathlike(d)

        ##  A list of directory filenames to search for rom files.
        self.path = path

        ##  Cache romanizations that have been loaded.
        #   A 'default' romanization is always available.
        self.cache = {'default': Romanization('default')}

    ##  Convert a name to a '.rom' filename that exists in one of the
    #   path directories.  Returns None if no existing rom file is found.

    def find_filename (self, name):
        for d in self.path:
            fn = os.path.join(d, name + '.rom')
            if exists(fn):
                return fn

    ##  Load a named romanization, ignoring the cache.

    def load (self, name):
        fn = self.find_filename(name)
        if fn:
            return Romanization(name, fn)
        else:
            raise Exception(f'No such rom file: {name}')

    ##  Get the romanization with the given name, loading it from file
    #   if it exists and is not already cached.

    def get (self, name):
        if name in self.cache:
            return self.cache[name]
        else:
            fn = self.find_filename(name)
            if fn:
                rom = Romanization(name, fn)
                self.cache[name] = rom
                return rom
    
    ##  Get the named romanization, signalling an error if it does not exist.

    def __getitem__ (self, name):
        if isinstance(name, Romanization): return name
        rom = self.get(name)
        if rom is None:
            raise KeyError('Romanization not found: %s' % repr(name))
        return rom

    ##  Whether the named romanization exists.

    def __contains__ (self, name):
        return name in self.cache or self.find_filename(name)

    ##  Iterate over all valid romanization names.  Does not load them.

    def __iter__ (self):
        for d in self.path:
            if os.path.exists(d):
                for name in os.listdir(d):
                    if name.endswith('.rom'):
                        yield name[:-4]


def _create_default_registry ():
    path = ['.']
    try:
        path = config['data']['rompath']
    except:
        pass
    path.append(datapath('roms'))
    return Registry(path)
    
##  The seal registry.
default_registry = _create_default_registry()

##  Backwards compatibility.

def require_rom (name):
    global default_registry
    return default_registry[name]

##  Backwards compatibility.

def rom_filename (name):
    global default_registry
    return default_registry.filename(name)

##  Backwards compatibility.

def load_rom (name):
    global default_registry
    return default_registry.load(name)

##  Backwards compatibility.

def find_rom (name):
    global default_registry
    return default_registry.get(name)

##  Find or create a codec from the named romanization.

def find_codec (name):
    global default_registry
    if name == 'html':
        return CodecInfo(to_html_1, None, name='html')
    else:
        rom = default_registry.get(name)
        if rom:
            return CodecInfo(None,
                             rom.std_decoder,
                             name=name)

codecs.register(find_codec)


#--  RomFormat  ----------------------------------------------------------------

RomFormat = FileFormat('rom', read_romfile, encoding=False)


#--  Main  ---------------------------------------------------------------------

##  Main function.
#   Argument: [INFILE].
#   Flags:
#
#       -d DIR - set the registry directory.
#       -h - set the output encoding to 'html'.
#       -o FN - specify the output filename.
#       -r ROM - specify a romanization.
#
#   Uses the named romanization to decode the input to the output.

def main ():
    global default_registry
    registry = default_registry
    rom = None
    outenc = 'utf8'
    infile = '-'
    outfile = '-'
    while shift.isflag():
        flag = shift()
        if flag == '-d':
            registry = Registry(shift())
        elif flag == '-h':
            outenc = 'html'
        elif flag == '-o':
            outfile = shift()
        elif flag == '-r':
            rom = shift()
        else:
            shift.error('Bad flag: %s' % flag)
    if not shift.isdone():
        infile = shift()
    shift.done()

    decoder = Decoder(rom=rom, registry=registry)
    instream = byte_infile(infile)
    outstream = byte_outfile(outfile)
    for line in instream:
        line = decoder(line)
        line = line.encode(outenc)
        outstream.write(line)
    outstream.close()

if __name__ == '__main__':
    main()
