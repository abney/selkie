##  @package seal.cld.core
#   The CLDApp class.

import sys
from pathlib import Path
from .seal.config import environ
from .seal.sh import chmod
from .app import SealApp
from .corpus.core import open_corpus
from .corpus.export import CorpusContainer
from .ui.corpus import CorpusEditor


#--  cld_app  ------------------------------------------------------------------


##  The CLD application.

class CLD (SealApp):

    ##  Open the CLD application file.

    def open_file (self, filename):
        return open_corpus(filename, context=self.context)

    ##  Create the CLD root web directory.

    def make_root (self, cpt):
        c = self.context
        return CorpusEditor(file=c.file, cpt=cpt, context=c)

    def lib_file_pathname (self, name):
        return Path(__file__).parent / 'lib' / name

#    def _corpus (self):
#        if self.filename is None:
#            raise Exception('No filename')
#        return Corpus(filename=self.filename)
#    
#    def _corpus_container (self):
#        return CorpusContainer(self._corpus())
#    
#    def com_delete (self, *sels):
#        self._corpus_container().com_delete(sels)
#    
#    def com_export (self, export_filename, *sels):
#        self._corpus_container(cfg).com_export(export_filename, sels)
#    
#    def com_import (self, export_filename, *sels):
#        self._corpus_container().com_import(export_filename, sels)
#    
#    def com_list (self, *sels):
#        self._corpus_container().com_list(sels)
#
#    def com_tree (self, **kwargs):
#        self._corpus().print_tree(**kwargs)

