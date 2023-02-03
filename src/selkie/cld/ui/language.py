##  @package seal.cld.ui.language
#   Provides LanguageEditor and related classes.

from seal.app.html import *
from seal.data.langdb import languages
from seal.cld.db.disk import writer
from seal.cld.ui.file import MetadataEditor
from seal.cld.ui.toc import TocEditor
from seal.cld.ui.lexicon import LexiconEditor
from seal.cld.ui.conc import concordance


#--  language_attributes  ------------------------------------------------------

##  Returns a list of pairs representing attributes of the given language.

def language_attributes (lg):
    specs = [('639-3', lg.code)]
    if lg.code2b:
        specs.append(('639-2/B', lg.code2b))
    if lg.code2t:
        specs.append(('639-2/T', lg.code2t))
    if lg.code1:
        specs.append(('639-1', lg.code1))
    scopes = {'I': 'language',
              'M': 'macrolanguage',
              'S': 'special code',
              'R': 'retired code'}
    specs.append(('scope', scopes[lg.scope]))
    types = {'A': 'ancient',
             'C': 'constructed',
             'E': 'extinct',
             'H': 'historical',
             'L': 'living',
             'S': 'special code',
             'R': 'retired code'}
    specs.append(('type', types[lg.type]))
    specs.append(('name', lg.name))
    aka = sorted(nm for nm in lg.names if nm != lg.name)
    if aka:
        specs.append(('aka', ', '.join(aka)))
    if lg.parent:
        specs.append(('parent', lg.parent))
    if lg.members:
        specs.append(('members', ', '.join(x.name for x in lg.members)))
    ret = lg.retirement
    if ret:
        if ret.reason == 'C':
            specs.append(('changed-to', ret.replacement))
        elif ret.reason == 'D':
            specs.append(('duplicate-of', ret.replacement))
        elif ret.reason == 'M':
            specs.append(('merger', ret.replacement))
        elif ret.reason == 'S':
            specs.append(('split-into', ret.split))
        elif ret.reason == 'N':
            specs.append(('non-existent', ''))
        else:
            specs.append(('retired', '??'))
    return specs


def _as_string (x):
    if isinstance(x, str): return x
    else: return repr(x)

##  Inserts a table of language information into the page.

def LanguageInfo (page, lang):
    H2(page, 'Language: %s (%s)' % (lang.name, lang.code))
    table = Table(page)
    for (key,value) in language_attributes(lang):
        row = Row(table)
        String(Cell(row), _as_string(key))
        String(Cell(row), _as_string(value))


#--  LanguageListEditor  -----------------------------------------------------

##  A language list editor.
#   Clicking on 'Languages' on the corpus page takes you here.
#   Each Language represents a different language for which we have items.

class LanguageListEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'home': 'view',
                 'view': 'view',
                 'lang': 'lang',
                 'add': 'addlang',
                 'lgsel': 'lgsel',
                 'confirm': 'confirm',
                 'confirmed': 'confirmed'}

    ##  Returns the corpus.

    def corpus (self):
        return self.file.env['root']

    ##  Main entry point.

    def view (self):
        page = HtmlPage(self, title='Languages')
        PathWithLogin(page)
        menu = MenuBar(page)
        Button(menu, '<<', '..')
        Button(menu, 'Search', 'lgsel/')
        H1(page, 'Languages')
        ul = UL(page)
        for (name, id) in sorted((languages[name].name, name) for name in self.file):
            Link(ul, '%s [%s]' % (name, id), 'lang.%s/' % id)
        if self.file.permitted('write'):
            Button(page, '+', 'add')
        return page

    ##  Returns a LanguageSelector.

    def addlang (self): return LanguageSelector(self, self.file)

    ##  Synonym for addlang().

    def lgsel (self): return LanguageSelector(self, self.file)

    ##  Returns a LanguageEditor for the language with the given code.
    #   If the language is not already present in the corpus, this
    #   returns a confirmation page.

    def lang (self, code):
        if code in self.file:
            return LanguageEditor(self, self.file[code])
        else:
            return self.confirm(code)

    ##  Generates the confirmation page.  It shows a language description
    #   and asks whether to add it to the corpus.

    def confirm (self, code):
        if code in languages:
            lang = languages[code]
            writable = self.corpus().permitted('write')
            if writable: title = 'Confirm Add Language'
            else: title = code
            page = HtmlPage(self, title=title)
            PathWithLogin(page)
            H1(page, title)
            LanguageInfo(page, lang)
            p = P(page)
            if writable:
                Button(p, 'Confirm', 'confirmed.%s' % lang.code)
                NBSP(p)
                Button(p, 'Cancel', 'view')
            else:
                Button(p, 'Back', 'view')
            return page
        else:
            page = HtmlPage(self, title='Error')
            P(page, 'Not a language: %s' % code)
            Button(page, '', 'Return')
            return page

    ##  Callback from the confirmation page.

    def confirmed (self, code):
        if code in languages:
            ll = self.file
            with writer(ll):
                ll.new_child(code)
            return Redirect('lang.%s/' % code)
        else:
            page = HtmlPage(self, title='Error')
            P(page, 'Not a language: %s' % code)
            Button(page, '', 'Return')
            return page


##  Language selector.

class LanguageSelector (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'home': 'view',
                 'bycode': 'bycode',
                 'selected': 'selected',
                 'commit': 'commit',
                 'search_results': 'search_results'}

    ##  Constructor.

    def __init__ (self, parent, langlist):
        HtmlDirectory.__init__(self, parent)

        ##  The list of languages.
        self.langlist = langlist

    ##  Gets the corpus from the environment.

    def corpus (self): return self.langlist.env.corpus()

    ##  Main entry point.

    def view (self):
        corp = self.corpus()
        writable = corp.permitted('write')
        if writable: title = 'Add Language'
        else: title = 'Search'
        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        menu = MenuBar(page)
        Button(menu, '<<', '../')
        H1(page, title)

        form = Form(page, 'bycode')
        p = P(form, htmlclass='display')
        String(p, 'Language Code:')
        NBSP(p, 2)
        TextBox(p, 'lang', size='3')
        BR(p)
        Submit(p, 'Submit')
        Submit(p, 'Cancel')

        form = Form(page, 'search_results')
        Hidden(form, 'action', 'add')
        p = P(form, htmlclass='display')
        String(p, 'Search: ')
        NBSP(p, 2)
        TextBox(p, 'text', size='30')
        BR(p)        
        Submit(p, 'Submit')
        Submit(p, 'Cancel')

        return page

    ##  Callback from the selection page.  Asks the user for confirmation
    #   to add the language.

    def bycode (self, submit, lang):
        if submit == 'Cancel':
            return Redirect('../')
        else:
            return self.selected(lang)

    ##  Generates the confirmation page.

    def selected (self, lang):
        if lang in languages:
            lg = languages[lang]
            corp = self.corpus()
            writable = corp.permitted('write')
            if writable: title = 'Add Language'
            else: title = 'Search Results'
            page = HtmlPage(self, title=lg.code)
            PathWithLogin(page)
            bar = MenuBar(page)
            Button(bar, '<<', './')
            LanguageInfo(page, lg)
            p = P(page)
            if writable:
                Button(p, 'Confirm', 'commit.%s' % lg.code)
                NBSP(p)
                Button(p, 'Cancel', './')
            else:
                Button(p, 'Back', './')
            return page
        else:
            page = HtmlPage(self, title='Error')
            P(page, 'Not a language: %s' % lang)
            Button(page, '', 'Return')
            return page

    ##  Callback from the confirmation page.

    def commit (self, lang):
        if lang in languages:
            return Redirect('../confirmed.%s' % lang)
        else:
            page = HtmlPage(self, title='Error')
            P(page, 'Not a language: %s' % lang)
            Button(page, 'Back', './')
            return page

    ##  Display page for a list of search results.

    def search_results (self, submit, text, action):
        if submit == 'Cancel':
            return Redirect('../')
        else:
            results = [set(languages.named(text) or []),
                       set(languages.find(text) or []),
                       set(languages.search(text) or [])]
            titles = ['Name is', 'Name word is', 'Name word contains']
            displayed = set()
            page = HtmlPage(self, title='Results')
            PathWithLogin(page)
            menu = MenuBar(page)
            Button(menu, '<<', './')
            H2(page, 'Languages matching: %s' % text)
            if not any(results):
                I(page, 'No matches found')
            else:
                for i in range(3):
                    increment = results[i] - displayed
                    if increment:
                        H3(page, titles[i] + ' ' + text)
                        table = Table(page)
                        for lg in sorted(increment, key=lambda lg: lg.name):
                            displayed.add(lg)
                            row = Row(table)
                            String(Cell(row), ', '.join(lg.names))
                            if lg.code in self.langlist: tgt = '../lang.%s' % lg.code
                            else: tgt = 'selected.%s' % lg.code
                            Link(Cell(row), lg.code, tgt)
            return page


