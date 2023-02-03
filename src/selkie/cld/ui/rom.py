##  @package seal.cld.ui.rom
#   The class RegistryEditor, which also edits romanizations.

from seal.app.html import *
from seal.nlp.rom import decode
from seal.cld.db.disk import writer
from seal.cld.ui.file import MetadataEditor


##  Romanization registry editor.

class RegistryEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'home': 'home',
                 'new': 'new',
                 'view': 'view',
                 'edit': 'edit',
                 'do_edit': 'do_edit',
                 'do_new': 'do_new',
                 'do_decode': 'do_decode',
                 'metadata': 'metadata'}

    ##  Main entry point.

    def home (self):
        page = HtmlPage(self, title='Romanizations')
        PathWithLogin(page)
        menubar = MenuBar(page)
        Button(menubar, '<<', '..')
        Button(menubar, 'Metadata', 'metadata')
        H1(page, 'Romanizations')
        ul = UL(page)
        action = 'view'
        if self.file.permitted('write'):
            action = 'edit'
        for name in self.file:
            Link(LI(ul), name, action + '.' + name)
        if action == 'edit':
            Button(page, '+', 'new')
        return page

    ##  Page to create a new romanization.

    def new (self, err=None):
        page = HtmlPage(self, title='New Romanization')
        H1(page, 'New Romanization')
        if err == 'bad':
            B(P(page), 'Name may contain only alphanumerics and underscore')
        form = Form(page, 'do_new')
        p = P(form)
        String(p, 'Name: ')
        TextBox(p, 'name')
        p = P(form)
        Submit(p, 'Submit')
        Submit(p, 'Cancel')
        return page

    ##  Callback from the new-romanization page.

    def do_new (self, name=None, submit=None):
        if submit == 'Submit':
            if not all(c.isalnum() or c == '_' for c in name):
                return Redirect('new.bad')
            else:
                reg = self.file
                with writer(reg):
                    reg.new_child(name)
                return Redirect('edit.%s' % name)
        else:
            return Redirect('home')

    ##  Page for viewing a particular romanization.

    def view (self, name):
        self.file.check_permission('read')
        rom = self.file.get(name)
        if rom is None:
            raise HttpException('No such romanization: %s' % name)
        page = HtmlPage(self, title=name)
        PathWithLogin(page)
        menubar = MenuBar(page)
        Button(menubar, '<<', 'home')
        H1(page, name)
        table = Table(page)
        hdr = Header(table)
        Cell(hdr, 'Rom')
        Cell(hdr, 'Expansion', colspan=2)
        for (k,v) in sorted(rom.items()):
            row = Row(table)
            String(Cell(row), k)
            String(Cell(row), v)
            String(Cell(row), decode(v.encode('ascii')))
        return page

    ##  Page for editing a particular romanization.

    def edit (self, name):
        rom = self.file.get(name)
        rom.check_permission('write')
        if rom is None:
            page = HtmlPage(self, title='No such romanization')
            H1(page, 'No such romanization')
            Button(P(page), 'OK', 'home')
            return page

        else:
            page = HtmlPage(self, title=name)
            PathWithLogin(page)
            menubar = MenuBar(page)
            Button(menubar, '<<', 'home')
            H1(page, name)
            p = P(page)
            String(p,
                   'In the righthand column, you may specify Unicode code points '
                   'by writing them as one or more hexadecimal numbers surrounded '
                   'by \( ).  For example: \(e1 014b 306e 10330) represents the '
                   'sequence acute_a engma Hiragana_no Gothic_A.  A listing of '
                   'Unicode code points is available ')
            Link(p, 'here', 'https://www.unicode.org/Public/UCD/latest/charts/CodeCharts.pdf')
            String(p, ' (108 MB).')
    
            p = P(page)
            B(p, 'Caution:')
            NBSP(p)
            I(p, 'No edits are saved until you click the Save button')
            form = Form(page, 'do_edit')
            Hidden(form, 'rom', name)
            table = Table(form, id='main_table')
            hdr = Header(table)
            Cell(hdr, 'Ins')
            Cell(hdr, 'Del')
            Cell(hdr, 'Rom')
            Cell(hdr, 'Expansion', colspan=2)
            for (k,v) in sorted(rom.items()):
                row = Row(table)
                Button(Cell(row), '^', htmlclass='ins_button')
                Button(Cell(row), 'x', htmlclass='del_button')
                TextBox(Cell(row), '*keys', k, size="20")
                TextBox(Cell(row), '*values', v, size="20")
                String(Cell(row), decode(v.encode('ascii')))
            Button(P(form), '+', id='plus_button')
            p = P(form)
            Submit(p, 'Save')
            Submit(p, 'Cancel')
    
            page.add_import('RomEditor')
            script = Script(page)
            script.write("new RomEditor('%s');" % name)

            return page

    ##  Callback from the edit page.

    def do_edit (self, rom=None, keys=None, values=None, submit=None):
        if submit == 'Cancel':
            return Redirect('home')
        if len(keys) != len(values):
            raise Exception('Different numbers of keys and values')
        rom = self.file[rom]
        with writer(rom):
            for (k,v) in zip(keys,values):
                rom[k] = v
        return Redirect('home')

    ##  Ajax callback from the edit page.

    def do_decode (self, rom=None, ascii=None):
        rom = self.file[rom]
        return Text(decode(ascii.encode('ascii')))

    ##  Returns a MetadataEditor.

    def metadata (self):
        return MetadataEditor(self, self.file.metadata())
