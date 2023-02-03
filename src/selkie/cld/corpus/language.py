##  @package seal.cld.corpus.language
#   A language.

import os
from seal.core.io import pprint
from seal.cld.db.meta import MetaPropList
from seal.cld.db.file import PropDict
from seal.cld.db.dir import Directory, Structure
from seal.cld.corpus.env import CorpusMixin
from seal.cld.corpus.lexicon import Lexicon
from seal.cld.corpus.text import Toc, Text


##  Language info.  Currently, just a list of orthographies.

class LanguageInfo (MetaPropList):

    ##  Metadata properties: just 'orthographies'.
    property_names = ('orthographies',)


#--  Language  -----------------------------------------------------------------

##  Language.

class Language (CorpusMixin, Structure):

    ##  Maps child name to class.
    signature = {'texts': Toc,
                 'lexicon': Lexicon}

    ##  Which suffixes are included in the index, to provide direct access by ID.
    indexed = ('txt',)

    __metadata__ = Structure.__metadata__ + (('_info', LanguageInfo),)


    ##  Constructor.

    def __init__ (self, **kwargs):
        Structure.__init__(self, **kwargs)
        self._dbentry = None

    def create_env (self):
        env = CorpusMixin.create_env(self)
        env['language'] = self
        return env

    ##  Language 3-character code.

    def id (self): return self.name()

    ##  Long name.

    def fullname (self): return self.dbentry().name

    ##  The info.

    def info (self): return self._info

    ##  Synonym for info.

    def metadata (self): return self._info

    ##  The database entry for this language.

    def dbentry (self):
        if self._dbentry is None:
            from seal.data.langdb import languages
            self._dbentry = languages[self.name()]
        return self._dbentry

    ##  A list of texts.

    def all_texts (self):
        return self.env.index().files('txt')

    #- Global resources ------------------------------------
    #  These implement the corresponding CLDObject methods
    #
    
    ##  The orthographies of this language.  Accessible via the env for
    #   all descendants of the language instance.

    def orthographies (self):
        s = self._info.get('orthographies') or ''
        return [w.strip() for w in s.split(',')]

    ##  The default orthography, a string.  Accessible via the env for
    #   all descendants of the language instance.

    def default_orthography (self):
        return self.orthographies()[0] or 'default'

    ##  The romanization corresponding to the default orthography.
    #   Accessible via the env for
    #   all descendants of the language instance.

    def romanization (self):
        return self.env.require_rom(self.default_orthography())

    ##  Get the filename for the text with the given ID.  Looks it up in the index.

    def get_text (self, id):
        return self.env.index().file('txt', id)
        

#--  LanguageList  -------------------------------------------------------------

##  A list of languages.

class LanguageList (Directory):

    ##  The children are Languages.
    childtype = Language

#     def import_allocate (self, name):
#         tab = self.contents()
#         if name in tab:
#             return tab[name]
#         else:
#             with self.writer() as w:
#                 return w.intern(name)
