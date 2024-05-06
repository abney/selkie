##  \package seal.cld.corpus.export_file
#   Manipulating export files directly, without a corpus.

from os import makedirs
from os.path import exists, join, dirname


##  A block of records representing a single item.  (Items are languages,
#   lexicons, texts, romanizations, or glab notebooks.)

class Block (object):

    ##  Constructor.  The argument is the 'I' record that starts the block.

    def __init__ (self, rec):

        ##  The records constituting the block, including the 'I' record.
        self.records = [rec]

    ##  Append another record.

    def append (self, rec):
        self.records.append(rec)

    ##  The type, from the 'I' record.  May be 'language', 'lexicon', 'text',
    #   'rom, or 'notebook'.

    def type (self):
        return self.records[0][1]

    ##  The directory portion (subcorpus) of the global ID.  May be a
    #   language code, 'roms', or 'glab'.

    def directory (self):
        return self.records[0][2]

    ##  The item name within the subcorpus.

    def name (self):
        return self.records[0][3]

    ##  The global ID, of form directory/name.

    def id (self):
        return '%s/%s' % (self.directory(), self.name())

    ##  The total length in characters of all records in the block.
    #   Since the representation is ASCII, that is also the total length in bytes.

    def file_size (self):
        total = 0
        for rec in self.records:
            for field in rec:
                total += len(field) + 1
        return total

    ##  Print readably.

    def print_contents (self):
        for rec in self.records:
            print('\t'.join(rec))

    ##  Extract this item.  That is, write it to the filename dir/subcorpus/name.
    #   If dir is not provided, write to subcorpus/name.

    def extract (self, dir=None):
        if dir is None:
            dir = self.directory()
        else:
            dir = join(dir, self.directory())
        fn = join(dir, self.name())
        print('Writing', fn)
        # because glab notebook names contain slashes
        dir = dirname(fn)
        if not exists(dir):
            makedirs(dir)
        with open(fn, 'w') as f:
            for rec in self.records:
                f.write('\t'.join(rec))
                f.write('\n')

    ##  An iteration over the records.

    def __iter__ (self):
        return self.records.__iter__()


##  A reader for ef files.

class Reader (object):

    ##  Constructor.  Takes the filename of the ef file, with '-' for stdin.

    def __init__ (self, filename):

        ##  The filename.
        self.filename = filename

        ##  The open stream, when inside a 'with' statement.
        self.stream = None

        ##  Whether to close on exit or not.
        self.close_on_exit = None

        ##  Whether currently at EOF or not.
        self.at_eof = False

        ##  The next record to return.
        self.lookahead = None

    ##  Enter the 'with' statement.  Opens the file and sets close_on_exit to True
    #   unless the file is stdin.

    def __enter__ (self):
        if self.filename == '-':
            self.stream = stdin
            self.close_on_exit = False
        else:
            self.stream = open(self.filename, 'r')
            self.close_on_exit = True
        self.at_eof = False
        self.lookahead = None
        return self

    ##  Exit.  Close the file if it is not stdin.

    def __exit__ (self, t, v, tb):
        if self.close_on_exit:
            self.stream.close()
        self.stream = None
        self.close_on_exit = None

    ##  Returns self.

    def __iter__ (self):
        return self

    ##  Returns the next record without consuming it.

    def peek (self):
        if self.lookahead is None and not self.at_eof:
            try:
                line = next(self.stream)
                self.lookahead = line.rstrip('\r\n').split('\t')
            except StopIteration:
                self.at_eof = True
        return self.lookahead

    ##  Discards the next record.

    def advance (self):
        self.lookahead = None

    ##  Returns the next record and calls advance().

    def next_record (self):
        rec = self.peek()
        self.advance()
        if rec is None:
            raise StopIteration
        else:
            return rec

    ##  Iterator method.  Returns a record.

    def __next__ (self):
        rec = self.next_record()
        if rec[0] == 'Z':
            raise StopIteration
        elif rec[0] != 'I':
            raise Exception("Expecting an 'I' record")
        block = Block(rec)
        while True:
            rec = self.peek()
            if rec is None or rec[0] in 'ZI':
                break
            self.advance()
            block.append(rec)
        return block


##  An export (ef) file.

class ExportFile (object):

    ##  Constructor.  Uses a Reader to read the contents of the ef file into memory.

    def __init__ (self, filename):

        ##  The filename.
        self.filename = filename

        ##  A table mapping global IDs to record blocks, for random access.
        self.tab = {}

        ##  Sequential list of all record blocks.
        self.blocks = []

        with Reader(filename) as f:
            for block in f:
                self.blocks.append(block)
                id = block.id()
                if id in self.tab:
                    print('** Multiple items with ID %s' % repr(id))
                self.tab[id] = block

    ##  Iterate over the blocks sequentially.

    def __iter__ (self):
        return self.blocks.__iter__()

    ##  Whether the given global ID corresponds to an existing item.

    def __contains__ (self, id):
        return self.tab.__contains__(id)

    ##  Get the item corresponding to the given ID.

    def __getitem__ (self, id):
        return self.tab.__getitem__(id)

    ##  The number of blocks (items).

    def __len__ (self):
        return self.blocks.__len__()

    ##  Print a listing of items.

    def print_listing (self):
        for block in self.blocks:
            print('%-8s %10d %s' % (block.type(), block.file_size(), block.id()))

    ##  Print a single item given its ID.

    def print_item (self, id):
        block = self.tab[id]
        block.print_contents()

    ##  Extract all items, writing them to files.

    def extract_all (self, dir=None):
        for block in self.blocks:
            block.extract(dir)
