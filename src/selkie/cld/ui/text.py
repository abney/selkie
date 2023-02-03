##  @package seal.cld.ui.text
#   Provides TextEditor and TextMetadataEditor.

import os
from seal.app.html import *
from seal.cld.ui.file import MetadataEditor, hex_encode, hex_decode
from seal.cld.corpus.text import Toc


##  Text editor.  The file member contains a Text.

class TextEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'home': 'home',
                 'edit': 'home',
                 'page': 'page',
                 'toc': 'toc'}

    ##  Main entry point.  Redirects either to page() or toc(), depending
    #   on the type of Text.

    def home (self):
        text = self.file
        if 'toc' in text: return Redirect('toc/home')
        else: return Redirect('page/home')

    ##  Main entry point for a leaf Text.  Returns a PageEditor.

    def page (self, nt=None):
        from seal.cld.ui.page import PageEditor
        return PageEditor(self, self.file, nt)

    ##  Main entry point for a complex Text.  Returns a TocEditor.

    def toc (self):
        from seal.cld.ui.toc import TocEditor
        return TocEditor(self, self.file['toc'])


#--  TextInfoEditor  -----------------------------------------------------------

##  Text metadata editor.

class TextMetadataEditor (MetadataEditor):

    ##  Insert the contents into the permissions page.

    def insert_rows (self, table, form, disabled):

        metadata = self.file
        orths = metadata.env.orthographies()

        t = metadata.get('subtype') or 'regular'
        row = Row(table)
        String(row, 'Subtype:')
        DropDown(row, 'subtype', ['regular', 'lesson'], selected=t, disabled=disabled)

        row = Row(table)
        String(row, 'Author:')
        TextBox(row, 'author', metadata.get('author') or '', disabled=disabled)

        row = Row(table)
        String(row, 'Title:')
        TextBox(row, 'title', metadata.get('title') or '', disabled=disabled)

        row = Row(table)
        String(row, 'Orthography:')
        DropDown(row, 'orthography', orths, disabled=disabled)

    ##  Insert an informational message after the form.

    def insert_coda (self, page):
        p = P(page)
        I(p, 'Subtype = lesson enables the drill button, if type = page')
