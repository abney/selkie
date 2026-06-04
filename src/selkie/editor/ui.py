
from asyncio import ensure_future
from types import NoneType
from .config import in_browser
from ..corpus.corpus import Corpus, CorpusLocation, Language, Text, Sentence

if in_browser:
    import js
    from urllib.parse import urlencode
    from pyodide.ffi import create_proxy
    from pyodide.http import pyfetch
    from .bootstrap import server


# class Application:
# 
#     def __init__ (self):
#         self.page = Document()
# 
#     # json in and json out
# 
#     async def server_call (self, msg):
#         resp = await pyfetch(f'http://localhost:8000/fetch/{urlencode(msg)}')
#         if not (resp.ok and resp.status == 200):
#             raise Exception(f'Server call error {resp.status}')
#         data = await resp.json()
#         return data


#--  Element  ------------------------------------------------------------------

class Element:

    def __init__ (self, parent, label, **kwargs):
        if parent is None:
            self.parent = None
            self.document = Document()
            self._js = self.document._js
        else:
            self.parent = parent
            self.document = parent.document
            self._js = self.document.createElement(label)            
            self.style = self._js.style

            self._js._python = self
            for (key, value) in kwargs.items():
                if key == 'classname':
                    key = 'class'
                self._js.setAttribute(key, str(value))

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self._js}>'

    def create (self, cls, *args, attach=True, **kwargs):
        elt = cls(self, *args, **kwargs)
        if attach:
            self.append(elt)
        return elt

    def set_attribute (self, key, value):
        self._js.setAttribute(key, value)

    def append (self, elt):
        elt.parent = self
        self._js.appendChild(elt._js)

    def write (self, *objs, end='\n'):
        doc = self.document
        s = ' '.join(str(x) for x in objs)
        self._js.appendChild(doc.createTextNode(s))

    def br (self, attach=True):
        self._js.appendChild(self.document.createElement('br'))

    def add_listener (self, name, action):
        self._js.addEventListener(name, create_proxy(action))

    def focus (self):
        self._js.focus()

    def clear (self):
        self._js.replaceChildren()

    def replace_children (self, *newchildren):
        newjschildren = [newchild._js for newchild in newchildren]
        self._js.replaceChildren(*newjschildren)
        for newchild in newchildren:
            newchild.parent = self

    def delete (self):
        self._js.remove()

    def value (self):
        return self._js.value

    def Element (self, label, **kwargs):
        return self.create(Element, label, **kwargs)

    def Button (self, text=None, type='button', name=None, value=None, onclick=None, attach=True):
        button = self.Element('button', type=type, name=name, value=value, attach=attach)
        if text is not None:
            button.write(text)
        if onclick is not None:
            button.add_listener('click', onclick)
        return button

    def Table (self, classname='display', **kwargs):
        return self.Element('table', classname=classname, **kwargs)

    def Row (self, **kwargs):
        return self.Element('tr', **kwargs)

    def TD (self, **kwargs):
        return self.Element('td', **kwargs)

    def TH (self, **kwargs):
        return self.Element('th', **kwargs)

    def TextEntry (self, **kwargs):
        return self.create(TextEntry, **kwargs)

    def Div (self, classname=None, attach=True):
        return self.Element('div', classname=classname, attach=attach)

    def _heading (self, label, string=None, **kwargs):
        elt = self.Element(label, **kwargs)
        if string:
            elt.write(string)
        return elt

    def H1 (self, string=None, **kwargs):
        return self._heading('h1', string, **kwargs)

    def H2 (self, string=None, **kwargs):
        return self._heading('h2', string, **kwargs)

    def H3 (self, string=None, **kwargs):
        return self._heading('h3', string, **kwargs)

    def H4 (self, string=None, **kwargs):
        return self._heading('h4', string, **kwargs)

    def PlainTextPanel (self, text, **kwargs):
        return self.create(PlainTextPanel, text, **kwargs)

    def MenuBar (self, **kwargs):
        return self.create(MenuBar, **kwargs)


