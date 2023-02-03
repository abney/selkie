##  @package seal.cld.corpus.rom

import os, seal.nlp.rom
from seal.core.io import load_dict, pprint
from seal.nlp.rom import Decoder, find_rom, reg as global_registry
from seal.cld.db.file import File
from seal.cld.db.dir import Directory


##  A romanization.  It is a transduction represented as a list of
#   mappings from codes to unicode text.  It is internally compiled
#   into a seal.nlp.rom.Romanization.

class Romanization (File):

    ##  Signals an error if type is not 'rom'.

    def check_type (self, type):
        if type != 'rom':
            raise Exception('Fails type check: %s %s' % (type, self))

    ##  Read one from file.

    def __read__ (self, f):
        self._table = table = {}
        for line in f:
            (k,v) = line.rstrip('\r\n').split('\t')
            table[k] = v
        self._make_rom()

    def _make_rom (self):
        self._rom = rom = seal.nlp.rom.Romanization(self.parent(), self.name())
        decode = Decoder()
        for (key, value) in self._table.items():
            key = key.encode('ascii')
            value = decode(value.encode('ascii'))
            rom[key] = value

    ##  Decode the given bytes, returning a unicode string.

    def decode (self, b):
        self.require_load()
        return self._rom.decode(b)

    ##  Fetch a mapping pair by index.

    def __getitem__ (self, i):
        self.require_load()
        return self._table.__getitem__(i)

    ##  The number of mapping pairs.

    def __len__ (self):
        self.require_load()
        return self._table.__len__()

    ##  Iterate over (code, output) pairs.

    def items (self):
        self.require_load()
        return self._table.items()

    ##  Returns the actual romanization that this File wraps.

    def romanization (self):
        self.require_load()
        return self._rom

    ##  Return a Decoder constructed from this romanization.

    def decoder (self):
        self.require_load()
        return Decoder(rom=self._rom)

    ##  Add a mapping pair.

    def __setitem__ (self, k, v):
        with self.writer():
            self.modified()
            self._table[k] = v

    ##  Write the contents to an open file.

    def __write__ (self, f):
        for (k,v) in self._table.items():
            f.write(k)
            f.write('\t')
            f.write(v)
            f.write('\n')
        self._make_rom()


##  A romanization that cannot be modified.  It does not contain

class ReadOnlyRomanization (object):

    ##  Constructor.

    def __init__ (self, rom):
        self._rom = rom

    ##  Signals an error if type is not 'rom'.

    def check_type (self, type):
        if type != 'rom':
            raise Exception('Fails type check: %s %s' % (type, self))

    ##  Decode a byte sequence.

    def decode (self, s):
        return self._rom.decode(s)

    ##  Returns a decoder based on this romanization.

    def decoder (self):
        return Decoder(rom=self._rom)

    ##  Returns the actual romanization that this File wraps.

    def romanization (self):
        return self._rom

    ##  Signals an error.

    def __setitem__ (self, k, v):
        raise Exception('Read-only romanization')

    ##  String representation.

    def __repr__ (self):
        return '<ReadOnlyRomanization %s>' % self._rom.name


##  A directory containing romanizations.

class Registry (Directory):

    ##  The child type is Romanization.
    childtype = Romanization

    ##  Unlike get, this method also returns read-only romanizations:
    #   for 'default' and romanizations that are in the global registry.

    def find_rom (self, name):
        if name == 'default':
            return ReadOnlyRomanization(seal.nlp.rom.Romanization())
        elif name in self:
            return self[name]
        else:
            rom = find_rom(name)
            if rom is not None:
                return ReadOnlyRomanization(rom)

    ##  Calls find_rom(), but signals an error on failure.

    def require_rom (self, name):
        rom = self.find_rom(name)
        if rom is None:
            raise Exception('Romanization not found: %s' % name)
        return rom
