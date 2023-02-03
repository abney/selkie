##  @package seal.cld.corpus.course
#   The Drill class.

import os
from seal.cld.db.file import File
from seal.cld.corpus.lexicon import parse_lexid


# class Course (File):
# 
#     def load (self): return CourseContents(self)
# 
# 
# class CourseContents (object):
# 
#     def __init__ (self, crsfile):
#         self.file = crsfile
#         self.language = crsfile.language()
#         self.filename = fn = crsfile.filename()
#         self.lessons = []
#         if os.path.exists(fn):
#             with open(fn) as f:
#                 for line in f:
#                     ids = line.rstrip('\r\n').split()
#                     self.lessons.append(Lesson(self, ids))
# 
#     def __len__ (self): return self.lessons.__len__()
#     def __getitem__ (self, i): return self.lessons.__getitem__(i)
#     def __iter__ (self): return self.lessons.__iter__()
#     def __bool__ (self): return bool(self.lessons)
# 
# 
# class Lesson (object):
# 
#     def __init__ (self, crs, ids):
#        self.course = crs
#        self.index = len(crs.lessons)
#        self.lexents = []
#        lexicon = crs.language.lexicon()
#        for id in ids:
#            key = parse_lexid(id)
#            if key in lexicon:
#                self.lexents.append(lexicon[key])
# 
#     def __getitem__ (self, i): return self.lexents.__getitem__(i)
#     def __iter__ (self): return self.lexents.__iter__()
#     def __len__ (self): return self.lexents.__len__()
#     def __bool__ (self): return bool(self.lexents)


# A selection is a list of Items
# An Item is a wordlist page and an index into the wordlist


##  Very crude vocabulary drill.

class Drill (object):

    ##  Constructor.

    def __init__ (self, page):

        ##  The page containing the vocabulary.
        self.page = page

        ##  Location in the vocabulary.
        self.index = None

        ##  The user.
        self.user = page.user()

        textid = page.id()
        ctextid = self.user.props.get('text')
        if ctextid == textid:
            i = self.user.props.get('index')
            if i is None: self.index = 0
            else: self.index = int(i)
        else:
            self.index = 0

    ##  Go to the next vocabulary item.

    def advance (self):
        n = len(self.page)
        i = self.index + 1
        if i >= n: i = 0
        self.index = i
        with self.user.props.writer() as w:
            w['text'] = self.page.id()
            w['index'] = str(i)

    ##  Returns the current form.

    def form (self):
        return str(self.page.orig[self.index])

    ##  Returns the current glosses.

    def glosses (self):
        return self.page.trans[self.index]
