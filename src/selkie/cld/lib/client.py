
from collections.abc import MutableMapping

try:
 
    import js
    from js import XMLHttpRequest
    from pyodide.ffi import create_proxy


    class Element (object):

        def __init__ (self, doc, label):
            self._doc = doc
            self._js = doc.createElement(label)            

        def document (self):
            return self._doc

        def _create (self, cls, arg, atts):
            elt = cls(self.document(), arg)
            self._js.appendChild(elt._js)
            for (key, value) in atts.items():
                if key == 'classname':
                    key = 'class'
                elt._js.setAttribute(key, str(value))
            return elt

        def Element (self, label, **kwargs):
            return self._create(Element, label, kwargs)

        def Text (self, s, **kwargs):
            return self._create(TextNode, s, kwargs)

        def Button (self, type='button', name=None, value=None, onclick=None):
            button = self.Element('button', type=type, name=name, value=value)
            if onclick is not None:
                button._js.addEventListener('click', create_proxy(onclick))
            return button

        def TextArea (self, init=None, rows=None, cols=None):
            elt = self.Element('textarea', rows=rows, cols=cols)
            if init is not None:
                elt._js.value = str(init)
            return elt
        
        def br (self):
            return self.Element('br')

        def Div (self, classname=None):
            return self.Element('div', classname=classname)

        def clear (self):
            self._js.replaceChildren()

            
    class TextNode (object):

        def __init__ (self, doc, s):
            self._js = doc.createTextNode(s)


    class Document (Element):

        def __init__ (self):
            self._js = js.document.getElementById("root")
            self.createTextNode = js.document.createTextNode
            self.createElement = js.document.createElement

        def write (self, *objs):
            s = ' '.join(str(x) for x in objs)
            self._js.appendChild(self.createTextNode(s))
            self._js.appendChild(self.createElement('BR'))

        def document (self):
            return self
            

    doc = Document()
    doc.write('[__main__] Hello, world')
    elt = doc.Element('link', rel='stylesheet', type='text/css', href='.lib/default.css')

    div = doc.Div(classname='path')
    div.Text('Test')

    doc.TextArea('test', rows=1)
    doc.br()

    def doit (*args, **kwargs):
        global div
        print('[doit]', args, kwargs)
        div.clear()
        div.Text('Blah blah blah')

    button = doc.Button(onclick=doit)
    button.Text('Push Me')
    doc.br()

#     res = await pyfetch('langs')
#     print('res.status=', res)
#     if res.status == 200:
#         text = await res.text()
#         print('text=', repr(text))

    class HttpDisk (MutableMapping):

        def __init__ (self, root):
            self.root = root

        def iterdirectory (self, dname):
            raise Exception('Not implemented')

        def __iter__ (self):
            raise Exception('Not implemented')

        def __contains__ (self, name):
            raise Exception('Not implemented')

        def mkdir (self, name):
            raise Exception('Not implemented')

        def __getitem__ (self, name):
            if self.root:
                name = self.root + '/' + name
            req = XMLHttpRequest.new()
            req.open('GET', f'http://localhost:8000/{name}', False)
            req.send()
            return str(req.response)

        def __setitem__ (self, fn, lines):
            raise Exception('Not implemented')

        def __delitem__ (self, fn):
            raise Exception('Not implemented')

        def __len__ (self):
            return sum(1 for _ in self.__iter__())

        def keys (self):
            return self.__iter__()

        def items (self):
            for key in self.__iter__():
                yield (key, self.__getitem__(key))

        def values (self):
            for key in self.__iter__():
                yield self.__getitem__(key)


    disk = HttpDisk('')
    print("disk['langs'] =", repr(disk['langs']))


except Exception as e:
    pass
