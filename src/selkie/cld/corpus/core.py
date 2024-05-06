
'''The Corpus class.'''

from os.path import expanduser, join, exists
from ..seal import sh
from ..app.config import Config
from ..seal.io import pprint
from ..db.meta import MetaPropList
from ..db.file import File, PropDict
from ..db.dir import Structure
from ..db.core import open_database
from .rom import Romanization, Registry
from .user import User, UserList
from .export import ExportStream, ImportStream
from .language import Language, LanguageList
from .lexicon import Lexicon
from .env import CorpusMixin
from .media import MediaFile, MediaIndex, MediaDirectory
from .transcript import ClipsFile, ParagraphFile, Transcription
from .text import Text, Toc, Translation
from .token import TokenFile
from ..glab.file import GLabDirectory, Library, Notebook


#--  Corpus  -------------------------------------------------------------------

class CorpusPropList (MetaPropList):
    '''The corpus metadata.  Behaves like a dict.'''
    
    property_names = ('title', 'desc')
    '''The permissible dict keys.'''


class Corpus (CorpusMixin, Structure):
    '''The CLD application file.'''

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
    '''A dict mapping file suffix to class.'''

    # indexed = (Text,)

    signature = {'langs': LanguageList,
                 'users': UserList,
                 'roms': Registry,
                 'glab': GLabDirectory}
    '''A dict mapping child names to classes.'''

    ##  Metadata
    __metadata__ = Structure.__metadata__ + (('_meta', CorpusPropList),)


    def config (self):
        '''The configuration file.  Only if this is a root corpus.'''

        assert self.parent() is None
        return Config(join(self.filename(), '_config'))

    def metadata (self):
        '''The metadata object.'''

        return self._meta

    def filename (self):
        '''Filename.'''
        
        return self.env['filename']

    def set_metadata (self, title, desc, owners, editors, shared):
        '''Callback for setting the metadata.'''

        with writer(self._meta, self._perm):
            self._meta['title'] = title
            self._meta['desc'] = desc
            self._perm.set(owners, editors, shared, [False, False, False])

    def __repr__ (self):
        '''String representation.'''

        try:
            fn = self.filename()
        except:
            fn = '?'
        return '<Corpus %s>' % fn

    def languages (self):
        '''A child.'''

        return self.langs.children()

    def create (self, force=False):
        '''Create a new corpus.'''

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

def open_corpus (fn, context=None):
    '''
    Open a corpus.
    '''
    db = open_database(Corpus, fn)
    if context is not None:
        db.env.set_context(context)
    return db


def copy_corpus (src, tgt):
    '''
    Duplicate an existing corpus file.  Just does a deep file copy.
    '''
    src = expanduser(src)
    tgt = expanduser(tgt)
    sh.cpr(src, tgt)


def delete_corpus (fn, noerror=False):
    '''
    Delete a corpus file.
    '''
    fn = expanduser(fn)
    if exists(fn):
        sh.rmrf(fn)
    elif not noerror:
        raise Exception('Corpus does not exist: %s' % fn)
