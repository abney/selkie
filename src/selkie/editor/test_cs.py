
print('browser.py: load, file=', __file__)

from .doc import BaseClientSide
import selkie


class ClientSide (BaseClientSide):

    def __init__ (self):
        print('Init Test v3')
        BaseClientSide.__init__(self)
        self.goto_temp_page()

    def goto_temp_page (self):
        page = self.page
        page.clear()
        page.write('[__init__] Selkie version =', selkie.__version__)
        page.write('[__init__] Selkie file    =', selkie.__file__)
        page.Button('Continue', onclick=self.goto_front_page)
        return page

    def goto_front_page (self, evt):
        page = self.page
        page.clear()

        self.path = path = page.Div(classname='path')
        path.Text('Test')

        page.TextArea('test', rows=1)
        page.br()

        page.Button('Push Me', onclick=self.doit)
        page.br()

        page.Button('Red', onclick=self.make_red)
        page.br()

        page.Button('Call', onclick=self.server_test)

    def doit (self, evt):
        self.path.clear()
        self.path.Text('Blah blah blah')

    def make_red (self, evt):
        self.path.style.backgroundColor = 'red'

    async def server_test (self, evt):
        text = await self.server_call({'msg': 'foo'})
        self.path.Text(text)
