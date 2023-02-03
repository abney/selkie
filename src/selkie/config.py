
import os, ast
from os.path import expanduser as Filename
from .object import Object

O = Object
F = Filename

__file__ = Filename(os.environ.get('SELKIE_CONFIG') or '~/.selkie')

with open(__file__) as f:
    exec(compile(f.read(), __file__, 'exec'))
