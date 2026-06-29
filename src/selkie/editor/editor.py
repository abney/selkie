
from asyncio import ensure_future
from pathlib import Path
from ..corpus.corpus import Corpus, CorpusLocation, Language, Text, Sentence
from ..wap import Element, EditableCell


def first (g):
    try:
        return next(g)
    except StopIteration:
        return None


class EditorElement (Element):

    def PlainTextPanel (self, text, **kwargs):
        return self.create(PlainTextPanel, text, **kwargs)


class Editor (EditorElement):

    def __init__ (self, server_proxy):
        EditorElement.__init__(self, None, None)
        self.server_proxy = server_proxy
        self.location = CorpusLocation(None)
        self.location.view = 'open'
        self.viewers = {
            'open': OpenPage,
            'corp': CorpusPage,
            'lang': LanguagePage,
            'text': TextPage
        }

        self.goto_page('open')

    def edit (self, item):
        self.set_location(item)
        loc = self.location
        view = loc.view or item.key_type()
        self.goto_page(view)

    def goto_page (self, name=None):
        self.clear()
        if name is None:
            name = self.location.view
            assert name is not None
        else:
            self.location.view = name
        page = self.viewers[name]
        self.construct_menu()
        self.create(page)

    def set_location (self, item):
        old_loc = self.location
        loc = self.location = item.location()
        for key in ('corpus', 'language', 'text', 'sentence', 'token', 'word'):
            if getattr(loc, key) is None:
                setattr(loc, key, getattr(old_loc, key))
        if isinstance(item, Corpus):
            if loc.language is None:
                loc.language = first(item.children())
            if loc.text is None and loc.language is not None:
                loc.text = first(loc.language.children())

    def construct_menu (self):
        loc = self.location
        menubar = self.document.MenuBar()
        views = []

        if loc.corpus is None:

            menu = menubar.Menu('open')

        else:

            menu = menubar.Menu(loc.corpus.key, self.edit_corpus)
            menu.MenuItem('+', self.choose_file)

#            views.append('corp')

            title = 'Langs'
            if loc.language is not None:
                title = loc.language.key
                views.append('lang')
            menu = menubar.Menu(title, self.edit_language, title)
            for name in loc.corpus.table:
                if name != title:
                    menu.MenuItem(name, self.edit_language, name)

            title = 'Texts'
            if loc.text is not None:
                title = loc.text.key
                views.append('text')
            menu = menubar.Menu(title, self.edit_text, title)
            if loc.language:
                for name in loc.language.table:
                    if name != title:
                        menu.MenuItem(name, self.edit_text, name)

#         view = loc.view
#         menu = menubar.Menu(view)
# 
#         for alt in views:
#             if alt != view:
#                 menu.MenuItem(alt, self.goto_page, alt)

    def choose_file (self):
        self.goto_page('open')

    def open_corpus (self, fn):
        doc = self.document
        doc.clear()
        doc.write('Opening corpus', fn, '...')
        ensure_future(self._open_corpus(fn))

    async def _open_corpus (self, fn):
        print('Enter _open_corpus', fn)
        contents = await self.server_proxy.load(fn)
        print('Got contents')
        self.edit(Corpus(fn, contents=contents))

    def edit_corpus (self):
        self.edit(self.location.corpus)

    def edit_language (self, name):
        lang = self.location.corpus.table[name]
        self.edit(lang)

    def edit_text (self, name):
        text = self.location.language.table[name]
        self.edit(text)
        

#--  Mid-level components  -----------------------------------------------------

class SentenceCell (EditableCell):

    def __init__ (self, parent, sent, **kwargs):
        EditableCell.__init__(self, parent, sent.string, sent.set_string, **kwargs)


class PlainTextPanel (EditorElement):

    def __init__ (self, parent, text):
        Element.__init__(self, parent, 'div')
        assert isinstance(text, Text)
        self.text = text
        self.H2('Text')
        self.table = self.Table(classname='grid')

        for sent in text:
            row = self.table.Row()
            row.create(SentenceCell, sent)


class PropertyCell (EditableCell):

    def __init__ (self, parent, meta, key):
        # EditableCell.__init__ is going to call self.get in order to display itself
        self.meta = meta
        self.key = key
        EditableCell.__init__(self, parent, self.get, self.set, classname='editable')

    def get (self):
        return self.meta[self.key]

    def set (self, value):
        self.meta[self.key] = value
    

class PropertyTable (EditorElement):

    def __init__ (self, parent, meta):
        Element.__init__(self, parent, 'table', classname='noborder')
        self.meta = meta

        for (key, value) in self.meta.items():
            if not isinstance(value, dict):
                row = self.Row()
                cell = row.TD()
                cell.write(key)
                row.create(PropertyCell, self.meta, key)

        
#--  Pages  --------------------------------------------------------------------

class Page (EditorElement):

    def __init__ (self, editor, **kwargs):
        Element.__init__(self, editor, 'div', **kwargs)
        self.editor = editor


class OpenPage (Page):

    def __init__ (self, editor, **kwargs):
        Page.__init__(self, editor, **kwargs)
        self.H2('Open')
        div = self.Div()
        self.ul = div.UL()
        li = self.ul.LI()
        li.write('Corpus: ')
        box = li.TextEntry(submit=self.editor.open_corpus)
        box.focus()
        ensure_future(self.list_dir())

    async def list_dir (self):
        print('List Dir')
        text = await self.editor.server_proxy.list_dir()
        lst = [fn for fn in text.split('\n') if fn.endswith('.cld')]
        print('lst=', repr(lst))
        for fn in lst:
            li = self.ul.LI()
            button = li.Button(value=fn)
            button.write(fn)
            button.add_listener('click', self.submit)

    def submit (self, evt):
        self.editor.open_corpus(evt.target.value)


