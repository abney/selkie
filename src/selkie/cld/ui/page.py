##  @package seal.cld.ui.page
#   Provides PageEditor and PlainTextPanel.

from seal.core.misc import as_ascii
from seal.app.html import *
from seal.cld.db.disk import writer
from seal.cld.ui.text import TextMetadataEditor
from seal.cld.ui.igt import IGTEditor
from seal.cld.ui.course import DrillViewer
from seal.cld.ui.media import Media, MediaSelector, Transcriber, media_suffixes
from seal.cld.ui.audio import AudioEditor, WaveData
from seal.cld.ui.video import VideoData


#--  PlainText Editor  ---------------------------------------------------------
#
#  Text API:
#      t.title() - string
#      t.author() - string
#      t.orthography() - string
#      t.language() - a Language
#      t.has_translation() - boolean
#      t.plaintext() - a list of strings; ascii paragraphs
#      t.translation() - ditto
#      t.set_paragraph(i, orig, trans)
#      t.insert_paragraph(i, orig, trans)
#      t.delete_paragraph(i)
#      t.set_metadata(title, author, orthography)
#
#  Language API:
#      l.name() - string, ISO code
#      l.orthographies() - list of strings
#
#  EditableText API:
#      EditableText(roms, callback, cols, htmlclass)
#          - roms is list of Romanizations
#          - cols is list of (list of strings)
#      Callback: (command, idx, rom, text)
#          Forms:
#              'insert' i[.j] -- text
#              'set' i[.j] -- text
#              'delete' i -- --
#          If two-column, i.j, j=0 for orig, j=1 for trans
#          Else just i
#          Callback passes through __edit__ first; rom is only used for that
#


##  Page editor.
#   A page is a Text that has orig or media, and (optionally) trans.

class PageEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'home': 'root',
                 'edit': 'edit',
                 'call': 'call',
                 'edit_par': 'edit_par',
                 'meta': 'meta',
                 'igt': 'igt',
                 'media': 'media',
                 'audio': 'audio',
                 'xscript': 'xscript',
                 'drill': 'drill',
                 'data': 'data',
                 'add_par': 'add_par',
                 'add_sec': 'add_sec',
                 'translate': 'translate',
                 'uploader': 'uploader',
                 'upload': 'upload'}

    ##  Constructor.

    def __init__ (self, parent, page, nt=None): # page: Text
        HtmlDirectory.__init__(self, parent, page)
        if nt is None:

            ##  Indicates whether the translation column should be displayed (bool).
            self.parallel = None

        elif nt == 'wt':
            self.parallel = True
        elif nt == 'nt':
            self.parallel = False
        else:
            raise Exception('Bad value for nt: %s' % repr(nt))

    ##  Redirects to edit().
    def root (self): return Redirect('edit')

    ##  Returns a TextMetadataEditor.
    def meta (self): return TextMetadataEditor(self, self.file.info())

    ##  Returns an IGTEditor.
    def igt (self, *args): return IGTEditor(self, self.file, *args)

    ##  Returns an AudioEditor.
    def audio (self): return AudioEditor(self, self.file.audio)

    ##  Returns a Transcriber.
    def xscript (self):
        text = self.file
        if 'xscript' in text:
            xscript = text.xscript
        else:
            xscript = text.new_child('xscript')
        return Transcriber(self, xscript)

    ##  Returns a DrillViewer.
    def drill (self): return DrillViewer(self, self.file)

    ##  Returns the contents of the media file.
    def data (self, type): return self.file.media.data(type)

    ##  The main entry point.

    def edit (self):
        text = self.file #: Text
        title = text.title()
        rom = text.orthography()
        # **FIX** Should really generate an error page
        if rom and not text.env.find_rom(rom):
            rom = 'default'
        lang = text.language().name()
        subtype = text._info.get('subtype')
        media = text.get('media')
        plain = text.plaintext()

        htmlpage = HtmlPage(self, title=title)
        PathWithLogin(htmlpage)
        menu = MenuBar(htmlpage)
        # ../ is text, ../../ is higher toc
        Button(menu, '<<', '../../')
        if media is not None:
            if not text.permitted('write'):
                transcribe_url = None
            elif 'wav' in media:
                transcribe_url = 'audio/edit'
            else:
                transcribe_url = 'xscript/edit'
            Button(menu, 'Transcribe', transcribe_url)
        if self.parallel is None:
            self.parallel = 'trans' in text
            stem = self.cpt
        else:
            stem = self.cpt[:-3]
        if plain is not None:
            if 'trans' not in text:
                Button(menu, 'Translate', 'translate')
            elif self.parallel:
                Button(menu, 'Hide Translation', '../%s.nt/edit' % stem)
            else:
                Button(menu, 'Show Translation', '../%s.wt/edit' % stem)
        Button(menu, 'Properties', 'meta')
        if subtype == 'lesson':
            Button(menu, 'Drill', 'drill')

        # Header
        H1(htmlpage, text.title())
        p = P(htmlpage)
        it = I(p)
        String(it, 'Author: ')
        String(it, text.author() or 'not specified')
        String(it, '.  Language: ')
        String(it, text.language().name())
        String(it, '.  TextID: ')
        String(it, text.id())
        String(it, '.  Orthography: ')
        String(it, text.orthography())
        String(it, '.')

        # Add a Media element to the page
        if media: Media(htmlpage, media)

        if plain is None:
            if media:
                P(htmlpage, 'This recording has not been transcribed')
                ul = UL(htmlpage)
                Button(ul, 'Transcribe', transcribe_url)
            else:
                P(htmlpage, 'This text has no content yet.  What kind of text should it be?')
                ul = UL(htmlpage)
                Button(ul, 'Written text', 'add_par')
                Button(ul, 'Recording', 'uploader')
                Button(ul, 'Multi-page document', 'add_sec')
        else:
            PlainTextPanel(htmlpage, 'panel', plain, text.get('trans'), self.parallel)

        return htmlpage

    ##  The action for the 'Add Paragraph' button, when displaying a stub.

    def add_par (self):
        text = self.file
        with writer(text):
            text.append_par()
        return Redirect('edit')

    ##  The action for the 'Add Section' button, when displaying a stub.

    def add_sec (self):
        text = self.file
        with writer(text):
            text.create_toc()
        return Redirect('../edit')

    ##  Callback from PlainTextPanel.js.
    #   @arg op - 'insert', 'replace', 'delete'.
    #   @arg i - unit number, from 0.
    #   @arg j - column number: 0 = original, 1 = translation.

    def edit_par (self, op=None, i=None, j=None, text=None):
        value = as_ascii(text, use='alts')
        text = self.file
        i = int(i)
        j = int(j)

        with writer(text):
            if op == 'insert':
                assert j == 0
                text.insert_par(i, value)

            elif op == 'replace':
                if j == 0: text.set_orig(i, value)
                else: text.set_trans(i, value)
    
            elif op == 'delete': text.delete_par(i)
    
            else: raise Exception('Unrecognized command: %s' % op)

        # Decode the romanized text and return it to the javascript
        if j == 0: rom = text.romanization()
        else: rom = text.env.require_rom('default')
        return Text(rom.decode(value))

