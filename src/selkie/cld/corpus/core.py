##  @package seal.cld.corpus.core
#   The Corpus class.

from os.path import expanduser, join, exists
from seal.core import sh
from seal.app.config import Config
from seal.core.io import pprint
from seal.cld.db.meta import MetaPropList
from seal.cld.db.file import File, PropDict
from seal.cld.db.dir import Structure
from seal.cld.db.core import open_database
from seal.cld.corpus.rom import Romanization, Registry
from seal.cld.corpus.user import User, UserList
from seal.cld.corpus.export import ExportStream, ImportStream
from seal.cld.corpus.language import Language, LanguageList
from seal.cld.corpus.lexicon import Lexicon
from seal.cld.corpus.env import CorpusMixin
from seal.cld.corpus.media import MediaFile, MediaIndex, MediaDirectory
from seal.cld.corpus.transcript import ClipsFile, ParagraphFile, Transcription
from seal.cld.corpus.text import Text, Toc, Translation
from seal.cld.corpus.token import TokenFile
from seal.cld.glab.file import GLabDirectory, Library, Notebook


#--  Corpus  -------------------------------------------------------------------

##  The corpus metadata.  Behaves like a dict.

class CorpusPropList (MetaPropList):
    
    ##  The permissible dict keys.

    property_names = ('title', 'desc')


##  The CLD application file.

class Corpus (CorpusMixin, Structure):

    ##  A dict mapping file suffix to class.
    types = {'cl': ClipsFile,
             'gd': GLabDirectory,
             'gl': Library,
             'gn': Notebook,
             'lg': Language,
             'll': LanguageList,
             'lx': Lexicon,
             'mf': MediaFile,
             'mi': MediaIndex,
             'pd': PropDict,
             'pp': ParagraphFile,
             'reg': Registry,
             'rom': Romanization,
             'tf': TokenFile,
             'toc': Toc,
             'tr': Translation,
             'txt': Text,
             'ul': UserList,
             'usr': User,
             'xs': Transcription
             }

    # indexed = (Text,)

    ##  A dict mapping child names to classes.
    signature = {'langs': LanguageList,
                 'users': UserList,
                 'roms': Registry,
                 'glab': GLabDirectory}

    ##  Metadata
    __metadata__ = Structure.__metadata__ + (('_meta', CorpusPropList),)


    ##  The configuration file.  Only if this is a root corpus.

    def config (self):
        assert self.parent() is None
        return Config(join(self.filename(), '_config'))

    ##  The metadata object.

    def metadata (self):
        return self._meta

    ##  Filename.

    def filename (self):
        return self.env['filename']

    ##  Callback for setting the metadata.

    def set_metadata (self, title, desc, owners, editors, shared):
        with writer(self._meta, self._perm):
            self._meta['title'] = title
            self._meta['desc'] = desc
            self._perm.set(owners, editors, shared, [False, False, False])

    ##  String representation.

    def __repr__ (self):
        try:
            fn = self.filename()
        except:
            fn = '?'
        return '<Corpus %s>' % fn

    ##  A child.

    def languages (self):
        return self.langs.children()

    ##  Create a new corpus.

    def create (self, force=False):
        Structure.create(self, force=force)
        


# ##  Create a new corpus file.
# 
# def create_corpus (fn, media=None, owner=None):
# 
#     # Process fn
#     fn = os.path.abspath(os.path.expanduser(fn))
#     fn = fn.rstrip('/')
#     parentdir = os.path.dirname(fn)
#     if not parentdir:
#         raise Exception('No parent directory')
# 
#     # Process media
#     media = _aux_dir('media', media, parentdir, 'media')
# 
#     # Create fn
#     if os.path.exists(fn):
#         raise Exception('File already exists: %s' % repr(fn))
#     os.makedirs(fn)
# 
#     # Create _perm
#     if not owner:
#         owner = os.getenv('USER')
#     if owner:
#         print('owner =', owner)
#     else:
#         print('Warning: No owner - will not be able to use cgi')
#     with open(os.path.join(fn, '_perm'), 'w') as f:
#         f.write('set\towners\t')
#         f.write(owner or '')
#         f.write('\n')
#         f.write('set\teditors\t')
#         f.write(owner or '')
#         f.write('\n')
#         f.write('set\tshared\teveryone\n')
# 
#     # Create _config file
#     cfg = os.path.join(fn, '_config')
#     with open(cfg, 'w') as f:
#         if media is not None:
#             f.write('media\t%s\n' % media)


#--  Copy, delete  -------------------------------------------------------------

##  Open a corpus.

def open_corpus (fn, context=None):
    db = open_database(Corpus, fn)
    if context is not None:
        db.env.set_context(context)
    return db

##  Duplicate an existing corpus file.  Just does a deep file copy.

def copy_corpus (src, tgt):
    src = expanduser(src)
    tgt = expanduser(tgt)
    sh.cpr(src, tgt)

##  Delete a corpus file.

def delete_corpus (fn, noerror=False):
    fn = expanduser(fn)
    if exists(fn):
        sh.rmrf(fn)
    elif not noerror:
        raise Exception('Corpus does not exist: %s' % fn)
