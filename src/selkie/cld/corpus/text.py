##  @package seal.cld.corpus.text
#   The classes Text, Toc, Translation.

import os
from seal.core.io import pprint
from seal.core.misc import difference, uniq
from seal.cld.db.disk import writer
from seal.cld.db.meta import MetaPropList
from seal.cld.db.file import File, Strings
from seal.cld.db.dir import Directory, Structure
from seal.cld.corpus.token import TokenFile, TranslationUnits, TransTokenFile
from seal.cld.corpus.media import MediaFile
from seal.cld.corpus.transcript import Transcription
#from seal.cld.corpus.audio import AudioDirectory


#--  Toc  ----------------------------------------------------------------------

##  A complex text made up of other texts.

class Toc (Directory):

    ##  Child type is Text.
    childtype = None # set below

    ##  Constructor.

    def __init__ (self, *args, **kwargs):
        Directory.__init__(self, *args, **kwargs)
        parent = self.parent()
        if isinstance(parent, Text): self._text = parent
        else: self._text = None

    ##  Return the Text that this belongs to.
    #   The 'texts' child of a Language is a Toc without a Text.

    def text (self): return self._text

    ##  The parent toc.

    def parent_toc (self):
        if self._text is not None:
            parent = self._text.parent()
            # shouldn't actually have to test, but we're being safe
            if isinstance(parent, Toc):
                return parent

    ##  The TID.

    def id (self):
        if self._text is not None:
            return self._text.id()

    ##  The text's metadata.

    def metadata (self): return self.parent().metadata()

    ##  The text's permissions.

    def permissions (self): return self.parent().permissions()

    ##  The text's title.

    def title (self):
        if self._text is None:
            return '%s Texts' % self.parent().name()
        else:
            return self._text._info.get('title') or 'Untitled'

    ##  Transfer some children to the next toc up.

    def eject_children (self, indices, leftward):
        parent_toc = self.parent_toc()
        if parent_toc is None:
            raise Exception('No parent toc')
        tgt_index = parent_toc.index(self._text)
        if not leftward: tgt_index += 1

        with writer(self):
            index = self.env.index()
            with writer(parent_toc, index):
                self.modified()
                parent_toc.modified()
                # precompute as list, because the next loop will spoil indices
                selected = [self._contents[i] for i in indices]
                for child in selected:
                    child.reparent(parent_toc, i=tgt_index)
                    tgt_index += 1

#     def import_allocate (self, name):
#         with self.writer() as w:
#             (i, child) = w.new_child()
#         return child


#--  Translation  --------------------------------------------------------------

##  Effectively, an infinite list of strings aligned to the units of an
#   external Text.

class Translation (Strings):

    ##  The number of units in the external text.

    def __len__ (self):
        return len(self._parent.plaintext())

    ##  Get the i-th translation.

    def __getitem__ (self, i):
        self.require_load()
        pars = self._value
        if i < 0: raise IndexError('Cannot handle negative indices')
        elif i < len(pars): return pars[i]
        else: return ''

    ##  Iterate over the translations.  Stops when it reaches the last
    #   non-empty translation, which may be before (or after) the end of
    #   the external text.

    def __iter__ (self):
        self.require_load()
        pars = self._value
        n = len(self)
        for par in pars:
            if n <= 0: break
            yield par
            n -= 1
        while n > 0:
            yield ''
            n -= 1


#--  TextInfo  -----------------------------------------------------------------

##  Metadata information for a text.

class TextInfo (MetaPropList):

    ##  Properties are author, title, orthography, type, subtype.
    property_names = ('author', 'title', 'orthography', 'type', 'subtype')


#--  Text  ---------------------------------------------------------------------

##  A text.  This is a shell around the contents, which may be tokenized text,
#   with or without a translation, a media file, with or without transcription,
#   or a TOC.
#
#   A text has a plaintext rendering if its type is 'orig', or if its type is
#   'media' and it has a transcription.  A plaintext is conceptually a list of
#   <i>(translation) units</i> that are typically sentences but may be just words,
#   or may be whole paragraphs.

