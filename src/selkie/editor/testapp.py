
from .app import WapApplication
from .bootstrap import write, get_text
from .ui import Document
from ..corpus import Corpus


class Application (WapApplication):

    def __init__ (self):
        WapApplication.__init__(self, 'selkie.editor.testapp')

        print('Instantating Application')
        print('  module_name         :', repr(self.module_name))
        print('  toplevel_module     :', repr(self.toplevel_module))
        print('  name                :', repr(self.name))
        print('  document_dir        :', self.document_dir)
        print('  document_source_dir :', self.document_source_dir)

    async def ui (self):
        write('Testapp: Hello, world!')
        doc = self.document = Document()
        doc.write('doc created')

        elt = doc.Element('link', rel='stylesheet', type='text/css', href='stylesheet.css')
        div = self.div = doc.Div(classname='path')
        div.write('Test')

        self.textbox = doc.TextBox('type here')
        self.textbox.addEventListener('keypress', self.handle_keypress)

        doc.TextArea('test', rows=1)
        doc.br()

        button = doc.Button(onclick=self.doit)
        button.write('Push Me')
        doc.br()

        doc.EditableText('editable')

        button = doc.Button(onclick=self.handle_quit)
        button.write('Quit')
        doc.br()

        try:
            import pyodide_js
            await pyodide_js.loadPackage('micropip')
            write('Installed micropip')

            import micropip
            write('Imported micropip')

            await micropip.install('numpy')
            write('Installed numpy')
            import numpy as np
            write('Imported numpy')

            await micropip.install('matplotlib')
            await micropip.install('matplotlib-inline')
            import matplotlib
            write('Imported matplotlib')

            import matplotlib.pyplot as plt
            x = np.linspace(0, 3*np.pi, 500)
            plt.plot(x, np.sin(x**2))
            plt.title('A simple chirp')
            plt.show()

            write('Post-plot')

            contents = await get_text('example.cld')
            corpus = Corpus(contents=contents)
            write('corpus', list(corpus))

            text = corpus.language('deu').text('2')
            write('text', list(text))

            doc.PlainTextPanel(text)

        except Exception as e:
            write('Exception', str(e))

    def doit (self, *args, **kwargs):
        print('[doit]', args, kwargs)
        div = self.div
        div.clear()
        div.write('Blah blah blah')

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
