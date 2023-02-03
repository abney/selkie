##  @package seal.cld.ui.lexicon
#   Contains LexiconEditor and related classes.

from seal.app.html import *

from seal.core.misc import quoted
from seal.cld.db.disk import writer
from seal.cld.ui.file import hex_encode, hex_decode
from seal.cld.ui.conc import concordance


#--  LexiconEditor  ------------------------------------------------------------

##  An editor for a lexicon.

class LexiconEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'': 'home',
                 'home': 'home',
                 'search': 'search',
                 'search_result': 'search_result',
                 'form': 'form',
                 'gloss': 'gloss',
                 'entry': 'entry',
                 'browse': 'browse',
                 'conc': 'conc'}

    ##  Constructor.

    def __init__ (self, parent, lexicon):
        HtmlDirectory.__init__(self, parent, lexicon)

        ##  The lexicon.
        self.lexicon = lexicon

    ##  Main entry point.

    def home (self):
        return Redirect('browse')

    ##  Construct and return a MenuBar.

    def lexicon_menu (self, page, omit=None):
        menu = MenuBar(page)
        Button(menu, '<<', '../')
        if omit != 'search':
            Button(menu, 'Search', 'search')
        if omit != 'browse':
            Button(menu, 'Browse', 'browse')
        Button(menu, 'Texts', '../texts')
        return menu

    ##  The search page.

    def search (self):
        lex = self.lexicon
        title = 'Lexicon %s' % lex.language().name()
        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        self.lexicon_menu(page, omit='search')
        H1(page, title)
        form = Form(page, 'search_result')
        table = Table(form, htmlclass='grid')
        row = Row(table)
        cell = Cell(row)
        String(cell, 'Form: ')
        cell = Cell(row)
        TextBox(cell, 'form', htmlid='textbox')
        row = Row(table)
        cell = Cell(row)
        String(cell, 'Gloss: ')
        cell = Cell(row)
        TextBox(cell, 'gloss')
        row = Row(table)
        cell = Cell(row, colspan=2)
        Submit(cell, 'Submit')
        page.focus('textbox')
        return page

    ##  Callback from the search page.

    def search_result (self, form=None, gloss=None, submit=None):
        if form:
            return Redirect('form.%s' % hex_encode(form))
        elif gloss:
            return Redirect('gloss.%s' % hex_encode(gloss))            
        else:
            raise HttpException('No POST data provided')

    ##  Return a lexical-entry viewer for a given form.

    def form (self, id):
        return self.lexent_viewer('Form', form=id)

    ##  Return a lexical-entry viewer for a given gloss.

    def gloss (self, id):
        return self.lexent_viewer('Gloss', gloss=id)

    ##  Create a lexent-viewer page.

    def lexent_viewer (self, title, form=None, gloss=None):
        if form is not None:
            term = form = hex_decode(form)
        if gloss is not None:
            term = gloss = hex_decode(gloss)
        title += ' ' + term
        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        self.lexicon_menu(page)
        H1(page, title)
        LexentViewer(page, 'lexent', self.lexicon, form=form, gloss=gloss,
                     notitle=True)
        return page

    ##  Create a lexent-viewer page for a particular lexical entry.

    def entry (self, index):
        index = int(index)
        lexent = self.lexicon.by_index(index)
        title = lexent.name()
        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        self.lexicon_menu(page)
        H1(page, title)
        LexentViewer(page, 'lexent', self.lexicon, form=lexent.form(), sense=lexent.sense(),
                     notitle=True)
        return page

    ##  Create a browsing page for a particular letter.

    def browse (self, letter=None):
        if letter is None: letter = 'a'
        forms = self.lexicon.forms
        page = HtmlPage(self, title=letter)
        PathWithLogin(page)
        menu = self.lexicon_menu(page, omit='browse')
        menu = MenuBar(page)
        for l in 'abcdefghijklmnopqrstuvwxyz':
            if l == letter: target = None
            else: target = 'browse.' + l
            if target: Link(menu, l.upper(), target)
            else: String(menu, l.upper())
        H2(page, letter)
        ul = UL(page)
        for form in self.lexicon.by_letter(letter):
            # this needs to be decoded
            Link(ul, form, 'form.' + hex_encode(form))
        return page

    ##  Create a concordance for a particular lexical entry.

    def conc (self, lxid):
        return concordance(self, self.lexicon, lxid)


#--  LexentViewer Element  -----------------------------------------------------

##  A LexentViewer widget.

