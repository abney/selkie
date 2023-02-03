##  @package seal.cld.glab.ui
#   User interface for GLab.

from seal.app.log import DEBUG

import os
from ..com import Timeout, TimedOut
from ..db.disk import writer, is_undoable, undo, is_redoable, redo
from .file import GLabDirectory, Library
from .eval import Interpreter


#===============================================================================
#
#                                GUI
#

#--  User Interface  -----------------------------------------------------------

# Usage:
# from seal import ui
# ui.test(RootDirectory())

##  The toplevel editor.

class GLabEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'home': 'toc',
                 'toc': 'toc',
                 'new': 'new_notebook',
                 'nb': 'notebook',
                 'dup': 'dup_notebook',
                 'delete': 'delete_notebook'}

    ##  Returns the library for the current user.

    def library (self):
        user = self.context.username
        if user and user in self.file:
            return self.file[user] # GLabDirectory[name] is a Library

    ##  Returns a notebook given its ID.

    def notebook (self, id):
        if not id.isdigit():
            raise PageNotFound()
        lib = self.library()
        if id not in lib:
            raise PageNotFound()
        return NotebookEditor(self, lib[id])

    ##  Returns a listing of notebooks.

    def toc (self):
        glab = self.file  # GLabDirectory
        user = self.context.username
        lib = self.library()

        page = HtmlPage(self, title='Grammar Lab')
        PathWithLogin(page)
        if glab.parent() is not None:
            bar = MenuBar(page)
            Button(bar, '<<', '../home')
        H1(page, 'Grammar Lab')

        if not user:
            I(P(page), 'No user provided')
            return page

        elif lib is None:
            I(P(page), 'No GLab library for user %s' % repr(user))
            return page

        else:
            p = P(page)
            String(p, 'GLab, User: %s' % user)
            table = None
            for (id, title, public) in sorted(lib.titles()):
                if table is None:
                    table = Table(page)
                    row = Header(table)
                    String(Cell(row), 'Title')
                    String(Cell(row), 'ID')
                    String(Cell(row), 'Pub?')
                    String(Cell(row), 'Edit/Del')
                row = Row(table)
                String(Cell(row), title)
                String(Cell(row), id)
                String(Cell(row), (public and 'Y') or 'N')
                cell = Cell(row)
                Button(cell, 'edit', 'nb.%s/edit' % id),
                Button(cell, 'X', 'delete.%s' % id)
            if table is None:
                String(P(page), 'No notebooks')
            Button(P(page), '+', 'new')
            return page

    ##  Returns the pathname of a notebook, given its ID.

    def notebook_pathname (self, id):
        return os.path.join(self.datadir, self.__user__, id + '.gl')

#    def allocate_notebook_id (self):
#        pass

    ##  Creates a new notebook.

    def new_notebook (self):
        lib = self.library()
        with writer(lib):
            nb = lib.new_child()
        return Redirect('nb.%s/edit' % nb.name())

    ##  Creates a new notebook by duplicating an existing one.

    def dup_notebook (self, srcid):
        new_nb = self.library().dup_notebook(srcid)
        tgtid = new_nb.name()

        title = 'Duplicate Notebook'
        page = HtmlPage(self, title=title)
        bar = MenuBar(page)
        Button(bar, '<<', 'home')
        H1(page, title)
        p = P(page)
        String(p, 'Duplicated notebook')
        table = Table(page, htmlclass='noborder')
        row = Row(table)
        Cell(row, 'Original:')
        Cell(row, '[%s]' % srcid)
        Button(Cell(row), 'edit', 'nb.%s/edit' % srcid)
        row = Row(table)
        Cell(row, 'Duplicate:')
        Cell(row, '[%s]' % tgtid)
        Button(Cell(row), 'edit', 'nb.%s/edit' % tgtid)
        return page

    ##  Deletes a notebook.

    def delete_notebook (self, id):
        self.library().delete_child(id)
        return Redirect('home')


def _dotted (com, arg):
    if arg is None: return com
    else: return com + '.' + arg
    

##  An editor for a notebook.

class NotebookEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'edit': 'edit',
                 'set_title': 'set_title',
                 'commit_title': 'commit_title',
                 'commit_text': 'commit_text',
                 'delete': 'delete',
                 'insertafter': 'insertafter',
                 'undo': 'undo',
                 'redo': 'redo'}

    ##  Get the title from the title file.

    def load_title (self):
        return notebook_title(self.filename)

    ##  Look at the file and count the lines.

    def current_text_count (self):
        n = 0
        if os.path.exists(self.filename):
            with open(self.filename) as f:
                for line in f:
                    if not line.startswith('#'):
                        n += 1
        return n

    ##  Produce an error page.

    def error_page (self, e, selected=None):
        page = HtmlPage(self, title='Error')
        P(page, 'ERROR:', str(e))
        Button(P(page), 'Back to notebook', _dotted('edit', selected))
        return page

    ##  Undo the last action.

    def undo (self, selected=None):
        undo(self.file)
        return Redirect(_dotted('edit', selected))

    ##  Redo the action that was just undone.

    def redo (self, selected=None):
        redo(self.file)
        return Redirect(_dotted('edit', selected))

    ##  Main entry point.

    def edit (self, selected=None):
        nb = self.file
        title = nb.title()
        texts = nb.texts()
        fn = nb._filename()
        id = nb.name()

        if selected is None:
            if len(texts) == 0: texts = ['']
            selected = str(len(texts) - 1)
        else:
            i = int(selected)
            while i >= len(texts):
                texts.append('')

        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        bar = MenuBar(page)
        Button(bar, '<<', '../home')

        if is_undoable(nb):
            tgt = _dotted('undo', selected)
        else:
            tgt = None
        Button(bar, 'Undo', tgt)

        if is_redoable(nb):
            tgt = _dotted('redo', selected)
        else:
            tgt = None
        Button(bar, 'Redo', tgt)

        Button(bar, 'Duplicate NB', '../dup.%s' % id)

        form = Form(page, 'commit_text')

        table = Table(form, htmlclass='grid')

        row = Row(table)
        H1(Cell(row), '[%s] %s' % (id, title))
        Button(Cell(row, colspan=2), 'edit', 'set_title')

        DEBUG(os.getpid(), 'starting')
        
        outputs = []
        with Timeout(2):
            interp = Interpreter(interruptable=TimedOut)
            interp.set('*notebook-dir*', os.path.dirname(fn))
            for (i, text) in enumerate(texts):
                outputs.append(interp(text))

        DEBUG(os.getpid(), 'done')

        for i in range(len(texts)):
            text = texts[i]
            if i < len(outputs):
                out = outputs[i]
            elif i == len(outputs):
                out = '** TIMED OUT **'
            else:
                out = None

            row = Row(table)
            TextBox(Cell(row), '*texts', text, size=70, htmlid=str(i)),
            Button(Cell(row), '-', 'delete.%s' % i)
            Button(Cell(row), '+', 'insertafter.%s' % i)
            if out:
                row = Row(table)
                Pre(row, out, htmlclass=None)

        Submit(form, 'Update')

        page.focus(selected)
        page.add_import('trigger')

        return page

    ##  Callback when a line ("text") is edited.

    def commit_text (self, trigger=None, texts=[], submit=None):
        nb = self.file
        with writer(nb):
            nb.set_texts(texts)
        if trigger: com = 'edit.%d' % (int(trigger) + 1)
        else: com = 'edit'
        return Redirect(com)

    ##  Set the title.

    def set_title (self):
        nb = self.file
        title = nb.title()
        page = HtmlPage(self, title='Set Title')
        form = Form(page, 'commit_title')
        table = Table(form)
        row = Row(table)
        String(Cell(row), 'Title:')
        TextBox(Cell(row), 'title', title, size=70)
        p = P(form)
        Submit(p, 'Submit')
        Submit(p, 'Cancel')
        return page

    ##  Callback to set the title.

    def commit_title (self, submit='', title=''):
        if submit == 'Submit':
            nb = self.file
            with writer(nb):
                nb.set_title(title)
        return Redirect('edit')

    ##  Delete the i-th line ("text").

    def delete (self, i):
        i = int(i)
        nb = self.file
        with writer(nb):
            nb.delete_text(i)
        if i < len(nb.texts()): sel = str(i)
        else: sel = None
        return self.edit(sel)

    ##  Insert a new line after the i-th one.

    def insertafter (self, i):
        i = int(i)
        nb = self.file
        with writer(nb):
            nb.insert_text(i+1)
        return self.edit(str(i+1))


#-------------------------------------------------------------------------------

# for use with Apache: in the wsgi file, do:
# application = make_application('/foo/bar/glab')

# def make_application (datadir):
#     return GlabDirectory(datadir).wsgi()
