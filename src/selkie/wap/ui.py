
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

        for (key, value) in kwargs.items():
            if key == 'classname':
                key = 'class'
            self._js.setAttribute(key, str(value))

    def document (self):
        return self._doc

    def create (self, cls, *args, attach=True, **kwargs):
        elt = cls(self.document(), *args, **kwargs)
        if attach:
            self.append(elt)
        return elt

    def append (self, elt):
        self._js.appendChild(elt._js)

    def Element (self, label, **kwargs):
        return self.create(Element, label, **kwargs)

    def Text (self, s, **kwargs):
        return self.create(TextNode, s, **kwargs)

    def Button (self, text=None, type='button', name=None, value=None, onclick=None, attach=True):
        button = self.Element('button', type=type, name=name, value=value, attach=attach)
        if text is not None:
            button.Text(text)
        if onclick is not None:
            button._js.addEventListener('click', create_proxy(onclick))
        return button

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
        

class EditableText (Element):

    def __init__ (self, doc, text, size=None):
        Element.__init__(self, doc, 'p')
        self._text = self.Text(text)
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
