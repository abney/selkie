##  @package seal.cld.ui.corpus
#   The toplevel application.

# import os
# from glob import glob
# from seal.io import pprint
# from seal.ui import EditableParagraph, HTML
# from seal.sh import mkdir, chmod
# from seal.cld.rom import find_rom, require_rom, decode
# from seal.data.langdb import languages
# from seal.cld.file import hex_encode, hex_decode, safe_name
# from seal.cld.audio import AudioEditor

import os
from os.path import abspath
from seal.app.html import *
from seal.cld.corpus.core import open_corpus
from seal.cld.ui.file import MetadataEditor
from seal.cld.ui.language import LanguageListEditor
from seal.cld.ui.users import GroupsEditor
from seal.cld.ui.rom import RegistryEditor
from seal.cld.glab.ui import GLabEditor


#--  Application  --------------------------------------------------------------

##  The root web page.

class CorpusEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'': 'home',
                 'home': 'home',
                 'cld': 'home',
                 'corpora': 'corpora',
                 'file': 'file_manager',
                 'langs': 'langs',
                 'meta': 'meta',
                 'users': 'users',
                 'roms': 'roms',
                 'glab': 'glab',
                 'login': 'login',
                 'do_login': 'do_login',
                 'not_readable': 'not_readable',
                 'logout': 'logout',
                 'do_logout': 'do_logout',
                 'do_password_change': 'do_password_change'
                 }

    ##  Returns the URL given a language code.

    def language_url (self, lang):
        return self.__extern__('/langs/lang.%s' % lang.id())

    ##  Returns the URL for a text.

    def text_url (self, text):
        cpts = [a.name() for a in text.ancestors() if a.name()]
        cpts.reverse()
        assert cpts[0] == 'langs'
        assert cpts[2] == 'texts'
        out = ['', cpts[0], 'lang.%s' % cpts[1]]
        for i in range(2, len(cpts), 2):
            out.append(cpts[i])
            out.append('text.%s' % cpts[i+1])
        return self.__extern__('/'.join(out))

    ##  Main entry point.

    def home (self):
        context = self.context
        execmode = context.execmode()
        is_desktop = (execmode == 'desktop')
        if is_desktop and self.file is None:
            return Redirect('file')
        corpus = self.file
        if not corpus.permitted('read'):
            if context.username:
                return Redirect('not_readable')
            else:
                return Redirect('login.%s' % hex_encode(self.cpt.pathname))
        meta = corpus.metadata()
        title = meta.get('title')
        if title: title = 'Corpus ' + title
        else: title = 'Corpus'
        desc = meta.get('desc')
        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        bar = MenuBar(page)
        if is_desktop:
            Button(bar, 'File', 'file')
        Button(bar, 'Metadata', 'meta')
        H1(page, title)
        table = Table(page)
        if is_desktop:
            row = Row(table)
            String(Cell(row), 'Filename:')
            String(Cell(row), corpus.filename())
        if desc:
            row = Row(table)
            String(Cell(row), 'Description: ')
            String(Cell(row), desc)
        row = Row(table)
        String(Cell(row), 'Mode:')
        String(Cell(row), execmode)
        if not is_desktop:
            row = Row(table)
            String(Cell(row), 'Secure:')
            if context.https_on():
                String(Cell(row), 'yes')
            else:
                String(Cell(row), 'no')
        if context.username:
            row = Row(table)
            String(Cell(row), 'User:')
            String(Cell(row), context.username)
        
        H3(page, 'Contents')
        ul = UL(page)
        Link(ul, 'Languages', 'langs/home')
        #Link(ul, 'Imported Corpora', 'corpora/')
        if corpus.permitted('admin'):
            Link(ul, 'Users', 'users/home')
        if corpus.roms.permitted('read'):
            Link(ul, 'Romanizations', 'roms/home')

