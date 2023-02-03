##  @package seal.cld.corpus.env
#   The CorpusEnvironment.

import os
from os.path import abspath, expanduser
from seal.core import sh
from seal.app import Config
from seal.cld.db.env import Environment
from seal.cld.corpus.user import UnknownUser
from seal.cld.corpus.media import MediaDirectory


#--  CorpusMixin  --------------------------------------------------------------

##  A corpus that may be embedded in another corpus.  Languages are subcorpora.
#   This is here and not in core because core imports language.

class CorpusMixin (object):

    ##  Create a CorpusEnvironment.

    def create_env (self):
        return CorpusEnvironment(self)


#--  Environment  --------------------------------------------------------------

#  Old __init__ method:
# 
#     def __init__ (self, host, username=None, context=None, media=None, **kwargs):
#         if context is not None:
#             if username is None:
#                 username = context.username
#             if media is None:
#                 media = context.config.get('media_dir')
# 
#         Environment.__init__(self, host, **kwargs)
#         if host.isroot():
#             if username:
#                 env['username'] = username
#             if media:
#                 fn = os.path.abspath(os.path.expanduser(media))
#                 env['media'] = MediaDirectory(fn, self)


##  The corpus environment, a specialization of Environment.

class CorpusEnvironment (Environment):

    ##  Constructor.

    def __init__ (self, host):
        Environment.__init__(self, host)
        self._media = None

    ##  Set the context.
    def set_context (self, context):
        if context.username is not None:
            self._table['username'] = context.username
        mfn = context.config.get('media_dir')
        if mfn:
            self.set_media(mfn)

    ##  The argument is a filename.  Use it to create a MediaDirectory
    #   and store the MediaDirectory as the value of 'media' in the table.
    def set_media (self, mfn):
        mfn = abspath(expanduser(mfn))
        self._table['media'] = MediaDirectory(mfn, self)

    ##  The corpus.
    def corpus (self): return self._table['root']

    ##  The registry of romanizations.
    def registry (self): return self.corpus().roms

    ##  Fetch a romanization by name.
    def require_rom (self, name): return self.registry().require_rom(name)

    ##  Fetch a romanization by name, returning None if it does not exist.
    def find_rom (self, name): return self.registry().find_rom(name)

    ##  The user name.
    def username (self): return self._table['username']

    ##  The media directory (a string).
    def media (self): return self._table.get('media')

    ##  The GLab library filename.
    def glab_library (self, name): return self.user(name).glab.public

    ##  Get a text by ID.
    def get_text (self, id): return self.index().file('txt', id)

    ##  Return the current language.  Not available at the root, only within
    #   languages.
    def language (self): return self._table['language']

    ##  Return the current language's lexicon.  Not available at the root, only
    #   within languages.
    def lexicon (self): return self.language().lexicon

    ##  Return the current language's orthographies.  Not available at the root.
    def orthographies (self): return self.language().orthographies()

    ##  Return the current language's default orthography.  Not available at the root.
    def default_orthography (self): return self.language().default_orthography()

    ##  Return the current language's default romanization.  Not available at the root.
    def romanization (self): return self.language().romanization()

    ##  Get a user by name.  Returns the authenticated user if no name is provided.

    def get_user (self, name=None, allow_unknown=True):
        if name is None:
            name = self._table['username']
        return self.corpus().users.get(name, allow_unknown)

    ##  Intern a (possibly new) user.

    def intern_user (self, name):
        # this also interns the name in groups()
        return self.corpus().users.intern(name)

    ##  Return the paragraph that has the given PARID.  A PARID is a pair of
    #   text ID and text-relative paragraph ID.

    def deref_parid (self, parid):
        (t,p) = parid
        text = self.get_text(t)
        return text.plaintext().by_id(p)
