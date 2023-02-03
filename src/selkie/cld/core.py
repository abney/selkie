##  @package seal.cld.core
#   The CLDApp class.

import sys, seal
from seal.core.config import environ
from seal.core.sh import chmod
from seal.app import SealApp
from seal.cld.corpus.core import open_corpus
from seal.cld.corpus.export import CorpusContainer
from seal.cld.ui.corpus import CorpusEditor


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

