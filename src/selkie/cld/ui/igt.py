##  @package seal.cld.ui.igt
#   Provides IGTEditor.

from seal.app.html import *
from seal.cld.ui.text import TextMetadataEditor
from seal.cld.ui.lexicon import LexentViewer
from seal.cld.ui.conc import concordance


#--  IGT  ----------------------------------------------------------------------

##  Inserts a page element representing a word with its gloss.

def glossed_word (parent, index, token):
    glossed = Span(parent, htmlclass='glossed')
    glossed.set_attribute('data-index', index)
    glossed.set_attribute('data-ascii', token.form())
    glossed.set_attribute('data-seqno', str(token.sense()))

    String(glossed, token.unicode())
    BR(glossed)
    gloss = Span(glossed, htmlclass='gloss')
    String(gloss, token.lexent().get_gloss() or '?')


##  The IGT editor.

class IGTEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'home': 'edit',
                 'edit': 'edit',
                 #'get_lexent': 'get_lexent',
                 #'get_lexents': 'get_lexents',
                 #'save_lemma': 'save_lemma',
                 'save_token': 'save_token',
                 'save_text': 'save_text',
                 'conc': 'conc',
                 'meta': 'meta'}

    ##  Constructor.

    def __init__ (self, parent, text, parno=0, index=None):
        HtmlDirectory.__init__(self, parent, text) # text: Text

        ##  The plaintext.
        self.plain = text.plaintext()

        if self.plain is None:
            raise Exception('No plaintext: %s orig=%s' % (text, text['orig']))

        ##  The lexicon.
        self.lexicon = text.lexicon()

        ##  The sequence number of the displayed unit.
        self.parno = int(parno)

        ##  @var index
        ##  The index of the selected word, if any.

        if index is None: self.index = None
        else: self.index = int(index)

    ##  Returns a metadata editor for the containing text.

    def meta (self): return TextMetadataEditor(self, self.file.info())

    ##  Main entry point.

    def edit (self):
        page = HtmlPage(self, title='IGT: ' + self.file.title())
        PathWithLogin(page)
        menu = MenuBar(page)
        Button(menu, '<<', '../edit')
        Button(menu, 'Metadata', 'meta/')
        H1(page, self.file.title())

        table = Table(page, htmlclass='grid')
        row = Row(table)
        col1 = Cell(row)

        parno = self.parno
        H3(col1, 'Paragraph %d' % parno)

        #  parnos range from 0 to len(self.file)-1, inclusive.
        #  self.file is the Text.  self.plain is the plain text.

        if parno > 0: prev = '../igt.%d/edit' % (parno-1)
        else: prev = None
        if parno < len(self.plain)-1: next = '../igt.%d/edit' % (parno+1)
        else: next = None

        Button(col1, 'Prev', prev)
        String(col1, ' ')
        Button(col1, 'Next', next)

        textsDiv = Div(col1, htmlid='textsDiv')

        div = Div(textsDiv, htmlclass='igtparagraphs bordered')
        par = self.plain[parno]
        div.set_attribute('data-ascii', str(par))
        for (i, token) in enumerate(par):
            if div.contents: String(div, ' ')
            glossed_word(div, i, token)

        if 'trans' in self.file:
            trans = Div(textsDiv, htmlclass='trans bordered')
            String(trans, self.file.trans[parno])

        Button(col1, 'Prev', prev)
        String(col1, ' ')
        Button(col1, 'Next', next)

        col2 = Cell(row, htmlid='col2')

        LexentViewer(col2, 'lexentViewer', self.lexicon)

        page.add_stylesheet('IGTEditor')
        page.add_import('IGTEditor')

        index = self.index
        if index is None: index = 'null'
        else: index = "'%s'" % index
        if self.file.permitted('write'): writable = 'true'
        else: writable = 'false'
        Script(page, "IGTEditor(lexentViewer,'%s',%s,%s);\r\n" % (parno, index, writable))

        return page

#    def get_lexents (self, form, sense):
#        return LexentPanelText(self.lexicon, form, int(sense))
#
#    def get_lexent (self, form, sense):
#        return LexentText(self.lexicon[form, int(sense)])
#
#    def save_lemma (self, parno, index, lemma, seqno, submit, **kwargs):
#        seqno = int(seqno)
#        with self.lexicon.lock() as lock:
#            lock.set_fields(lemma, seqno, kwargs)
#        # self.file.set_seqno(parno, index, seqno)
#        # self.file.save()
#        return Redirect('edit.%s.%s' % (parno, index))
        
    ##  Callback to modify a token.

    def save_token (self, parno, index, seqno, ascii):
        try:
            i = ascii.rindex('.')
            s = ascii[i+1:]
            if s.isdigit():
                ascii = ascii[:i]
                seqno = s
        except: pass
        parno = int(parno)
        index = int(index)
        seqno = int(seqno)
        token = self.file.orig.set_token(parno, index, ascii, seqno)
        return Text(token.unicode())

    ##  Callback to save the text.

    def save_text (self, orig=None, trans=None, submit=None):
        if orig is not None:
            self.file.set_orig(self.parno, orig)
        if trans is not None:
            self.file.set_trans(self.parno, trans)
        return Redirect('edit')

    ##  Produce a concordance.

    def conc (self, lxid):
        return concordance(self, self.lexicon, lxid)

        