class Document (Element):

    def __init__ (self):
        self._js = js.document.getElementsByTagName('body')[0]
        self.document = self
        self.createTextNode = js.document.createTextNode
        self.createElement = js.document.createElement
        #js.document.addEventListener('visibilitychange', create_proxy(self._visibility_change))

    def write (self, *objs):
        s = ' '.join(str(x) for x in objs)
        self._js.appendChild(self.createTextNode(s))

    async def _visibility_change (self, evt):
        if js.document.hidden:
            await self.close()

    async def __del__ (self):
        self.close()

    async def close (self):
        print('Closing')
        server.close()


#--  EditableCell  -------------------------------------------------------------

class TextEntry (Element):

    def __init__ (self, parent, rows=1, init=None, submit=None, **kwargs):
        if rows == 1:
            label = 'input'
            kwargs['type'] = 'text'
        else:
            label = 'textarea'
            kwargs['rows'] = rows

        Element.__init__(self, parent, label, **kwargs)
        self.submit = submit

        if init is not None:
            self._js.value = str(init)
        if submit is not None:
            self.add_listener('keypress', self.on_keypress)

    def on_keypress (self, evt):
        if evt.key != 'Enter':
            return True
        else:
            self.submit(self._js.value)


class EditableCell (Element):

    def __init__ (self, parent, getvalue, setvalue, **kwargs):
        Element.__init__(self, parent, 'td', **kwargs)

        self.getvalue = getvalue
        self.setvalue = setvalue
        self.box = None

        self.add_listener('click', self.on_click)
        self.view()

    def view (self):
        if self.box is not None:
            self.clear()
            self.box = None
        self.write(self.getvalue())

    def edit (self):
        if self.box is None:
            width = self._js.getBoundingClientRect().width
            self.clear()
            self.box = box = self.TextEntry(init=self.getvalue(), rows=3, submit=self.done)
            box.style.width = f'{width}px'
            box.focus()
            box.add_listener('blur', self.on_blur)

    def done (self, newstring):
        self.setvalue(newstring)
        self.view()

    def on_click (self, evt):
        self.edit()

    def on_blur (self, evt):
        self.view()


class SentenceCell (EditableCell):

    def __init__ (self, parent, sent, **kwargs):
        EditableCell.__init__(self, parent, sent.string, sent.set_string, **kwargs)


# class PlainTextCell (Element):
# 
#     def __init__ (self, parent, sent, **kwargs):
#         Element.__init__(self, parent, 'td', **kwargs)
#         assert isinstance(sent, Sentence)
# 
#         self.sent = sent
#         self.box = None
#         self.add_listener('click', self.on_click)
#         self.view()
# 
#     def view (self):
#         if self.box is not None:
#             self.clear()
#             self.box = None
#         self.write(self.sent.string())
# 
#     def edit (self):
#         if self.box is None:
#             width = self._js.getBoundingClientRect().width
#             self.clear()
#             self.box = box = self.TextEntry(init=self.sent.string(), rows=3, submit=self.done)
#             box.style.width = f'{width}px'
#             box.focus()
#             box.add_listener('blur', self.on_blur)
# 
#     def done (self, newstring):
#         self.sent.set_string(newstring)
#         self.view()
# 
#     def on_click (self, evt):
#         self.edit()
# 
#     def on_blur (self, evt):
#         self.view()


class PlainTextPanel (Element):

    def __init__ (self, parent, text):
        Element.__init__(self, parent, 'div')
        assert isinstance(text, Text)
        self.text = text
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
    

class PropertyTable (Element):

    def __init__ (self, parent, meta):
        Element.__init__(self, parent, 'table', classname='noborder')
        self.meta = meta

        for (key, value) in self.meta.items():
            if not isinstance(value, dict):
                row = self.Row()
                cell = row.TD()
                cell.write(key)
                row.create(PropertyCell, self.meta, key)


