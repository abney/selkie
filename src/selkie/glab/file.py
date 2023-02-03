##  @package seal.cld.glab.file
#   GLab notebooks.

import os
from collections import namedtuple, OrderedDict
from ..io import BackingSave, BackingAdmin
from ..object import Object
from ..db.disk import writer
from ..db.meta import Metadata
from ..db.file import File
from ..db.dir import Directory


#--  Encode, decode  -----------------------------------------------------------

_charmap = {'\t': ' ',
            '\r': ' ',
            '\n': ' ',
            '\f': ' ',
            '\v': ' ',
            '\u2000': ' ',
            '\u2001': ' ',
            '\u2002': ' ',
            '\u2003': ' ',
            '\u2004': ' ',
            '\u2005': ' ',
            '\u2006': ' ',
            '\u2007': ' ',
            '\u2008': ' ',
            '\u2010': '-',
            '\u2011': '-',
            '\u2012': '-',
            '\u2013': '-',
            '\u2014': '-',
            '\u2015': '-',
            '\u2016': '|',
            '\u2018': "'",
            '\u2019': "'",
            '\u201a': "'",
            '\u201b': "'",
            '\u201c': '"',
            '\u201d': '"',
            '\u201e': '"',
            '\u201f': '"',
            '\u2022': '.',
            '\u2024': '.',
            '\u2027': '.',
            '\u2039': '<',
            '\u203a': '>',
            '\u2208': '@', # element of
            '\u220a': '@',
            '\u2219': '.',
            '\u222a': '+', # union
            '\u2229': '&', # intersection
            '\u2212': '-', # minus
            '\u2254': ':=',
            '\u22c5': '.',
            '\u2286': ':<', # subset
            '\u2287': ':>', # superset
            '\u2223': '|',
            '\u2205': '_0_'
            }


def _encode_text (text):
    bytes = bytearray()
    for c in text:
        if c in _charmap:
            s = _charmap[c]
            for c in s:
                bytes.append(ord(c))
        else:
            n = ord(c)
            if n < 32:
                raise Exception('Control character encountered in text: %s' % unicodedata.name(c))
            if n >= 127:
                raise Exception('Non-ascii character encountered in text: %s' % unicodedata.name(c))
            bytes.append(n)
    return bytes.decode('ascii')

def _digest_text (text):
    bs = bytearray(len(text))
    
def _encode_title (title):
    return '#T ' + _encode_text(title)

def _read_title (f):
    line = next(f).rstrip('\r\n')
    if line.startswith('#T '): line = line[3:]
    return line.strip()


#--  Notebook  -----------------------------------------------------------------

##  Extract the title of a notebook from the file.

def notebook_title (fn):
    with open(fn) as f:
        return _read_title(f)


##  A GLab notebook.

class Notebook (File):

    ##  Character encoding is 'ascii'.
    encoding = 'ascii'

#    Contents = namedtuple('Contents', ['title', 'texts'])

    ##  Read contents from a stream.

    def __read__ (self, f):
        try:
            self._title = _read_title(f)
            self._texts = [line.rstrip('\r\n') for line in f if not line.startswith('#')]
        except StopIteration:
            self._title = 'Untitled'
            self._texts = []

    ##  Iterate over lines to be written.

    def output_lines (self):
        self.require_load()
        yield _encode_title(self._title)
        for text in self._texts:
            yield _encode_text(text)

    ##  Write the contents to a stream.

    def __write__ (self, f):
        for line in self.output_lines():
            f.write(line)
            f.write('\n')
        redofn = self._contents_filename() + '.redo'
        if os.path.exists(redofn):
            os.unlink(redofn)

    ##  Get the title.

    def title (self):
        self.require_load()
        return self._title
    
    ##  Get the texts.

    def texts (self):
        self.require_load()
        return self._texts

    ##  Undo.

    def undo (self):
        with BackingAdmin(self._contents_filename()) as adm:
            adm.undo()

    ##  Redo.

    def redo (self):
        with BackingAdmin(self._contents_filename()) as adm:
            adm.redo()

    #--  Writing  ----------------------------------------------

    ##  Set the title.

    def set_title (self, title):
        lib = self.parent()
        with writer(self, lib):
            self.modified()
            self._title = title
            if lib is not None:
                lib.titles().update(self)

    ##  Set the texts.

    def set_texts (self, texts):
        with writer(self):
            if len(texts) < len(self._texts) - 1:
                raise Exception('Shrinking texts by more than one')
            self.modified()
            self._texts = texts

    # next two - not update library?

    ##  Delete the i-th text.

    def delete_text (self, i):
        with writer(self):
            self.modified()
            del self._texts[i]

    ##  Insert a text at i.

    def insert_text (self, i, text=''):
        with writer(self):
            self.modified()
            self._texts[i:i] = [text]

    ##  Append a text at the end.

    def append_text (self, text):
        with writer(self):
            self.modified()
            self._texts.append(text)


