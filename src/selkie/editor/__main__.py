from .app import WapApplication
from .editor import Editor


class Application (WapApplication):

    def __init__ (self):
        WapApplication.__init__(self, 'selkie.editor.__main__')

    async def ui (self):
        Editor()


if __name__ == '__main__':
    Application().start()
