##  @package seal.cld.ui.file
#   Contains MetadataEditor.

from binascii import hexlify, unhexlify
from seal.app.html import *
from seal.cld.db.disk import writer

from seal.app.ui import hex_encode, hex_decode


#--  Hex Encode/Decode  --------------------------------------------------------

# def hex_encode (s):
#     return hexlify(s.encode('utf8')).decode('ascii')
# 
# def hex_decode (s):
#     return unhexlify(s).decode('utf8')


#--  MetadataEditor  -----------------------------------------------------------

##  A generic metadata editor.

class MetadataEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'home': 'edit',
                 'edit': 'edit',
                 'post_info': 'post_info',
                 'post_perm': 'post_perm'}

    ##  The main entry point.

    def edit (self):
        info = self.file  # type MetaPropList
        item = info.host
        keys = list(info.keys())
        disabled = (not item.permitted('write'))

        page = HtmlPage(self, title='Metadata')
        PathWithLogin(page)
        bar = MenuBar(page)
        Button(bar, '<<', '../')
        H1(page, 'Metadata')

        if keys:
            self.insert_preamble(page)

            form = Form(page, 'post_info')
            table = Table(form)

            # Specializations may override
            self.insert_rows(table, form, disabled)

            if not disabled:
                p = P(form)
                Submit(p, 'Submit')
                Submit(p, 'Cancel')

            self.insert_coda(page)

        hasparent = (item.parent() is not None)
        perm = item.permissions()
        loc = perm.local()
        inh = perm.inherit()
        inheritable = perm.inheritable()

        disabled = (not perm.permitted('admin'))
        H2(page, 'Permissions')

        p = P(page)
        I(p, 'Multiple user names should be separated by spaces')
        form = Form(page, 'post_perm')
        table = Table(form)
        hdr = Header(table)
        String(hdr, 'Role')
        String(hdr, 'Local')
        if hasparent:
            String(Cell(hdr, colspan=2), 'Inherited')

        for (i, role) in enumerate(['owners', 'editors', 'shared']):
            row = Row(table)
            String(row, role.title())
            TextBox(row, role, ' '.join(sorted(loc[i])), disabled=disabled)
            if hasparent:
                CheckBox(row, '*inherit', role, checked=inh[i], disabled=disabled)
                String(row, ' '.join(sorted(inheritable[i] - loc[i])))

        if not disabled:
            p = P(form)
            Submit(p, 'Submit')
            Submit(p, 'Cancel')

        else:
            Button(P(page), 'Back', '../')

        return page

    ##  The metadata editor is a section in the permissions page.
    #   This is the main body of it, inside the form.
    #   Specialization may override.

    def insert_rows (self, table, form, disabled):
        info = self.file
        for key in info.keys():
            row = Row(table)
            String(row, '%s:' % (key.title()))
            TextBox(row, key, info.get(key) or '', disabled=disabled)

    ##  The metadata editor is a section in the permissions page.
    #   This is called to insert material before the form.
    #   Specialization may override.  The default implementation is a no-op.

    def insert_preamble (self, page): pass

    ##  The metadata editor is a section in the permissions page.
    #   This is called to insert material after the form.
    #   Specialization may override.  The default implementation is a no-op.

    def insert_coda (self, page): pass

    ##  Callback from the form.

    def post_info (self, submit=None, **kwargs):
        if submit == 'Submit':
            info = self.file
            with writer(info):
                for (key, value) in kwargs.items():
                    info[key] = value
        return Redirect('../')

    ##  Callback from the permissions portion of the form.
    #   If this is the root file, inherit is None, otherwise it is a list.

    def post_perm (self, submit=None, owners=None, editors=None, shared=None, inherit=None):
        owners = owners.split()
        editors = editors.split()
        shared = shared.split()
        if inherit is None: inherit = []

        if submit == 'Submit':
            perm = self.file.host.permissions()
            with perm.writer():
                perm.set(owners, editors, shared, inherit)
        return Redirect('../')