#         page.add(UL(Link('Languages', 'langs'),
#                     Link('Documents', 'docs'),
#                     Link('Bitext annotation', 'bitexts/list'),
#                     Link('Items', 'items'),
#                     Link('Universal schema', 'schema'),
#                     Link('External corpora', 'corpora'))),
#         page.add(H3('Manual'))
#         page.add(UL(Link('Help', 'https://webservices.itcs.umich.edu/mediawiki/compling/index.php/Bitext_annotator'),
#                     Link('Manual', 'manual')))

        if corpus.glab.permitted('read'):
            Link(ul, 'GLab', 'glab/home')

        #Link(ul, 'Test', 'test')
        return page

#    def test (self):
#        return Redirect('/langs/lang.oji/texts/text.16/audio/')

    ##  Returns a CorpusListEditor.

    def corpora (self):
        return CorpusListEditor(self, self.file.corpora)

    ##  Returns a CorpusManager.

    def file_manager (self):
        return CorpusManager(self, self.file)

    ##  Returns a LanguageListEditor.

    def langs (self):
        return LanguageListEditor(self, self.file.langs)

    ##  Returns a CorpusMetadataEditor.

    def meta (self):
        return CorpusMetadataEditor(self, self.file.metadata())

    ##  Returns a GroupsEditor.

    def users (self):
        return GroupsEditor(self, self.file._groups)

    ##  Returns a RegistryEditor.

    def roms (self):
        return RegistryEditor(self, self.file.roms)

    ##  Returns a GLabEditor.

    def glab (self):
        return GLabEditor(self, self.file.glab)

    ##  Returns a login page.

    def login (self, caller, previously_failed=False):
        page = HtmlPage(self, title='Login')
        H1(page, 'Login')
        if previously_failed:
            B(P(page), 'Incorrect username or password')
        form = Form(page, 'do_login')
        Hidden(form, 'caller', caller)
        table = Table(form, htmlclass='grid')
        row = Row(table)
        String(Cell(row), 'User:')
        TextBox(Cell(row), 'user', size=20)
        row = Row(table)
        String(Cell(row), 'Password:')
        Password(Cell(row), 'password')
        BR(form)
        Submit(form, 'Submit')
        NBSP(form)
        Submit(form, 'Cancel')
        return page

    ##  Callback from the login page.

    def do_login (self, caller=None, user=None, password=None, submit=None):
        if submit == 'Submit':
            if self.context.login(user, password):
                print('** login was successful')
                return Redirect(hex_decode(caller))
            else:
                print('** login failed')
                return self.login(caller, True)
        else:
            return Redirect(hex_decode(caller))

    ##  User logged in, but does not have read access.

    def not_readable (self):
        page = HtmlPage(self, title='Not Readable')
        PathWithLogin(page)        
        H1(page, 'Not Readable')
        P(page, 'Sorry, you do not have read permission for this corpus')
        return page

    ##  Creates a logout page.  Also permits the user to change their password.

    def logout (self, caller):
        page = HtmlPage(self, title='Logout')
        H1(page, 'Logged In')
        form = Form(page, 'do_logout')
        Hidden(form, 'caller', caller)
        String(form, 'Logged in as: %s' % self.context.username)
        BR(form)
        Submit(form, 'Logout')
        BR(form)
        Submit(form, 'Change password')
        BR(form)
        Submit(form, 'Cancel')
        return page

    ##  Callback from the logout page.

    def do_logout (self, caller=None, submit=None):
        if submit == 'Logout':
            self.context.logout()
            return Redirect(hex_decode(caller))
        elif submit == 'Change password':
            return self.change_password(caller)
        else:
            return Redirect(hex_decode(caller))

    ##  Callback from the logout page; generates a password-change page.

    def change_password (self, caller=None, msg=None):
        user = self.context.username
        page = HtmlPage(self, title='Change Password')
        H1(page, 'Change Password')
        if msg:
            B(P(page), msg)
        form = Form(page, 'do_password_change')
        Hidden(form, 'caller', caller)
        table = Table(form, htmlclass='grid')
        row = Row(table)
        String(Cell(row), 'User:')
        String(Cell(row), user)
        row = Row(table)
        String(Cell(row), 'Old Password:')
        Password(Cell(row), 'old_password')
        row = Row(table)
        String(Cell(row), 'New Password:')
        Password(Cell(row), 'new_password')
        row = Row(table)
        String(Cell(row), 'Verify New Password:')
        Password(Cell(row), 'verify_new_password')
        BR(form)
        Submit(form, 'Submit')
        NBSP(form)
        Submit(form, 'Cancel')
        return page

    ##  Callback from the password-change page.

    def do_password_change (self, caller, old_password, new_password, verify_new_password, submit):
        if submit == 'Submit':
            if new_password != verify_new_password:
                return self.change_password(caller, 'New Password and Verify New Password do not match')
            if self.context.change_password(old_password, new_password):
                page = HtmlPage(self, title='Password Changed')
                H1(page, 'Password Changed')
                Button(page, 'OK', Pathname(hex_decode(caller)))
                return page
            else:
                return self.change_password(caller, 'Incorrect Old Password')
        else:
            return Redirect(hex_decode(caller))