class CorpusPage (Page):

    def __init__ (self, editor, **kwargs):
        Page.__init__(self, editor, **kwargs)
        corpus = editor.location.corpus
        self.H2('Corpus')
        self.write('Filename: ', corpus.filename())
        p = self.P()
        button = p.Button()
        button.write('Download')
        button.add_listener('click', self.download)

    def download (self, evt):
        print('Click Download')
        corpus = self.editor.location.corpus
        self.download_file(corpus.name, corpus.cld_format())
        print('End Click')


class LanguagePage (Page):

    def __init__ (self, editor, **kwargs):
        Page.__init__(self, editor, **kwargs)
        lang = self.language = editor.location.language
        self.H2('Language')
        self.create(PropertyTable, lang.meta)


class TextPage (Page):

    def __init__ (self, editor, **kwargs):
        Page.__init__(self, editor, **kwargs)
        self.PlainTextPanel(editor.location.text)
        

class IGTPage (Page):

    def __init__ (self, editor, **kwargs):
        Page.__init__(self, editor, **kwargs)
        


#     var table = div.firstElementChild;
#     var ncols = table.rows[0].cells.length;
# 
#     this.writable = writable;
#     this.transcribed = transcribed;
#     this.elt = table;
#     this.ncols = ncols;
#     this.plusButton = null;
#     this.server = new Server();
#     this.editbox = new EditBox();
# 
#     // Initialize existing cells
#     var rows = table.rows;
#     for (var i = 0; i < rows.length; ++i) {
# 	var cells = rows[i].cells;
# 	var par = new Par(this, i, 'old');
# 	// cell 0 contains the row number
# 	for (var k = 1; k < cells.length; ++k) {
# 	    var cell = cells[k];
# 	    var p = cell.firstChild;
# 	    var ascii = Element.htmlValueDecode(p.getAttribute('data-value'));
# 	    var text = new Text(par, k-1, ascii, p);
# 	    cell.text = text;
# 	    par.texts[k-1] = text;
# 	}
#     }
# 
#     // Add-button
#     if (writable) {
# 	var button = Element.button('+', PlainTextPanel.clickPlusButton, this);
# 	div.appendChild(Element.par(button));
# 	this.plusButton = button;
#     }
# }
# 
# PlainTextPanel.clickPlusButton = function (evt) {
#     var table = evt.target.control;
#     var text = table.appendRow();
#     text.edit();
# };
# 
# PlainTextPanel.prototype.insertText = function (ascii, i) {
#     var row = this.elt.insertRow(i);
# 
#     var cell = row.insertCell(-1);
#     cell.appendChild(document.createTextNode('' + i));
#     cell.className = 'parno';
# 
#     var tgtText;
#     var par = new Par(this, i, 'new');
#     for (var k = 1; k < this.ncols; ++k) {
# 	var text = new Text(par, k-1, ascii);
# 	par.texts[k-1] = text;
# 	if (k === 1) tgtText = text;
# 	ascii = '';
# 	cell = row.insertCell(-1);
# 	cell.className = 'par';
# 	cell.appendChild(text.elt);
# 	cell.text = text;
#     }
#     this.updateIndices(i+1);
#     return tgtText;
# };
# 
# PlainTextPanel.prototype.appendRow = function () {
#     var i = this.elt.rows.length;
#     return this.insertText('', i);
# };
# 
# PlainTextPanel.prototype.deleteRow = function (i) {
#     this.elt.deleteRow(i);
#     this.updateIndices(i);
# };
# 
# PlainTextPanel.prototype.updateIndices = function (i) {
#     var rows = this.elt.rows;
#     while (i < rows.length) {
# 	var cells = rows[i].cells;
# 	// cell 0 shows the row number
# 	cells[0].firstChild.textContent = i;
# 	for (var k = 1; k < this.ncols; ++k) {
# 	    var cell = cells[k];
# 	    cell.text.i = i;
# 	}
# 	++i;
#     }
# };
# 
# PlainTextPanel.prototype.nextText = function (i, j) {
#     var k = j+1;
#     k += 1;
#     if (k >= this.ncols) {
# 	i += 1;
# 	k = 1;
#     }
#     var rows = this.elt.rows;
#     if (i >= rows.length) return null;
#     return rows[i].cells[k].text;
# };
# 
# PlainTextPanel.prototype.nextRowText = function (i) {
#     i += 1;
#     var rows = this.elt.rows;
#     if (i >= rows.length) return null;
#     return rows[i].cells[1].text;
# };
# 

# class EditableText (Element):
# 
#     def __init__ (self, doc, text, size=None):
#         Element.__init__(self, doc, 'p')
#         self._text = self.write(text)
#         self._box = self.Element('input', type='text', size=size, attach=False)



# doc = Document()
# doc.write('[__main__] Hello, world')
# elt = doc.Element('link', rel='stylesheet', type='text/css', href='default.css')
# 
# div = doc.Div(classname='path')
# div.Text('Test')
# 
# doc.TextArea('test', rows=1)
# doc.br()
# 
# 
# 
# 
# def doit (*args, **kwargs):
#     global div
#     print('[doit]', args, kwargs)
#     div.clear()
#     div.Text('Blah blah blah')
# 
# button = doc.Button(onclick=doit)
# button.Text('Push Me')
# doc.br()
# 
