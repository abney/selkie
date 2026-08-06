from ..wap import exec_app
from .editor import Editor

# not usually wrapped, in a __main__.py file, but I do an import test,
# and I don't want it running automatically on import

if __name__ == '__main__':
    exec_app(Editor)
