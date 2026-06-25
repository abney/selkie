
from .config import in_browser

if in_browser:
    import js
    from urllib.parse import urlencode
    from pyodide.ffi import create_proxy
    from pyodide.http import pyfetch
    from .bootstrap import server_proxy


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

    def __init__ (self, parent=None, label=None, **kwargs):
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
        global server_proxy
        print('Closing')
        server_proxy.close()


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


#--  Menu bar  -----------------------------------------------------------------

class MenuBar (Element):

    def __init__ (self, parent, **kwargs):
        Element.__init__(self, parent, 'nav', **kwargs)

        self.bar = self.Element('ul', classname='menu-bar')

    def Menu (self, title, action=None, *args):
        return self.bar.create(Menu, title, action, *args)


class Menu (Element):

    def __init__ (self, parent, title, action=None, *args, **kwargs):
        kwargs['classname'] = 'dropdown-menu'
        Element.__init__(self, parent, 'li', **kwargs)
        self.name = title
        self.action = action
        self.args = args

        a = self.Element('a')
        a.write(title)
        if action:
            a.add_listener('click', self.on_click)
        self.items = self.Element('ul', classname='dropdown-items')

    def on_click (self, _):
        self.action(*self.args)

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