#    def replace_par (self, i=None, j=None, text=None):
#        i = int(i)
#        j = int(j)
#        if j == 0:
#            rom = self.text.romanization()
#            orig = text
#            trans = None
#        else:
#            rom = self.text.require_rom('default')
#            orig = None
#            trans = text
#        self.text.insert_paragraph(i, orig, trans)
#        return Text(self, rom.decode(text))

    ##  Ajax callback.
    #   @arg command - 'edit', 'insert', 'delete'.
    #   @arg idx - a string representing either a single digit or two digits joined
    #   by '.'.
    #   @arg rom - ignored.
    #   @arg text - contents of the target-language unit, unless the idx is a pair
    #   whose second element is 1, in which case this is the contents of the
    #   translation.

    def call (self, command=None, idx=None, rom=None, text=None):
        indices = tuple(int(i) for i in idx.split('.'))
        if len(indices) == 2:
            i = indices[0]
            if indices[1] == 0:
                orig = text
                trans = None
            elif indices[1] == 1:
                orig = None
                trans = text
            else:
                raise Exception('Bad indices: %s' % idx)
        elif len(indices) == 1:
            i = indices[0]
            orig = text
            trans = None
        else:
            raise Exception('Bad indices: %s' % idx)
        if command == 'edit':
            self.text.set_paragraph(i, orig, trans)
        elif command == 'insert':
            self.text.insert_paragraph(i, orig, trans)
        elif command == 'delete':
            self.text.delete_paragraph(i)
        else:
            raise Exception('Unrecognized command: %s' % command)
        
    ##  Return a media-file uploader page.

    def uploader (self):
        text = self.file
        id = text.id()
        title = 'Upload Media File %s' % id
        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        bar = MenuBar(page)
        Button(bar, '<<', '../')
        H1(page, title)

        form = Form(page, 'upload')
        table = Table(form, htmlclass='tabbing')
        cell = Cell(Row(table))
        BrowseButton(cell, 'contents')
        cell = Cell(Row(table))
        RadioButtons(cell, 'suffix', media_suffixes(), 'mp3')
        cell = Cell(Row(table))
        Submit(cell, 'Submit')
        Submit(cell, 'Abort')
        return page

    ##  Callback for the uploader page.

    def upload (self, contents=None, suffix=None, submit=None):
        if submit == 'Submit':
            if not (contents and suffix):
                raise Exception('Require both contents and suffix')
            text = self.file
            id = text.id()
            username = self.context.username
            fname = id + '.' + suffix
            mediadir = text.env.media()
            # this writes the physical media file
            mediadir.add(username, fname, contents)
            if 'media' in text:
                mf = text.media
            else:
                mf = text.new_child('media')
            with writer(mf):
                mf.set(username, fname)
            if 'xscript' not in text:
                text.new_child('xscript')

        return Redirect('../edit')

    ##  Create a trans child, if it does not already exist.

    def translate (self):
        text = self.file
        if 'trans' not in text:
            text.new_child('trans')
        return Redirect('edit')


#--  PlainTextPanel  -----------------------------------------------------------
#
#  The text must provide:
#    - romanization()
#    - plaintext()
#    - translation()
#  The editor that includes a PlainTextPanel in one of its pages must also
#  handle the callback:
#
#      edit_par(op, i, j, text)
#

##  A widget for displaying plaintext.

class PlainTextPanel (Widget):

    ##  Constructor.
    #   @arg plain - TokenFile or TransTokenFile.
    #   @arg trans - the Translation.
    #   @arg parallel - True if the translation should be displayed.

    def __init__ (self, parent, name, plain, trans, parallel):
        Widget.__init__(self, parent, name)
        
        if parallel:
            cls = 'ParallelText'
            dflt = self.file.env.require_rom('default')
            roms = [plain.romanization(), dflt]
            cols = [plain, trans]
        else:
            cls = 'PlainText'
            roms = [plain.romanization()]
            cols = [plain]

        H2(self, 'Text')

        npars = len(plain)
        writable = plain.permitted('write')

        if writable or npars > 0:
    
            div = Div(self, htmlid='textdiv')
            table = Table(div, htmlclass=cls)
                
            for i in range(npars):
                row = Row(table)
                String(Cell(row, htmlclass="parno"), str(i))
                for j in range(len(cols)):
                    s = str(cols[j][i])
                    cell = Cell(row, htmlclass="par")
                    EditableParagraph(cell, s, roms[j])

            init = Script(self)
            init.write('new PlainTextPanel(%s,%s);\r\n' % (
                    _js_bool_str(writable),
                    _js_bool_str(plain.transcription())))

        else:
            I(parent, 'There is currently no text.')

def _js_bool_str (x):
    if x: return 'true'
    else: return 'false'