##  A specialization of CorpusEditor, but adds nothing.

class Application (CorpusEditor):
    pass

#     __pages__ = {'': 'root',
#                  'adoc': 'adoc',
#                  'apage': 'apage',
#                  'bitexts': 'bitexts',
#                  'cards': 'cards',
#                  'corpora': 'corpora',
#                  'doc': 'doc',
#                  'docs': 'docs',
#                  'items': 'items',
#                  'kernel': 'kernel',
#                  'lang': 'lang',
#                  'langs': 'langs',
#                  'lex': 'lex',
#                  'manual': 'manual',
#                  'pages': 'pages',
#                  'save': 'save',
#                  'schema': 'schema',
#                  'snt': 'snt',
#                  'tok': 'tok',
#                  'treebank': 'treebank',
#                  'txt': 'txt',
#                  'users': 'users'}

#     def docs (self): return DocsDirectory()
#     def doc (self): return DocDirectory(self.corpus.documents[args[0]])
#     def adoc (self): return AnnotationSetDirectory(self.corpus.annotated[args])
#     def apage (self): return self.apage(*args)
#     def kernel (self): return KernelDirectory()
#     def bitexts (self): return BitextsDirectory()
#     def items (self): return ItemStoreEditor(self.corpus)
#     def lang (self, name): return LanguageEditor(self.corpus[name])
#     def save (self): return self.save_page()
#     def txt (self): return TextStoreDirectory(self.corpus)
#     def snt (self): return SegmentationStoreDirectory(self.corpus)
#     def tok (self): return TokenizationStoreDirectory(self.corpus)
#     def lex (self): return WordlistStoreDirectory(self.corpus)
#     def manual (self): return RawFile('%s/txt/doc/seal/manual.pdf' % Dest)
#     def schema (self): return SchemaDirectory(self.corpus)
#     def treebank (self): return TreebankDirectory(self.corpus)


#--  CorpusManager  ------------------------------------------------------------

##  A corpus manager.
#   This is the home page if running as a desktop application.

class CorpusManager (HtmlDirectory):

    ##  Constructor.

    def __init__ (self, parent=None, file=None, cpt=None, context=None):
        HtmlDirectory.__init__(self, parent, file, cpt, context)
        if self.context.execmode() != 'desktop':
            raise Exception('CorpusManager is only available in command-line application')

    ##  The home page is 'browse'.
    __home__ = 'browse'

    ##  Maps page names to method names.
    __pages__ = {'browse': 'browse',
                 'choose': 'choose',
                 'c': 'corpus',
                 'do_new': 'do_new'}

    ##  Main entry point.

    def browse (self, dir=None):
        if dir is None:
            dir = os.getcwd()
        else:
            dir = hex_decode(dir)
        if self.file:
            filename = self.file.filename()

        page = HtmlPage(self, title='File Manager')
        Path(page)
        bar = MenuBar(page)
        Button(bar, '<<', self.parent.cpt.pathname)
        H1(page, 'File Manager')

        H2(page, dir)
        stack = Stack(page)
        up = os.path.abspath(os.path.join(dir, '..'))
        Link(stack, '(up)', 'browse.%s' % hex_encode(up))
        for name in os.listdir(dir):
            filename = os.path.join(dir, name)
            if name.endswith('.cld') or name.endswith('.cfg'):
                Link(TT(stack), name, 'choose.%s' % hex_encode(filename))
            elif os.path.isdir(filename):
                Link(I(stack), name, 'browse.%s' % hex_encode(filename))

        cfg = self.context.config

        # do_new (filename, media, server_dir, submit)
        form = Form(P(page), 'do_new')
        H3(form, 'New File')
        table = Table(form)

        row = Row(table)
        String(Cell(row), 'File:')
        TextBox(Cell(row), 'filename')

