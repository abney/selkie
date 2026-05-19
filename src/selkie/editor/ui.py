
from .config import in_browser

if in_browser:
    import js
    from urllib.parse import urlencode
    from pyodide.ffi import create_proxy
    from pyodide.http import pyfetch
    from .bootstrap import file_contents


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


class Element:

    def __init__ (self, doc, label, **kwargs):
        self._doc = doc
        self._js = doc.createElement(label)            
        self.style = self._js.style

        self._js._python = self

        for (key, value) in kwargs.items():
            if key == 'classname':
                key = 'class'
            self._js.setAttribute(key, str(value))

    def document (self):
        return self._doc

    def __repr__ (self):
        return f'<{self.__class__.__name__} {self._js}>'

    def create (self, cls, *args, attach=True, **kwargs):
        elt = cls(self.document(), *args, **kwargs)
        if attach:
            self.append(elt)
        return elt

    def append (self, elt):
        elt.parent = self
        self._js.appendChild(elt._js)

    def Element (self, label, **kwargs):
        return self.create(Element, label, **kwargs)

    def write (self, s, **kwargs):
        return self.create(TextNode, s, **kwargs)

    def add_listener (self, name, action):
        self._js.addEventListener(name, create_proxy(action))

    def Button (self, text=None, type='button', name=None, value=None, onclick=None, attach=True):
        button = self.Element('button', type=type, name=name, value=value, attach=attach)
        if text is not None:
            button.write(text)
        if onclick is not None:
            button.add_listener('click', onclick)
        return button

    def focus (self):
        self._js.focus()

    def Table (self, classname='display', attach=True):
        return self.Element('table', classname=classname, attach=attach)

    def Row (self, attach=True):
        return self.Element('tr', attach=attach)

    def TD (self, attach=True):
        return self.Element('td', attach=attach)

    def TH (self, attach=True):
        return self.Element('th', attach=attach)

    def TextArea (self, init=None, rows=None, cols=None, attach=True):
        elt = self.Element('textarea', rows=rows, cols=cols, attach=attach)
        if init is not None:
            elt._js.value = str(init)
        return elt
    
    def TextBox (self, init=None, size=None, attach=True):
        elt = self.Element('input', type='text', size=size, attach=attach)
        if init is not None:
            elt._js.value = str(init)
        return elt

    def EditableText (self, text, **kwargs):
        return self.create(EditableText, text, **kwargs)

    def PlainTextPanel (self, text, **kwargs):
        return self.create(PlainTextPanel, text, **kwargs)

    def br (self, attach=True):
        return self.Element('br', attach=attach)

    def Div (self, classname=None, attach=True):
        return self.Element('div', classname=classname, attach=attach)

    def clear (self):
        self._js.replaceChildren()

    def delete (self):
        self._js.remove()

    def addEventListener (self, name, f):
        self._js.addEventListener(name, create_proxy(f))

    def value (self):
        return self._js.value


class Document (Element):

    def __init__ (self):
        self._js = js.document.getElementById("root")
        self.createTextNode = js.document.createTextNode
        self.createElement = js.document.createElement
        #js.document.addEventListener('visibilitychange', create_proxy(self._visibility_change))

    def write (self, *objs):
        s = ' '.join(str(x) for x in objs)
        self._js.appendChild(self.createTextNode(s))
        self._js.appendChild(self.createElement('BR'))

    async def _visibility_change (self, evt):
        if js.document.hidden:
            await self.close()

    async def __del__ (self):
        self.close()

    async def close (self):
        print('Closing')
        self.write('Closing')
        self.write(await file_contents('call/close'))

    def document (self):
        return self
        

#--  PlainTextPanel  -----------------------------------------------------------

class PlainTextPanel (Element):

    def __init__ (self, doc, text):
        Element.__init__(self, doc, 'div')
        self.text = text
        self.table = self.Table(classname='grid')
        for (idx, sent) in enumerate(text):
            row = self.table.Row()
            cell = row.TD()
            cell.write(sent.meta['w'])
            cell.add_listener('click', self.on_cell_click)
            cell.idx = idx
            cell.sent = sent
            cell.box = None

    def on_cell_click (self, evt):
        cell = evt.target._python
        if cell.box is None:
            width = cell._js.getBoundingClientRect().width
            cell.clear()
            self.box = box = cell.TextArea(init=cell.sent.string())
            box._js.style.width = f'{width}px'
            box.focus()

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

class EditableText (Element):

    def __init__ (self, doc, text, size=None):
        Element.__init__(self, doc, 'p')
        self._text = self.write(text)
        self._box = self.Element('input', type='text', size=size, attach=False)


class TextNode:

    def __init__ (self, doc, s):
        self._js = doc.createTextNode(s)


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
