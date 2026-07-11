
from asyncio import ensure_future
from pathlib import Path
from ..corpus import Item, Corpus, Node, Lang, Toc, Text, Sent, Props
from ..wap import Element, EditableCell


class Location:
        
    def __init__ (self, node, item, oldloc):
        self.node = node
        self.item = item
        self.nodes = list(self.get_context(oldloc))
        self.corpus = self.nodes[0]
        self.language = self.nodes[1]
        self.text = self.nodes[2]
        self.sentence = self.nodes[3]
    
    def get_context (self, oldloc):
        lvl = 0
        if self.node is not None:
            for anc in self.node.ancestors():
                yield anc
                lvl += 1
            # if this is not a new node
            if oldloc and oldloc.nodes[lvl-1] == self.node:
                while lvl < 4:
                    yield oldloc.nodes[lvl]
                    lvl += 1
        for _ in range(lvl, 4):
            yield None


class EditorElement (Element):

    def PlainTextPanel (self, text, **kwargs):
        return self.create(PlainTextPanel, text, **kwargs)


class Editor (EditorElement):

    def __init__ (self, server_proxy):
        EditorElement.__init__(self, None, None)
        self.server_proxy = server_proxy
        self.current_view_table = {}
        self.location = None

        # this needs current_view_table to exist already
        self.edit(Root())

    def edit (self, item):
        item = self.update_location(item)
        self.goto_page(item.page)

    def current_view (self, node):
        if node.full_name in self.current_view_table:
            return self.current_view_table[node.full_name]
        else:
            return node.views()[0]

    def set_current_view (self, node, item):
        self.current_view_table[node.full_name] = item

    def update_location (self, item):
        if isinstance(item, Node):
            node = item
            item = self.current_view(node)
        else:
            node = item.node()
        self.location = Location(node, item, self.location)
        node = self.location.node
        if node is not None:
            self.set_current_view(node, self.location.item)
        return item

    def goto_page (self, page):
        self.clear()
        self.create(page)

    def choose_file (self):
        self.goto_page('open')

    def open_corpus (self, fn):
        doc = self.document
        doc.clear()
        doc.write('Opening corpus', fn, '...')
        ensure_future(self._open_corpus(fn))

    async def _open_corpus (self, fn):
        contents = await self.server_proxy.load(fn)
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


class StandardPage (Page):

    def __init__ (self, editor):
        Page.__init__(self, editor)
        self.construct_menu()
        self.construct_title()

    def construct_menu (self):
        editor = self.editor
        loc = editor.location
        menubar = self.document.MenuBar()
        views = []

        if loc.corpus is None:

            menu = menubar.Menu('open')

        else:

            menu = menubar.Menu(loc.corpus.key, editor.edit_corpus)
            menu.MenuItem('+', editor.choose_file)

#            views.append('corp')

            title = 'Langs'
            if loc.language is not None:
                title = loc.language.key
                views.append('lang')
            menu = menubar.Menu(title, editor.edit_language, title)
            for name in loc.corpus.table:
                if name != title:
                    menu.MenuItem(name, editor.edit_language, name)

            title = 'Texts'
            if loc.text is not None:
                title = loc.text.key
                views.append('text')
            menu = menubar.Menu(title, editor.edit_text, title)
            if loc.language:
                for name in loc.language.table:
                    if name != title:
                        menu.MenuItem(name, editor.edit_text, name)

#         view = loc.view
#         menu = menubar.Menu(view)
# 
#         for alt in views:
#             if alt != view:
#                 menu.MenuItem(alt, self.goto_page, alt)

    def construct_title (self):
        editor = self.editor
        loc = editor.location
        if loc.node is None:
            self.H2('Open')
        else:
            node = loc.node
            h2 = self.H2()
            h2.write(node.item_type().capitalize())
            views = node.views()
            if len(views) > 1:
                current = editor.current_view(node)
                h2.write(' : ')
                for view in views:
                    button = h2.Button(view.key, (editor.edit, view))
                    button.style.marginLeft = '5px'
                    if view == current:
                        button.disable()

    def goto_view (self, cls):
        editor = self.editor
        node = editor.location.node
        if isinstance(node, cls):
            item = node
        else:
            item = cls(node)
        editor.edit(item)


class OpenPage (StandardPage):

    def __init__ (self, editor, **kwargs):
        StandardPage.__init__(self, editor, **kwargs)
        div = self.Div()
        self.ul = div.UL()
        li = self.ul.LI()
        li.write('Corpus: ')
        box = li.TextEntry(submit=self.editor.open_corpus)
        box.focus()
        ensure_future(self.list_dir())

    async def list_dir (self):
        text = await self.editor.server_proxy.list_dir()
        lst = [fn for fn in text.split('\n') if fn.endswith('.cld')]
        for fn in lst:
            li = self.ul.LI()
            li.Button(fn, (self.editor.open_corpus, fn))


class CorpusPage (StandardPage):

    def __init__ (self, editor, **kwargs):
        StandardPage.__init__(self, editor, **kwargs)
        corpus = editor.location.corpus
        self.write('Filename: ', corpus.filename())
        p = self.P()
        button = p.Button()
        button.write('Download')
        button.add_listener('click', self.download)

    def download (self, evt):
        corpus = self.editor.location.corpus
        self.download_file(corpus.name, corpus.cld_format())


class PropsPage (StandardPage):

    def __init__ (self, editor, **kwargs):
        StandardPage.__init__(self, editor, **kwargs)
        self.create(PropertyTable, editor.location.item)
        p = self.P()


class TocPage (StandardPage):

    def __init__ (self, editor, **kwargs):
        StandardPage.__init__(self, editor, **kwargs)
        toc = self.toc = editor.location.item
        self._produce_ul(self, toc.roots())

    def _produce_ul (self, parent, texts):
        ul = parent.UL()
        for text in texts:
            li = ul.LI()
            li.Button(text=text.key, action=(self.editor.edit, text))
            children = text.children()
            if children:
                self._produce_ul(li, children)


class TextPage (StandardPage):

    def __init__ (self, editor, **kwargs):
        StandardPage.__init__(self, editor, **kwargs)
        self.PlainTextPanel(editor.location.text)
        

class IGTPage (StandardPage):

    def __init__ (self, editor, **kwargs):
        StandardPage.__init__(self, editor, **kwargs)
        


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


#--  Node updates  -------------------------------------------------------------

class Root (Item):

    page = OpenPage

    def __init__ (self):
        Item.__init__(self, None, 'open')


Corpus.page = CorpusPage
Props.page = PropsPage
Text.page = TextPage
Toc.page = TocPage
