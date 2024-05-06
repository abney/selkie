##  @package seal.cld.corpus.drill
#   Seal.cld.corpus.course is the bare beginning of a replacement.
#   This is older code that used a special file that contained lessons.
#   Though maybe that's not a bad idea.

import random, sys, curses


#--  Reader  -------------------------------------------------------------------

##  Reader for a lesson file.

class Reader (object):

    ##  Constructor.

    def __init__ (self, fn, commands=None):

        ##  Current line number.
        self.lno = 0

        ##  The open file.
        self.stream = open(fn)

        ##  Commands.
        self.commands = commands or []

    ##  It's an iterator.

    def __next__ (self):
        while True:
            self.lno += 1
            line = next(self.stream)
            line = line.rstrip('\r\n')
            if line in self.commands: return line
            i = line.find('#')
            if i >= 0: line = line[:i]
            if not line: continue
            fields = line.split('\t')
            if len(fields) != 2:
                raise Exception("Line %d: wrong number of fields" % self.lno)
            return fields


#--  Text  ---------------------------------------------------------------------

##  A text.

class Text (object):

    ##  Constructor.

    def __init__ (fn):

        ##  The target-language sentences.
        self.target_sents = []

        ##  The gloss-language sentences.
        self.gloss_sents = []

        ##  The target-language word set.
        self.target_lex = set()

        ##  The gloss-language word set.
        self.gloss_lex = set()

#    for (tgt, gloss) in Reader(fn):
        

#--  Drill  --------------------------------------------------------------------

##  A Drill.

class Drill (object):

    ##  Constructor.  Takes a lesson file.

    def __init__ (self, fn):

        ##  List of lessons.
        self.lessons = []

        ##  The current lesson.
        self.current = None

        lesson = None
        block = None
        reader = Reader(fn, commands=('#LESSON', '#BLOCK'))
        try:
            while True:
                line = next(reader)
                if line == '#LESSON':
                    lesson = self.new_lesson()
                    block = None
                elif line == '#BLOCK':
                    if lesson is None:
                        raise Exception('Line %d: no lesson' % reader.lno)
                    block = lesson.new_block()
                else:
                    if block is None:
                        raise Exception('Line %d: no block' % reader.lno)
                    block.append(line)
        except StopIteration:
            pass

    ##  Create a new lesson.

    def new_lesson (self):
        lesson = Lesson(self, len(self.lessons))
        self.lessons.append(lesson)
        return lesson

    ##  Fetch an item.  Key is (n,i) where n is lesson number and i is item number.

    def __getitem__ (self, key):
        (i, j) = key
        return self.lessons[i][j]

    ##  Return the next item and advance.

    def __next__ (self):
        if self.current is None:
            self.current = self.first()
        else:
            self.current = next(self.current)
        return self.current
            
    ##  Return the first item.

    def first (self):
        return self.lessons[0].first()


##  A lesson.

class Lesson (object):

    ##  Constructor.

    def __init__ (self, drill, i):

        ##  The drill this belongs to.
        self.drill = drill

        ##  The lesson number.
        self.index = i

        ##  The lesson blocks.
        self.blocks = []

    ##  Create a new block.

    def new_block (self):
        block = Block(self, len(self.blocks))
        self.blocks.append(block)
        return block

    ##  Fetch a block.

    def __getitem__ (self, i):
        return self.blocks[i]

    ##  The first block.

    def first (self):
        return self.blocks[0]

    ##  Return the next block and advance.

    def __next__ (self):
        i = self.index + 1
        if i < len(self.drill.lessons):
            return self.drill.lessons[i]
        else:
            raise StopIteration

    ##  String representation.

    def __repr__ (self):
        return '<Lesson %d>' % self.index


##  A block.

class Block (object):
    
    ##  Constructor.

    def __init__ (self, lesson, i):

        ##  The lesson it belongs to.
        self.lesson = lesson

        ##  Its index in the lesson.
        self.index = i

        ##  The target-language/glossing-language pairs.
        self.pairs = []
        
    ##  Add a new pair.

    def append (self, pair):
        self.pairs.append(pair)

    ##  Run.  Shuffles the pairs before going through them.

    def run (self, reverse=False):
        pairs = list(self.pairs)
        random.shuffle(pairs)
        for pair in pairs:
            if reverse: pair = (pair[1], pair[0])
            print()
            print(pair[0])
            response = input(' : ')
            if response == pair[1]:
                print('Right')
            else:
                print('No, should be:', pair[1])

    ##  Returns the next pair and advances.

    def __next__ (self):
        i = self.index + 1
        if i < len(self.lesson.blocks):
            return self.lesson.blocks[i]
        else:
            return next(self.lesson).first()

    ##  String representation.

    def __repr__ (self):
        return '<Block %d %d>' % (self.lesson.index, self.index)
