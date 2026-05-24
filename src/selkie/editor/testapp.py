
from .app import WapApplication
from .bootstrap import server
from .ui import Document, Editor
from ..corpus import Corpus


class Application (WapApplication):

    def __init__ (self):
        WapApplication.__init__(self, 'selkie.editor.testapp')

        print('Application')
        print('  module_name         :', repr(self.module_name))
        print('  toplevel_module     :', repr(self.toplevel_module))
        print('  name                :', repr(self.name))
        print('  document_dir        :', self.document_dir)
        print('  document_source_dir :', self.document_source_dir)

    async def ui (self):
        print('Enter ui')

        doc = self.document = Document()
        doc.write('doc created')

        # menubar = doc.MenuBar([['Home', 'Contact'], ['File', 'Open', 'Save']])

        elt = doc.Element('link', rel='stylesheet', type='text/css', href='stylesheet.css')
        div = self.div = doc.Div(classname='path')
        div.write('Test')

        # self.textbox = doc.TextBox('type here')
        # self.textbox.add_listener('keypress', self.handle_keypress)

        # doc.TextArea('test', rows=1)
        # doc.br()

        button = doc.Button(onclick=self.doit)
        button.write('Push Me')
        doc.br()

        button = doc.Button(onclick=self.handle_quit)
        button.write('Quit')
        doc.br()

        try:
            import pyodide_js
            await pyodide_js.loadPackage('micropip')
            print('Installed micropip')

            import micropip
            print('Imported micropip')

            await micropip.install('numpy')
            print('Installed numpy')
            import numpy as np
            print('Imported numpy')

            await micropip.install('matplotlib')
            await micropip.install('matplotlib-inline')
            import matplotlib
            print('Imported matplotlib')

            import matplotlib.pyplot as plt
            x = np.linspace(0, 3*np.pi, 500)
            plt.plot(x, np.sin(x**2))
            plt.title('A simple chirp')
            plt.show()

            print('Post-plot')

            contents = await server.load('example.cld')
            corpus = Corpus(contents=contents)
            print('corpus', list(corpus))

            text = corpus.language('deu').text('2')
            print('text', list(text))

            doc.PlainTextPanel(text)

        except Exception as e:
            print('Exception', str(e))

    def old_doit (self, *args, **kwargs):
        print('[doit]', args, kwargs)
        div = self.div
        div.clear()
        div.write('Blah blah blah')

    def doit (self, evt):
        Editor()

    def handle_keypress (self, event):
        if event.key == 'Enter':
            self.document.write(self.textbox.value())
            return False
        else:
            return True

    def handle_quit (self, evt):
        self.quit()


if __name__ == '__main__':
    Application().start()