#--  Language Editor  --------------------------------------------------------

##  A language editor.  Lists the texts for this language.

class LanguageEditor (HtmlDirectory):

    ##  Maps page names to method names.
    __pages__ = {'home': 'view',
                 'view': 'view',
                 'meta': 'meta',
                 'texts': 'texts',
                 'lexicon': 'lexicon',
                 'conc': 'concordance',
                 'course': 'course'}

    ##  Constructor.

    def __init__ (self, parent, lang):
        HtmlDirectory.__init__(self, parent, lang)
        context = self.context
        context.lang_editor = self
        context.lang = lang

        ##  The language, a file of type Language.
        self.lang = lang

    ##  The main entry point.

    def view (self):
        ent = self.lang.dbentry()
        title = '%s (%s)' % (ent.name, ent.code)
        page = HtmlPage(self, title=title)
        PathWithLogin(page)
        menu = MenuBar(page)
        Button(menu, '<<', '../')
        Button(menu, 'Metadata', 'meta')
        H1(page, title)
        ul = UL(page)
        if self.lang.texts.permitted('read'):
            Link(ul, 'Texts', 'texts')
        Link(ul, 'Lexicon', 'lexicon/')
        #Link(ul, 'Course', 'course')
        return page

    ##  Returns a LanguageMetadataEditor.

    def meta (self):
        return LanguageMetadataEditor(self, self.lang.metadata())

    ##  Returns a TocEditor.

    def texts (self):
        return TocEditor(self, self.lang.texts)

    ##  Returns a LexiconEditor.

    def lexicon (self):
        return LexiconEditor(self, self.lang.lexicon)

    ##  Returns a concordance page.

    def concordance (self, index):
        return concordance(self, self.lang.lexicon, int(index))

    ##  Returns a CourseEditor.

    def course (self):
        return CourseEditor(self, self.lang.course)


##  A language metadata editor.

class LanguageMetadataEditor (MetadataEditor):

    ##  The metadata keys.  Currently just 'orthographies'.
    __keys__ = ['orthographies']

    ##  Insert a header before the form.

    def insert_preamble (self, page):
        lang = self.file.host
        LanguageInfo(page, lang.dbentry())
        H3(page, 'Properties')

    ##  Insert the actual contents.

    def insert_rows (self, table, form, disabled):
        orths = self.file.host.get('orthographies')
        row = Row(table)
        String(row, 'Orthographies:')
        TextBox(row, 'orthographies', orths, disabled=disabled)

    ##  Insert an informational message after the form.

    def insert_coda (self, page):
        I(P(page), 'Orthographies are comma-separated.  The first listed will be the default.')