#--  NotebookList  -------------------------------------------------------------
#
#  This is used so that we do not have to open all notebook files in order to
#  get a title listing.
#


##  An entry in the title list.  Elements are 'id', 'title', 'public'.
TitleListEntry = namedtuple('TitleListEntry', ['id', 'title', 'public'])


##  A title list.

class TitleList (Metadata):

    ##  Read the contents from a stream.

    def __read__ (self, f):
        self._table = tab = OrderedDict()
        for line in f:
            (id, title, public) = line.rstrip('\r\n').split('\t')
            public = (public == 'True')
            tab[id] = TitleListEntry(id, title, public)

    ##  Write the contents to a stream.

    def __write__ (self, f):
        for rec in self._table.values():
            print(rec.id, rec.title, str(rec.public), sep='\t', file=f)

    ##  Iterate over the titles.

    def __iter__ (self):
        self.require_load()
        return self._table.values().__iter__()

    ##  Update the title entry for the given notebook.

    def update (self, nb):
        with self.writer():
            self.modified()
            id = nb.name()
            if id in self._table:
                public = self._table[id].public
            else:
                public = False
            self._table[id] = TitleListEntry(id, nb.title(), public)

    ##  Delete a title.

    def delete (self, id):
        with self.writer():
            self.modified()
            del self._table[id]


#--  Library  ------------------------------------------------------------------

##  A Library contains the notebooks belonging to a single user.
#
#   env.glab_library(user) returns the Library for the given user.
#
#   A Library contains a _public file listing those notebooks that
#   have been published, and a _private file giving the titles of unpublished
#   notebooks.

class Library (Directory):

    ##  Child type is Notebook.
    childtype = Notebook

    ##  Metadata.
    __metadata__ = Directory.__metadata__ + (('_titles', TitleList),)


    ##  The titles.

    def titles (self):
        return self._titles

    ##  Allocate a name.  Overrides the Directory method.

    def allocate_name (self, suffix):
        assert suffix == 'gn'
        maxid = 0
        for id in self:
            id = int(id)
            if id > maxid: maxid = id
        return str(maxid + 1)

    ##  Whether the given notebook is public.

    def is_public (self, id):
        titles = self.titles()
        if id in titles:
            return titles[id].public
        else:
            return False

    ##  Create a new notebook.

    def new_child (self, name=None, suffix=None, cls=None, i=None):
        child = Directory.new_child(self, name, suffix, cls, i)
        self._titles.update(child)
        return child

    ##  Duplicate a notebook.

    def dup_notebook (self, id):
        old = self[id]
        nb = self.new_child()
        titles = self._titles
        with writer(nb, titles):
            nb.set_title(old.title())
            nb.set_texts(old.texts())
            titles.update(nb)
        return nb

    ##  Delete a notebook.

    def delete_child (self, id):
        Directory.delete_child(self, id)
        titles = self._titles
        with writer(titles):
            titles.delete(id)


#--  GLabDirectory  ------------------------------------------------------------

##  A GLab directory.
#   Contains one subdirectory per user

class GLabDirectory (Directory):

    ##  The child type is Library.
    childtype = Library

    ##  Add users.

    def add_users (self, names):
        for name in names:
            if name not in self._children:
                lib = self.new_child(name=name)
                lib.permissions().add(name, 'editors')

    ##  Delete users.

    def delete_users (self, names):
        for name in names:
            if name in self._children:
                lib = self._children[name]
                lib.delete()