#        row = Row(table)
#        String(Cell(row), 'Media:')
#        TextBox(Cell(row), 'media_dir', cfg.get('media_dir') or '')
#
#        row = Row(table)
#        String(Cell(row), 'ServerDir:')
#        TextBox(Cell(row), 'server_dir', cfg.get('server_dir') or '')

        row = Row(table)
        cell = Cell(row, colspan=2)
        Submit(cell, 'Create')
#        NBSP(cell)
#        Submit(cell, 'Cancel')

        return page

    ##  Callback; sets the filename of the current corpus.

    def choose (self, filename):
        return self._choose1(hex_decode(filename))

    def _choose1 (self, filename):
        # the context is the Request
        self.context.set_application_file(filename)
        return Redirect('/home')

    ##  Callback; creates a new corpus.

    def do_new (self, filename, submit=None):
        if submit == 'Create':
            from seal.cld.toplevel import CLDManager
            mgr = CLDManager(filename)
            mgr.create()
            return self._choose1(filename)
        else:
            return Redirect('/')


#--  External Corpora  ---------------------------------------------------------

##  Corpus list editor.

class CorpusListEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'': 'root',
                 'corpus': 'corpus'}

    ##  Constructor.

    def __init__ (self, lst):
        HtmlDirectory.__init__(self)

        ##  The list of corpora.
        self.contents = lst

    ##  The main entry point.

    def root (self):
        page = HtmlPage(title='External Corpora')
        page.add(PathWithLogin(self))
        page.add(UL(Link(TT(corp.filename()), 'corpus.%d' % i)
                    for (i, corp) in enumerate(self.contents)))
        return page

    ##  Edit a particular corpus.  Returns a CorpusEditor.

    def corpus (self, i):
        return CorpusEditor(self.contents[int(i)])

    ##  A page for creating a new corpus in the list.

    def new (self):
        page = HtmlPage(title='New Corpus')
        form = Form('new_callback')
        page.add(form)
        t = Table(Row(['Name:', TextBox('name')]),
                  Row([Submit('Create'), NBSP(), Submit('Cancel')]))
        form.add(t)
        return page

    ##  Callback from the new-corpus page.

    def new_callback (self, action=None, name=None):
        if action == 'Cancel': return Redirect('')
        else:
            if name.endswith('.cld'): fn = name
            else: fn = name + '.cld'
            Corpus.create(fn)
            return Redirect('corpus.%s' % hex_encode(fn))


#--  Corpus Metadata  ----------------------------------------------------------

##  Corpus metadata editor.
#   TODO: should modify MetadataEditor to take an optional 'keys' argument,
#   and do what this does.

class CorpusMetadataEditor (MetadataEditor):

    ##  The keys are 'title' and 'desc'.
    __keys__ = ['title', 'desc']

    ##  This is not an independent page; it provides a section of the
    #   permissions page.

    def insert_rows (self, table, form, disabled):
        metadata = self.file
        row = Row(table)
        String(row, 'Title:')
        TextBox(row, 'title', metadata.get('title') or '', disabled=disabled)
        row = Row(table)
        String(row, 'Desc:')
        TextArea(row, 'desc', metadata.get('desc') or '', disabled=disabled)
