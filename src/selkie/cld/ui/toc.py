##  @package seal.cld.ui.toc
#   Provides TocEditor.

from seal.app.html import *
from seal.cld.db.disk import writer
from seal.cld.corpus.text import Toc, Text
from seal.cld.ui.text import TextEditor, TextMetadataEditor
from seal.cld.ui.page import PageEditor
from seal.cld.ui.audio import AudioEditor


#--  TocEditor  ----------------------------------------------------------------

##  Table of contents editor.

class TocEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'': 'view',
                 'home': 'view',
                 'view': 'view',
                 'edit': 'edit',
                 'edit_callback': 'edit_callback',
                 'deletion_confirmed': 'deletion_confirmed',
                 'add_child': 'add_child',
                 'text': 'text',
                 'meta': 'meta'}

    ##  Returns a TextMetadataEditor.
    def meta (self): return TextMetadataEditor(self, self.file.text().info())

    ##  Add a new child.

    def add_child (self): 
        toc = self.file
        with writer(toc):
            child = toc.new_child()
        return Redirect('text.%s/edit' % child.id())

    ##  Main entry point.

    def view (self):
        toc = self.file
        title = toc.title()
        writable = toc.permitted('write')

        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        menu = MenuBar(page)
        if isinstance(toc.parent(), Text): back = '../../home'
        else: back = '../home'
        Button(menu, '<<', back)
        if writable: Button(menu, 'Edit', 'edit')
        if toc.text():
            Button(menu, 'Metadata', 'meta/')
        lang = self.file.env.language()
        Button(menu, 'Lexicon', Pathname(self.context.root.language_url(lang) + '/lexicon'))
        H1(page, title)
        table = Table(page, htmlclass='tabbing')
        for (i, child) in enumerate(toc.children(), 1):
            row = Row(table)
            String(Cell(row), str(i))
            if child.permitted('read'):
                Link(Cell(row),
                     '[%s] %s' % (child.id(), child.title()),
                     'text.%s/' % child.id())
            else:
                I(Cell(row), 'Private text')
        if writable: Button(P(page), '+', 'add_child')
        return page

    ##  Main edit point for editing.

    def edit (self):
        toc = self.file
        can_move_up = isinstance(toc.parent(), Text)

        title = 'Table of Contents [%s]' % toc.title()
        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        menu = MenuBar(page)
        Button(menu, '<<', '../../')
        Button(menu, 'View', 'view')
        H1(page, title)
        form = Form(page, 'edit_callback')
        table = Table(form, htmlclass='tabbing')

        row = Row(table)
        B(Cell(row), 'Sel')
        B(Cell(row), 'Tgt')

        if can_move_up:
            row = Row(table)
            Cell(row) # Sel
            RadioButton(Cell(row), 'target', '<')
            String(Cell(row), '..')
            String(Cell(row), '\u25b3')

        for (i, child) in enumerate(toc.children(), 1):
            p = str(i)
            row = Row(table)
            CheckBox(Cell(row), '*items', p)
            RadioButton(Cell(row), 'target', p)
            String(Cell(row), p)
            if child.permitted('read'): title = child.title()
            else: title = '(Title not accessible)'
            String(Cell(row),
                   '[%s] %s' % (child.id(), title))

        if can_move_up:
            row = Row(table)
            Cell(row) # Sel
            RadioButton(Cell(row), 'target', '>')
            String(Cell(row), '..')
            String(Cell(row), '\u25bd')

        # positions = [str(i) for i in range(1, len(self.file)+1)]

        String(P(form), 'Create new text:')

        p = P(form)
        Submit(p, 'Append')
        NBSP(p)
        String(p, '- Add new text in last position')
        BR(p)

        Submit(p, 'Insert')
        NBSP(p)
        String(p, '- Insert a new text at the position')
        B(p, ' Tgt')

        String(P(form), 'Manipulate selected texts [Sel]:')

        p = P(form)
        Submit(p, 'Move to')
        NBSP(p)
        String(p, '- Move')
        B(p, ' Sel ')
        String(p, 'to the position')
        B(p, ' Tgt')
        BR(p)

        Submit(p, 'Move into')
        NBSP(p)
        String(p, '- Move')
        B(p, ' Sel ')
        String(p, 'into the text at')
        B(p, ' Tgt')
        BR(p)

        if isinstance(toc.parent(), Toc):
    
            Submit(p, 'Move out')
            NBSP(p)
            String(p, '- Move')
            B(p, ' Sel ')
            String(p, 'up and out')
            BR(p)

        Submit(p, 'Delete')
        NBSP(p)
        String(p, '- Delete')
        B(p, ' Sel')