#--  Tokenized Text  -----------------------------------------------------------

# class TokenizedTextEditor (Editor):
# 
#     __pages__ = {'': 'root',
#                  'copy': 'copy',
#                  'sent': 'sent',
#                  'view': 'view'}
# 
#     def __init__ (self, text):
#         HtmlDirectory.__init__(self)
#         self.file = text
# 
#     def root (self):
#         text = self.file
#         name = text.name()
#         writable = text.writable()
# 
#         page = HtmlPage(title=self.file.name())
#         page.add(PathWithLogin(self))
#         page.add(MenuBar(Button('Copy', 'copy')))
#         table = Table()
#         page.add(table)
#         for (i, sent) in enumerate(text.sentences, 1):
#             contents = ' '.join(sent.words())
#             if writable: edit = 'sent.%s/edit' % i
#             else: edit = None
#             table.add(Row(Link(contents, 'sent.%d/view' % i), Button('Edit', edit)))
#         return page
# 
#     def copy (self):
#         text = self.file.copy()
#         return Redirect('../text.%s' % text.name())
# 
#     def sent (self, i):
#         i = int(i)
#         text = self.file
#         s = text.sentences[i-1]
#         return SentenceEditor(s, text, i)


#--  Sentence Editor  ----------------------------------------------------------

#class SentenceEditor (HtmlDirectory):
#
#    __pages__ = {'': 'root',
#                 'edit': 'edit',
#                 'edit_callback': 'edit_callback',
#                 'view': 'view'}
#
#    def __init__ (self, sent, text, i):
#        HtmlDirectory.__init__(self)
#        self.sentence = sent
#        self.text = text
#        self.i = i
#
#    def root (self):
#        return Redirect('view')
#
#    def view (self):
#        sent = self.sentence
#
#        page = HtmlPage(title='%s sentence %d' % (self.text.name(), self.i))
#        page.add(PathWithLogin(self))
#        table = Table(Header('', 'Form', 'Cat', 'CPos', 'Lemma', 'Morph', 'Govr', 'Role'))
#        page.add(table)
#        for w in sent[1:]:
#            if w.govr or w.govr == 0: g = str(w.govr)
#            else: g = ''
#            table.add(Row(str(w.index),
#                          w.form or '',
#                          w.cat or '',
#                          w.cpos or '',
#                          w.lemma or '',
#                          w.morph or '',
#                          g,
#                          w.role or ''))
#        return page
#
#    def edit (self):
#        sent = self.sentence
#
#        page = HtmlPage(title='%s sentence %d' % (self.text.name(), self.i))
#        page.add(PathWithLogin(self))
#        form = Form('edit_callback')
#        page.add(form)
#        table = Table(Header('', 'Form', 'Cat', 'CPos', 'Lemma', 'Morph', 'Govr', 'Role'))
#        form.add(table)
#        for i in range(1, len(sent)):
#            w = sent[i]
#            if w.govr or w.govr == 0: g = str(w.govr)
#            else: g = ''
#            table.add(Row(str(w.index),
#                          TextBox('form.%d' % i, w.form or '', size=10),
#                          TextBox('cat.%d' % i, w.cat or '', size=6),
#                          TextBox('cpos.%d' % i, w.cpos or '', size=6),
#                          TextBox('lemma.%d' % i, w.lemma or '', size=10),
#                          TextBox('morph.%d' % i, w.morph or '', size=6),
#                          TextBox('govr.%d' % i, g, size=4),
#                          TextBox('role.%d' % i, w.role or '', size=6)))
#        form.add(P(Submit('Submit'), Submit('Cancel')))
#        return page
#
#    def edit_callback (self, **kwargs):
#        if kwargs['action'] == 'Submit':
#            sent = self.sentence
#            for key in kwargs:
#                if key == 'action': continue
#                (attr, i) = key.split('.')
#                i = int(i)
#                if attr not in ('form', 'cat', 'cpos', 'lemma', 'morph', 'govr', 'role'):
#                    raise Exception('Bad attribute')
#                w = sent[i]
#                setattr(w, attr, kwargs[key])
#            self.text.save()
#        return Redirect('..')
#            