class Text (Directory):

    ##  Maps child names to types.
    signature = {'orig': TokenFile,
                 'trans': Translation,
                 'media': MediaFile,
                 #'audio': AudioDirectory,
                 'xscript': Transcription,
                 'toc': Toc}

    __metadata__ = Directory.__metadata__ + (('_info', TextInfo),)


    ##  Type.  One of: 'toc', 'orig', 'media', 'stub'.

    def type (self):
        if 'toc' in self: return 'toc'
        elif 'orig' in self: return 'orig'
        elif 'media' in self: return 'media'
        #elif 'audio' in self: return 'audio'
        else: return 'stub'

    ##  The TID.

    def id (self): return self.name()

    ##  The language it belongs to.  Texts are monolingual.

    def language (self): return self.env.language()

    ##  The lexicon of its language.

    def lexicon (self): return self.env.lexicon()

    ##  The metadata.

    def info (self): return self._info

    ##  The title, from the metadata.

    def title (self): return self.info()['title'] or 'Untitled'

    ##  The author, from the metadata.

    def author (self): return self.info()['author']

    ##  The orthography, from the metadata.

    def orthography (self):
        return self.info()['orthography'] or self.env.default_orthography()

    ##  The romanization, from the orthography.

    def romanization (self):
        return self.env.require_rom(self.orthography())

    ##  The plaintext contents, if this is a leaf text.
    #   If the type is 'orig', the plaintext is a TokenFile.
    #   If the type is 'media' and it has a transcription, the plaintext
    #   is a TransTokenFile.

    def plaintext (self):
        if 'orig' in self: return self['orig']
        elif 'media' in self:
            xs = self.get('xscript')
            if xs is not None:
                return TransTokenFile(xs)
        #elif 'audio' in self:
        #    tr = self['audio'].get('transcript')
        #    if tr is not None:
        #        return TranslationUnits(tr)

    ##  The source text.  If the type is 'orig', the source text is the
    #   TokenFile.  If the type is 'media', then the source text is the
    #   TokenFile inside the Transcription.  In the latter case, the segmentation
    #   in the source text does not agree with the segmentation in the plaintext.

    def sourcetext (self):
        if 'orig' in self: return self.orig
        elif 'media' in self: return self.xscript.transcript
        #elif 'audio' in self: return self.audio.transcript
        
    #--  Hierarchy  --------------------------------------------

    ##  An attempt to attach a child here will attach it to my toc,
    #   which must exist.

    def attachment_target (self):
        toc = self.toc
        if toc.exists():
            return toc
        else:
            raise Exception('Not a valid target for attachment')

    #--  Writing  ----------------------------------------------

    ##  Create a 'toc' child.

    def create_toc (self):
        return self.new_child(name='toc')

    ##  Set the i-th unit in the TokenFile.

    def set_orig (self, i, s):
        # if self.file.audio: raise Exception('Read only')
        n = len(self.orig)
        if i >= n: raise IndexError('Out of bounds: i=%d, n=%d' % (i,n))
        self.orig[i] = s

    ##  Set the translation of the i-th unit.

    def set_trans (self, i, s):
        n = len(self.orig)
        if i >= n: raise IndexError('Out of bounds: i=%d, n=%d' % (i,n))
        if 'trans' not in self:
            self.new_child('trans')
        self.trans[i] = s

    ##  Insert a new unit.

    def insert_par (self, i, s):
        if 'orig' not in self:
            self.new_child('orig')
        orig = self.orig
        n = len(orig)
        if i is None: i = n
        elif i > n: raise IndexError('Out of bounds: i=%d, n=%d' % (i,n))
        orig.insert(i, s)
        if 'trans' in self:
            self.trans.insert(i, '')

    ##  Add a new unit at the end.

    def append_par (self, s=''):
        if 'orig' not in self:
            self.new_child('orig')
        self.insert_par(len(self.orig), s)

    ##  Delete a unit.

    def delete_par (self, i):
        #if self.audio: raise Exception('Read only')
        del self.orig[i]
        if 'trans' in self:
            del self.trans[i]

    ##  Set the j-th token of the i-th unit.

    def set_token (self, i, j, s):
        # if self.audio: raise Exception('Read only')
        self.orig.set_token(i, j, s)


Toc.childtype = Text