class LexentViewer (Widget):

    ##  Maps page names to method names.
    __pages__ = {'get_contents': 'get_contents',
                 'get_lexent': 'get_lexent',
                 'save_lemma': 'save_lemma'}

    ##  Constructor.

    def __init__ (self, parent, name, lexicon, form=None, sense=None, gloss=None, notitle=False):
        Widget.__init__(self, parent, name)
        viewer_url = self.__relative__()
        lang_url = self.__extern__('/langs/lang.%s' % lexicon.language().name())

        ##  The lexicon.
        self.lexicon = lexicon

        ##  The form.
        self.form = form

        ##  The gloss.
        self.gloss = gloss

        Div(self, htmlclass='groupingDiv', htmlid='lexentViewer')
        
        script = Script(self)
        if lexicon.permitted('write'): writable = 'true'
        else: writable = 'false'
        String(script, "var %s = new LexentPanel('%s','%s',%s);\r\n" % (name, viewer_url, lang_url, writable))
        
        # This is clunky, may break depending on language
        # should be improved
        if form or gloss:
            text = LexentPanelText(self, lexicon, form, sense, gloss, notitle=notitle)
            cnts = text.to_string(headers=False)
            String(script, "%s.setContents(JSON.parse(%s));\r\n" % (name, repr(cnts)))

    ##  Returns a LexentText instance.

    def get_lexent (self, form, sense):
        return LexentText(self, self.lexicon[form, int(sense)])

    ##  Returns a LexentPanelText instance.
    #   Called by LexentPanel.display1 (LexentViewer.js).
    #   That in turn is called by IGTEditor when a token is selected.

    def get_contents (self, form=None, sense=None, gloss=None):
        if sense: sense = int(sense)
        return LexentPanelText(self, self.lexicon, form, sense, gloss)

    ##  Callback to save a modified lemma.

    def save_lemma (self, lemma=None, seqno=None, submit=None, **fields):
        page = self.__page__()
        seqno = int(seqno)
        lex = self.lexicon
        with writer(lex):
            lex.set_fields(lemma, seqno, fields)
        # self.text.set_seqno(parno, index, seqno)
        # self.text.save()

        # The current URL is e.g. .../igt.2.2/edit/lexentViewer/save_lemma.
        # Doing Redirect('..') is interpreted by the browser as redirect to
        # .../igt.2.2/edit/, with a trailing slash.  Therefore we use the complete
        # pathname for the page instead.
        #
        return Redirect(page.cpt.pathname)



#--  Lexent Texts  -------------------------------------------------------------
#
#  JSON response texts
#

##  Write the lexent in JSON format to the text.

def write_lexent (ent, text):
    text.write('{')
    text.write('"index":"%d"' % ent.index())
    text.write(',"lemma":%s' % quoted(ent.form()))
    text.write(',"seqno":"%d"' % ent.sense())
    for (f,v) in ent.fields():
        text.write(',"%d":%s' % (f.index, quoted(f.value.tostring(v))))
    text.write('}')


##  Text containing the JSON representation of a lexical entry, for an Ajax callback.

class LexentText (Text):

    ##  Constructor.

    def __init__ (self, parent, lexent):
        Text.__init__(self)
        write_lexent(lexent, self)


#   The buried calls to _write_toggle have the side-effect of recording the
#   lexents that are encountered.

##  A Text containing JSON information for a Lexent panel.

class LexentPanelText (Text):

    ##  Constructor.

    def __init__ (self, parent, lexicon, form=None, sense=None, gloss=None, notitle=False):
        assert (form or gloss)
        assert (not (form and gloss))
        Text.__init__(self)

        ##  The lexicon
        self.lexicon = lexicon

        ##  The form.
        self.form = None

        ##  The title.
        self.title = None

        ##  The senses.
        self.senses = None

        ##  The gloss.
        self.gloss = None

        ##  The lexents
        self.lexents = set()

        if form is not None:
            self.form = form
            if notitle: self.title = ''
            elif sense is None: self.title = form
            else: self.title = '%s.%d' % (form, sense)
            self.senses = lexicon.get(form)
            if sense: self.gloss = self.senses[sense].get_gloss()
            else: self.gloss = None
        elif gloss is not None:
            self.gloss = gloss
            self.title = gloss
            self.form = None
            self.senses = None
        self.write_panel()

    ##  Write the JSON data for the panel.

    def write_panel (self):
        self.write('{')
        self.write('"title":%s' % quoted(self.title))
        self.write(',"senses":')
        self.write_senses()
        self.write(',"similar":')
        self.write_similar_forms()
        self.write(',"glosses":')
        self.write_similar_glosses()
        self.write(',"lexents":')
        self.write_lexents()
        self.write('}')

    ##  Write the list of senses.

    def write_senses (self):
        self.write('[')
        if self.senses:
            first = True
            for lexent in self.senses:
                if lexent is not None:
                    if first: first = False
                    else: self.write(',')
                    self.write_toggle(lexent)
        self.write(']')

    ##  Write the toggle information.  Has the side effect of adding the lexent
    #   to the list of lexents.

    def write_toggle (self, lexent):
        self.lexents.add(lexent)
        self.write('[%s,"%d"]' % (quoted(lexent.form()), lexent.sense()))

    # TO FIX: this will fail if there is a " in the form

    ##  Write the list of similar forms.

    def write_similar_forms (self):
        self.write('[')
        if self.form:
            forms = self.lexicon.similar_forms(self.form)
            first = True
            for form in forms:
                for lexent in self.lexicon[form]:
                    if first: first = False
                    else: self.write(',')
                    self.write_toggle(lexent)
        self.write(']')

    ##  Write the list of similar glosses.

    def write_similar_glosses (self):
        self.write('[')
        if self.gloss:
            glosses = self.lexicon.similar_glosses(self.gloss, exclude_self=False)
            first = True
            for gloss in glosses:
                for lexent in self.lexicon.by_gloss(gloss):
                    if first: first = False
                    else: self.write(',')
                    self.write_toggle(lexent)
        self.write(']')

    ##  Write the list of lexents.

    def write_lexents (self):
        self.write('[')
        first = True
        for ent in self.lexents:
            if first: first = False
            else: self.write(',')
            write_lexent(ent, self)
        self.write(']')