#        p = P(form)
#        B(p, 'Target position:')
#        NBSP(p)
#        if positions:
#            DropDown(p, 'target', positions)
#        else:
#            String(I(p), 'No positions available')
        
        Submit(P(form), 'Cancel/Done')

        return page

    ##  Callback from the edit page.

    def edit_callback (self, items=None, target=None, submit=None):

        if submit == 'Cancel/Done':
            return Redirect('view')

        children = list(self.file.children())
        if items is None:
            indices = seltexts = None
        else:
            indices = [int(item) - 1 for item in items]
            seltexts = [children[i] for i in indices]

        if target in (None, '<', '>'): tgt_index = None
        else: tgt_index = int(target) - 1

        toc = self.file

        if submit == 'Append':
            with writer(toc):
                toc.new_child()
            return Redirect('edit')

        elif submit == 'Insert':
            with writer(toc):
                toc.new_child(tgt_index)
            return Redirect('edit')

        elif submit == 'Delete':
            title = 'Confirm Deletion'
            page = HtmlPage(self, title=title)
            PathWithLogin(page)
            menu = MenuBar(page)
            Button(menu, '<<', '../../')
            Button(menu, 'View', 'view')
            Button(menu, 'Edit', 'edit')
            H1(page, title)
            String(B(P(page)), 'The following item(s) will be permanently deleted:')
            form = Form(page, 'deletion_confirmed')
            table = Table(form, htmlclass='tabbing')
            for (item, text) in zip(items, seltexts):
                row = Row(table)
                Hidden(form, '*items', item)
                String(Cell(row), item)
                String(Cell(row),
                       '[%s] %s' % (text.id(), text.title()))
            p = P(form)
            Submit(p, 'Confirm Deletion')
            Submit(p, 'Cancel')
            return page

        elif submit.startswith('Move') and target in '<>':
            with toc.writer():
                toc.eject_children(indices, leftward=(target == '<'))
            return Redirect('edit')

        elif submit == 'Move to':
            with writer(toc):
                toc.reorder_children(indices, tgt_index)
            return Redirect('edit')

        elif submit == 'Move into':
            toc = self.file
            tgtchild = toc[tgt_index]
            if not tgtchild.toc.exists():
                return self.error_page(tgt_index, toc2)
            with writer(toc):
                toc.reparent_children(indices, tgt_index)
            return Redirect('edit')

        else:
            raise Exception('Bad value for submit: %s' % submit)

    ##  Callback from the deletion confirmation page.

    def deletion_confirmed (self, submit=None, items=None):
        indices = [int(item) - 1 for item in items]
        toc = self.file
        with writer(toc):
            toc.delete_children(indices)
        return Redirect('edit')

    ##  Constructs an error page.

    def error_page (self, i, text):
        page = HtmlPage(self, title='Error')
        String(P(page), 'Text #%d (%s) is a single-page text, cannot contain other texts.' % (i, text.title()))
        Button(P(page), 'OK', 'edit')
        return page

    ##  Returns a TextEditor for the i-th child text.

    def text (self, i):
        toc = self.file
        if i not in toc:
            raise PageNotFound()
        return TextEditor(self, toc[i])


#--  TextCreator  --------------------------------------------------------------

##  Text creator.

class TextCreator (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'': 'edit',
                 'edit': 'edit',
                 'doit': 'doit'}

    ##  Main entry point.  The file is a Text stub.

    def edit (self):
        title = self.file.title()
        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        menu = MenuBar(page)
        Button(menu, '<<', '../../')
        Button(menu, 'Properties', '../meta')
        H1(page, title)
        form = Form(page, 'doit')
        String(P(form), 'What type of text would you like to create?')
        table = Table(form, htmlclass='tabbing')
        row = Row(table)
        Submit(row, 'Page')
        String(row, 'A page of text')
        row = Row(table)
        Submit(row, 'Audio')
        String(row, 'An audio recording')
        row = Row(table)
        Submit(row, 'Toc')
        String(row, 'A list of texts')
        row = Row(table)
        Submit(row, 'Cancel')
        return page

    ##  Callback from the main page.

    def doit (self, submit=None):
        if submit == 'Page': type = 'page'
        elif submit == 'Audio': type = 'audio'
        elif submit == 'Toc': type = 'toc'
        else: return Redirect('../')
            
        toc = self.file
        i = len(toc)
        with writer(toc):
            toc.new_child(type)
        return Redirect('../text.%d/edit' % (i+1))