#--  Menu bar  -----------------------------------------------------------------

class MenuBar (Element):

    def __init__ (self, parent, **kwargs):
        Element.__init__(self, parent, 'nav', **kwargs)

        self.bar = self.Element('ul', classname='menu-bar')

    def Menu (self, title):
        return self.bar.create(Menu, title)


class Menu (Element):

    def __init__ (self, parent, title, **kwargs):
        kwargs['classname'] = 'dropdown-menu'
        Element.__init__(self, parent, 'li', **kwargs)
        a = self.Element('a')
        a.write(title)
        self.items = self.Element('ul', classname='dropdown-items')

    def MenuItem (self, string, action, *args):
        return self.items.create(MenuItem, string, action, *args)


class MenuItem (Element):

    def __init__ (self, parent, string, action, *args):
        Element.__init__(self, parent, 'li')
        self.string = string
        self.action = action
        self.args = args

        a = self.Element('a')
        a.write(string)
        if action is None:
            a.set_attribute('class', 'disabled');
            print('a', string, 'disabled')
        else:
            a.add_listener('click', self.on_click)

    def on_click (self, _):
        self.action(*self.args)


#--  Editor  -------------------------------------------------------------------

class Editor (Element):

    def __init__ (self):
        Element.__init__(self, None, None)
        self.document = Document()
        self.location = CorpusLocation()
        self.location.view = 'open'
        self.viewers = {
            'open': OpenPage,
            'corpus': CorpusPage,
            'lang': LanguagePage,
            'text': TextPage
        }

        self.goto_page('open')

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

    def construct_menu (self):
        loc = self.location
        menubar = self.document.MenuBar()

        menu = menubar.Menu('File')
        menu.MenuItem('Open', self.choose_file)
        menu.MenuItem('Corpus', None if loc.corpus is None else self.edit_corpus)
        print('loc.corpus=', loc.corpus)

        if loc.corpus:

            title = 'Langs' if loc.language is None else loc.language.key
            menu = menubar.Menu(title)
            for name in loc.corpus.table:
                if name != title:
                    menu.MenuItem(name, self.edit_language, name)

            title = 'Texts' if loc.text is None else loc.text.key 
            menu = menubar.Menu(title)
            if loc.language:
                for name in loc.language.table:
                    if name != title:
                        menu.MenuItem(name, self.edit_text, name)

        

    def choose_file (self):
        self.goto_page('open')

    def open_corpus (self, fn):
        doc = self.document
        doc.clear()
        doc.write('Opening corpus', fn, '...')
        ensure_future(self._open_corpus(fn))

    async def _open_corpus (self, fn):
        print('Enter _open_corpus', fn)
        contents = await server.load(fn)
        print('Got contents')
        self.edit(Corpus(fn, contents=contents))

    def edit (self, item):
        loc = self.location = item.location()
        view = loc.view or item.key_type()
        self.goto_page(view)

    def edit_corpus (self):
        self.edit(self.location.corpus)

    def edit_language (self, name):
        lang = self.location.corpus.table[name]
        self.edit(lang)

    def edit_text (self, name):
        text = self.location.language.table[name]
        self.edit(text)
        
    

        
#--  Pages  --------------------------------------------------------------------

class Page (Element):

    def __init__ (self, editor, **kwargs):
        Element.__init__(self, editor, 'div', **kwargs)
        self.editor = editor


class OpenPage (Page):

    def __init__ (self, editor, **kwargs):
        Page.__init__(self, editor, **kwargs)
        self.write('Corpus: ')
        box = self.TextEntry(submit=self.editor.open_corpus)
        box.focus()


class CorpusPage (Page):

    def __init__ (self, editor, **kwargs):
        Page.__init__(self, editor, **kwargs)
        corpus = editor.location.corpus
        self.H2('Corpus')
        self.write('Filename: ', corpus.filename())


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
